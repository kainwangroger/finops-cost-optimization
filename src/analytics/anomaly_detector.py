from datetime import datetime, timezone
from statistics import mean, stdev


class AnomalyDetector:
    def __init__(self, threshold: float = 2.0):
        self.threshold = threshold

    def z_scores(self, values: list[float]) -> list[float]:
        if len(values) < 2:
            return [0.0] * len(values)
        avg = mean(values)
        sd = stdev(values)
        if sd == 0:
            return [0.0] * len(values)
        return [round((v - avg) / sd, 3) for v in values]

    def detect_spikes(self, values: list[float]) -> list[int]:
        scores = self.z_scores(values)
        return [i for i, z in enumerate(scores) if abs(z) > self.threshold]

    def detect_by_iqr(self, values: list[float]) -> list[int]:
        if len(values) < 4:
            return []
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        q1 = sorted_vals[n // 4]
        q3 = sorted_vals[(3 * n) // 4]
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        return [i for i, v in enumerate(values) if v < lower or v > upper]

    def moving_average(self, values: list[float], window: int = 7) -> list[float]:
        if len(values) < window:
            return [mean(values)] * len(values)
        result = []
        for i in range(len(values)):
            start = max(0, i - window + 1)
            result.append(round(mean(values[start:i + 1]), 2))
        return result

    def detect_trend(self, values: list[float]) -> str:
        if len(values) < 2:
            return "insufficient_data"
        first_half = mean(values[:len(values) // 2])
        second_half = mean(values[len(values) // 2:])
        if second_half > first_half * 1.1:
            return "increasing"
        if second_half < first_half * 0.9:
            return "decreasing"
        return "stable"

    def anomaly_report(self, daily_costs: list[float]) -> dict:
        spikes = self.detect_spikes(daily_costs)
        iqr_anomalies = self.detect_by_iqr(daily_costs)
        trend = self.detect_trend(daily_costs)
        return {
            "total_days": len(daily_costs),
            "spike_indices": spikes,
            "iqr_anomalies": iqr_anomalies,
            "trend": trend,
            "spike_count": len(spikes),
            "anomaly_count": len(iqr_anomalies),
            "mean_daily_cost": round(mean(daily_costs), 2) if daily_costs else 0,
            "max_daily_cost": round(max(daily_costs), 2) if daily_costs else 0,
            "min_daily_cost": round(min(daily_costs), 2) if daily_costs else 0,
        }
