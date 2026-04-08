import unittest

import pandas as pd

from snt_malaria_budgeting.core.quantification_functions import (
    SMCQuantification,
)


class TestSMCQuantification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up mock dataframes and settings once for all tests."""
        cls.settings = {}

        admin1 = "State A"
        admin2 = "LGA 1"
        year = 2025

        cls.scen_data = pd.DataFrame(
            {
                "adm1": [admin1],
                "adm2": [admin2],
                "year": [year],
                "scenario_name": ["Scenario with SMC intervention code"],
                "scenario_description": ["Test with only SMC intervention code"],
                "code_smc": [1],
                "type_smc": ["SMC"],
            }
        )

        cls.mock_population_data = pd.DataFrame(
            {
                "adm1": [admin1],
                "adm2": [admin2],
                "year": [year],
                "pop_0_5": [342988.7383],
            }
        )

        cls.cost_data = pd.DataFrame(
            {
                "code_intervention": [
                    "SMC",
                ],
                "type_intervention": [
                    "SMC",
                ],
                "unit": ["per SP"],
                "cost_class": ["Commodity"],
                "cost_year_for_analysis": 2025,
                "usd_cost": [1.0],
                "local_currency_cost": [584.0],
                "cost_name": ["test"],
            }
        )

    def test_smc_quantification(self):
        """Test that SMCQuantification returns expected results for a known code."""

        quant = SMCQuantification(
            spacial_unit="adm2",
            assumptions={
                "smc_coverage": 0.5,
                "smc_buffer_mult": 1.1,
                "smc_monthly_rounds": 1.5,
                "smc_pop_prop_3_11": 0.6,
                "smc_pop_prop_12_59": 0.3,
            },
        )
        result = quant.get_quantification(self.scen_data, self.mock_population_data)

        assumption_ratio = 0.5 * 1.1 * 1.5
        pop_0_5 = self.mock_population_data["pop_0_5"][0]
        expected_quantity_3_11 = pop_0_5 * 0.6 * assumption_ratio
        expected_quantity_12_59 = pop_0_5 * 0.3 * assumption_ratio

        self.assertEqual(len(result), 2)
        self.assertIn("quantity", result.columns)
        self.assertIn("target_pop", result.columns)
        self.assertIn("code_intervention", result.columns)
        self.assertIn("type_intervention", result.columns)
        self.assertIn("unit", result.columns)

        result_3_11 = result[result["unit"] == "per SPAQ pack 3-11 month olds"].iloc[0]

        self.assertAlmostEqual(result_3_11["quantity"], expected_quantity_3_11)
        self.assertAlmostEqual(
            result_3_11["target_pop"],
            pop_0_5 * (0.6 + 0.3) * 0.5,
        )

        result_12_59 = result[result["unit"] == "per SPAQ pack 12-59 month olds"].iloc[
            0
        ]
        self.assertAlmostEqual(result_12_59["quantity"], expected_quantity_12_59)
        self.assertAlmostEqual(
            result_12_59["target_pop"],
            pop_0_5 * (0.3 + 0.6) * 0.5,
        )

    def test_smc_quantification_empty_base(self):
        """Test that SMCQuantification returns an empty DataFrame when base data is empty."""

        empty_scen_data = self.scen_data[self.scen_data["adm2"] == "Nonexistent LGA"]
        empty_population_data = self.mock_population_data[
            self.mock_population_data["adm2"] == "Nonexistent LGA"
        ]

        quant = SMCQuantification(
            spacial_unit="adm2",
            assumptions={
                "smc_coverage": 0.5,
                "smc_buffer_mult": 1.1,
                "smc_monthly_rounds": 1.5,
                "smc_pop_prop_3_11": 0.6,
                "smc_pop_prop_12_59": 0.3,
            },
        )
        result = quant.get_quantification(empty_scen_data, empty_population_data)

        self.assertTrue(result.empty)

    def test_smc_quantification_missing_assumption(self):
        """Test that SMCQuantification uses default coverage when specific coverage assumption is missing."""

        quant_missing_coverage = SMCQuantification(
            spacial_unit="adm2",
            assumptions={
                "smc_buffer_mult": 1.1,
                "smc_monthly_rounds": 1.5,
                "smc_pop_prop_3_11": 0.6,
                "smc_pop_prop_12_59": 0.3,
            },
        )
        with self.assertRaises(ValueError):
            quant_missing_coverage.get_quantification(
                self.scen_data, self.mock_population_data
            )

        quant_missing_monthly_rounds = SMCQuantification(
            spacial_unit="adm2",
            assumptions={
                "smc_coverage": 0.5,
                "smc_buffer_mult": 1.1,
                "smc_pop_prop_3_11": 0.6,
                "smc_pop_prop_12_59": 0.3,
            },
        )
        with self.assertRaises(ValueError):
            quant_missing_monthly_rounds.get_quantification(
                self.scen_data, self.mock_population_data
            )

        quant_missing_buffer_mult = SMCQuantification(
            spacial_unit="adm2",
            assumptions={
                "smc_coverage": 0.5,
                "smc_monthly_rounds": 1.5,
                "smc_pop_prop_3_11": 0.6,
                "smc_pop_prop_12_59": 0.3,
            },
        )
        with self.assertRaises(ValueError):
            quant_missing_buffer_mult.get_quantification(
                self.scen_data, self.mock_population_data
            )

        quant_missing_prop_3_11 = SMCQuantification(
            spacial_unit="adm2",
            assumptions={
                "smc_coverage": 0.5,
                "smc_buffer_mult": 1.1,
                "smc_monthly_rounds": 1.5,
                "smc_pop_prop_12_59": 0.3,
            },
        )
        with self.assertRaises(ValueError):
            quant_missing_prop_3_11.get_quantification(
                self.scen_data, self.mock_population_data
            )

        quant_missing_prop_12_59 = SMCQuantification(
            spacial_unit="adm2",
            assumptions={
                "smc_coverage": 0.5,
                "smc_buffer_mult": 1.1,
                "smc_monthly_rounds": 1.5,
                "smc_pop_prop_3_11": 0.6,
            },
        )
        with self.assertRaises(ValueError):
            quant_missing_prop_12_59.get_quantification(
                self.scen_data, self.mock_population_data
            )

    def test_smc_quantification_different_code(self):
        """Test that SMCQuantification returns empty DataFrame when code does not match any column in scen_data."""

        quant = SMCQuantification(
            spacial_unit="adm2",
            assumptions={
                "smc_coverage": 0.5,
                "smc_buffer_mult": 1.1,
                "smc_monthly_rounds": 1.5,
                "smc_pop_prop_3_11": 0.6,
                "smc_pop_prop_12_59": 0.3,
            },
        )
        result = quant.get_quantification(pd.DataFrame(), self.mock_population_data)

        self.assertTrue(result.empty)

    def test_smc_quantification_missing_pop_column(self):
        """Test that SMCQuantification raises an error when population column is missing."""

        quant = SMCQuantification(
            spacial_unit="adm2",
            assumptions={
                "smc_coverage": 0.5,
                "smc_buffer_mult": 1.1,
                "smc_monthly_rounds": 1.5,
                "smc_pop_prop_3_11": 0.6,
                "smc_pop_prop_12_59": 0.3,
            },
        )
        with self.assertRaises(ValueError):
            quant.get_quantification(self.scen_data, pd.DataFrame())
