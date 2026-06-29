import subprocess
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCKER_COMPOSE = REPO_ROOT / "docker-compose.yml"


class TestDockerCompose:
    def test_compose_file_exists(self):
        assert DOCKER_COMPOSE.exists()

    def test_compose_syntax(self):
        result = subprocess.run(
            ["docker", "compose", "-f", str(DOCKER_COMPOSE), "config", "-q"],
            capture_output=True, timeout=30,
        )
        assert result.returncode == 0, f"Invalid compose syntax: {result.stderr.decode()}"

    def test_compose_has_services(self):
        result = subprocess.run(
            ["docker", "compose", "-f", str(DOCKER_COMPOSE), "config", "--services"],
            capture_output=True, timeout=30,
        )
        services = result.stdout.decode().strip().split("\n")
        assert "clickhouse" in services
        assert "postgres" in services
        assert "streamlit" in services


class TestSourceModules:
    def test_collector_imports(self):
        from collector import AWSCollector, AzureCollector, GCPCollector
        assert AWSCollector().provider == "aws"
        assert AzureCollector().provider == "azure"
        assert GCPCollector().provider == "gcp"

    def test_analytics_imports(self):
        from analytics import AnomalyDetector, RecommendationEngine, TaggingAnalyzer
        assert AnomalyDetector().threshold == 2.0
        assert RecommendationEngine().rates is not None
        assert TaggingAnalyzer().required_tags is not None

    def test_automation_import(self):
        from automation import RemediationEngine
        assert RemediationEngine().dry_run is True

    def test_forecasting_import(self):
        from forecasting import CostForecaster
        assert CostForecaster().budget == 500000

    def test_policies_import(self):
        from policies import PolicyEngine
        assert PolicyEngine().policies is not None

    def test_compute_daily_costs(self):
        from collector.aws_collector import AWSCollector
        from collector.azure_collector import AzureCollector
        from collector.gcp_collector import GCPCollector
        aws = AWSCollector()
        azure = AzureCollector()
        gcp = GCPCollector()
        aws.collect(30)
        azure.collect(30)
        gcp.collect(30)
        assert aws.total_cost() > 0
        assert azure.total_cost() > 0
        assert gcp.total_cost() > 0

    def test_end_to_end_cost_flow(self):
        from collector.aws_collector import AWSCollector
        from analytics.anomaly_detector import AnomalyDetector
        from analytics.recommendations import RecommendationEngine
        from forecasting.forecaster import CostForecaster

        collector = AWSCollector()
        collector.collect(30)
        total = collector.total_cost()
        assert total > 0

        detector = AnomalyDetector()
        report = detector.anomaly_report([total] * 30)
        assert report["mean_daily_cost"] > 0

        engine = RecommendationEngine()
        recs = engine.ri_sp_recommendations([{"resource_id": "test", "monthly_cost": total}])
        assert len(recs) > 0

        forecaster = CostForecaster()
        tracking = forecaster.budget_tracking([total / 30] * 30, [total / 30] * 30)
        assert tracking["status"] in ("on_track", "over_budget")


class TestConfigFiles:
    def test_requirements_dev(self):
        path = REPO_ROOT / "requirements-dev.txt"
        assert path.exists()
        content = path.read_text()
        assert "pytest" in content

    def test_gitignore(self):
        path = REPO_ROOT / ".gitignore"
        assert path.exists()
        content = path.read_text()
        assert "__pycache__" in content

    def test_src_directory_structure(self):
        src = REPO_ROOT / "src"
        assert (src / "collector").is_dir()
        assert (src / "analytics").is_dir()
        assert (src / "automation").is_dir()
        assert (src / "forecasting").is_dir()
        assert (src / "policies").is_dir()
        assert (src / "dashboard").is_dir()

    def test_tests_directory_has_files(self):
        tests = REPO_ROOT / "tests"
        files = list(tests.glob("test_*.py"))
        assert len(files) >= 6
