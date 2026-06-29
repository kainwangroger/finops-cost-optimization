from analytics.anomaly_detector import AnomalyDetector
from analytics.recommendations import RecommendationEngine
from analytics.tagging import TaggingAnalyzer
from conftest import SAMPLE_RESOURCES, SAMPLE_DAILY_COSTS


class TestAnomalyDetector:
    def setup_method(self):
        self.detector = AnomalyDetector(threshold=2.0)

    def test_z_scores(self):
        values = [10, 10, 10, 10, 10]
        scores = self.detector.z_scores(values)
        assert all(s == 0.0 for s in scores)

    def test_z_scores_identifies_spike(self):
        values = [10, 10, 10, 500, 10, 10, 10, 10]
        scores = self.detector.z_scores(values)
        assert abs(scores[3]) > 2.0

    def test_detect_spikes(self):
        values = [10, 10, 10, 500, 10, 10, 10]
        spikes = self.detector.detect_spikes(values)
        assert 3 in spikes

    def test_detect_spikes_no_spikes(self):
        values = [10, 11, 10, 12, 10]
        spikes = self.detector.detect_spikes(values)
        assert len(spikes) == 0

    def test_detect_by_iqr(self):
        values = [10, 12, 11, 13, 10, 100, 11, 12]
        anomalies = self.detector.detect_by_iqr(values)
        assert 5 in anomalies

    def test_detect_by_iqr_insufficient(self):
        assert self.detector.detect_by_iqr([1, 2, 3]) == []

    def test_moving_average(self):
        values = [10, 20, 30, 40, 50]
        ma = self.detector.moving_average(values, window=3)
        assert len(ma) == 5
        assert ma[-1] == 40.0  # (30+40+50)/3

    def test_moving_average_small_window(self):
        values = [10, 20]
        ma = self.detector.moving_average(values, window=5)
        assert ma == [15.0, 15.0]

    def test_detect_trend_increasing(self):
        values = [10, 20, 30, 40, 50, 60]
        assert self.detector.detect_trend(values) == "increasing"

    def test_detect_trend_decreasing(self):
        values = [60, 50, 40, 30, 20, 10]
        assert self.detector.detect_trend(values) == "decreasing"

    def test_detect_trend_stable(self):
        values = [30, 31, 29, 30, 31, 30]
        assert self.detector.detect_trend(values) == "stable"

    def test_detect_trend_insufficient(self):
        assert self.detector.detect_trend([10]) == "insufficient_data"

    def test_anomaly_report(self):
        report = self.detector.anomaly_report(SAMPLE_DAILY_COSTS)
        assert report["total_days"] == 10
        assert report["spike_count"] >= 0
        assert report["mean_daily_cost"] > 0
        assert report["max_daily_cost"] > report["min_daily_cost"]


class TestRecommendationEngine:
    def setup_method(self):
        self.engine = RecommendationEngine()

    def test_detect_idle_resources(self):
        idle = self.engine.detect_idle_resources(SAMPLE_RESOURCES)
        assert len(idle) >= 1
        assert all(r["action"] == "stop_or_delete" for r in idle)

    def test_idle_resource_has_savings(self):
        idle = self.engine.detect_idle_resources(SAMPLE_RESOURCES)
        for r in idle:
            assert r["savings_monthly"] > 0

    def test_detect_orphaned_volumes(self):
        volumes = [
            {"volume_id": "vol-orphan-001", "size_gb": 100, "monthly_cost": 45, "attached_to": None},
            {"volume_id": "vol-attached-002", "size_gb": 50, "monthly_cost": 30, "attached_to": "i-xyz"},
        ]
        orphaned = self.engine.detect_orphaned_volumes(volumes)
        assert len(orphaned) == 1
        assert orphaned[0]["volume_id"] == "vol-orphan-001"

    def test_orphaned_volume_action(self):
        volumes = [{"volume_id": "vol-orphan-001", "size_gb": 100, "monthly_cost": 45, "attached_to": None}]
        orphaned = self.engine.detect_orphaned_volumes(volumes)
        assert orphaned[0]["action"] == "delete"

    def test_rightsizing_downsize(self):
        recs = self.engine.rightsizing_recommendations(SAMPLE_RESOURCES)
        downsize = [r for r in recs if r.get("monthly_savings", 0) > 0]
        assert len(downsize) >= 1

    def test_rightsizing_upsize(self):
        resources = [{"resource_id": "i-small", "type": "ec2", "instance_type": "ec2_t3_medium",
                      "cpu_utilization": 90, "memory_utilization": 85, "monthly_cost": 100}]
        recs = self.engine.rightsizing_recommendations(resources)
        upsize = [r for r in recs if r.get("note")]
        assert len(upsize) == 1
        assert upsize[0]["recommended_type"] == "ec2_m5_large"

    def test_ri_sp_recommendations(self):
        recs = self.engine.ri_sp_recommendations(SAMPLE_RESOURCES)
        assert len(recs) >= 1
        for r in recs:
            assert r["ri_savings"] > 0

    def test_ri_sp_low_cost_no_rec(self):
        recs = self.engine.ri_sp_recommendations([{"resource_id": "low", "monthly_cost": 10}])
        assert len(recs) == 0


class TestTaggingAnalyzer:
    def setup_method(self):
        self.analyzer = TaggingAnalyzer()

    def test_compliance_rate_full(self):
        resources = [{"tags": {"environment": "prod", "team": "a", "cost_center": "b", "project": "c", "owner": "d"}}]
        assert self.analyzer.compliance_rate(resources) == 100.0

    def test_compliance_rate_partial(self):
        resources = [{"tags": {"environment": "prod"}}]
        rate = self.analyzer.compliance_rate(resources)
        assert rate == 20.0  # 1/5 tags present

    def test_compliance_rate_empty(self):
        assert self.analyzer.compliance_rate([]) == 100.0

    def test_untagged_resources(self):
        resources = [{"resource_id": "r1", "type": "ec2", "tags": {"env": "prod"}}]
        untagged = self.analyzer.untagged_resources(resources)
        assert len(untagged) == 1
        assert "environment" in untagged[0]["missing_tags"]
        assert "team" in untagged[0]["missing_tags"]

    def test_untagged_resources_suggestions(self):
        resources = [{"resource_id": "r1", "type": "ec2", "tags": {}}]
        untagged = self.analyzer.untagged_resources(resources)
        assert "environment" in untagged[0]["suggested_tags"]

    def test_tag_coverage_report(self):
        resources = [
            {"resource_id": "r1", "type": "ec2", "tags": {"environment": "prod", "team": "a", "cost_center": "b", "project": "c", "owner": "d"}},
            {"resource_id": "r2", "type": "s3", "tags": {"environment": "dev"}},
        ]
        report = self.analyzer.tag_coverage_report(resources)
        assert report["total_resources"] == 2
        assert report["overall"] == 60.0  # 6/10
        assert report["untagged_count"] == 1

    def test_tag_coverage_report_empty(self):
        report = self.analyzer.tag_coverage_report([])
        assert report["overall"] == 100.0
