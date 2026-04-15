import unittest

import pandas as pd

from snt_malaria_budgeting.core.quantification_functions import (
    PMCQuantification,
)


class TestPMCQuantification(unittest.TestCase):
    def setUp(self):
        """Set up mock dataframes and settings once for all tests."""
        self.settings = {}

        admin1 = "State A"
        admin2 = "LGA 1"
        year = 2025

        self.scen_data = pd.DataFrame(
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

        self.mock_population_data = pd.DataFrame(
            {
                "adm1": [admin1],
                "adm2": [admin2],
                "year": [year],
                "pop_0_1": [342988.7383],
                "pop_1_2": [20134.897],
                "pop_0_1_custom": [32988.7383],
                "pop_1_2_custom": [2134.897],
            }
        )

        self.cost_data = pd.DataFrame(
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
            spatial_unit="adm2",
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

    def test_pmc_quantification_custom_target_population(self):
        """Test that PMCQuantification returns expected results for a known code with custom target population columns."""

        quant = PMCQuantification(
            spatial_unit="adm2",
            assumptions={
                "pmc_coverage": 0.5,
                "pmc_touchpoints": 1.5,
                "pmc_tablet_factor": 1.1,
                "pmc_buffer_mult": 1.1,
            },
        )

        scen_data = self.scen_data.copy()
        scen_data["target_population_columns_pmc"] = [
            ["pop_0_1_custom", "pop_1_2_custom"]
        ]
        result = quant.get_quantification(scen_data, self.mock_population_data)

        assumption_ratio = 0.5 * 1.5 * 1.1 * 1.1
        expected_quantity = (
            self.mock_population_data["pop_0_1_custom"][0] * assumption_ratio
            + self.mock_population_data["pop_1_2_custom"][0] * assumption_ratio * 2
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
            self.mock_population_data["pop_0_1_custom"][0] * 0.5
            + self.mock_population_data["pop_1_2_custom"][0] * 0.5,
        )

    def test_pmc_quantitification_invalid_target_population_columns(self):
        """Test that PMCQuantification raises an error when target_population_columns does not contain exactly 2 items."""

        scen_data_invalid_pop_cols = self.scen_data.copy()
        scen_data_invalid_pop_cols["target_population_columns_pmc"] = [["pop_0_1"]]

        quant = PMCQuantification(
            spatial_unit="adm2",
            assumptions={
                "pmc_coverage": 0.5,
                "pmc_touchpoints": 1.5,
                "pmc_tablet_factor": 1.1,
                "pmc_buffer_mult": 1.1,
            },
        )
        with self.assertRaisesRegex(
            ValueError, r"target_population_columns_pmc must contain exactly 2 items"
        ):
            quant.get_quantification(
                scen_data_invalid_pop_cols, self.mock_population_data
            )

    def test_pmc_quantification_empty_base(self):
        """Test that PMCQuantification returns an empty DataFrame when base data is empty."""

        empty_scen_data = self.scen_data[self.scen_data["adm2"] == "Nonexistent LGA"]
        empty_population_data = self.mock_population_data[
            self.mock_population_data["adm2"] == "Nonexistent LGA"
        ]

        quant = PMCQuantification(
            spatial_unit="adm2",
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
            spatial_unit="adm2",
            assumptions={
                "pmc_touchpoints": 1.5,
                "pmc_tablet_factor": 1.1,
                "pmc_buffer_mult": 1.1,
            },
        )
        with self.assertRaisesRegex(
            ValueError, r"Missing assumptions for pmc: pmc_coverage"
        ):
            quant_missing_coverage.get_quantification(
                self.scen_data, self.mock_population_data
            )

        quant_missing_touchpoints = PMCQuantification(
            spatial_unit="adm2",
            assumptions={
                "pmc_coverage": 0.5,
                "pmc_tablet_factor": 1.1,
                "pmc_buffer_mult": 1,
            },
        )
        with self.assertRaisesRegex(
            ValueError, r"Missing assumptions for pmc: pmc_touchpoints"
        ):
            quant_missing_touchpoints.get_quantification(
                self.scen_data, self.mock_population_data
            )

        quant_missing_tablet_factor = PMCQuantification(
            spatial_unit="adm2",
            assumptions={
                "pmc_coverage": 0.5,
                "pmc_touchpoints": 1.5,
                "pmc_buffer_mult": 1,
            },
        )
        with self.assertRaisesRegex(
            ValueError, r"Missing assumptions for pmc: pmc_tablet_factor"
        ):
            quant_missing_tablet_factor.get_quantification(
                self.scen_data, self.mock_population_data
            )

        quant_missing_buffer = PMCQuantification(
            spatial_unit="adm2",
            assumptions={
                "pmc_coverage": 0.5,
                "pmc_touchpoints": 1.5,
                "pmc_tablet_factor": 1.1,
            },
        )
        with self.assertRaisesRegex(
            ValueError, r"Missing assumptions for pmc: pmc_buffer_mult"
        ):
            quant_missing_buffer.get_quantification(
                self.scen_data, self.mock_population_data
            )

    def test_pmc_quantification_different_code(self):
        """Test that PMCQuantification returns empty DataFrame when code does not match any column in scen_data."""

        quant = PMCQuantification(
            spatial_unit="adm2",
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
            spatial_unit="adm2",
            assumptions={
                "pmc_coverage": 0.5,
                "pmc_touchpoints": 1.5,
                "pmc_tablet_factor": 1.1,
                "pmc_buffer_mult": 1,
            },
        )
        with self.assertRaisesRegex(
            ValueError,
            r"Target population DataFrame must contain columns: \['adm2', 'year', 'pop_0_1', 'pop_1_2'\]",
        ):
            quant.get_quantification(self.scen_data, pd.DataFrame())
