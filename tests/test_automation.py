from automation.remediation import RemediationEngine
from conftest import SAMPLE_RESOURCES


class TestRemediationEngine:
    def setup_method(self):
        self.engine = RemediationEngine(dry_run=True)

    def test_auto_stop_idle(self):
        resources = [
            {"resource_id": "i-idle-01", "type": "ec2", "cpu_utilization": 2, "monthly_cost": 100,
             "tags": {"environment": "development"}},
        ]
        actions = self.engine.auto_stop_idle(resources, hour=0)
        assert len(actions) >= 1
        assert all(a["dry_run"] is True for a in actions)

    def test_auto_stop_protected_resource(self):
        resources = [
            {"resource_id": "i-idle-01", "type": "ec2", "cpu_utilization": 2, "monthly_cost": 100,
             "tags": {"environment": "development"}},
            {"resource_id": "i-prod-critical", "type": "rds", "cpu_utilization": 1, "monthly_cost": 500,
             "tags": {"environment": "production", "critical": "true"}},
        ]
        actions = self.engine.auto_stop_idle(resources, hour=0)
        prod_ids = [a["resource_id"] for a in actions]
        assert "i-prod-critical" not in prod_ids
        assert "i-idle-01" in prod_ids

    def test_downsize_overprovisioned(self):
        actions = self.engine.downsize_overprovisioned(SAMPLE_RESOURCES)
        assert len(actions) >= 1
        assert all(a["action"] == "downsize" for a in actions)

    def test_downsize_protected(self):
        actions = self.engine.downsize_overprovisioned(SAMPLE_RESOURCES)
        prod_ids = [a["resource_id"] for a in actions]
        assert "i-prod-db-primary" not in prod_ids

    def test_enforce_budget(self):
        actions = self.engine.enforce_budget(SAMPLE_RESOURCES, budget=100)
        assert len(actions) >= 1

    def test_enforce_budget_no_action(self):
        actions = self.engine.enforce_budget(SAMPLE_RESOURCES, budget=100000)
        assert len(actions) == 0

    def test_dry_run_true_by_default(self):
        assert self.engine.dry_run is True

    def test_execute_action_no_dry_run(self):
        engine = RemediationEngine(dry_run=False)
        action = engine._execute_action("stop", {"resource_id": "test", "type": "ec2"})
        assert action["dry_run"] is False
        assert len(engine.actions_log) == 1

    def test_summary_empty(self):
        assert self.engine.summary()["total_actions"] == 0

    def test_summary_with_actions(self):
        engine = RemediationEngine(dry_run=False)
        engine._execute_action("stop", {"resource_id": "r1", "type": "ec2"})
        summary = engine.summary()
        assert summary["total_actions"] == 1
