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
                "key": [1, 2],
                "year": [2025, 2025],
                "pop_total": [POP_TOTAL, POP_TOTAL * 2],
                "pop_pw": [POP_PW, POP_PW * 2],
                "pop_0_5": [POP_0_5, POP_0_5 * 2],
                "pop_0_1": [POP_0_1, POP_0_1 * 2],
                "pop_1_2": [POP_1_2, POP_1_2 * 2],
                "pop_vaccine_5_36_months": [
                    POP_VACCINE_5_36_MONTHS,
                    POP_VACCINE_5_36_MONTHS * 2,
                ],
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
            local_currency="ngn",
            budget_currency="ngn",
        )

        self.assertIn("year", result.keys())
        self.assertIn("interventions", result.keys())

        iptp = next(i for i in result["interventions"] if i["name"] == "iptp")

        correct_target_pop = POP_PW
        correct_iptp_cost = correct_target_pop * 0.8 * 3 * 1.1

        # formula: pop * coverage * doses * buffer
        self.assertAlmostEqual(iptp["total_pop"], correct_target_pop)
        self.assertAlmostEqual(iptp["total_cost"], correct_iptp_cost)
        self.assertEqual(len(iptp["cost_breakdown"]), 1)
        self.assertEqual(iptp["cost_breakdown"][0]["name"], "iptp")
        self.assertEqual(iptp["cost_breakdown"][0]["cost_class"], "Commodity")
        self.assertAlmostEqual(iptp["cost_breakdown"][0]["cost"], correct_iptp_cost)

    def test_get_budget_itn_routine(self):
        interventions = [
            InterventionDetailModel(name="itn_routine", type="PBO", places=[1]),
            InterventionDetailModel(
                name="itn_routine", type="Standard Pyrethroid", places=[2]
            ),
        ]

        cost_df = pd.DataFrame(
            {
                "code_intervention": ["itn_routine", "itn_routine"],
                "type_intervention": ["PBO", "Standard Pyrethroid"],
                "unit": ["per ITN", "per ITN"],
                "cost_class": ["Procurement", "Procurement"],
                "cost_year_for_analysis": [2025, 2025],
                "usd_cost": [3.49, 0.87],
                "ngn_cost": [5584.97, 1396.24],
                "cost_name": ["test", "test"],
            }
        )

        result = get_budget(
            year=2025,
            interventions_input=interventions,
            settings=DEFAULT_COST_ASSUMPTIONS,
            cost_df=cost_df,
            population_df=self.population_df,
            spatial_planning_unit="key",
            local_currency="ngn",
            budget_currency="usd",
        )

        self.assertIn("year", result.keys())
        self.assertIn("interventions", result.keys())

        itn_routine = next(
            i for i in result["interventions"] if i["name"] == "itn_routine"
        )

        correct_target_pop = (POP_PW + POP_0_5) * 3

        correct_target_pbo_cost = 3.49 * (POP_PW + POP_0_5) * 0.3 * 1.1
        correct_target_pyr_cost = 0.87 * (POP_PW * 2 + POP_0_5 * 2) * 0.3 * 1.1

        # formula: pop * coverage * doses * buffer
        self.assertAlmostEqual(itn_routine["total_pop"], correct_target_pop)
        self.assertAlmostEqual(
            itn_routine["total_cost"], correct_target_pbo_cost + correct_target_pyr_cost
        )
        self.assertEqual(len(itn_routine["cost_breakdown"]), 1)
        self.assertEqual(itn_routine["cost_breakdown"][0]["name"], "itn_routine")
        self.assertEqual(itn_routine["cost_breakdown"][0]["cost_class"], "Procurement")
        self.assertAlmostEqual(
            itn_routine["cost_breakdown"][0]["cost"],
            correct_target_pbo_cost + correct_target_pyr_cost,
        )

    def test_get_budget_itn_campaign(self):
        interventions = [
            InterventionDetailModel(name="itn_campaign", type="PBO", places=[1])
        ]

        cost_df = pd.DataFrame(
            {
                "code_intervention": ["itn_campaign"],
                "type_intervention": ["PBO"],
                "unit": ["per ITN"],
                "cost_class": ["Procurement"],
                "cost_year_for_analysis": [2025],
                "usd_cost": [3.49],
                "local_currency_cost": [5584.97],
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
            local_currency="ngn",
            budget_currency="usd",
        )

        self.assertIn("year", result.keys())
        self.assertIn("interventions", result.keys())

        itn_campaign = next(
            i for i in result["interventions"] if i["name"] == "itn_campaign"
        )

        correct_target_pop = (
            POP_TOTAL * DEFAULT_COST_ASSUMPTIONS["itn_campaign_coverage"]
        )

        correct_itn_campaign_cost = (
            3.49
            * POP_TOTAL
            * DEFAULT_COST_ASSUMPTIONS["itn_campaign_coverage"]
            * DEFAULT_COST_ASSUMPTIONS["itn_campaign_buffer_mult"]
            / DEFAULT_COST_ASSUMPTIONS["itn_campaign_divisor"]
        )

        # formula: ((pop * coverage) / divisor) * buffer * unit_cost
        self.assertAlmostEqual(itn_campaign["total_pop"], correct_target_pop)
        self.assertAlmostEqual(itn_campaign["total_cost"], correct_itn_campaign_cost)
        self.assertEqual(len(itn_campaign["cost_breakdown"]), 1)
        self.assertEqual(itn_campaign["cost_breakdown"][0]["name"], "itn_campaign")
        self.assertEqual(itn_campaign["cost_breakdown"][0]["cost_class"], "Procurement")
        self.assertAlmostEqual(
            itn_campaign["cost_breakdown"][0]["cost"], correct_itn_campaign_cost
        )

    def test_get_budget_smc(self):
        interventions = [InterventionDetailModel(name="smc", type="SP+AQ", places=[1])]

        cost_df = pd.DataFrame(
            {
                "code_intervention": ["smc", "smc"],
                "type_intervention": ["SP+AQ", "SP+AQ"],
                "unit": [
                    "per SPAQ pack 3-11 month olds",
                    "per SPAQ pack 12-59 month olds",
                ],
                "cost_class": ["Commodity", "Commodity"],
                "cost_year_for_analysis": [2025, 2025],
                "usd_cost": [0.29, 0.35],
                "local_currency_cost": [480.0, 480.0],
                "cost_name": ["test", "test"],
            }
        )

        result = get_budget(
            year=2025,
            interventions_input=interventions,
            settings=DEFAULT_COST_ASSUMPTIONS,
            cost_df=cost_df,
            population_df=self.population_df,
            spatial_planning_unit="key",
            local_currency="ngn",
            budget_currency="usd",
        )

        self.assertIn("year", result.keys())
        self.assertIn("interventions", result.keys())

        smc = next(i for i in result["interventions"] if i["name"] == "smc")

        # TODO
        # Each age group row in the budget has the full target_pop assigned
        # When summed across both age groups, this doubles the target_pop.
        # Note: This is the behaviour of the budget script, but it doesn't feel right
        correct_target_pop = (
            POP_0_5
            * (
                DEFAULT_COST_ASSUMPTIONS["smc_pop_prop_3_11"]
                + DEFAULT_COST_ASSUMPTIONS["smc_pop_prop_12_59"]
            )
            * DEFAULT_COST_ASSUMPTIONS["smc_coverage"]
            * 2
        )

        correct_smc_cost_3_11 = (
            0.29
            * POP_0_5
            * DEFAULT_COST_ASSUMPTIONS["smc_pop_prop_3_11"]
            * DEFAULT_COST_ASSUMPTIONS["smc_coverage"]
            * DEFAULT_COST_ASSUMPTIONS["smc_monthly_rounds"]
            * DEFAULT_COST_ASSUMPTIONS["smc_buffer_mult"]
        )
        correct_smc_cost_12_59 = (
            0.35
            * POP_0_5
            * DEFAULT_COST_ASSUMPTIONS["smc_pop_prop_12_59"]
            * DEFAULT_COST_ASSUMPTIONS["smc_coverage"]
            * DEFAULT_COST_ASSUMPTIONS["smc_monthly_rounds"]
            * DEFAULT_COST_ASSUMPTIONS["smc_buffer_mult"]
        )
        correct_smc_cost = correct_smc_cost_3_11 + correct_smc_cost_12_59

        # formula: target_pop * pop_prop * coverage * monthly_rounds * buffer * unit_cost
        # (for each age group)
        # target_pop = pop * (pop_prop_3_11 + pop_prop_12_59) * coverage
        # TODO: target_pop is duplicated across both age group rows, so total_pop is 2x
        self.assertAlmostEqual(smc["total_pop"], correct_target_pop)
        self.assertAlmostEqual(smc["total_cost"], correct_smc_cost)
        self.assertEqual(len(smc["cost_breakdown"]), 1)
        self.assertEqual(smc["cost_breakdown"][0]["name"], "smc")
        self.assertEqual(smc["cost_breakdown"][0]["cost_class"], "Commodity")
        self.assertAlmostEqual(smc["cost_breakdown"][0]["cost"], correct_smc_cost)

    def test_get_budget_pmc(self):
        interventions = [InterventionDetailModel(name="pmc", type="SP", places=[1])]

        cost_df = pd.DataFrame(
            {
                "code_intervention": ["pmc"],
                "type_intervention": ["SP"],
                "unit": ["per SP"],
                "cost_class": ["Commodity"],
                "cost_year_for_analysis": [2025],
                "usd_cost": [0.25],
                "local_currency_cost": [400.0],
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
            local_currency="ngn",
            budget_currency="usd",
        )

        self.assertIn("year", result.keys())
        self.assertIn("interventions", result.keys())

        pmc = next(i for i in result["interventions"] if i["name"] == "pmc")

        correct_target_pop = (
            POP_0_1 * DEFAULT_COST_ASSUMPTIONS["pmc_coverage"]
            + POP_1_2 * DEFAULT_COST_ASSUMPTIONS["pmc_coverage"]
        )

        # sp_0_1 = pop_0_1 * coverage * touchpoints * 1 * tablet_factor * buffer
        # sp_1_2 = pop_1_2 * coverage * touchpoints * 2 * tablet_factor * buffer
        sp_0_1 = (
            0.25
            * POP_0_1
            * DEFAULT_COST_ASSUMPTIONS["pmc_coverage"]
            * DEFAULT_COST_ASSUMPTIONS["pmc_touchpoints"]
            * 1  # 1 tablet per contact
            * DEFAULT_COST_ASSUMPTIONS["pmc_tablet_factor"]
            * DEFAULT_COST_ASSUMPTIONS["pmc_buffer_mult"]
        )
        sp_1_2 = (
            0.25
            * POP_1_2
            * DEFAULT_COST_ASSUMPTIONS["pmc_coverage"]
            * DEFAULT_COST_ASSUMPTIONS["pmc_touchpoints"]
            * 2  # 2 tablets per contact
            * DEFAULT_COST_ASSUMPTIONS["pmc_tablet_factor"]
            * DEFAULT_COST_ASSUMPTIONS["pmc_buffer_mult"]
        )
        correct_pmc_cost = sp_0_1 + sp_1_2

        # formula: (pop_0_1 * 1 tablet + pop_1_2 * 2 tablets)
        #           * coverage * scaling factor * touch points * buffer
        self.assertAlmostEqual(pmc["total_pop"], correct_target_pop)
        self.assertAlmostEqual(pmc["total_cost"], correct_pmc_cost)
        self.assertEqual(len(pmc["cost_breakdown"]), 1)
        self.assertEqual(pmc["cost_breakdown"][0]["name"], "pmc")
        self.assertEqual(pmc["cost_breakdown"][0]["cost_class"], "Commodity")
        self.assertAlmostEqual(pmc["cost_breakdown"][0]["cost"], correct_pmc_cost)

    def test_get_budget_vacc(self):
        interventions = [InterventionDetailModel(name="vacc", type="R21", places=[1])]

        cost_df = pd.DataFrame(
            {
                "code_intervention": ["vacc"],
                "type_intervention": ["R21"],
                "unit": ["per dose"],
                "cost_class": ["Commodity"],
                "cost_year_for_analysis": [2025],
                "usd_cost": [3.00],
                "local_currency_cost": [4800.0],
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
            local_currency="ngn",
            budget_currency="usd",
        )

        self.assertIn("year", result.keys())
        self.assertIn("interventions", result.keys())

        vacc = next(i for i in result["interventions"] if i["name"] == "vacc")

        correct_target_pop = (
            POP_VACCINE_5_36_MONTHS * DEFAULT_COST_ASSUMPTIONS["vacc_coverage"]
        )

        correct_vacc_cost = (
            3.00
            * POP_VACCINE_5_36_MONTHS
            * DEFAULT_COST_ASSUMPTIONS["vacc_coverage"]
            * DEFAULT_COST_ASSUMPTIONS["vacc_doses_per_child"]
            * DEFAULT_COST_ASSUMPTIONS["vacc_buffer_mult"]
        )

        # formula: pop * coverage * doses_per_child * buffer * unit_cost
        # target_pop = pop * coverage
        self.assertAlmostEqual(vacc["total_pop"], correct_target_pop)
        self.assertAlmostEqual(vacc["total_cost"], correct_vacc_cost)
        self.assertEqual(len(vacc["cost_breakdown"]), 1)
        self.assertEqual(vacc["cost_breakdown"][0]["name"], "vacc")
        self.assertEqual(vacc["cost_breakdown"][0]["cost_class"], "Commodity")
        self.assertAlmostEqual(vacc["cost_breakdown"][0]["cost"], correct_vacc_cost)
