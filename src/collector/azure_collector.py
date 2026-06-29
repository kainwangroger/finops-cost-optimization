from datetime import datetime, timezone
from collector.base_collector import CostCollector, CostEntry


class AzureCollector(CostCollector):
    SERVICES = {
        "vm": {"vms": 120, "hourly_rate": 0.28},
        "storage": {"tb": 25, "monthly_per_tb": 20.0},
        "sql_database": {"databases": 15, "hourly_rate": 0.52},
        "databricks": {"workers": 20, "hourly_rate": 0.55},
        "synapse": {"units": 10, "hourly_rate": 1.20},
        "function_app": {"executions_m": 80, "cost_per_m": 0.15},
        "cosmos_db": {"rUs": 5000, "cost_per_100ru": 0.008},
        "aks": {"nodes": 8, "hourly_rate": 0.12},
    }
    REGIONS = ["eastus", "westeurope", "francecentral", "southeastasia"]

    def __init__(self):
        super().__init__("azure")

    def collect(self, days_back: int = 30) -> list[CostEntry]:
        self._entries.clear()
        for service, specs in self.SERVICES.items():
            for region in self.REGIONS:
                daily = self._compute_daily(service, specs)
                amount = round(daily * days_back, 2)
                entry = CostEntry(
                    service=service,
                    region=region,
                    amount=amount,
                    date=datetime.now(timezone.utc).isoformat()[:10],
                    tags={"environment": self._env_for(service), "team": self._team_for(service),
                          "cost_center": self._cost_center_for(service)},
                    account_id="sub-aaaa-bbbb-cccc-dddd",
                )
                self._entries.append(entry)
        return self._entries

    def _compute_daily(self, service: str, specs: dict) -> float:
        if "hourly_rate" in specs:
            count_key = {"vm": "vms", "databricks": "workers", "sql_database": "databases", "aks": "nodes"}
            count = specs.get(count_key.get(service, ""), 1)
            return count * specs["hourly_rate"] * 24
        if "monthly_per_tb" in specs:
            return specs["tb"] * specs["monthly_per_tb"] / 30
        if "cost_per_m" in specs:
            return specs["executions_m"] * specs["cost_per_m"] / 30
        if "cost_per_100ru" in specs:
            return specs["rUs"] * specs["cost_per_100ru"] * 24 / 100
        return 0.0

    def _env_for(self, service: str) -> str:
        if service in ("sql_database", "synapse", "cosmos_db"):
            return "production"
        if service in ("databricks",):
            return "analytics"
        return "mixed"

    def _team_for(self, service: str) -> str:
        teams = {"vm": "platform", "storage": "data", "sql_database": "backend",
                 "databricks": "data", "synapse": "analytics", "function_app": "backend",
                 "cosmos_db": "backend", "aks": "platform"}
        return teams.get(service, "unknown")

    def _cost_center_for(self, service: str) -> str:
        centers = {"vm": "infra", "storage": "data", "sql_database": "prod-data",
                   "databricks": "analytics", "synapse": "analytics",
                   "function_app": "dev", "cosmos_db": "prod-data", "aks": "infra"}
        return centers.get(service, "general")
