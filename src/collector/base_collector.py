from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class CostEntry:
    service: str
    region: str
    amount: float
    currency: str = "USD"
    date: str = ""
    tags: dict = field(default_factory=dict)
    resource_id: str = ""
    account_id: str = ""


class CostCollector(ABC):
    def __init__(self, provider: str):
        self.provider = provider
        self._entries: list[CostEntry] = []

    @abstractmethod
    def collect(self, days_back: int = 30) -> list[CostEntry]:
        pass

    def total_cost(self) -> float:
        return round(sum(e.amount for e in self._entries), 2)

    def cost_by_service(self) -> dict[str, float]:
        result: dict[str, float] = {}
        for e in self._entries:
            result[e.service] = round(result.get(e.service, 0) + e.amount, 2)
        return result

    def cost_by_region(self) -> dict[str, float]:
        result: dict[str, float] = {}
        for e in self._entries:
            result[e.region] = round(result.get(e.region, 0) + e.amount, 2)
        return result

    def cost_by_tag(self, tag_key: str) -> dict[str, float]:
        result: dict[str, float] = {}
        for e in self._entries:
            val = e.tags.get(tag_key, "untagged")
            result[val] = round(result.get(val, 0) + e.amount, 2)
        return result

    def filter_by_service(self, service: str) -> list[CostEntry]:
        return [e for e in self._entries if e.service == service]

    def filter_by_region(self, region: str) -> list[CostEntry]:
        return [e for e in self._entries if e.region == region]

    def top_services(self, n: int = 5) -> list[dict]:
        by_service = self.cost_by_service()
        sorted_services = sorted(by_service.items(), key=lambda x: x[1], reverse=True)
        return [{"service": svc, "cost": cost} for svc, cost in sorted_services[:n]]
