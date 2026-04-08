import unittest

import pandas as pd

from snt_malaria_budgeting.core.quantification_functions import (
    PMCQuantification,
)


class TestPMCQuantification(unittest.TestCase):
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
                "scenario_name": ["Scenario with PMC intervention code"],
                "scenario_description": ["Test with only PMC intervention code"],
                "code_pmc": [1],
                "type_pmc": ["PMC"],
            }
        )

        cls.mock_population_data = pd.DataFrame(
            {
                "adm1": [admin1],
                "adm2": [admin2],
                "year": [year],
                "pop_0_1": [342988.7383],
                "pop_1_2": [20134.897],
            }
        )

        cls.cost_data = pd.DataFrame(
            {
                "code_intervention": [
                    "pmc",
                ],
                "type_intervention": [
                    "PMC",
                ],
                "unit": ["per SP"],
                "cost_class": ["Commodity"],
                "cost_year_for_analysis": 2025,
                "usd_cost": [1.0],
                "local_currency_cost": [584.0],
                "cost_name": ["test"],
            }
        )

    def test_pmc_quantification(self):
        """Test that PMCQuantification returns expected results for a known code."""

        quant = PMCQuantification(
            spacial_unit="adm2",
            assumptions={
                "pmc_coverage": 0.5,
                "pmc_touchpoints": 1.5,
                "pmc_tablet_factor": 1.1,
                "pmc_buffer_mult": 1.1,
            },
        )
        result = quant.get_quantification(self.scen_data, self.mock_population_data)

        assumption_ratio = 0.5 * 1.5 * 1.1 * 1.1
        expected_quantity = (
            self.mock_population_data["pop_0_1"][0] * assumption_ratio
            + self.mock_population_data["pop_1_2"][0] * assumption_ratio * 2
        )

        self.assertEqual(len(result), 1)
        self.assertIn("quantity", result.columns)
        self.assertIn("target_pop", result.columns)
        self.assertIn("code_intervention", result.columns)
        self.assertIn("type_intervention", result.columns)
        self.assertIn("unit", result.columns)

        net_result = result[result["unit"] == "per SP"].iloc[0]

        self.assertAlmostEqual(net_result["quantity"], expected_quantity)
        self.assertAlmostEqual(
            net_result["target_pop"],
            self.mock_population_data["pop_0_1"][0] * 0.5
            + self.mock_population_data["pop_1_2"][0] * 0.5,
        )

    def test_pmc_quantification_empty_base(self):
        """Test that PMCQuantification returns an empty DataFrame when base data is empty."""

        empty_scen_data = self.scen_data[self.scen_data["adm2"] == "Nonexistent LGA"]
        empty_population_data = self.mock_population_data[
            self.mock_population_data["adm2"] == "Nonexistent LGA"
        ]

        quant = PMCQuantification(
            spacial_unit="adm2",
            assumptions={
                "pmc_coverage": 0.5,
                "pmc_touchpoints": 1.5,
                "pmc_tablet_factor": 1.1,
                "pmc_buffer_mult": 1.1,
            },
        )
        result = quant.get_quantification(empty_scen_data, empty_population_data)

        self.assertTrue(result.empty)

    def test_pmc_quantification_missing_assumption(self):
        """Test that PMCQuantification uses default coverage when specific coverage assumption is missing."""

        quant_missing_coverage = PMCQuantification(
            spacial_unit="adm2",
            assumptions={
                "pmc_touchpoints": 1.5,
                "pmc_tablet_factor": 1.1,
                "pmc_buffer_mult": 1.1,
            },
        )
        with self.assertRaises(ValueError):
            quant_missing_coverage.get_quantification(
                self.scen_data, self.mock_population_data
            )

        quant_missing_touchpoints = PMCQuantification(
            spacial_unit="adm2",
            assumptions={
                "pmc_coverage": 0.5,
                "pmc_tablet_factor": 1.1,
                "pmc_buffer_mult": 1,
            },
        )
        with self.assertRaises(ValueError):
            quant_missing_touchpoints.get_quantification(
                self.scen_data, self.mock_population_data
            )

        quant_missing_tablet_factor = PMCQuantification(
            spacial_unit="adm2",
            assumptions={
                "pmc_coverage": 0.5,
                "pmc_touchpoints": 1.5,
                "pmc_buffer_mult": 1,
            },
        )
        with self.assertRaises(ValueError):
            quant_missing_tablet_factor.get_quantification(
                self.scen_data, self.mock_population_data
            )

        quant_missing_buffer = PMCQuantification(
            spacial_unit="adm2",
            assumptions={
                "pmc_coverage": 0.5,
                "pmc_touchpoints": 1.5,
                "pmc_tablet_factor": 1.1,
            },
        )
        with self.assertRaises(ValueError):
            quant_missing_buffer.get_quantification(
                self.scen_data, self.mock_population_data
            )

    def test_pmc_quantification_different_code(self):
        """Test that PMCQuantification returns empty DataFrame when code does not match any column in scen_data."""

        quant = PMCQuantification(
            spacial_unit="adm2",
            assumptions={
                "pmc_coverage": 0.5,
                "pmc_touchpoints": 1.5,
                "pmc_tablet_factor": 1.1,
                "pmc_buffer_mult": 1,
            },
        )
        result = quant.get_quantification(pd.DataFrame(), self.mock_population_data)

        self.assertTrue(result.empty)

    def test_pmc_quantification_missing_pop_column(self):
        """Test that PMCQuantification raises an error when population column is missing."""

        quant = PMCQuantification(
            spacial_unit="adm2",
            assumptions={
                "pmc_coverage": 0.5,
                "pmc_touchpoints": 1.5,
                "pmc_tablet_factor": 1.1,
                "pmc_buffer_mult": 1,
            },
        )
        with self.assertRaises(ValueError):
            quant.get_quantification(self.scen_data, pd.DataFrame())
