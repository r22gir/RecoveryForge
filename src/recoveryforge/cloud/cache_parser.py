"""
Cloud service cache parser.

Detects installed cloud sync clients and parses their local caches
to recover file metadata and content for Google Drive, OneDrive,
Dropbox, and iCloud.
"""

import logging
import os
import platform
import re
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass, field


logger = logging.getLogger(__name__)

# Allowlists for each service's known table names
_GDRIVE_TABLES = frozenset(("local_entry", "entry", "file_entry"))
_ONEDRIVE_TABLES = frozenset(("SyncTokenData", "LocalItem", "Item", "items"))
_DROPBOX_TABLES = frozenset(("file_journal", "block_cache", "filecache"))

_SAFE_IDENTIFIER_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')


def _safe_table_name(name: str, allowlist: frozenset) -> str:
    """
    Validate *name* against an allowlist and safe identifier pattern.

    Raises ValueError if the name is not acceptable.
    """
    if name not in allowlist:
        raise ValueError(f"Table name '{name}' is not in the allowlist.")
    if not _SAFE_IDENTIFIER_RE.match(name):
        raise ValueError(f"Table name '{name}' contains unsafe characters.")
    return name


@dataclass
class CloudFile:
    """A file recovered from a cloud service cache."""
    name: str
    local_path: str
    cloud_path: str = ""
    size: int = 0
    modified_time: str = ""
    service: str = ""
    checksum: str = ""
    is_deleted: bool = False


@dataclass
class CloudApp:
    """Detected cloud synchronisation application."""
    name: str
    service: str
    config_path: str
    is_available: bool = True


def _home() -> Path:
    """Return the current user's home directory."""
    return Path.home()


def _platform() -> str:
    return platform.system()


