REQUIRED_TAGS = ["environment", "team", "cost_center", "project", "owner"]
RECOMMENDED_TAGS = ["version", "terraform", "backup", "encryption"]


class TaggingAnalyzer:
    def __init__(self, required_tags: list[str] | None = None):
        self.required_tags = required_tags or REQUIRED_TAGS

    def compliance_rate(self, resources: list[dict]) -> float:
        if not resources:
            return 100.0
        total = len(resources) * len(self.required_tags)
        if total == 0:
            return 100.0
        present = sum(
            1 for r in resources
            for tag in self.required_tags
            if r.get("tags", {}).get(tag)
        )
        return round(present / total * 100, 1)

    def untagged_resources(self, resources: list[dict]) -> list[dict]:
        untagged = []
        for r in resources:
            tags = r.get("tags", {})
            missing = [t for t in self.required_tags if not tags.get(t)]
            if missing:
                untagged.append({
                    "resource_id": r["resource_id"],
                    "type": r.get("type", "unknown"),
                    "missing_tags": missing,
                    "suggested_tags": self._suggest_tags(r),
                })
        return untagged

    def tag_coverage_report(self, resources: list[dict]) -> dict:
        if not resources:
            return {"coverage": {}, "overall": 100.0, "untagged_count": 0}
        coverage = {}
        for tag in self.required_tags:
            tagged = sum(1 for r in resources if r.get("tags", {}).get(tag))
            coverage[tag] = round(tagged / len(resources) * 100, 1)
        untagged = len(self.untagged_resources(resources))
        return {
            "coverage": coverage,
            "overall": self.compliance_rate(resources),
            "total_resources": len(resources),
            "untagged_count": untagged,
            "untagged_pct": round(untagged / len(resources) * 100, 1),
        }

    def _suggest_tags(self, resource: dict) -> dict:
        rtype = resource.get("type", "").lower()
        env = "production" if any(k in rtype for k in ["prod", "db", "redis"]) else "development"
        return {"environment": env, "team": "unknown", "cost_center": "general"}
