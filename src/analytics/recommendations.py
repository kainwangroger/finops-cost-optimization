from typing import Optional


RESOURCE_RATES = {
    "ec2_t3_medium": {"compute": 0.0416, "memory_gb": 4},
    "ec2_m5_large": {"compute": 0.096, "memory_gb": 8},
    "ec2_c5_2xlarge": {"compute": 0.34, "memory_gb": 16},
    "ec2_r5_xlarge": {"compute": 0.252, "memory_gb": 32},
    "aks_d2s_v3": {"compute": 0.075, "memory_gb": 8},
    "aks_d4s_v3": {"compute": 0.15, "memory_gb": 16},
    "aks_d8s_v3": {"compute": 0.30, "memory_gb": 32},
    "gce_n2_standard_2": {"compute": 0.079, "memory_gb": 8},
    "gce_n2_standard_4": {"compute": 0.158, "memory_gb": 16},
    "gce_n2_standard_8": {"compute": 0.316, "memory_gb": 32},
}

RI_DISCOUNT = 0.30
SP_DISCOUNT = 0.15


class RecommendationEngine:
    def __init__(self):
        self.rates = RESOURCE_RATES

    def detect_idle_resources(self, resources: list[dict]) -> list[dict]:
        idle = []
        for r in resources:
            if r.get("cpu_utilization", 100) < 5 and r.get("days_active", 30) > 7:
                idle.append({
                    "resource_id": r["resource_id"],
                    "type": r.get("type", "unknown"),
                    "cpu_pct": r.get("cpu_utilization", 0),
                    "monthly_cost": r.get("monthly_cost", 0),
                    "action": "stop_or_delete",
                    "savings_monthly": round(r.get("monthly_cost", 0) * 0.9, 2),
                })
        return idle

    def detect_orphaned_volumes(self, volumes: list[dict]) -> list[dict]:
        orphaned = []
        for v in volumes:
            if not v.get("attached_to"):
                orphaned.append({
                    "volume_id": v["volume_id"],
                    "size_gb": v.get("size_gb", 0),
                    "monthly_cost": v.get("monthly_cost", 0),
                    "action": "delete",
                    "savings_monthly": v.get("monthly_cost", 0),
                })
        return orphaned

    def rightsizing_recommendations(self, resources: list[dict]) -> list[dict]:
        recommendations = []
        for r in resources:
            cpu = r.get("cpu_utilization", 50)
            memory = r.get("memory_utilization", 50)
            current_type = r.get("instance_type", "")
            current_cost = r.get("monthly_cost", 0)

            if cpu < 20 and memory < 20:
                target = self._downsize(current_type)
                if target:
                    target_rate = self.rates.get(target, {}).get("compute", 0)
                    current_rate = self.rates.get(current_type, {}).get("compute", 0.1)
                    savings = round((current_rate - target_rate) * 730, 2) if current_rate > 0 else 0
                    recommendations.append({
                        "resource_id": r["resource_id"],
                        "current_type": current_type,
                        "recommended_type": target,
                        "reason": "Low utilization (CPU < 20%, Memory < 20%)",
                        "monthly_savings": savings,
                    })
            elif cpu > 80 and memory > 80:
                target = self._upsize(current_type)
                if target:
                    recommendations.append({
                        "resource_id": r["resource_id"],
                        "current_type": current_type,
                        "recommended_type": target,
                        "reason": "High utilization (CPU > 80%, Memory > 80%)",
                        "monthly_savings": 0,
                        "note": "Upsize recommended to prevent performance degradation",
                    })
        return recommendations

    def ri_sp_recommendations(self, resources: list[dict]) -> list[dict]:
        recommendations = []
        for r in resources:
            monthly = r.get("monthly_cost", 0)
            if monthly > 100:
                ri_cost = round(monthly * (1 - RI_DISCOUNT), 2)
                sp_cost = round(monthly * (1 - SP_DISCOUNT), 2)
                recommendations.append({
                    "resource_id": r["resource_id"],
                    "instance_type": r.get("instance_type", ""),
                    "on_demand_cost": monthly,
                    "ri_cost": ri_cost,
                    "ri_savings": round(monthly - ri_cost, 2),
                    "sp_cost": sp_cost,
                    "sp_savings": round(monthly - sp_cost, 2),
                    "recommendation": "ri" if monthly > 500 else "sp",
                })
        return recommendations

    def _downsize(self, instance_type: str) -> Optional[str]:
        chain = {
            "ec2_c5_2xlarge": "ec2_m5_large",
            "ec2_m5_large": "ec2_t3_medium",
            "aks_d8s_v3": "aks_d4s_v3",
            "aks_d4s_v3": "aks_d2s_v3",
            "gce_n2_standard_8": "gce_n2_standard_4",
            "gce_n2_standard_4": "gce_n2_standard_2",
        }
        return chain.get(instance_type)

    def _upsize(self, instance_type: str) -> Optional[str]:
        chain = {
            "ec2_t3_medium": "ec2_m5_large",
            "ec2_m5_large": "ec2_c5_2xlarge",
            "aks_d2s_v3": "aks_d4s_v3",
            "aks_d4s_v3": "aks_d8s_v3",
            "gce_n2_standard_2": "gce_n2_standard_4",
            "gce_n2_standard_4": "gce_n2_standard_8",
        }
        return chain.get(instance_type)
