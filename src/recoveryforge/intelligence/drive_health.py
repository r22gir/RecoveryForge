"""
Drive health monitoring using SMART data.
"""

import logging
import platform
import subprocess
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Drive health status."""
    GOOD = "good"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class SmartAttribute:
    """SMART attribute data."""
    id: int
    name: str
    value: int
    worst: int
    threshold: int
    raw_value: str
    status: str = "OK"


@dataclass
class DriveHealth:
    """Drive health information."""
    device: str
    model: str = "Unknown"
    serial: str = "Unknown"
    health_status: HealthStatus = HealthStatus.UNKNOWN
    health_percent: float = 0.0
    temperature: Optional[int] = None
    power_on_hours: Optional[int] = None
    power_cycle_count: Optional[int] = None
    reallocated_sectors: int = 0
    pending_sectors: int = 0
    attributes: List[SmartAttribute] = None
    
    def __post_init__(self):
        if self.attributes is None:
            self.attributes = []


class DriveHealthMonitor:
    """
    Monitor drive health using SMART data.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.system = platform.system()
    
    def get_drive_health(self, device: str) -> DriveHealth:
        """
        Get health information for a drive.
        
        Args:
            device: Device path
            
        Returns:
            DriveHealth object
        """
        health = DriveHealth(device=device)
        
        try:
            # Try to get SMART data
            smart_data = self._query_smart(device)
            
            if smart_data:
                health = self._parse_smart_data(device, smart_data)
                health.health_percent = self._calculate_health_score(health)
                health.health_status = self._determine_health_status(health)
            
        except Exception as e:
            self.logger.error(f"Error getting health for {device}: {e}")
        
        return health
    
    def _query_smart(self, device: str) -> Optional[str]:
        """
        Query SMART data from device.
        
        Args:
            device: Device path
            
        Returns:
            Raw SMART output or None
        """
        try:
            if self.system == "Linux":
                # Use smartctl on Linux
                result = subprocess.run(
                    ['smartctl', '-a', device],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                return result.stdout
            
            elif self.system == "Windows":
                # Use smartctl on Windows (requires smartmontools)
                result = subprocess.run(
                    ['smartctl', '-a', device],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                return result.stdout
            
            else:
                self.logger.warning(f"SMART monitoring not implemented for {self.system}")
                return None
                
        except FileNotFoundError:
            self.logger.warning("smartctl not found. Install smartmontools for drive health monitoring.")
            return None
        except subprocess.TimeoutExpired:
            self.logger.error(f"Timeout querying SMART data for {device}")
            return None
        except Exception as e:
            self.logger.error(f"Error querying SMART: {e}")
            return None
    
    def _parse_smart_data(self, device: str, smart_output: str) -> DriveHealth:
        """
        Parse SMART output.
        
        Args:
            device: Device path
            smart_output: Raw SMART output
            
        Returns:
            DriveHealth object
        """
        health = DriveHealth(device=device)
        
        lines = smart_output.split('\n')
        
        # Parse basic info
        for line in lines:
            if 'Device Model:' in line:
                health.model = line.split(':', 1)[1].strip()
            elif 'Serial Number:' in line:
                health.serial = line.split(':', 1)[1].strip()
            elif 'Temperature_Celsius' in line or '194 Temperature' in line:
                parts = line.split()
                if len(parts) >= 10:
                    try:
                        health.temperature = int(parts[9])
                    except ValueError:
                        pass
            elif 'Power_On_Hours' in line or '9 Power_On_Hours' in line:
                parts = line.split()
                if len(parts) >= 10:
                    try:
                        health.power_on_hours = int(parts[9])
                    except ValueError:
                        pass
            elif 'Reallocated_Sector' in line or '5 Reallocated_Sector_Ct' in line:
                parts = line.split()
                if len(parts) >= 10:
                    try:
                        health.reallocated_sectors = int(parts[9])
                    except ValueError:
                        pass
            elif 'Current_Pending_Sector' in line or '197 Current_Pending_Sector' in line:
                parts = line.split()
                if len(parts) >= 10:
                    try:
                        health.pending_sectors = int(parts[9])
                    except ValueError:
                        pass
        
        # TODO: Parse full attribute table
        
        return health
    
    def _calculate_health_score(self, health: DriveHealth) -> float:
        """
        Calculate overall health score (0-100).
        
        Args:
            health: DriveHealth object
            
        Returns:
            Health percentage
        """
        score = 100.0
        
        # Penalize for bad sectors
        if health.reallocated_sectors > 0:
            score -= min(30, health.reallocated_sectors * 5)
        
        if health.pending_sectors > 0:
            score -= min(40, health.pending_sectors * 10)
        
        # Penalize for high temperature
        if health.temperature:
            if health.temperature > 60:
                score -= 20
            elif health.temperature > 50:
                score -= 10
        
        # Penalize for high power-on hours (wear)
        if health.power_on_hours:
            years = health.power_on_hours / 8760  # Hours per year
            if years > 5:
                score -= min(20, (years - 5) * 5)
        
        return max(0.0, min(100.0, score))
    
    def _determine_health_status(self, health: DriveHealth) -> HealthStatus:
        """
        Determine overall health status.
        
        Args:
            health: DriveHealth object
            
        Returns:
            HealthStatus enum
        """
        score = health.health_percent
        
        # Critical if bad sectors present
        if health.reallocated_sectors > 10 or health.pending_sectors > 0:
            return HealthStatus.CRITICAL
        
        # Status based on score
        if score >= 80:
            return HealthStatus.GOOD
        elif score >= 60:
            return HealthStatus.WARNING
        else:
            return HealthStatus.CRITICAL
    
    def predict_failure(self, health: DriveHealth) -> Dict[str, Any]:
        """
        Predict drive failure probability.
        
        Args:
            health: DriveHealth object
            
        Returns:
            Prediction results
        """
        # Simple rule-based prediction
        failure_score = 0
        warnings = []
        
        if health.reallocated_sectors > 0:
            failure_score += 30
            warnings.append(f"Reallocated sectors detected: {health.reallocated_sectors}")
        
        if health.pending_sectors > 0:
            failure_score += 40
            warnings.append(f"Pending sectors detected: {health.pending_sectors}")
        
        if health.temperature and health.temperature > 55:
            failure_score += 20
            warnings.append(f"High temperature: {health.temperature}°C")
        
        if health.power_on_hours and health.power_on_hours > 43800:  # 5 years
            failure_score += 10
            warnings.append(f"Drive age: {health.power_on_hours // 8760} years")
        
        # Predict time to failure
        if failure_score > 70:
            prediction = "Imminent (days to weeks)"
        elif failure_score > 40:
            prediction = "Likely (months)"
        elif failure_score > 20:
            prediction = "Possible (1-2 years)"
        else:
            prediction = "Unlikely (>2 years)"
        
        return {
            'failure_score': failure_score,
            'prediction': prediction,
            'warnings': warnings,
            'recommendation': self._get_recommendation(failure_score)
        }
    
    def _get_recommendation(self, failure_score: int) -> str:
        """Get recommendation based on failure score."""
        if failure_score > 70:
            return "⚠️ BACKUP IMMEDIATELY and replace drive"
        elif failure_score > 40:
            return "⚠️ Backup data soon and monitor closely"
        elif failure_score > 20:
            return "ℹ️ Regular backups recommended"
        else:
            return "✓ Drive appears healthy"
