import unittest
import pandas as pd

from snt_malaria_budgeting.core.budget_calculator import BudgetCalculator
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
                "key": [1001, 1002, 1001, 1002],
                "year": [2025, 2025, 2026, 2026],
                "pop_total": [POP_TOTAL, POP_TOTAL * 2, POP_TOTAL, POP_TOTAL * 2],
                "pop_pw": [POP_PW, POP_PW * 2, POP_PW, POP_PW * 2],
                "pop_0_5": [POP_0_5, POP_0_5 * 2, POP_0_5, POP_0_5 * 2],
                "pop_0_1": [POP_0_1, POP_0_1 * 2, POP_0_1, POP_0_1 * 2],
                "pop_1_2": [POP_1_2, POP_1_2 * 2, POP_1_2, POP_1_2 * 2],
                "pop_vaccine_5_36_months": [
                    POP_VACCINE_5_36_MONTHS,
                    POP_VACCINE_5_36_MONTHS * 2,
                    POP_VACCINE_5_36_MONTHS,
                    POP_VACCINE_5_36_MONTHS * 2,
                ],
            }
        )

    def test_get_budget_use_default_currency(self):
        interventions = [InterventionDetailModel(code="iptp", type="SP", places=[1001])]
        cost_df = pd.DataFrame(
            {
                "code_intervention": ["iptp", "iptp"],
                "type_intervention": ["SP", "SP"],
                "unit": ["per SP", "per SP"],
                "cost_class": ["Commodity", "Commodity"],
                "cost_year_for_analysis": [2025, 2026],
                "usd_cost": [0.50558094, 0.6069094],
                "local_currency_cost": [1, 1],
                "cost_name": ["test", "test"],
            }
        )

        budget_calculator = BudgetCalculator(
            interventions,
            DEFAULT_COST_ASSUMPTIONS,
            cost_df,
            self.population_df,
            local_currency="ngn",
            spatial_planning_unit="key",
        )

        interventions_costs = budget_calculator.get_intervention_costs(2025)
        places_costs = budget_calculator.get_places_costs(2025)

        self.assertIn("year", interventions_costs.keys())
        self.assertIn("interventions", interventions_costs.keys())

        iptp = next(
            i for i in interventions_costs["interventions"] if i["type"] == "SP"
        )

        correct_target_pop = POP_PW
        correct_iptp_cost = correct_target_pop * 0.8 * 3 * 1.1

        # formula: pop * coverage * doses * buffer
        self.assertAlmostEqual(iptp["total_pop"], correct_target_pop)
        self.assertAlmostEqual(iptp["total_cost"], correct_iptp_cost)
        self.assertEqual(iptp["type"], "SP")
        self.assertEqual(iptp["code"], "iptp")
        self.assertEqual(len(iptp["cost_breakdown"]), 1)
        self.assertEqual(iptp["cost_breakdown"][0]["cost_class"], "Commodity")
        self.assertAlmostEqual(iptp["cost_breakdown"][0]["cost"], correct_iptp_cost)

        self.assertIn(1001, places_costs.keys())
        place_1001 = places_costs[1001]
        self.assertAlmostEqual(place_1001["total_cost"], correct_iptp_cost)
        self.assertEqual(len(place_1001["interventions"]), 1)
        place_iptp = place_1001["interventions"][0]
        self.assertEqual(place_iptp["type"], "SP")
        self.assertEqual(place_iptp["code"], "iptp")
        self.assertAlmostEqual(place_iptp["cost"], correct_iptp_cost)

    def test_get_budget_iptp(self):
        interventions = [InterventionDetailModel(code="iptp", type="SP", places=[1001])]
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

        budget_calculator = BudgetCalculator(
            interventions_input=interventions,
            settings=DEFAULT_COST_ASSUMPTIONS,
            cost_df=cost_df,
            population_df=self.population_df,
            local_currency="ngn",
            spatial_planning_unit="key",
        )

        interventions_costs = budget_calculator.get_intervention_costs(2025)
        places_costs = budget_calculator.get_places_costs(2025)

        self.assertIn("year", interventions_costs.keys())
        self.assertIn("interventions", interventions_costs.keys())

        iptp = next(
            i for i in interventions_costs["interventions"] if i["type"] == "SP"
        )

        correct_target_pop = POP_PW
        correct_iptp_cost = correct_target_pop * 0.8 * 3 * 1.1

        # formula: pop * coverage * doses * buffer
        self.assertAlmostEqual(iptp["total_pop"], correct_target_pop)
        self.assertAlmostEqual(iptp["total_cost"], correct_iptp_cost)
        self.assertEqual(iptp["type"], "SP")
        self.assertEqual(iptp["code"], "iptp")
        self.assertEqual(len(iptp["cost_breakdown"]), 1)
        self.assertEqual(iptp["cost_breakdown"][0]["cost_class"], "Commodity")
        self.assertAlmostEqual(iptp["cost_breakdown"][0]["cost"], correct_iptp_cost)

        self.assertIn(1001, places_costs.keys())
        place_1001 = places_costs[1001]
        self.assertAlmostEqual(place_1001["total_cost"], correct_iptp_cost)
        self.assertEqual(len(place_1001["interventions"]), 1)
        place_iptp = place_1001["interventions"][0]
        self.assertEqual(place_iptp["type"], "SP")
        self.assertEqual(place_iptp["code"], "iptp")
        self.assertAlmostEqual(place_iptp["cost"], correct_iptp_cost)

    def test_get_budget_itn_routine(self):
        interventions = [
            InterventionDetailModel(code="itn_routine", type="PBO", places=[1001]),
            InterventionDetailModel(
                code="itn_routine", type="Standard Pyrethroid", places=[1002]
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

        budget_calculator = BudgetCalculator(
            interventions_input=interventions,
            settings=DEFAULT_COST_ASSUMPTIONS,
            cost_df=cost_df,
            population_df=self.population_df,
            local_currency="ngn",
            spatial_planning_unit="key",
            budget_currency="usd",
        )

        interventions_costs = budget_calculator.get_intervention_costs(2025)

        self.assertIn("year", interventions_costs.keys())
        self.assertIn("interventions", interventions_costs.keys())

        pbo_budget = next(
            i for i in interventions_costs["interventions"] if i["type"] == "PBO"
        )
        pyr_budget = next(
            i
            for i in interventions_costs["interventions"]
            if i["type"] == "Standard Pyrethroid"
        )

        correct_pbo_target_pop = POP_PW + POP_0_5
        correct_target_pbo_cost = 3.49 * correct_pbo_target_pop * 0.3 * 1.1

        # formula: pop * coverage * doses * buffer
        self.assertAlmostEqual(pbo_budget["total_pop"], correct_pbo_target_pop)
        self.assertAlmostEqual(pbo_budget["total_cost"], correct_target_pbo_cost)
        self.assertEqual(pbo_budget["type"], "PBO")
        self.assertEqual(pbo_budget["code"], "itn_routine")
        self.assertEqual(len(pbo_budget["cost_breakdown"]), 1)
        self.assertEqual(pbo_budget["cost_breakdown"][0]["cost_class"], "Procurement")
        self.assertAlmostEqual(
            pbo_budget["cost_breakdown"][0]["cost"], correct_target_pbo_cost
        )

        correct_pyr_target_pop = (POP_PW + POP_0_5) * 2
        correct_target_pyr_cost = 0.87 * correct_pyr_target_pop * 0.3 * 1.1

        self.assertAlmostEqual(pyr_budget["total_pop"], correct_pyr_target_pop)
        self.assertAlmostEqual(pyr_budget["total_cost"], correct_target_pyr_cost)
        self.assertEqual(pyr_budget["type"], "Standard Pyrethroid")
        self.assertEqual(pyr_budget["code"], "itn_routine")
        self.assertEqual(len(pyr_budget["cost_breakdown"]), 1)
        self.assertEqual(pyr_budget["cost_breakdown"][0]["cost_class"], "Procurement")
        self.assertAlmostEqual(
            pyr_budget["cost_breakdown"][0]["cost"], correct_target_pyr_cost
        )

    def test_get_budget_itn_campaign(self):
        interventions = [
            InterventionDetailModel(code="itn_campaign", type="PBO", places=[1001])
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

        budget_calculator = BudgetCalculator(
            interventions_input=interventions,
            settings=DEFAULT_COST_ASSUMPTIONS,
            cost_df=cost_df,
            population_df=self.population_df,
            local_currency="ngn",
            spatial_planning_unit="key",
            budget_currency="usd",
        )

        interventions_costs = budget_calculator.get_intervention_costs(2025)
        places_costs = budget_calculator.get_places_costs(2025)

        self.assertIn("year", interventions_costs.keys())
        self.assertIn("interventions", interventions_costs.keys())

        itn_campaign = next(
            i for i in interventions_costs["interventions"] if i["type"] == "PBO"
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
        self.assertEqual(itn_campaign["type"], "PBO")
        self.assertEqual(itn_campaign["code"], "itn_campaign")
        self.assertEqual(len(itn_campaign["cost_breakdown"]), 1)
        self.assertEqual(itn_campaign["cost_breakdown"][0]["cost_class"], "Procurement")
        self.assertAlmostEqual(
            itn_campaign["cost_breakdown"][0]["cost"], correct_itn_campaign_cost
        )

        self.assertIn(1001, places_costs.keys())
        place_1001 = places_costs[1001]
        self.assertAlmostEqual(place_1001["total_cost"], correct_itn_campaign_cost)
        self.assertEqual(len(place_1001["interventions"]), 1)
        place_iptp = place_1001["interventions"][0]
        self.assertEqual(place_iptp["type"], "PBO")
        self.assertEqual(place_iptp["code"], "itn_campaign")
        self.assertAlmostEqual(place_iptp["cost"], correct_itn_campaign_cost)

    def test_get_budget_smc(self):
        interventions = [
            InterventionDetailModel(code="smc", type="SP+AQ", places=[1001])
        ]

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

        budget_calculator = BudgetCalculator(
            interventions_input=interventions,
            settings=DEFAULT_COST_ASSUMPTIONS,
            cost_df=cost_df,
            population_df=self.population_df,
            local_currency="ngn",
            spatial_planning_unit="key",
            budget_currency="usd",
        )

        interventions_costs = budget_calculator.get_intervention_costs(2025)
        places_costs = budget_calculator.get_places_costs(2025)

        self.assertIn("year", interventions_costs.keys())
        self.assertIn("interventions", interventions_costs.keys())

        smc = next(
            i for i in interventions_costs["interventions"] if i["type"] == "SP+AQ"
        )

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
        self.assertEqual(smc["type"], "SP+AQ")
        self.assertEqual(smc["code"], "smc")
        self.assertEqual(len(smc["cost_breakdown"]), 1)
        self.assertEqual(smc["cost_breakdown"][0]["cost_class"], "Commodity")
        self.assertAlmostEqual(smc["cost_breakdown"][0]["cost"], correct_smc_cost)

        self.assertIn(1001, places_costs.keys())
        place_1001 = places_costs[1001]
        self.assertAlmostEqual(place_1001["total_cost"], correct_smc_cost)
        self.assertEqual(len(place_1001["interventions"]), 1)
        place_iptp = place_1001["interventions"][0]
        self.assertEqual(place_iptp["type"], "SP+AQ")
        self.assertEqual(place_iptp["code"], "smc")
        self.assertAlmostEqual(place_iptp["cost"], correct_smc_cost)

    def test_get_budget_pmc(self):
        interventions = [InterventionDetailModel(code="pmc", type="SP", places=[1001])]

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

        budget_calculator = BudgetCalculator(
            interventions_input=interventions,
            settings=DEFAULT_COST_ASSUMPTIONS,
            cost_df=cost_df,
            population_df=self.population_df,
            local_currency="ngn",
            spatial_planning_unit="key",
            budget_currency="usd",
        )

        interventions_costs = budget_calculator.get_intervention_costs(2025)
        places_costs = budget_calculator.get_places_costs(2025)

        self.assertIn("year", interventions_costs.keys())
        self.assertIn("interventions", interventions_costs.keys())

        pmc = next(i for i in interventions_costs["interventions"] if i["type"] == "SP")

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
        self.assertEqual(pmc["type"], "SP")
        self.assertEqual(pmc["code"], "pmc")
        self.assertEqual(len(pmc["cost_breakdown"]), 1)
        self.assertEqual(pmc["cost_breakdown"][0]["cost_class"], "Commodity")
        self.assertAlmostEqual(pmc["cost_breakdown"][0]["cost"], correct_pmc_cost)

        self.assertIn(1001, places_costs.keys())
        place_1001 = places_costs[1001]
        self.assertAlmostEqual(place_1001["total_cost"], correct_pmc_cost)
        self.assertEqual(len(place_1001["interventions"]), 1)
        place_iptp = place_1001["interventions"][0]
        self.assertEqual(place_iptp["type"], "SP")
        self.assertEqual(place_iptp["code"], "pmc")
        self.assertAlmostEqual(place_iptp["cost"], correct_pmc_cost)

    def test_get_budget_vacc(self):
        interventions = [
            InterventionDetailModel(code="vacc", type="R21", places=[1001])
        ]

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

        budget_calculator = BudgetCalculator(
            interventions_input=interventions,
            settings=DEFAULT_COST_ASSUMPTIONS,
            cost_df=cost_df,
            population_df=self.population_df,
            local_currency="ngn",
            spatial_planning_unit="key",
            budget_currency="usd",
        )

        interventions_costs = budget_calculator.get_intervention_costs(2025)
        places_costs = budget_calculator.get_places_costs(2025)

        self.assertIn("year", interventions_costs.keys())
        self.assertIn("interventions", interventions_costs.keys())

        vacc = next(
            i for i in interventions_costs["interventions"] if i["type"] == "R21"
        )

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
        self.assertEqual(vacc["type"], "R21")
        self.assertEqual(vacc["code"], "vacc")
        self.assertEqual(len(vacc["cost_breakdown"]), 1)
        self.assertEqual(vacc["cost_breakdown"][0]["cost_class"], "Commodity")
        self.assertAlmostEqual(vacc["cost_breakdown"][0]["cost"], correct_vacc_cost)

        self.assertIn(1001, places_costs.keys())
        place_1001 = places_costs[1001]
        self.assertAlmostEqual(place_1001["total_cost"], correct_vacc_cost)
        self.assertEqual(len(place_1001["interventions"]), 1)
        place_iptp = place_1001["interventions"][0]
        self.assertEqual(place_iptp["type"], "R21")
        self.assertEqual(place_iptp["code"], "vacc")
        self.assertAlmostEqual(place_iptp["cost"], correct_vacc_cost)

    def test_get_budget_multiple_interventions(self):
        interventions = [
            InterventionDetailModel(code="iptp", type="SP", places=[1001, 1002]),
            InterventionDetailModel(code="smc", type="SP+AQ", places=[1002]),
        ]

        cost_df = pd.DataFrame(
            {
                "code_intervention": ["iptp", "smc", "smc"],
                "type_intervention": ["SP", "SP+AQ", "SP+AQ"],
                "unit": [
                    "per SP",
                    "per SPAQ pack 3-11 month olds",
                    "per SPAQ pack 12-59 month olds",
                ],
                "cost_class": ["Commodity", "Commodity", "Commodity"],
                "cost_year_for_analysis": [2025, 2025, 2025],
                "usd_cost": [0.50558094, 0.29, 0.35],
                "local_currency_cost": [1, 480.0, 480.0],
                "cost_name": ["test", "test", "test"],
            }
        )

        budget_calculator = BudgetCalculator(
            interventions_input=interventions,
            settings=DEFAULT_COST_ASSUMPTIONS,
            cost_df=cost_df,
            population_df=self.population_df,
            local_currency="ngn",
            spatial_planning_unit="key",
            budget_currency="usd",
        )

        interventions_costs = budget_calculator.get_intervention_costs(2025)
        places_costs = budget_calculator.get_places_costs(2025)

        self.assertIn("year", interventions_costs.keys())
        self.assertIn("interventions", interventions_costs.keys())

        self.assertEqual(len(interventions_costs["interventions"]), 2)

        iptp = next(
            i for i in interventions_costs["interventions"] if i["type"] == "SP"
        )
        smc = next(
            i for i in interventions_costs["interventions"] if i["type"] == "SP+AQ"
        )

        correct_iptp_pop_location_1001 = POP_PW
        correct_iptp_pop_location_1002 = POP_PW * 2
        correct_iptp_target_pop = (
            correct_iptp_pop_location_1001 + correct_iptp_pop_location_1002
        )
        correct_iptp_cost = (
            correct_iptp_target_pop * 0.8 * 3 * 1.1 * 0.50558094
        )  # mutliplied by usd_cost

        correct_iptp_cost_location_1001 = (
            correct_iptp_pop_location_1001 * 0.8 * 3 * 1.1 * 0.50558094
        )
        correct_iptp_cost_location_1002 = (
            correct_iptp_pop_location_1002 * 0.8 * 3 * 1.1 * 0.50558094
        )

        self.assertAlmostEqual(iptp["total_pop"], correct_iptp_target_pop)
        self.assertAlmostEqual(iptp["total_cost"], correct_iptp_cost)
        self.assertEqual(iptp["type"], "SP")
        self.assertEqual(iptp["code"], "iptp")
        self.assertEqual(len(iptp["cost_breakdown"]), 1)
        self.assertEqual(iptp["cost_breakdown"][0]["cost_class"], "Commodity")
        self.assertAlmostEqual(iptp["cost_breakdown"][0]["cost"], correct_iptp_cost)

        correct_smc_target_pop = (
            POP_0_5
            * (
                DEFAULT_COST_ASSUMPTIONS["smc_pop_prop_3_11"]
                + DEFAULT_COST_ASSUMPTIONS["smc_pop_prop_12_59"]
            )
            * DEFAULT_COST_ASSUMPTIONS["smc_coverage"]
            * 2
        ) * 2  # Doubled for location 1002

        correct_smc_cost_3_11 = (
            0.29
            * POP_0_5
            * DEFAULT_COST_ASSUMPTIONS["smc_pop_prop_3_11"]
            * DEFAULT_COST_ASSUMPTIONS["smc_coverage"]
            * DEFAULT_COST_ASSUMPTIONS["smc_monthly_rounds"]
            * DEFAULT_COST_ASSUMPTIONS["smc_buffer_mult"]
        ) * 2  # Doubled for location 1002
        correct_smc_cost_12_59 = (
            0.35
            * POP_0_5
            * DEFAULT_COST_ASSUMPTIONS["smc_pop_prop_12_59"]
            * DEFAULT_COST_ASSUMPTIONS["smc_coverage"]
            * DEFAULT_COST_ASSUMPTIONS["smc_monthly_rounds"]
            * DEFAULT_COST_ASSUMPTIONS["smc_buffer_mult"]
        ) * 2  # Doubled for location 1002

        correct_smc_cost = correct_smc_cost_3_11 + correct_smc_cost_12_59

        self.assertAlmostEqual(smc["total_pop"], correct_smc_target_pop)
        self.assertAlmostEqual(smc["total_cost"], correct_smc_cost)
        self.assertEqual(smc["type"], "SP+AQ")
        self.assertEqual(smc["code"], "smc")
        self.assertEqual(len(smc["cost_breakdown"]), 1)
        self.assertEqual(smc["cost_breakdown"][0]["cost_class"], "Commodity")
        self.assertAlmostEqual(smc["cost_breakdown"][0]["cost"], correct_smc_cost)

        self.assertIn(1001, places_costs.keys())
        place_1001 = places_costs[1001]
        self.assertAlmostEqual(
            place_1001["total_cost"], correct_iptp_cost_location_1001
        )
        self.assertEqual(len(place_1001["interventions"]), 1)
        place_iptp = place_1001["interventions"][0]
        self.assertEqual(place_iptp["type"], "SP")
        self.assertEqual(place_iptp["code"], "iptp")
        self.assertAlmostEqual(place_iptp["cost"], correct_iptp_cost_location_1001)

        self.assertIn(1002, places_costs.keys())
        place_1002 = places_costs[1002]
        self.assertAlmostEqual(
            place_1002["total_cost"], correct_iptp_cost_location_1002 + correct_smc_cost
        )
        self.assertEqual(len(place_1002["interventions"]), 2)
        place_iptp = place_1002["interventions"][0]
        self.assertEqual(place_iptp["type"], "SP")
        self.assertEqual(place_iptp["code"], "iptp")
        self.assertAlmostEqual(place_iptp["cost"], correct_iptp_cost_location_1002)
        place_smc = place_1002["interventions"][1]
        self.assertEqual(place_smc["type"], "SP+AQ")
        self.assertEqual(place_smc["code"], "smc")
        self.assertAlmostEqual(place_smc["cost"], correct_smc_cost)
