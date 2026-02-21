"""
Ransomware detection and decryption assistant.

Detects encrypted/ransomware-affected files via entropy analysis,
known extension patterns, and signature matching. Suggests available
decryptors from No More Ransom project.
"""

import logging
import math
import os
import platform
import subprocess
from collections import Counter
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path


logger = logging.getLogger(__name__)


# Known ransomware file extensions mapped to family names
_RANSOMWARE_EXTENSIONS: Dict[str, str] = {
    ".locked": "generic",
    ".encrypted": "generic",
    ".enc": "generic",
    ".crypt": "CryptXXX",
    ".crypted": "CryptXXX",
    ".cerber": "Cerber",
    ".cerber2": "Cerber",
    ".cerber3": "Cerber",
    ".locky": "Locky",
    ".zzzzz": "Locky",
    ".aesir": "Locky",
    ".thor": "Locky",
    ".zepto": "Locky",
    ".osiris": "Locky",
    ".wncry": "WannaCry",
    ".wncryt": "WannaCry",
    ".wcry": "WannaCry",
    ".sage": "Sage",
    ".spora": "Spora",
    ".dharma": "Dharma",
    ".cezar": "Dharma",
    ".java": "Dharma",
    ".adobe": "Dharma",
    ".arrow": "Dharma",
    ".wallet": "Dharma",
    ".onion": "Dharma",
    ".ryuk": "Ryuk",
    ".ryk": "Ryuk",
    ".revil": "REvil",
    ".sodinokibi": "REvil",
    ".sodin": "REvil",
    ".phobos": "Phobos",
    ".eking": "Phobos",
    ".snake": "Snake",
    ".ekans": "Snake",
    ".maze": "Maze",
    ".stop": "STOP/Djvu",
    ".djvu": "STOP/Djvu",
    ".djvuu": "STOP/Djvu",
    ".uudjvu": "STOP/Djvu",
}

# No More Ransom decryptor database (family -> decryptor info)
_NO_MORE_RANSOM_DECRYPTORS: Dict[str, Dict[str, str]] = {
    "WannaCry": {
        "name": "WannaKiwi / WannaDecrypt0r",
        "url": "https://www.nomoreransom.org/en/decryption-tools.html",
        "notes": "Works on Windows XP/Vista/7/2003/2008 only.",
    },
    "CryptXXX": {
        "name": "RannohDecryptor",
        "url": "https://support.kaspersky.com/viruses/disinfection/8547",
        "notes": "Covers CryptXXX v1, v2, v3.",
    },
    "Cerber": {
        "name": "Trend Micro Ransomware Decryptor",
        "url": "https://success.trendmicro.com/solution/1114221",
        "notes": "Limited to older Cerber variants.",
    },
    "Locky": {
        "name": "No free decryptor currently available",
        "url": "https://www.nomoreransom.org/en/decryption-tools.html",
        "notes": "Check No More Ransom regularly for updates.",
    },
    "STOP/Djvu": {
        "name": "Emsisoft Decryptor for STOP Djvu",
        "url": "https://www.emsisoft.com/ransomware-decryption/stop-djvu",
        "notes": "Requires original + encrypted file pair for offline keys.",
    },
    "Dharma": {
        "name": "Kaspersky Rakhni Decryptor",
        "url": "https://support.kaspersky.com/viruses/disinfection/10556",
        "notes": "Covers many Dharma variants.",
    },
    "generic": {
        "name": "No More Ransom Tool Selector",
        "url": "https://www.nomoreransom.org/crypto-sheriff.php",
        "notes": "Upload a ransom note or encrypted file to identify the family.",
    },
}

# High-entropy threshold (encrypted data is typically > 7.5 bits/byte)
_ENTROPY_THRESHOLD = 7.5
# Sample size for entropy calculation (first 256 KB)
_ENTROPY_SAMPLE_SIZE = 262144


@dataclass
class DecryptorInfo:
    """Information about an available decryptor tool."""
    name: str
    url: str
    notes: str


@dataclass
class RansomwareFamily:
    """Identified ransomware family."""
    name: str
    confidence: float
    indicators: List[str] = field(default_factory=list)


@dataclass
class RansomwareAnalysis:
    """Analysis result for a single file."""
    file_path: str
    entropy: float = 0.0
    is_likely_encrypted: bool = False
    extension_match: Optional[str] = None
    family: Optional[RansomwareFamily] = None
    decryptor: Optional[DecryptorInfo] = None
    error: Optional[str] = None


@dataclass
class ShadowCopy:
    """Windows Volume Shadow Copy."""
    volume_path: str
    creation_time: str
    id: str


