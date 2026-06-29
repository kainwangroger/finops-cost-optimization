from typing import Any

BUDGET_POLICIES = [
    {"name": "monthly_budget_500k", "max_monthly": 500000, "action": "alert"},
    {"name": "team_budget_100k", "max_monthly": 100000, "scope": "team", "action": "alert"},
    {"name": "dev_budget_10k", "max_monthly": 10000, "scope": "environment", "env": "development", "action": "auto_stop"},
]

TAGGING_POLICIES = [
    {"name": "require_environment_tag", "tag": "environment", "required": True},
    {"name": "require_team_tag", "tag": "team", "required": True},
    {"name": "require_cost_center_tag", "tag": "cost_center", "required": True},
]


class PolicyEngine:
    def __init__(self, policies: list[dict] | None = None):
        self.policies = policies or BUDGET_POLICIES + TAGGING_POLICIES

    def validate_budget(self, current_spend: float, policy_name: str = "monthly_budget_500k") -> dict:
        policy = next((p for p in BUDGET_POLICIES if p["name"] == policy_name), None)
        if not policy:
            return {"policy": policy_name, "valid": True, "error": "not_found"}
        max_budget = policy["max_monthly"]
        return {
            "policy": policy_name,
            "current_spend": current_spend,
            "max_budget": max_budget,
            "valid": current_spend <= max_budget,
            "overage": round(max(0, current_spend - max_budget), 2),
            "action": policy["action"],
        }

    def validate_tagging(self, resource: dict) -> dict:
        tags = resource.get("tags", {})
        violations = []
        for policy in TAGGING_POLICIES:
            tag_key = policy["tag"]
            if policy["required"] and not tags.get(tag_key):
                violations.append({
                    "policy": policy["name"],
                    "tag": tag_key,
                    "status": "violation",
                })
        return {
            "resource_id": resource.get("resource_id", "unknown"),
            "compliant": len(violations) == 0,
            "violations": violations,
        }

    def validate_all_tagging(self, resources: list[dict]) -> dict:
        results = [self.validate_tagging(r) for r in resources]
        compliant = sum(1 for r in results if r["compliant"])
        return {
            "total": len(resources),
            "compliant": compliant,
            "non_compliant": len(resources) - compliant,
            "compliance_pct": round(compliant / len(resources) * 100, 1) if resources else 100.0,
            "results": results,
        }

    def suggest_policy_actions(self, current_spend: float, resources: list[dict]) -> list[dict]:
        actions = []
        budget_result = self.validate_budget(current_spend)
        if not budget_result["valid"]:
            actions.append({
                "type": "budget_alert",
                "message": f"Monthly spend ${current_spend:,.0f} exceeds ${budget_result['max_budget']:,} budget by ${budget_result['overage']:,.0f}",
                "suggested_action": budget_result["action"],
            })
        tagging_results = self.validate_all_tagging(resources)
        if tagging_results["non_compliant"] > 0:
            actions.append({
                "type": "tagging_compliance",
                "message": f"{tagging_results['non_compliant']} resources have missing required tags",
                "suggested_action": "update_tags",
            })
        return actions
