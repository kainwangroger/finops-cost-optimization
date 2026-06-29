from datetime import datetime, timezone, timedelta
from collector.base_collector import CostCollector, CostEntry


class AWSCollector(CostCollector):
    SERVICES = {
        "ec2": {"instances": 45, "hourly_rate": 0.32},
        "s3": {"tb": 12, "monthly_per_tb": 23.0},
        "rds": {"instances": 8, "hourly_rate": 0.48},
        "lambda": {"invocations_m": 50, "cost_per_m": 0.20},
        "kinesis": {"shards": 24, "hourly_rate": 0.030},
        "emr": {"clusters": 3, "hourly_rate": 0.42},
        "redshift": {"nodes": 6, "hourly_rate": 0.85},
        "elasticache": {"nodes": 4, "hourly_rate": 0.34},
        "vpc": {"nat_gateways": 2, "hourly_rate": 0.045},
        "cloudwatch": {"metrics": 500, "cost_per_metric": 0.30},
    }
    REGIONS = ["us-east-1", "us-west-2", "eu-west-1", "eu-central-1", "ap-southeast-1"]

    def __init__(self):
        super().__init__("aws")

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
                    tags={"environment": self._env_for(service), "team": self._team_for(service)},
                    account_id="123456789012",
                )
                self._entries.append(entry)
        return self._entries

    def _compute_daily(self, service: str, specs: dict) -> float:
        if "hourly_rate" in specs:
            count_key = {"ec2": "instances", "rds": "instances", "kinesis": "shards",
                         "emr": "clusters", "redshift": "nodes", "elasticache": "nodes",
                         "vpc": "nat_gateways"}
            count = specs.get(count_key.get(service, ""), 1)
            return count * specs["hourly_rate"] * 24
        if "monthly_per_tb" in specs:
            return specs["tb"] * specs["monthly_per_tb"] / 30
        if "cost_per_m" in specs:
            return specs["invocations_m"] * specs["cost_per_m"] / 30
        return 0.0

    def _env_for(self, service: str) -> str:
        if service in ("rds", "redshift", "elasticache"):
            return "production"
        if service in ("emr", "kinesis"):
            return "analytics"
        return "mixed"

    def _team_for(self, service: str) -> str:
        teams = {"ec2": "platform", "s3": "data", "rds": "backend", "lambda": "backend",
                 "kinesis": "data", "emr": "data", "redshift": "analytics",
                 "elasticache": "backend", "vpc": "platform", "cloudwatch": "platform"}
        return teams.get(service, "unknown")