class CloudCacheParser:
    """
    Parse local caches of cloud sync clients to discover recoverable files.

    Supports Google Drive (Drive for Desktop), OneDrive, Dropbox, and iCloud.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    # ------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------

    def detect_cloud_apps(self) -> List[CloudApp]:
        """
        Detect installed cloud sync applications.

        Returns:
            List of CloudApp objects for each detected application.
        """
        apps: List[CloudApp] = []
        system = _platform()
        home = _home()

        candidates: List[tuple] = []

        if system == "Windows":
            candidates = [
                ("Google Drive", "google_drive",
                 home / "AppData" / "Local" / "Google" / "DriveFS"),
                ("OneDrive", "onedrive",
                 home / "AppData" / "Local" / "Microsoft" / "OneDrive"),
                ("Dropbox", "dropbox",
                 home / "AppData" / "Local" / "Dropbox"),
            ]
        elif system == "Darwin":
            candidates = [
                ("Google Drive", "google_drive",
                 home / "Library" / "Application Support" / "Google" / "DriveFS"),
                ("OneDrive", "onedrive",
                 home / "Library" / "CloudStorage" / "OneDrive-Personal"),
                ("Dropbox", "dropbox",
                 home / "Library" / "Application Support" / "Dropbox"),
                ("iCloud", "icloud",
                 home / "Library" / "Mobile Documents"),
            ]
        else:  # Linux / unknown
            candidates = [
                ("Google Drive", "google_drive",
                 home / ".local" / "share" / "google-drive"),
                ("Dropbox", "dropbox",
                 home / ".dropbox"),
            ]

        for name, service, config_path in candidates:
            apps.append(CloudApp(
                name=name,
                service=service,
                config_path=str(config_path),
                is_available=config_path.exists(),
            ))

        return apps

    # ------------------------------------------------------------------
    # Service-specific parsers
    # ------------------------------------------------------------------

    def parse_google_drive(self, cache_path: str) -> List[CloudFile]:
        """
        Parse a Google Drive for Desktop cache directory.

        Args:
            cache_path: Path to the Google Drive cache root.

        Returns:
            List of CloudFile objects discovered in the cache.
        """
        files: List[CloudFile] = []
        root = Path(cache_path)
        if not root.exists():
            self.logger.warning(f"Google Drive cache not found: {cache_path}")
            return files

        # Drive for Desktop stores a metadata SQLite DB
        for db_path in root.rglob("metadata_sqlite_db"):
            try:
                files.extend(self._parse_gdrive_db(str(db_path)))
            except Exception as e:
                self.logger.error(f"Error parsing GDrive DB {db_path}: {e}")

        # Fall back to filesystem scan
        if not files:
            files = self._scan_directory(cache_path, "google_drive")

        return files

    def parse_onedrive(self, cache_path: str) -> List[CloudFile]:
        """
        Parse an OneDrive cache directory.

        Args:
            cache_path: Path to the OneDrive cache root.

        Returns:
            List of CloudFile objects.
        """
        files: List[CloudFile] = []
        root = Path(cache_path)
        if not root.exists():
            self.logger.warning(f"OneDrive cache not found: {cache_path}")
            return files

        # OneDrive stores a SQLite database
        for db_path in root.rglob("*.db"):
            try:
                files.extend(self._parse_onedrive_db(str(db_path)))
            except Exception as e:
                self.logger.debug(f"Skipping OneDrive DB {db_path}: {e}")

        if not files:
            files = self._scan_directory(cache_path, "onedrive")

        return files

    def parse_dropbox(self, cache_path: str) -> List[CloudFile]:
        """
        Parse a Dropbox cache directory.

        Args:
            cache_path: Path to the Dropbox config root
                        (e.g. ~/.dropbox or AppData/Local/Dropbox).

        Returns:
            List of CloudFile objects.
        """
        files: List[CloudFile] = []
        root = Path(cache_path)
        if not root.exists():
            self.logger.warning(f"Dropbox cache not found: {cache_path}")
            return files

        # Dropbox stores filecache.dbx (SQLite)
        for db_path in root.rglob("filecache.dbx"):
            try:
                files.extend(self._parse_dropbox_db(str(db_path)))
            except Exception as e:
                self.logger.debug(f"Skipping Dropbox DB {db_path}: {e}")

        if not files:
            files = self._scan_directory(cache_path, "dropbox")

        return files

    def parse_icloud(self, cache_path: str) -> List[CloudFile]:
        """
        Parse an iCloud local cache (macOS).

        Args:
            cache_path: Path to the iCloud Mobile Documents directory.

        Returns:
            List of CloudFile objects.
        """
        return self._scan_directory(cache_path, "icloud")

    # ------------------------------------------------------------------
    # Path reconstruction
    # ------------------------------------------------------------------

    def reconstruct_paths(
        self, cloud_files: List[CloudFile]
    ) -> Dict[str, str]:
        """
        Reconstruct original cloud paths for a list of files.

        Args:
            cloud_files: List of CloudFile objects.

        Returns:
            Dictionary mapping local_path -> reconstructed cloud_path.
        """
        mapping: Dict[str, str] = {}
        for cf in cloud_files:
            mapping[cf.local_path] = cf.cloud_path or cf.local_path
        return mapping

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _scan_directory(self, root_path: str, service: str) -> List[CloudFile]:
        """Generic filesystem scan fallback."""
        files: List[CloudFile] = []
        root = Path(root_path)
        if not root.exists():
            return files
        try:
            for entry in root.rglob("*"):
                if entry.is_file():
                    stat = entry.stat()
                    files.append(CloudFile(
                        name=entry.name,
                        local_path=str(entry),
                        cloud_path="/" + str(entry.relative_to(root)).replace("\\", "/"),
                        size=stat.st_size,
                        service=service,
                    ))
        except PermissionError as e:
            self.logger.warning(f"Permission denied scanning {root_path}: {e}")
        except Exception as e:
            self.logger.error(f"Error scanning {root_path}: {e}")
        return files

    def _parse_gdrive_db(self, db_path: str) -> List[CloudFile]:
        """Parse a Google Drive for Desktop SQLite metadata database."""
        files: List[CloudFile] = []
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.cursor()
            # Try common schema; exact column names vary by Drive version
            for table_candidate in ("local_entry", "entry", "file_entry"):
                try:
                    table = _safe_table_name(table_candidate, _GDRIVE_TABLES)
                    cursor.execute(f"SELECT * FROM {table} LIMIT 0")
                    cols = [d[0].lower() for d in cursor.description]
                    name_col = next((c for c in cols if "name" in c), None)
                    path_col = next((c for c in cols if "path" in c or "local" in c), None)
                    if not name_col:
                        continue
                    cursor.execute(f"SELECT * FROM {table}")
                    for row in cursor.fetchall():
                        row_dict = dict(zip(cols, row))
                        name = str(row_dict.get(name_col, ""))
                        local_path = str(row_dict.get(path_col or name_col, ""))
                        files.append(CloudFile(
                            name=name,
                            local_path=local_path,
                            cloud_path="/" + name,
                            service="google_drive",
                        ))
                    break
                except (sqlite3.OperationalError, ValueError):
                    continue
        finally:
            conn.close()
        return files

    def _parse_onedrive_db(self, db_path: str) -> List[CloudFile]:
        """Parse a OneDrive SQLite database."""
        files: List[CloudFile] = []
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.cursor()
            for table_candidate in ("SyncTokenData", "LocalItem", "Item", "items"):
                try:
                    table = _safe_table_name(table_candidate, _ONEDRIVE_TABLES)
                    cursor.execute(f"SELECT * FROM {table} LIMIT 0")
                    cols = [d[0].lower() for d in cursor.description]
                    name_col = next((c for c in cols if "name" in c or "filename" in c), None)
                    if not name_col:
                        continue
                    path_col = next((c for c in cols if "path" in c or "local" in c), None)
                    cursor.execute(f"SELECT * FROM {table}")
                    for row in cursor.fetchall():
                        row_dict = dict(zip(cols, row))
                        name = str(row_dict.get(name_col, ""))
                        local = str(row_dict.get(path_col or name_col, ""))
                        files.append(CloudFile(
                            name=name,
                            local_path=local,
                            cloud_path="/" + name,
                            service="onedrive",
                        ))
                    break
                except (sqlite3.OperationalError, ValueError):
                    continue
        finally:
            conn.close()
        return files

    def _parse_dropbox_db(self, db_path: str) -> List[CloudFile]:
        """Parse a Dropbox filecache SQLite database."""
        files: List[CloudFile] = []
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.cursor()
            for table_candidate in ("file_journal", "block_cache", "filecache"):
                try:
                    table = _safe_table_name(table_candidate, _DROPBOX_TABLES)
                    cursor.execute(f"SELECT * FROM {table} LIMIT 0")
                    cols = [d[0].lower() for d in cursor.description]
                    path_col = next((c for c in cols if "path" in c or "local_path" in c), None)
                    if not path_col:
                        continue
                    cursor.execute(f"SELECT * FROM {table}")
                    for row in cursor.fetchall():
                        row_dict = dict(zip(cols, row))
                        local_path = str(row_dict.get(path_col, ""))
                        name = Path(local_path).name if local_path else ""
                        files.append(CloudFile(
                            name=name,
                            local_path=local_path,
                            cloud_path="/" + name,
                            service="dropbox",
                        ))
                    break
                except (sqlite3.OperationalError, ValueError):
                    continue
        finally:
            conn.close()
        return files
