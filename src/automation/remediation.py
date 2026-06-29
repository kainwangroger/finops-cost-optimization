from datetime import datetime, timezone
from typing import Optional

PRODUCTION_TAGS = {"environment": "production"}
PROTECTED_RESOURCES = ["prod-db-primary", "prod-etl-master", "prod-api-core"]


class RemediationEngine:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.actions_log: list[dict] = []

    def auto_stop_idle(self, resources: list[dict], hour: int = 19) -> list[dict]:
        actions = []
        now_hour = datetime.now(timezone.utc).hour
        for r in resources:
            if self._is_protected(r):
                continue
            cpu = r.get("cpu_utilization", 100)
            if cpu < 5 and now_hour >= hour:
                action = self._execute_action("stop", r)
                actions.append(action)
        return actions

    def downsize_overprovisioned(self, resources: list[dict]) -> list[dict]:
        actions = []
        for r in resources:
            if self._is_protected(r):
                continue
            cpu = r.get("cpu_utilization", 50)
            memory = r.get("memory_utilization", 50)
            if cpu < 20 and memory < 20:
                action = self._execute_action("downsize", r)
                actions.append(action)
        return actions

    def enforce_budget(self, resources: list[dict], budget: float) -> list[dict]:
        actions = []
        total = sum(r.get("monthly_cost", 0) for r in resources)
        if total > budget:
            for r in sorted(resources, key=lambda x: x.get("monthly_cost", 0), reverse=True):
                if self._is_protected(r):
                    continue
                action = self._execute_action("stop", r)
                actions.append(action)
                total -= r.get("monthly_cost", 0)
                if total <= budget:
                    break
        return actions

    def _is_protected(self, resource: dict) -> bool:
        if resource.get("resource_id") in PROTECTED_RESOURCES:
            return True
        tags = resource.get("tags", {})
        return tags.get("environment") == "production" and tags.get("critical") == "true"

    def _execute_action(self, action_type: str, resource: dict) -> dict:
        action = {
            "action": action_type,
            "resource_id": resource.get("resource_id", "unknown"),
            "type": resource.get("type", "unknown"),
            "dry_run": self.dry_run,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if not self.dry_run:
            self.actions_log.append(action)
        return action

    def summary(self) -> dict:
        return {
            "total_actions": len(self.actions_log),
            "dry_run": self.dry_run,
            "actions": self.actions_log,
        }
