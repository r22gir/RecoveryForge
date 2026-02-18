"""
Advanced deduplication using hashing and fuzzy matching.
"""

import logging
import hashlib
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict

try:
    import ssdeep
    SSDEEP_AVAILABLE = True
except ImportError:
    SSDEEP_AVAILABLE = False


logger = logging.getLogger(__name__)


@dataclass
class DuplicateGroup:
    """Group of duplicate files."""
    hash: str
    files: List[str]
    total_size: int
    similarity: float = 100.0  # Percentage similarity
    
    @property
    def duplicate_count(self) -> int:
        """Number of duplicates (excluding original)."""
        return len(self.files) - 1
    
    @property
    def wasted_space(self) -> int:
        """Space wasted by duplicates."""
        return self.total_size * self.duplicate_count


class Deduplicator:
    """
    Advanced deduplication using multiple hashing strategies.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.hash_cache: Dict[str, str] = {}
        self.ssdeep_cache: Dict[str, str] = {}
    
    def find_duplicates_exact(self, file_paths: List[str]) -> List[DuplicateGroup]:
        """
        Find exact duplicates using SHA-256.
        
        Args:
            file_paths: List of file paths to check
            
        Returns:
            List of duplicate groups
        """
        self.logger.info(f"Finding exact duplicates in {len(file_paths)} files")
        
        # Group files by hash
        hash_groups = defaultdict(list)
        
        for path in file_paths:
            try:
                file_hash = self._calculate_hash(path)
                if file_hash:
                    hash_groups[file_hash].append(path)
            except Exception as e:
                self.logger.error(f"Error hashing {path}: {e}")
        
        # Create duplicate groups (only groups with > 1 file)
        duplicates = []
        for file_hash, files in hash_groups.items():
            if len(files) > 1:
                # Get file size
                try:
                    size = Path(files[0]).stat().st_size
                except:
                    size = 0
                
                group = DuplicateGroup(
                    hash=file_hash,
                    files=files,
                    total_size=size,
                    similarity=100.0
                )
                duplicates.append(group)
        
        self.logger.info(f"Found {len(duplicates)} duplicate groups")
        return duplicates
    
    def find_duplicates_fuzzy(
        self,
        file_paths: List[str],
        similarity_threshold: int = 50
    ) -> List[DuplicateGroup]:
        """
        Find similar files using fuzzy hashing (ssdeep).
        
        Args:
            file_paths: List of file paths to check
            similarity_threshold: Minimum similarity (0-100)
            
        Returns:
            List of similar file groups
        """
        if not SSDEEP_AVAILABLE:
            self.logger.warning("ssdeep not available, falling back to exact matching")
            return self.find_duplicates_exact(file_paths)
        
        self.logger.info(f"Finding fuzzy duplicates in {len(file_paths)} files")
        
        # Calculate fuzzy hashes
        fuzzy_hashes = {}
        for path in file_paths:
            try:
                fuzzy_hash = self._calculate_ssdeep(path)
                if fuzzy_hash:
                    fuzzy_hashes[path] = fuzzy_hash
            except Exception as e:
                self.logger.error(f"Error calculating fuzzy hash for {path}: {e}")
        
        # Compare all pairs
        similar_groups = []
        processed = set()
        
        paths = list(fuzzy_hashes.keys())
        for i, path1 in enumerate(paths):
            if path1 in processed:
                continue
            
            group_files = [path1]
            hash1 = fuzzy_hashes[path1]
            
            for path2 in paths[i+1:]:
                if path2 in processed:
                    continue
                
                hash2 = fuzzy_hashes[path2]
                similarity = ssdeep.compare(hash1, hash2)
                
                if similarity >= similarity_threshold:
                    group_files.append(path2)
                    processed.add(path2)
            
            if len(group_files) > 1:
                try:
                    size = Path(path1).stat().st_size
                except:
                    size = 0
                
                group = DuplicateGroup(
                    hash=hash1,
                    files=group_files,
                    total_size=size,
                    similarity=similarity_threshold
                )
                similar_groups.append(group)
            
            processed.add(path1)
        
        self.logger.info(f"Found {len(similar_groups)} similar file groups")
        return similar_groups
    
    def find_duplicates_metadata(
        self,
        file_paths: List[str],
        check_name: bool = True,
        check_size: bool = True,
        check_timestamp: bool = False
    ) -> List[DuplicateGroup]:
        """
        Find potential duplicates based on metadata.
        
        Args:
            file_paths: List of file paths
            check_name: Check filename similarity
            check_size: Check file size
            check_timestamp: Check modification time
            
        Returns:
            List of potential duplicate groups
        """
        self.logger.info(f"Finding metadata-based duplicates in {len(file_paths)} files")
        
        # Group by metadata criteria
        groups = defaultdict(list)
        
        for path in file_paths:
            try:
                p = Path(path)
                
                # Build key from metadata
                key_parts = []
                
                if check_name:
                    key_parts.append(p.stem.lower())  # Filename without extension
                
                if check_size:
                    key_parts.append(str(p.stat().st_size))
                
                if check_timestamp:
                    key_parts.append(str(int(p.stat().st_mtime)))
                
                key = '|'.join(key_parts)
                groups[key].append(path)
                
            except Exception as e:
                self.logger.error(f"Error processing metadata for {path}: {e}")
        
        # Create duplicate groups
        duplicates = []
        for key, files in groups.items():
            if len(files) > 1:
                try:
                    size = Path(files[0]).stat().st_size
                except:
                    size = 0
                
                group = DuplicateGroup(
                    hash=key,
                    files=files,
                    total_size=size,
                    similarity=90.0  # Metadata-based is approximate
                )
                duplicates.append(group)
        
        self.logger.info(f"Found {len(duplicates)} metadata-based duplicate groups")
        return duplicates
    
    def select_best_copy(self, group: DuplicateGroup) -> str:
        """
        Select the best copy from a duplicate group.
        
        Args:
            group: Duplicate group
            
        Returns:
            Path to best copy
        """
        if not group.files:
            return ""
        
        # Scoring criteria:
        # 1. Prefer files not in temp/trash locations
        # 2. Prefer shorter paths (likely original location)
        # 3. Prefer older files (by modification time)
        
        scored_files = []
        
        for path in group.files:
            score = 0
            p = Path(path)
            
            # Penalize temp/trash locations
            path_lower = str(path).lower()
            if any(x in path_lower for x in ['temp', 'tmp', 'trash', 'recycle', 'cache']):
                score -= 100
            
            # Prefer shorter paths
            score -= len(path) // 10
            
            # Prefer older files
            try:
                mtime = p.stat().st_mtime
                score -= int(mtime) // 1000000  # Older = lower timestamp = higher score
            except:
                pass
            
            scored_files.append((score, path))
        
        # Return file with highest score
        best = max(scored_files, key=lambda x: x[0])
        return best[1]
    
    def calculate_space_savings(self, duplicate_groups: List[DuplicateGroup]) -> Dict[str, int]:
        """
        Calculate potential space savings from deduplication.
        
        Args:
            duplicate_groups: List of duplicate groups
            
        Returns:
            Dictionary with space statistics
        """
        total_wasted = sum(g.wasted_space for g in duplicate_groups)
        total_duplicates = sum(g.duplicate_count for g in duplicate_groups)
        total_files = sum(len(g.files) for g in duplicate_groups)
        
        return {
            'total_wasted_bytes': total_wasted,
            'total_duplicate_files': total_duplicates,
            'total_files_in_groups': total_files,
            'num_groups': len(duplicate_groups),
        }
    
    def _calculate_hash(self, file_path: str) -> Optional[str]:
        """Calculate SHA-256 hash of file."""
        if file_path in self.hash_cache:
            return self.hash_cache[file_path]
        
        try:
            hash_func = hashlib.sha256()
            
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    hash_func.update(chunk)
            
            file_hash = hash_func.hexdigest()
            self.hash_cache[file_path] = file_hash
            return file_hash
            
        except Exception as e:
            self.logger.error(f"Error hashing {file_path}: {e}")
            return None
    
    def _calculate_ssdeep(self, file_path: str) -> Optional[str]:
        """Calculate ssdeep fuzzy hash."""
        if not SSDEEP_AVAILABLE:
            return None
        
        if file_path in self.ssdeep_cache:
            return self.ssdeep_cache[file_path]
        
        try:
            fuzzy_hash = ssdeep.hash_from_file(file_path)
            self.ssdeep_cache[file_path] = fuzzy_hash
            return fuzzy_hash
        except Exception as e:
            self.logger.error(f"Error calculating ssdeep for {file_path}: {e}")
            return None
