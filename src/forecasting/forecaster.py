from datetime import datetime, timezone
from statistics import mean, stdev


class CostForecaster:
    def __init__(self, budget: float = 500000):
        self.budget = budget

    def moving_average_forecast(self, historical: list[float], window: int = 7, periods: int = 30) -> list[float]:
        if len(historical) < window:
            avg = mean(historical) if historical else 0
            return [round(avg, 2)] * periods
        forecast = []
        recent = historical[-window:]
        baseline = mean(recent)
        for i in range(periods):
            forecast.append(round(baseline, 2))
        return forecast

    def linear_regression_forecast(self, historical: list[float], periods: int = 30) -> list[float]:
        n = len(historical)
        if n < 2:
            avg = mean(historical) if historical else 0
            return [round(avg, 2)] * periods
        x = list(range(n))
        y = historical
        x_mean = mean(x)
        y_mean = mean(y)
        numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y))
        denominator = sum((xi - x_mean) ** 2 for xi in x)
        slope = numerator / denominator if denominator != 0 else 0
        intercept = y_mean - slope * x_mean
        forecast = []
        for i in range(periods):
            forecast.append(round(slope * (n + i) + intercept, 2))
        return forecast

    def budget_tracking(self, historical: list[float], forecast: list[float]) -> dict:
        if not historical:
            return {"budget": self.budget, "status": "no_data"}
        total_spent = sum(historical)
        projected_total = total_spent + sum(forecast)
        remaining = self.budget - total_spent
        over_budget = projected_total > self.budget
        return {
            "budget": self.budget,
            "total_spent": round(total_spent, 2),
            "projected_total": round(projected_total, 2),
            "remaining": round(remaining, 2),
            "over_budget": over_budget,
            "spend_pct": round(total_spent / self.budget * 100, 1) if self.budget > 0 else 0,
            "status": "over_budget" if over_budget else "on_track",
        }

    def what_if(self, historical: list[float], reduction_pct: float) -> dict:
        if not historical:
            return {}
        avg_daily = mean(historical)
        current_monthly = avg_daily * 30
        reduced_monthly = current_monthly * (1 - reduction_pct / 100)
        annual_savings = (current_monthly - reduced_monthly) * 12
        return {
            "current_monthly": round(current_monthly, 2),
            "reduced_monthly": round(reduced_monthly, 2),
            "savings_monthly": round(current_monthly - reduced_monthly, 2),
            "annual_savings": round(annual_savings, 2),
            "reduction_pct": reduction_pct,
        }

    def monthly_projections(self, historical: list[float], months: int = 12) -> list[dict]:
        if len(historical) < 30:
            avg = mean(historical) if historical else 0
            return [{"month": i + 1, "projected_cost": round(avg * 30, 2)} for i in range(months)]
        recent = historical[-30:]
        daily_avg = mean(recent)
        projections = []
        for m in range(months):
            projections.append({
                "month": m + 1,
                "projected_cost": round(daily_avg * 30, 2),
            })
        return projections
