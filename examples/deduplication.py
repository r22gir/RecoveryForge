"""Example: Deduplication"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from recoveryforge.intelligence.deduplicator import Deduplicator
from recoveryforge.utils import format_bytes

def main():
    print("RecoveryForge - Deduplication Example")
    print("=" * 50)
    
    dedup = Deduplicator()
    
    # Example: would analyze real recovered files
    files = []  # Add file paths here
    
    print(f"\nAnalyzing files for duplicates...")
    print("(Add file paths to analyze)")
    
    if files:
        duplicates = dedup.find_duplicates_exact(files)
        print(f"Found {len(duplicates)} duplicate groups")
        
        stats = dedup.calculate_space_savings(duplicates)
        print(f"Wasted space: {format_bytes(stats['total_wasted_bytes'])}")
    else:
        print("No files to analyze (this is an example)")
    
    print("\n✓ Deduplication example complete!")

if __name__ == "__main__":
    main()
