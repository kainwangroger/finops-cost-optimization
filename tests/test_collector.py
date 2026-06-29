from collector.base_collector import CostCollector, CostEntry
from collector.aws_collector import AWSCollector
from collector.azure_collector import AzureCollector
from collector.gcp_collector import GCPCollector


class TestCostEntry:
    def test_create_entry(self):
        e = CostEntry(service="ec2", region="us-east-1", amount=100.50)
        assert e.service == "ec2"
        assert e.region == "us-east-1"
        assert e.amount == 100.50
        assert e.currency == "USD"

    def test_entry_defaults(self):
        e = CostEntry(service="s3", region="eu-west-1", amount=50)
        assert e.tags == {}
        assert e.account_id == ""
        assert e.resource_id == ""


class TestAWSCollector:
    def setup_method(self):
        self.collector = AWSCollector()

    def test_collect_returns_entries(self):
        entries = self.collector.collect(30)
        assert len(entries) == 50  # 10 services * 5 regions

    def test_collect_clears_previous(self):
        self.collector.collect(30)
        self.collector.collect(7)
        assert len(self.collector._entries) == 50

    def test_total_cost(self):
        self.collector.collect(30)
        total = self.collector.total_cost()
        assert total > 0

    def test_cost_by_service(self):
        self.collector.collect(30)
        by_service = self.collector.cost_by_service()
        assert "ec2" in by_service
        assert "s3" in by_service
        assert by_service["ec2"] > 0

    def test_cost_by_region(self):
        self.collector.collect(30)
        by_region = self.collector.cost_by_region()
        assert "us-east-1" in by_region
        assert len(by_region) == 5

    def test_cost_by_tag(self):
        self.collector.collect(30)
        by_env = self.collector.cost_by_tag("environment")
        assert "production" in by_env or "mixed" in by_env

    def test_filter_by_service(self):
        self.collector.collect(30)
        ec2_entries = self.collector.filter_by_service("ec2")
        assert len(ec2_entries) == 5
        assert all(e.service == "ec2" for e in ec2_entries)

    def test_filter_by_region(self):
        self.collector.collect(30)
        use1 = self.collector.filter_by_region("us-east-1")
        assert all(e.region == "us-east-1" for e in use1)

    def test_top_services(self):
        self.collector.collect(30)
        top = self.collector.top_services(3)
        assert len(top) == 3
        assert top[0]["cost"] >= top[1]["cost"]

    def test_provider_name(self):
        assert self.collector.provider == "aws"


class TestAzureCollector:
    def setup_method(self):
        self.collector = AzureCollector()

    def test_collect_returns_entries(self):
        entries = self.collector.collect(30)
        assert len(entries) == 32  # 8 services * 4 regions

    def test_cost_by_service(self):
        self.collector.collect(30)
        by_service = self.collector.cost_by_service()
        assert "vm" in by_service
        assert "storage" in by_service

    def test_cost_by_tag(self):
        self.collector.collect(30)
        by_team = self.collector.cost_by_tag("team")
        assert "platform" in by_team

    def test_provider_name(self):
        assert self.collector.provider == "azure"

    def test_vm_cost(self):
        entry = self.collector._compute_daily("vm", {"vms": 1, "hourly_rate": 0.28})
        assert round(entry, 2) == 6.72  # 1 * 0.28 * 24

    def test_storage_cost(self):
        entry = self.collector._compute_daily("storage", {"tb": 1, "monthly_per_tb": 20})
        assert round(entry, 4) == round(20 / 30, 4)


class TestGCPCollector:
    def setup_method(self):
        self.collector = GCPCollector()

    def test_collect_returns_entries(self):
        entries = self.collector.collect(30)
        assert len(entries) == 21  # 7 services * 3 regions

    def test_cost_by_service(self):
        self.collector.collect(30)
        by_service = self.collector.cost_by_service()
        assert "compute_engine" in by_service
        assert "bigquery" in by_service

    def test_provider_name(self):
        assert self.collector.provider == "gcp"

    def test_bigquery_cost(self):
        entry = self.collector._compute_daily("bigquery", {"slots": 100, "cost_per_slot_hour": 0.04})
        assert entry == 96.0  # 100 * 0.04 * 24

    def test_total_cost_all_providers(self):
        aws = AWSCollector()
        azure = AzureCollector()
        gcp = GCPCollector()
        aws.collect(30)
        azure.collect(30)
        gcp.collect(30)
        grand_total = aws.total_cost() + azure.total_cost() + gcp.total_cost()
        assert grand_total > 10000


class TestCollectorEdgeCases:
    def test_collect_zero_days(self):
        aws = AWSCollector()
        entries = aws.collect(0)
        assert all(e.amount == 0 for e in entries)

    def test_empty_filter(self):
        aws = AWSCollector()
        aws.collect(30)
        none_entries = aws.filter_by_service("nonexistent")
        assert none_entries == []

    def test_top_services_all(self):
        aws = AWSCollector()
        aws.collect(30)
        top = aws.top_services(100)
        assert len(top) == 10
