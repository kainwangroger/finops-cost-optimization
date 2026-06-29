DASHBOARD_CONFIG = {
    "title": "FinOps Cost Dashboard",
    "refresh_interval": 300,
    "panels": [
        {"title": "Total Monthly Spend", "type": "stat", "metric": "total_monthly_cost"},
        {"title": "Cost by Service", "type": "bar", "metric": "cost_by_service"},
        {"title": "Cost by Team", "type": "pie", "metric": "cost_by_team"},
        {"title": "Anomaly Alerts", "type": "table", "metric": "anomalies"},
        {"title": "Tagging Compliance", "type": "gauge", "metric": "tagging_compliance"},
        {"title": "Forecast vs Budget", "type": "graph", "metric": "forecast"},
        {"title": "Top 10 Resources by Cost", "type": "table", "metric": "top_resources"},
        {"title": "Savings Opportunities", "type": "table", "metric": "savings"},
    ],
}


def get_panel_config(metric: str) -> dict | None:
    return next((p for p in DASHBOARD_CONFIG["panels"] if p["metric"] == metric), None)
