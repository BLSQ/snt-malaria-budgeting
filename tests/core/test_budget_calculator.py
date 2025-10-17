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

        cls.cost_df = pd.DataFrame(
            {
                "code_intervention": [
                    "itn_campaign",
                    "itn_campaign",
                    "itn_routine",
                    "iptp",
                    "smc",
                    "smc",
                    "smc",
                    "pmc",
                    "pmc",
                    "vacc",
                    "vacc",
                    "cm_public",
                    "cm_public",
                    "cm_public",
                    "cm_public",
                ],
                "type_intervention": [
                    "Dual AI",
                    "Dual AI",
                    "Dual AI",
                    "SP",
                    "SP+AQ",
                    "SP+AQ",
                    "SP+AQ",
                    "SP",
                    "SP",
                    "R21",
                    "R21",
                    "RDT kits",
                    "AL",
                    "Artesunate injections",
                    "RAS",
                ],
                "unit": [
                    "per ITN",
                    "per bale",
                    "per ITN",
                    "per SP",
                    "per SPAQ pack 3-11 month olds",
                    "per SPAQ pack 12-59 month olds",
                    "per child",
                    "per SP",
                    "per child",
                    "per dose",
                    "per child",
                    "per RDT kit",
                    "per AL",
                    "per 60mg powder",
                    "per RAS",
                ],
                "cost_class": ["Commodity"] * 15,
                "cost_year_for_analysis": 2025,
                "usd_cost": [
                    3.490605554,
                    6.25,
                    3.490605554,
                    0.50558094,
                    0.24375,
                    0.271875,
                    1.33,
                    0.204375,
                    0.08125,
                    4.0,
                    1.0,
                    0.4625,
                    1.22,
                    2.003125,
                    0.439375,
                ],
                "cost_name": ["test"] * 15,
            }
        )

    def test_get_budget_success(self):
        interventions = [InterventionDetailModel(name="iptp", type="SP", places=[1])]

        result = get_budget(
            country="RDC",
            year=2025,
            interventions_input=interventions,
            settings=DEFAULT_COST_ASSUMPTIONS,
            cost_df=self.cost_df,
            population_df=self.population_df,
            spatial_planning_unit="key",
        )

        self.assertIn("year", result.keys())
        self.assertIn("interventions", result.keys())

        iptp = next(i for i in result["interventions"] if i["name"] == "iptp")

        correct_target_pop = POP_PW

        # pop * coverage * doses * buffer
        self.assertAlmostEqual(iptp["total_pop"], correct_target_pop)
        self.assertAlmostEqual(iptp["total_cost"], correct_target_pop * 0.8 * 3 * 1.1)
        self.assertEqual(len(iptp["cost_breakdown"]), 1)
        self.assertEqual(iptp["cost_breakdown"][0]["name"], "iptp")
        self.assertEqual(iptp["cost_breakdown"][0]["cost_class"], "Commodity")
        self.assertAlmostEqual(
            iptp["cost_breakdown"][0]["cost"], correct_target_pop * 0.8 * 3 * 1.1
        )
