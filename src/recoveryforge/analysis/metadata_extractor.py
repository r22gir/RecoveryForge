"""
Metadata extractor for images, documents, and other files.
"""

import logging
from typing import Dict, Optional, Any
from pathlib import Path
import io

try:
    import exifread
    EXIF_AVAILABLE = True
except ImportError:
    EXIF_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    from PyPDF2 import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


logger = logging.getLogger(__name__)


class MetadataExtractor:
    """
    Extract metadata from various file types.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Dictionary of metadata
        """
        path = Path(file_path)
        metadata = {
            "filename": path.name,
            "size": path.stat().st_size if path.exists() else 0,
            "extension": path.suffix.lower(),
        }
        
        # Try different extractors based on file type
        ext = path.suffix.lower()
        
        if ext in ['.jpg', '.jpeg', '.tiff', '.tif'] and EXIF_AVAILABLE:
            metadata.update(self.extract_exif(file_path))
        
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'] and PIL_AVAILABLE:
            metadata.update(self.extract_image_info(file_path))
        
        if ext == '.pdf' and PDF_AVAILABLE:
            metadata.update(self.extract_pdf_metadata(file_path))
        
        return metadata
    
    def extract_exif(self, file_path: str) -> Dict[str, Any]:
        """
        Extract EXIF metadata from image.
        
        Args:
            file_path: Path to image file
            
        Returns:
            Dictionary of EXIF data
        """
        if not EXIF_AVAILABLE:
            return {}
        
        try:
            with open(file_path, 'rb') as f:
                tags = exifread.process_file(f, details=False)
            
            exif_data = {}
            
            # Extract common EXIF fields
            field_mapping = {
                'Image Make': 'camera_make',
                'Image Model': 'camera_model',
                'EXIF DateTimeOriginal': 'date_taken',
                'EXIF DateTimeDigitized': 'date_digitized',
                'Image DateTime': 'date_modified',
                'GPS GPSLatitude': 'gps_latitude',
                'GPS GPSLongitude': 'gps_longitude',
                'Image ImageWidth': 'image_width',
                'Image ImageLength': 'image_height',
                'EXIF ExposureTime': 'exposure_time',
                'EXIF FNumber': 'f_number',
                'EXIF ISOSpeedRatings': 'iso',
                'EXIF FocalLength': 'focal_length',
            }
            
            for exif_key, metadata_key in field_mapping.items():
                if exif_key in tags:
                    exif_data[metadata_key] = str(tags[exif_key])
            
            return exif_data
            
        except Exception as e:
            self.logger.error(f"Error extracting EXIF from {file_path}: {e}")
            return {}
    
    def extract_image_info(self, file_path: str) -> Dict[str, Any]:
        """
        Extract basic image information using PIL.
        
        Args:
            file_path: Path to image file
            
        Returns:
            Dictionary of image info
        """
        if not PIL_AVAILABLE:
            return {}
        
        try:
            with Image.open(file_path) as img:
                return {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode,
                }
        except Exception as e:
            self.logger.error(f"Error extracting image info from {file_path}: {e}")
            return {}
    
    def extract_pdf_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract PDF metadata.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dictionary of PDF metadata
        """
        if not PDF_AVAILABLE:
            return {}
        
        try:
            with open(file_path, 'rb') as f:
                pdf = PdfReader(f)
                
                metadata = {
                    'page_count': len(pdf.pages),
                }
                
                # Extract PDF info
                if pdf.metadata:
                    info = pdf.metadata
                    if info.title:
                        metadata['title'] = info.title
                    if info.author:
                        metadata['author'] = info.author
                    if info.subject:
                        metadata['subject'] = info.subject
                    if info.creator:
                        metadata['creator'] = info.creator
                
                return metadata
                
        except Exception as e:
            self.logger.error(f"Error extracting PDF metadata from {file_path}: {e}")
            return {}
    
    def extract_from_bytes(self, data: bytes, file_type: str) -> Dict[str, Any]:
        """
        Extract metadata from byte data.
        
        Args:
            data: File data
            file_type: File extension/type
            
        Returns:
            Dictionary of metadata
        """
        metadata = {
            'size': len(data),
            'extension': file_type,
        }
        
        # Try to extract EXIF from image bytes
        if file_type in ['jpg', 'jpeg', 'tiff'] and EXIF_AVAILABLE:
            try:
                tags = exifread.process_file(io.BytesIO(data), details=False)
                if tags:
                    metadata['has_exif'] = True
            except:
                pass
        
        return metadata
