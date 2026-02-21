"""
Example: Basic file recovery scan

This example demonstrates how to use RecoveryForge programmatically
to scan for and recover deleted files.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from recoveryforge.core import DiskScanner, RecoveryEngine
from recoveryforge.utils import format_bytes


def main():
    """Run a basic recovery scan."""
    print("RecoveryForge - Basic Recovery Example")
    print("=" * 50)
    
    # Initialize recovery engine
    print("\n1. Initializing recovery engine...")
    engine = RecoveryEngine()
    
    # Scan for available drives
    print("\n2. Scanning for drives...")
    drives = engine.scan_drives()
    
    if not drives:
        print("No drives found!")
        return
    
    print(f"Found {len(drives)} drives:")
    for i, drive in enumerate(drives):
        print(f"  [{i}] {drive.device} - {drive.model}")
        print(f"      Mount: {drive.mountpoint}")
        print(f"      Size: {format_bytes(drive.total_size)}")
        print(f"      Free: {format_bytes(drive.free_size)}")
        print()
    
    print("\n✓ Example complete!")


if __name__ == "__main__":
    main()
