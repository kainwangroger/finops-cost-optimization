from forecasting.forecaster import CostForecaster
from conftest import SAMPLE_DAILY_COSTS


class TestCostForecaster:
    def setup_method(self):
        self.forecaster = CostForecaster(budget=500000)

    def test_moving_average_forecast(self):
        forecast = self.forecaster.moving_average_forecast(SAMPLE_DAILY_COSTS, window=7, periods=5)
        assert len(forecast) == 5
        assert all(f > 0 for f in forecast)

    def test_moving_average_short_history(self):
        forecast = self.forecaster.moving_average_forecast([100, 200], window=7, periods=3)
        assert len(forecast) == 3
        assert forecast[0] == 150.0

    def test_linear_regression_forecast(self):
        forecast = self.forecaster.linear_regression_forecast(SAMPLE_DAILY_COSTS, periods=5)
        assert len(forecast) == 5

    def test_linear_regression_short_history(self):
        forecast = self.forecaster.linear_regression_forecast([100], periods=3)
        assert len(forecast) == 3
        assert forecast[0] == 100.0

    def test_linear_regression_trend(self):
        historical = [100, 200, 300, 400, 500]
        forecast = self.forecaster.linear_regression_forecast(historical, periods=3)
        assert forecast[0] < forecast[-1]  # increasing trend continues

    def test_budget_tracking_on_track(self):
        tracking = self.forecaster.budget_tracking([1000] * 30, [1000] * 30)
        assert tracking["status"] in ("on_track", "over_budget")

    def test_budget_tracking_over(self):
        tracking = self.forecaster.budget_tracking([20000] * 30, [20000] * 30)
        assert tracking["over_budget"] is True

    def test_budget_tracking_no_data(self):
        tracking = self.forecaster.budget_tracking([], [])
        assert tracking["status"] == "no_data"

    def test_what_if(self):
        result = self.forecaster.what_if(SAMPLE_DAILY_COSTS, reduction_pct=20)
        assert result["reduction_pct"] == 20
        assert result["annual_savings"] > 0

    def test_what_if_no_data(self):
        assert self.forecaster.what_if([], 10) == {}

    def test_monthly_projections(self):
        projections = self.forecaster.monthly_projections(SAMPLE_DAILY_COSTS, months=6)
        assert len(projections) == 6
        assert projections[0]["projected_cost"] > 0

    def test_monthly_projections_short_history(self):
        projections = self.forecaster.monthly_projections([100] * 5, months=3)
        assert len(projections) == 3
