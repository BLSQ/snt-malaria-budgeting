import unittest
import pandas as pd

from snt_malaria_budgeting.core.budget_calculator import get_budget
from snt_malaria_budgeting.models import (
    DEFAULT_COST_ASSUMPTIONS,
    InterventionDetailModel,
)

POP_TOTAL = 250000
POP_PW = 12500
POP_0_5 = 45000
POP_0_1 = 10000
POP_1_2 = 10000
POP_VACCINE_5_36_MONTHS = 8000


class TestGetBudget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.population_df = pd.DataFrame(
            {
                "key": [1],
                "year": [2025],
                "pop_total": [POP_TOTAL],
                "pop_pw": [POP_PW],
                "pop_0_5": [POP_0_5],
                "pop_0_1": [POP_0_1],
                "pop_1_2": [POP_1_2],
                "pop_vaccine_5_36_months": [POP_VACCINE_5_36_MONTHS],
            }
        )

    def test_get_budget_iptp(self):
        interventions = [InterventionDetailModel(name="iptp", type="SP", places=[1])]
        cost_df = pd.DataFrame(
            {
                "code_intervention": ["iptp"],
                "type_intervention": ["SP"],
                "unit": ["per SP"],
                "cost_class": ["Commodity"],
                "cost_year_for_analysis": 2025,
                "usd_cost": [0.50558094],
                "local_currency_cost": [1],
                "cost_name": ["test"],
            }
        )

        result = get_budget(
            year=2025,
            interventions_input=interventions,
            settings=DEFAULT_COST_ASSUMPTIONS,
            cost_df=cost_df,
            population_df=self.population_df,
            spatial_planning_unit="key",
            local_currency="EUR",
        )

        self.assertIn("year", result.keys())
        self.assertIn("interventions", result.keys())

        iptp = next(i for i in result["interventions"] if i["name"] == "iptp")

        correct_target_pop = POP_PW

        # formula: pop * coverage * doses * buffer
        self.assertAlmostEqual(iptp["total_pop"], correct_target_pop)
        self.assertAlmostEqual(iptp["total_cost"], correct_target_pop * 0.8 * 3 * 1.1)
        self.assertEqual(len(iptp["cost_breakdown"]), 1)
        self.assertEqual(iptp["cost_breakdown"][0]["name"], "iptp")
        self.assertEqual(iptp["cost_breakdown"][0]["cost_class"], "Commodity")
        self.assertAlmostEqual(
            iptp["cost_breakdown"][0]["cost"], correct_target_pop * 0.8 * 3 * 1.1
        )
