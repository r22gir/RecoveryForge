"""Example: Drive health monitoring"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from recoveryforge.intelligence.drive_health import DriveHealthMonitor

def main():
    print("RecoveryForge - Drive Health Example")
    print("=" * 50)
    
    monitor = DriveHealthMonitor()
    device = "/dev/sda"
    
    print(f"\nChecking health of {device}...")
    print("(Requires smartmontools installed)")
    
    health = monitor.get_drive_health(device)
    print(f"\nDevice: {health.device}")
    print(f"Model: {health.model}")
    print(f"Status: {health.health_status.value}")
    print(f"Health: {health.health_percent:.1f}%")
    
    prediction = monitor.predict_failure(health)
    print(f"\nPrediction: {prediction['prediction']}")
    print(f"Recommendation: {prediction['recommendation']}")
    
    print("\n✓ Health check complete!")

if __name__ == "__main__":
    main()
