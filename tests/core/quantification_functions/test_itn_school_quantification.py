import unittest

import pandas as pd

from snt_malaria_budgeting.core.quantification_functions import (
    ItnSchoolQuantification,
)


class TestItnSchoolQuantification(unittest.TestCase):
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
                "scenario_name": ["Scenario with itn school intervention code"],
                "scenario_description": ["Test with only itn school intervention code"],
                "code_itn_school": [1],
                "type_itn_school": ["ITN_SCHOOL"],
            }
        )

        self.mock_population_data = pd.DataFrame(
            {
                "adm1": [admin1],
                "adm2": [admin2],
                "year": [year],
                "pop_total": [342988.7383],
                "pop_custom": [32988.7383],
                "pop_custom_2": [30988.7383],
            }
        )

        self.cost_data = pd.DataFrame(
            {
                "code_intervention": [
                    "itn_school",
                    "itn_school",
                ],
                "type_intervention": [
                    "ITN_SCHOOL",
                    "ITN_SCHOOL",
                ],
                "unit": ["per ITN", "per bale"],
                "cost_class": ["Commodity"] * 2,
                "cost_year_for_analysis": 2025,
                "usd_cost": [1.0, 1.1],
                "local_currency_cost": [584.0, 642.4],
                "cost_name": ["test"] * 2,
            }
        )

    def test_itn_school_quantification(self):
        """Test that ItnSchoolQuantification returns expected results for a known code."""

        quant = ItnSchoolQuantification(
            spatial_unit="adm2",
            assumptions={
                "itn_school_coverage": 0.5,
                "itn_school_divisor": 1.5,
                "itn_school_buffer_mult": 1.1,
                "itn_school_bale_size": 10,
            },
        )
        result = quant.get_quantification(self.scen_data, self.mock_population_data)

        expected_net_quantity = (
            self.mock_population_data["pop_total"][0] * 0.5 * 1.1 / 1.5
        )

        self.assertEqual(len(result), 2)
        self.assertIn("quantity", result.columns)
        self.assertIn("target_pop", result.columns)
        self.assertIn("code_intervention", result.columns)
        self.assertIn("type_intervention", result.columns)
        self.assertIn("unit", result.columns)

        net_result = result[result["unit"] == "per ITN"].iloc[0]

        self.assertAlmostEqual(net_result["quantity"], expected_net_quantity)
        self.assertAlmostEqual(
            net_result["target_pop"], self.mock_population_data["pop_total"][0] * 0.5
        )

        expected_bale_quantity = expected_net_quantity / 10
        bale_result = result[result["unit"] == "per bale"].iloc[0]
        self.assertAlmostEqual(bale_result["quantity"], expected_bale_quantity)
        self.assertAlmostEqual(
            bale_result["target_pop"], self.mock_population_data["pop_total"][0] * 0.5
        )

    def test_itn_school_quantification_custom_pop_columns(self):
        """Test that ItnSchoolQuantification returns expected results for a known code with overridden population column."""

        quant = ItnSchoolQuantification(
            spatial_unit="adm2",
            assumptions={
                "itn_school_coverage": 0.5,
                "itn_school_divisor": 1.5,
                "itn_school_buffer_mult": 1.1,
                "itn_school_bale_size": 10,
            },
        )
        scen_data = self.scen_data.assign(
            target_population_columns_itn_school=[["pop_custom"]]
        )
        result = quant.get_quantification(scen_data, self.mock_population_data)

        expected_net_quantity = (
            self.mock_population_data["pop_custom"][0] * 0.5 * 1.1 / 1.5
        )

        self.assertEqual(len(result), 2)
        self.assertIn("quantity", result.columns)
        self.assertIn("target_pop", result.columns)
        self.assertIn("code_intervention", result.columns)
        self.assertIn("type_intervention", result.columns)
        self.assertIn("unit", result.columns)

        net_result = result[result["unit"] == "per ITN"].iloc[0]

        self.assertAlmostEqual(net_result["quantity"], expected_net_quantity)
        self.assertAlmostEqual(
            net_result["target_pop"], self.mock_population_data["pop_custom"][0] * 0.5
        )

        expected_bale_quantity = expected_net_quantity / 10
        bale_result = result[result["unit"] == "per bale"].iloc[0]
        self.assertAlmostEqual(bale_result["quantity"], expected_bale_quantity)
        self.assertAlmostEqual(
            bale_result["target_pop"], self.mock_population_data["pop_custom"][0] * 0.5
        )

    def test_itn_school_quantification_multiple_custom_pop_columns(self):
        """Test that ItnSchoolQuantification returns expected results for a known code with overridden population column."""

        quant = ItnSchoolQuantification(
            spatial_unit="adm2",
            assumptions={
                "itn_school_coverage": 0.5,
                "itn_school_divisor": 1.5,
                "itn_school_buffer_mult": 1.1,
                "itn_school_bale_size": 10,
            },
        )
        scen_data = self.scen_data.assign(
            target_population_columns_itn_school=[["pop_custom", "pop_custom_2"]]
        )
        result = quant.get_quantification(scen_data, self.mock_population_data)

        expected_net_quantity = (
            (
                self.mock_population_data["pop_custom"][0]
                + self.mock_population_data["pop_custom_2"][0]
            )
            * 0.5
            * 1.1
            / 1.5
        )

        self.assertEqual(len(result), 2)
        self.assertIn("quantity", result.columns)
        self.assertIn("target_pop", result.columns)
        self.assertIn("code_intervention", result.columns)
        self.assertIn("type_intervention", result.columns)
        self.assertIn("unit", result.columns)

        net_result = result[result["unit"] == "per ITN"].iloc[0]

        self.assertAlmostEqual(net_result["quantity"], expected_net_quantity)
        self.assertAlmostEqual(
            net_result["target_pop"],
            (
                self.mock_population_data["pop_custom"][0]
                + self.mock_population_data["pop_custom_2"][0]
            )
            * 0.5,
        )

        expected_bale_quantity = expected_net_quantity / 10
        bale_result = result[result["unit"] == "per bale"].iloc[0]
        self.assertAlmostEqual(bale_result["quantity"], expected_bale_quantity)
        self.assertAlmostEqual(
            bale_result["target_pop"],
            (
                self.mock_population_data["pop_custom"][0]
                + self.mock_population_data["pop_custom_2"][0]
            )
            * 0.5,
        )

    def test_itn_school_quantification_empty_base(self):
        """Test that ItnSchoolQuantification returns an empty DataFrame when base data is empty."""

        empty_scen_data = self.scen_data[self.scen_data["adm2"] == "Nonexistent LGA"]
        empty_population_data = self.mock_population_data[
            self.mock_population_data["adm2"] == "Nonexistent LGA"
        ]

        quant = ItnSchoolQuantification(
            spatial_unit="adm2",
            assumptions={
                "itn_school_coverage": 0.5,
                "itn_school_divisor": 1,
                "itn_school_buffer_mult": 1,
                "itn_school_bale_size": 10,
            },
        )
        result = quant.get_quantification(empty_scen_data, empty_population_data)

        self.assertTrue(result.empty)

    def test_itn_school_quantification_missing_assumption(self):
        """Test that ItnSchoolQuantification uses default coverage when specific coverage assumption is missing."""

        quant_missing_coverage = ItnSchoolQuantification(
            spatial_unit="adm2",
            assumptions={
                "itn_school_divisor": 1,
                "itn_school_buffer_mult": 1,
                "itn_school_bale_size": 10,
            },
        )
        with self.assertRaisesRegex(
            ValueError,
            "Missing assumptions for itn_school: itn_school_coverage",
        ):
            quant_missing_coverage.get_quantification(
                self.scen_data, self.mock_population_data
            )

        quant_missing_divisor = ItnSchoolQuantification(
            spatial_unit="adm2",
            assumptions={
                "itn_school_coverage": 0.5,
                "itn_school_buffer_mult": 1,
                "itn_school_bale_size": 10,
            },
        )
        with self.assertRaisesRegex(
            ValueError,
            "Missing assumptions for itn_school: itn_school_divisor",
        ):
            quant_missing_divisor.get_quantification(
                self.scen_data, self.mock_population_data
            )

        quant_missing_buffer = ItnSchoolQuantification(
            spatial_unit="adm2",
            assumptions={
                "itn_school_coverage": 0.5,
                "itn_school_divisor": 1,
                "itn_school_bale_size": 10,
            },
        )
        with self.assertRaisesRegex(
            ValueError,
            "Missing assumptions for itn_school: itn_school_buffer_mult",
        ):
            quant_missing_buffer.get_quantification(
                self.scen_data, self.mock_population_data
            )

        quant_missing_bale_size = ItnSchoolQuantification(
            spatial_unit="adm2",
            assumptions={
                "itn_school_coverage": 0.5,
                "itn_school_divisor": 1,
                "itn_school_buffer_mult": 1,
            },
        )
        with self.assertRaisesRegex(
            ValueError,
            "Missing assumptions for itn_school: itn_school_bale_size",
        ):
            quant_missing_bale_size.get_quantification(
                self.scen_data, self.mock_population_data
            )

    def test_itn_school_quantification_different_code(self):
        """Test that ItnSchoolQuantification returns empty DataFrame when code does not match any column in scen_data."""

        quant = ItnSchoolQuantification(
            spatial_unit="adm2",
            assumptions={
                "itn_school_coverage": 0.5,
                "itn_school_divisor": 1,
                "itn_school_buffer_mult": 1,
            },
        )
        result = quant.get_quantification(pd.DataFrame(), self.mock_population_data)

        self.assertTrue(result.empty)

    def test_itn_school_quantification_missing_pop_column(self):
        """Test that ItnSchoolQuantification raises an error when population column is missing."""

        quant = ItnSchoolQuantification(
            spatial_unit="adm2",
            assumptions={
                "itn_school_coverage": 0.5,
                "itn_school_divisor": 1,
                "itn_school_buffer_mult": 1,
            },
        )
        with self.assertRaisesRegex(
            ValueError,
            r"Target population DataFrame must contain columns: \['adm2', 'year', 'pop_total'\]",
        ):
            quant.get_quantification(self.scen_data, pd.DataFrame())
