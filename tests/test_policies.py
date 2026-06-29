from policies.policies import PolicyEngine
from conftest import SAMPLE_RESOURCES


class TestPolicyEngine:
    def setup_method(self):
        self.engine = PolicyEngine()

    def test_validate_budget_under(self):
        result = self.engine.validate_budget(100000)
        assert result["valid"] is True
        assert result["policy"] == "monthly_budget_500k"

    def test_validate_budget_over(self):
        result = self.engine.validate_budget(600000)
        assert result["valid"] is False
        assert result["overage"] == 100000

    def test_validate_budget_not_found(self):
        result = self.engine.validate_budget(100, "nonexistent")
        assert result["valid"] is True
        assert result["error"] == "not_found"

    def test_validate_tagging_compliant(self):
        resource = {"resource_id": "r1", "tags": {"environment": "prod", "team": "a", "cost_center": "b"}}
        result = self.engine.validate_tagging(resource)
        assert result["compliant"] is True

    def test_validate_tagging_violation(self):
        resource = {"resource_id": "r1", "tags": {"env": "prod"}}
        result = self.engine.validate_tagging(resource)
        assert result["compliant"] is False
        assert len(result["violations"]) >= 1

    def test_validate_all_tagging(self):
        result = self.engine.validate_all_tagging(SAMPLE_RESOURCES)
        assert result["total"] == 5
        assert result["compliance_pct"] >= 0

    def test_suggest_policy_actions_budget(self):
        actions = self.engine.suggest_policy_actions(600000, SAMPLE_RESOURCES)
        budget_actions = [a for a in actions if a["type"] == "budget_alert"]
        assert len(budget_actions) == 1

    def test_suggest_policy_actions_tagging(self):
        untagged_resources = [{"resource_id": "r1", "type": "ec2", "tags": {}}]
        actions = self.engine.suggest_policy_actions(100000, untagged_resources)
        tagging_actions = [a for a in actions if a["type"] == "tagging_compliance"]
        assert len(tagging_actions) == 1

    def test_suggest_policy_actions_all_ok(self):
        compliant = [{"resource_id": "r1", "tags": {"environment": "p", "team": "t", "cost_center": "c", "project": "p", "owner": "o"}}]
        actions = self.engine.suggest_policy_actions(100000, compliant)
        assert len(actions) == 0
