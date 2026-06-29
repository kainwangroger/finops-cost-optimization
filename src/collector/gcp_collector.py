from datetime import datetime, timezone
from collector.base_collector import CostCollector, CostEntry


class GCPCollector(CostCollector):
    SERVICES = {
        "compute_engine": {"vms": 65, "hourly_rate": 0.24},
        "cloud_storage": {"tb": 30, "monthly_per_tb": 15.0},
        "bigquery": {"slots": 2000, "cost_per_slot_hour": 0.04},
        "dataflow": {"workers": 15, "hourly_rate": 0.35},
        "pubsub": {"throughput_mb": 500, "cost_per_mb": 0.04},
        "dataproc": {"clusters": 4, "hourly_rate": 0.30},
        "composer": {"environments": 2, "hourly_rate": 0.45},
    }
    REGIONS = ["us-central1", "europe-west1", "asia-east1"]

    def __init__(self):
        super().__init__("gcp")

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
                          "project": self._project_for(service)},
                    account_id="project-123456",
                )
                self._entries.append(entry)
        return self._entries

    def _compute_daily(self, service: str, specs: dict) -> float:
        if "hourly_rate" in specs and "vms" in specs:
            return specs["vms"] * specs["hourly_rate"] * 24
        if "monthly_per_tb" in specs:
            return specs["tb"] * specs["monthly_per_tb"] / 30
        if "cost_per_slot_hour" in specs:
            return specs["slots"] * specs["cost_per_slot_hour"] * 24
        if "hourly_rate" in specs:
            return specs.get("workers", specs.get("clusters", specs.get("environments", 1))) * specs["hourly_rate"] * 24
        if "cost_per_mb" in specs:
            return specs["throughput_mb"] * specs["cost_per_mb"] * 24
        return 0.0

    def _env_for(self, service: str) -> str:
        if service in ("bigquery", "dataflow"):
            return "analytics"
        if service in ("composer",):
            return "orchestration"
        return "mixed"

    def _team_for(self, service: str) -> str:
        teams = {"compute_engine": "platform", "cloud_storage": "data", "bigquery": "analytics",
                 "dataflow": "data", "pubsub": "platform", "dataproc": "data", "composer": "data"}
        return teams.get(service, "unknown")

    def _project_for(self, service: str) -> str:
        projects = {"compute_engine": "shared-infra", "cloud_storage": "data-lake",
                    "bigquery": "analytics-prod", "dataflow": "streaming-pipelines",
                    "pubsub": "shared-infra", "dataproc": "batch-processing",
                    "composer": "orchestration"}
        return projects.get(service, "default")
