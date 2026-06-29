import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC))

SAMPLE_RESOURCES = [
    {"resource_id": "i-abc123", "type": "ec2", "instance_type": "ec2_m5_large",
     "cpu_utilization": 5, "memory_utilization": 10, "monthly_cost": 250,
     "tags": {"environment": "development", "team": "platform"}},
    {"resource_id": "i-def456", "type": "ec2", "instance_type": "ec2_c5_2xlarge",
     "cpu_utilization": 85, "memory_utilization": 90, "monthly_cost": 800,
     "tags": {"environment": "production", "team": "backend"}},
    {"resource_id": "i-prod-db-primary", "type": "rds", "instance_type": "ec2_m5_large",
     "cpu_utilization": 2, "memory_utilization": 5, "monthly_cost": 500,
     "tags": {"environment": "production", "critical": "true"}},
    {"resource_id": "vol-orphan-001", "type": "ebs", "monthly_cost": 45,
     "size_gb": 100, "attached_to": None,
     "tags": {"environment": "development"}},
    {"resource_id": "vol-attached-002", "type": "ebs", "monthly_cost": 30,
     "size_gb": 50, "attached_to": "i-xyz789",
     "tags": {"environment": "production", "team": "backend"}},
]

SAMPLE_DAILY_COSTS = [15000, 15200, 14800, 15100, 21000, 14900, 15300, 50000, 15200, 15100]
