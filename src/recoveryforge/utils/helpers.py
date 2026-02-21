"""
Helper utility functions.
"""

from typing import Union


def format_bytes(bytes_val: Union[int, float], decimals: int = 2) -> str:
    """
    Format bytes to human-readable string.
    
    Args:
        bytes_val: Number of bytes
        decimals: Number of decimal places
        
    Returns:
        Formatted string (e.g., "1.5 GB")
    """
    if bytes_val == 0:
        return "0 B"
    
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    unit_index = 0
    size = float(bytes_val)
    
    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1
    
    return f"{size:.{decimals}f} {units[unit_index]}"


def format_time(seconds: Union[int, float]) -> str:
    """
    Format seconds to human-readable time string.
    
    Args:
        seconds: Number of seconds
        
    Returns:
        Formatted string (e.g., "1h 23m 45s")
    """
    if seconds < 0:
        return "Unknown"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0 or hours > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    
    return " ".join(parts)


def calculate_eta(bytes_processed: int, total_bytes: int, elapsed_time: float) -> float:
    """
    Calculate estimated time remaining.
    
    Args:
        bytes_processed: Bytes processed so far
        total_bytes: Total bytes to process
        elapsed_time: Time elapsed so far (seconds)
        
    Returns:
        Estimated seconds remaining
    """
    if bytes_processed == 0 or elapsed_time == 0:
        return -1
    
    rate = bytes_processed / elapsed_time
    remaining_bytes = total_bytes - bytes_processed
    
    return remaining_bytes / rate


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Trim whitespace
    filename = filename.strip()
    
    # Ensure not empty
    if not filename:
        filename = "unnamed"
    
    return filename
