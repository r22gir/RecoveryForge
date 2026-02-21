"""
Content analyzer for file classification and quality assessment.
"""

import logging
import hashlib
from typing import Dict, Any, Optional
from pathlib import Path
import magic


logger = logging.getLogger(__name__)


class ContentAnalyzer:
    """
    Analyze file content for quality, corruption, and classification.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze a file's content.
        
        Args:
            file_path: Path to file
            
        Returns:
            Analysis results
        """
        path = Path(file_path)
        
        if not path.exists():
            return {'error': 'File not found'}
        
        analysis = {
            'filename': path.name,
            'size': path.stat().st_size,
            'extension': path.suffix.lower(),
        }
        
        # Calculate hash
        analysis['sha256'] = self.calculate_hash(file_path)
        
        # Detect MIME type
        try:
            mime_type = magic.from_file(str(path), mime=True)
            analysis['mime_type'] = mime_type
            analysis['detected_type'] = self._mime_to_category(mime_type)
        except:
            analysis['mime_type'] = 'unknown'
        
        # Calculate quality score
        analysis['quality_score'] = self.calculate_quality_score(file_path)
        
        # Check for corruption
        analysis['is_corrupted'] = self.check_corruption(file_path)
        
        return analysis
    
    def calculate_hash(self, file_path: str, algorithm: str = 'sha256') -> str:
        """
        Calculate file hash.
        
        Args:
            file_path: Path to file
            algorithm: Hash algorithm (sha256, md5, etc.)
            
        Returns:
            Hex digest of hash
        """
        try:
            hash_func = hashlib.new(algorithm)
            
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    hash_func.update(chunk)
            
            return hash_func.hexdigest()
            
        except Exception as e:
            self.logger.error(f"Error calculating hash for {file_path}: {e}")
            return ""
    
    def calculate_quality_score(self, file_path: str) -> float:
        """
        Calculate file quality score (0-100).
        
        Args:
            file_path: Path to file
            
        Returns:
            Quality score
        """
        # Basic quality heuristics
        score = 100.0
        
        try:
            size = Path(file_path).stat().st_size
            
            # Penalize very small files
            if size < 1024:  # < 1KB
                score -= 30
            elif size < 10240:  # < 10KB
                score -= 10
            
            # Check entropy (randomness)
            entropy = self._calculate_entropy(file_path)
            if entropy < 3.0:  # Low entropy might indicate corruption
                score -= 20
            elif entropy > 7.5:  # Very high entropy might indicate encryption/compression
                score -= 10
            
            # TODO: Add more sophisticated checks
            # - Header/footer validation
            # - Structure validation
            # - Content consistency checks
            
        except Exception as e:
            self.logger.error(f"Error calculating quality score: {e}")
            score = 50.0
        
        return max(0.0, min(100.0, score))
    
    def check_corruption(self, file_path: str) -> bool:
        """
        Check if file appears corrupted.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if corrupted, False otherwise
        """
        try:
            # Basic corruption checks
            size = Path(file_path).stat().st_size
            
            # Zero-byte files are corrupted
            if size == 0:
                return True
            
            # Check for null bytes throughout file
            with open(file_path, 'rb') as f:
                sample = f.read(min(1024, size))
                
                # If entire sample is null bytes, likely corrupted
                if sample and all(b == 0 for b in sample):
                    return True
            
            # TODO: Add file-type-specific corruption checks
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking corruption for {file_path}: {e}")
            return True
    
    def _calculate_entropy(self, file_path: str, sample_size: int = 8192) -> float:
        """
        Calculate Shannon entropy of file.
        
        Args:
            file_path: Path to file
            sample_size: Bytes to sample
            
        Returns:
            Entropy value (0-8)
        """
        try:
            import math
            from collections import Counter
            
            with open(file_path, 'rb') as f:
                data = f.read(sample_size)
            
            if not data:
                return 0.0
            
            # Count byte frequencies
            counter = Counter(data)
            entropy = 0.0
            
            for count in counter.values():
                probability = count / len(data)
                entropy -= probability * math.log2(probability)
            
            return entropy
            
        except Exception as e:
            self.logger.error(f"Error calculating entropy: {e}")
            return 0.0
    
    def _mime_to_category(self, mime_type: str) -> str:
        """Convert MIME type to file category."""
        if mime_type.startswith('image/'):
            return 'image'
        elif mime_type.startswith('video/'):
            return 'video'
        elif mime_type.startswith('audio/'):
            return 'audio'
        elif mime_type.startswith('text/'):
            return 'document'
        elif 'pdf' in mime_type:
            return 'document'
        elif 'word' in mime_type or 'document' in mime_type:
            return 'document'
        elif 'spreadsheet' in mime_type or 'excel' in mime_type:
            return 'document'
        elif 'zip' in mime_type or 'compressed' in mime_type:
            return 'archive'
        elif 'executable' in mime_type:
            return 'executable'
        else:
            return 'other'
    
    def is_system_file(self, file_path: str) -> bool:
        """
        Check if file is a Windows system file that should be filtered.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if system file, False otherwise
        """
        path = Path(file_path)
        name = path.name.lower()
        
        # Common system files to filter
        system_files = [
            'thumbs.db', 'desktop.ini', '.ds_store',
            'hiberfil.sys', 'pagefile.sys', 'swapfile.sys',
        ]
        
        if name in system_files:
            return True
        
        # System directories
        system_dirs = ['windows', 'system32', 'syswow64', '$recycle.bin']
        if any(d in path.parts for d in system_dirs):
            return True
        
        return False