class RansomwareDetector:
    """
    Detect ransomware-affected files using entropy analysis,
    extension matching, and signature databases.

    Suggests decryptors from the No More Ransom project.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def calculate_entropy(self, file_path: str) -> float:
        """
        Calculate Shannon entropy of a file (high = likely encrypted).

        Args:
            file_path: Path to the file.

        Returns:
            Entropy in bits per byte (0.0–8.0).
        """
        try:
            with open(file_path, "rb") as fh:
                data = fh.read(_ENTROPY_SAMPLE_SIZE)
            if not data:
                return 0.0
            counts = Counter(data)
            total = len(data)
            entropy = -sum(
                (c / total) * math.log2(c / total)
                for c in counts.values()
                if c > 0
            )
            return round(entropy, 4)
        except Exception as e:
            self.logger.error(f"Entropy calculation failed for {file_path}: {e}")
            return 0.0

    def analyze_file(self, file_path: str) -> RansomwareAnalysis:
        """
        Analyze a single file for ransomware indicators.

        Args:
            file_path: Path to the file.

        Returns:
            RansomwareAnalysis with findings.
        """
        analysis = RansomwareAnalysis(file_path=file_path)

        if not Path(file_path).exists():
            analysis.error = f"File not found: {file_path}"
            return analysis

        try:
            analysis.entropy = self.calculate_entropy(file_path)
            analysis.is_likely_encrypted = analysis.entropy >= _ENTROPY_THRESHOLD

            # Check extension
            suffix = Path(file_path).suffix.lower()
            if suffix in _RANSOMWARE_EXTENSIONS:
                analysis.extension_match = suffix
                family_name = _RANSOMWARE_EXTENSIONS[suffix]
                analysis.family = RansomwareFamily(
                    name=family_name,
                    confidence=0.8,
                    indicators=[f"Known ransomware extension: {suffix}"],
                )

            # Boost confidence if entropy also high
            if analysis.is_likely_encrypted:
                if analysis.family:
                    analysis.family.confidence = min(
                        1.0, analysis.family.confidence + 0.15
                    )
                    analysis.family.indicators.append(
                        f"High entropy: {analysis.entropy:.2f}"
                    )
                else:
                    analysis.family = RansomwareFamily(
                        name="unknown",
                        confidence=0.5,
                        indicators=[f"High entropy: {analysis.entropy:.2f}"],
                    )

            # Look up decryptor
            if analysis.family:
                analysis.decryptor = self.find_decryptor(analysis.family.name)

        except Exception as e:
            analysis.error = str(e)
            self.logger.error(f"Analysis failed for {file_path}: {e}")

        return analysis

    def scan_directory(self, directory: str) -> List[RansomwareAnalysis]:
        """
        Scan a directory for ransomware-affected files.

        Args:
            directory: Directory path to scan.

        Returns:
            List of RansomwareAnalysis for suspicious files.
        """
        results: List[RansomwareAnalysis] = []
        dir_path = Path(directory)

        if not dir_path.is_dir():
            self.logger.error(f"Not a directory: {directory}")
            return results

        for file_path in dir_path.rglob("*"):
            if not file_path.is_file():
                continue
            analysis = self.analyze_file(str(file_path))
            if analysis.is_likely_encrypted or analysis.extension_match:
                results.append(analysis)

        return results

    def identify_ransomware_family(
        self, file_path: str
    ) -> Optional[RansomwareFamily]:
        """
        Identify specific ransomware family for a file.

        Args:
            file_path: Path to the suspected ransomware-encrypted file.

        Returns:
            RansomwareFamily if identified, else None.
        """
        analysis = self.analyze_file(file_path)
        return analysis.family

    def find_decryptor(self, ransomware_family: str) -> Optional[DecryptorInfo]:
        """
        Find an available decryptor for a known ransomware family.

        Args:
            ransomware_family: Ransomware family name.

        Returns:
            DecryptorInfo if found, else None.
        """
        info = _NO_MORE_RANSOM_DECRYPTORS.get(ransomware_family)
        if info is None:
            # Fall back to generic entry
            info = _NO_MORE_RANSOM_DECRYPTORS.get("generic")
        if info:
            return DecryptorInfo(**info)
        return None

    def extract_shadow_copies(self, volume: str) -> List[ShadowCopy]:
        """
        Extract Windows Volume Shadow Copies for a given volume.

        Args:
            volume: Volume letter or path (e.g. 'C:').

        Returns:
            List of ShadowCopy objects.
        """
        copies: List[ShadowCopy] = []

        if platform.system() != "Windows":
            self.logger.warning("Shadow copy extraction is only supported on Windows.")
            return copies

        try:
            result = subprocess.run(
                ["vssadmin", "list", "shadows", f"/for={volume}"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            current_id = ""
            current_time = ""
            current_path = ""

            for line in result.stdout.splitlines():
                line = line.strip()
                if "Shadow Copy ID:" in line:
                    current_id = line.split(":", 1)[1].strip()
                elif "Creation Time:" in line:
                    current_time = line.split(":", 1)[1].strip()
                elif "Shadow Copy Volume:" in line:
                    current_path = line.split(":", 1)[1].strip()
                    copies.append(ShadowCopy(
                        volume_path=current_path,
                        creation_time=current_time,
                        id=current_id,
                    ))

        except FileNotFoundError:
            self.logger.error("vssadmin not found. Must run as administrator.")
        except subprocess.TimeoutExpired:
            self.logger.error("Timeout querying shadow copies.")
        except Exception as e:
            self.logger.error(f"Shadow copy extraction failed: {e}")

        return copies
