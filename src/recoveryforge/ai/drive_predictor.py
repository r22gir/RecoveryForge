"""
ML-based drive failure prediction.

Analyses SMART attributes to predict drive failure probability,
estimate remaining lifespan, and detect anomalous behaviour.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------
# Critical SMART attribute IDs and their failure weights
# -----------------------------------------------------------------------
_CRITICAL_ATTRS: Dict[int, Dict[str, Any]] = {
    5:   {"name": "Reallocated_Sector_Ct",       "weight": 0.25, "threshold": 0},
    10:  {"name": "Spin_Retry_Count",             "weight": 0.10, "threshold": 0},
    184: {"name": "End-to-End_Error",             "weight": 0.10, "threshold": 0},
    187: {"name": "Reported_Uncorrect",           "weight": 0.15, "threshold": 0},
    188: {"name": "Command_Timeout",              "weight": 0.05, "threshold": 5},
    196: {"name": "Reallocated_Event_Count",      "weight": 0.10, "threshold": 0},
    197: {"name": "Current_Pending_Sector",       "weight": 0.20, "threshold": 0},
    198: {"name": "Offline_Uncorrectable",        "weight": 0.20, "threshold": 0},
    199: {"name": "UDMA_CRC_Error_Count",         "weight": 0.05, "threshold": 50},
    201: {"name": "Soft_Read_Error_Rate",         "weight": 0.10, "threshold": 0},
}

# Temperature attribute IDs
_TEMP_ATTR_IDS = {190, 194}

# Power-on hours attribute ID
_POH_ATTR_ID = 9


@dataclass
class FailurePrediction:
    """Drive failure probability prediction."""
    failure_probability: float  # 0.0 – 1.0
    risk_level: str             # 'low', 'medium', 'high', 'critical'
    contributing_factors: List[str] = field(default_factory=list)


@dataclass
class LifespanEstimate:
    """Estimated remaining drive lifespan."""
    estimated_days_remaining: Optional[int]
    confidence: float  # 0.0 – 1.0
    basis: str = ""


@dataclass
class Anomaly:
    """Detected anomaly in SMART history."""
    attribute_id: int
    attribute_name: str
    description: str
    severity: str  # 'info', 'warning', 'critical'


@dataclass
class Recommendation:
    """Actionable recommendation based on SMART data."""
    action: str
    urgency: str   # 'immediate', 'soon', 'routine'
    details: str


class DriveFailurePredictor:
    """
    Predict drive failure probability from SMART attribute data.

    Provides failure probability, lifespan estimates, anomaly detection,
    and actionable recommendations without requiring cloud connectivity.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def predict_failure(self, smart_data: Dict[str, Any]) -> FailurePrediction:
        """
        Predict drive failure probability from SMART attributes.

        Args:
            smart_data: Dictionary of SMART attribute id/name -> raw value.
                        Accepts both integer IDs and string names as keys.

        Returns:
            FailurePrediction with probability and risk level.
        """
        score = 0.0
        factors: List[str] = []
        normalised = self._normalise_smart(smart_data)

        for attr_id, meta in _CRITICAL_ATTRS.items():
            value = normalised.get(attr_id, 0)
            threshold = meta["threshold"]
            if value > threshold:
                contribution = meta["weight"] * min(1.0, (value - threshold) / max(threshold + 1, 10))
                score += contribution
                factors.append(
                    f"{meta['name']} = {value} (threshold {threshold})"
                )

        # Temperature penalty
        temp = self._get_temperature(normalised)
        if temp is not None:
            if temp > 60:
                score += 0.20
                factors.append(f"Critical temperature: {temp}°C")
            elif temp > 50:
                score += 0.10
                factors.append(f"High temperature: {temp}°C")

        score = min(1.0, score)
        risk_level = (
            "critical" if score >= 0.7
            else "high" if score >= 0.4
            else "medium" if score >= 0.2
            else "low"
        )

        return FailurePrediction(
            failure_probability=round(score, 3),
            risk_level=risk_level,
            contributing_factors=factors,
        )

    def estimate_lifespan(self, smart_data: Dict[str, Any]) -> LifespanEstimate:
        """
        Estimate remaining drive lifespan based on SMART data.

        Args:
            smart_data: SMART attribute dictionary.

        Returns:
            LifespanEstimate with days remaining and confidence.
        """
        normalised = self._normalise_smart(smart_data)
        prediction = self.predict_failure(smart_data)

        poh = normalised.get(_POH_ATTR_ID)
        if poh is None:
            return LifespanEstimate(
                estimated_days_remaining=None,
                confidence=0.2,
                basis="Insufficient data (no power-on hours)",
            )

        # Consumer drives: median lifespan ~50,000 hours (~5.7 years)
        median_lifespan_hours = 50000
        remaining_hours = max(0, median_lifespan_hours - poh)

        # Adjust for current health
        failure_factor = 1.0 - prediction.failure_probability
        adjusted_hours = remaining_hours * failure_factor

        days = int(adjusted_hours / 24)
        confidence = 0.5 if prediction.risk_level in ("low", "medium") else 0.3

        return LifespanEstimate(
            estimated_days_remaining=days,
            confidence=confidence,
            basis=(
                f"Based on {poh} power-on hours and "
                f"{prediction.risk_level} risk level."
            ),
        )

    def detect_anomalies(
        self, smart_history: List[Dict[str, Any]]
    ) -> List[Anomaly]:
        """
        Detect anomalous SMART attribute patterns over time.

        Args:
            smart_history: Chronologically ordered list of SMART snapshots.

        Returns:
            List of detected Anomaly objects.
        """
        anomalies: List[Anomaly] = []

        if len(smart_history) < 2:
            return anomalies

        prev = self._normalise_smart(smart_history[-2])
        current = self._normalise_smart(smart_history[-1])

        for attr_id, meta in _CRITICAL_ATTRS.items():
            prev_val = prev.get(attr_id, 0)
            curr_val = current.get(attr_id, 0)
            delta = curr_val - prev_val

            if delta > 0:
                severity = "critical" if attr_id in {5, 187, 197, 198} else "warning"
                anomalies.append(Anomaly(
                    attribute_id=attr_id,
                    attribute_name=meta["name"],
                    description=f"Increased by {delta} (now {curr_val})",
                    severity=severity,
                ))

        # Temperature spike
        prev_temp = self._get_temperature(prev)
        curr_temp = self._get_temperature(current)
        if prev_temp is not None and curr_temp is not None:
            if curr_temp - prev_temp > 10:
                anomalies.append(Anomaly(
                    attribute_id=194,
                    attribute_name="Temperature_Celsius",
                    description=f"Temperature spike: {prev_temp}→{curr_temp}°C",
                    severity="warning",
                ))

        return anomalies

    def get_recommendations(
        self, smart_data: Dict[str, Any]
    ) -> List[Recommendation]:
        """
        Get actionable backup and replacement recommendations.

        Args:
            smart_data: SMART attribute dictionary.

        Returns:
            List of Recommendation objects.
        """
        prediction = self.predict_failure(smart_data)
        lifespan = self.estimate_lifespan(smart_data)
        recommendations: List[Recommendation] = []

        if prediction.risk_level == "critical":
            recommendations.append(Recommendation(
                action="Backup immediately",
                urgency="immediate",
                details="Drive is at critical risk. Back up all data now and replace the drive.",
            ))
            recommendations.append(Recommendation(
                action="Replace drive",
                urgency="immediate",
                details="Procure replacement drive and migrate data before complete failure.",
            ))
        elif prediction.risk_level == "high":
            recommendations.append(Recommendation(
                action="Back up data soon",
                urgency="soon",
                details="Drive shows multiple warning signs. Create a full backup within 24 hours.",
            ))
            recommendations.append(Recommendation(
                action="Plan drive replacement",
                urgency="soon",
                details="Schedule drive replacement within 1–4 weeks.",
            ))
        elif prediction.risk_level == "medium":
            recommendations.append(Recommendation(
                action="Increase backup frequency",
                urgency="routine",
                details="Run daily backups and monitor SMART data weekly.",
            ))
        else:
            recommendations.append(Recommendation(
                action="Continue routine monitoring",
                urgency="routine",
                details="Drive appears healthy. Monitor monthly.",
            ))

        if lifespan.estimated_days_remaining is not None:
            if lifespan.estimated_days_remaining < 90:
                recommendations.append(Recommendation(
                    action="Prepare replacement",
                    urgency="soon",
                    details=(
                        f"Estimated {lifespan.estimated_days_remaining} days remaining. "
                        "Order a replacement drive."
                    ),
                ))

        return recommendations

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _normalise_smart(
        self, smart_data: Dict[str, Any]
    ) -> Dict[int, int]:
        """Normalise SMART dict keys to integer attribute IDs."""
        normalised: Dict[int, int] = {}
        # Build reverse name->id lookup
        name_to_id = {meta["name"].lower(): attr_id
                      for attr_id, meta in _CRITICAL_ATTRS.items()}
        name_to_id["temperature_celsius"] = 194
        name_to_id["power_on_hours"] = _POH_ATTR_ID

        for key, value in smart_data.items():
            try:
                int_value = int(value) if not isinstance(value, int) else value
                if isinstance(key, int):
                    normalised[key] = int_value
                else:
                    # Try numeric string
                    try:
                        normalised[int(key)] = int_value
                    except (ValueError, TypeError):
                        attr_id = name_to_id.get(str(key).lower())
                        if attr_id is not None:
                            normalised[attr_id] = int_value
            except (ValueError, TypeError):
                continue

        return normalised

    def _get_temperature(self, normalised: Dict[int, int]) -> Optional[int]:
        """Extract temperature from normalised SMART data."""
        for attr_id in _TEMP_ATTR_IDS:
            if attr_id in normalised:
                return normalised[attr_id]
        return None
