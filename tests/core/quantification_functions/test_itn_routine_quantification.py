import unittest

import pandas as pd

from snt_malaria_budgeting.core.quantification_functions import (
    ItnRoutineQuantification,
)


class TestItnRoutineQuantification(unittest.TestCase):
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
                "scenario_name": ["Scenario with itn routine intervention code"],
                "scenario_description": [
                    "Test with only itn routine intervention code"
                ],
                "code_itn_routine": [1],
                "type_itn_routine": ["ITN_ROUTINE"],
            }
        )

        self.mock_population_data = pd.DataFrame(
            {
                "adm1": [admin1],
                "adm2": [admin2],
                "year": [year],
                "pop_0_5": [342988.7383],
                "pop_pw": [20134.897],
                "pop_0_5_custom": [32988.7383],
                "pop_pw_custom": [2134.897],
                "pop_0_5_custom_2": [30988.7383],
                "pop_pw_custom_2": [2034.897],
            }
        )

        self.cost_data = pd.DataFrame(
            {
                "code_intervention": [
                    "itn_routine",
                ],
                "type_intervention": [
                    "ITN_ROUTINE",
                ],
                "unit": ["per ITN"],
                "cost_class": ["Commodity"],
                "cost_year_for_analysis": year,
                "usd_cost": [1.0],
                "local_currency_cost": [584.0],
                "cost_name": ["test"],
            }
        )

    def test_itn_routine_quantification(self):
        """Test that ItnRoutineQuantification returns expected results for a known code."""

        quant = ItnRoutineQuantification(
            spatial_unit="adm2",
            assumptions={
                "itn_routine_coverage": 0.5,
                "itn_routine_buffer_mult": 1.1,
            },
        )
        result = quant.get_quantification(self.scen_data, self.mock_population_data)

        expected_quantity = (
            (
                self.mock_population_data["pop_0_5"][0]
                + self.mock_population_data["pop_pw"][0]
            )
            * 0.5
            * 1.1
        )

        self.assertEqual(len(result), 1)
        self.assertIn("quantity", result.columns)
        self.assertIn("target_pop", result.columns)
        self.assertIn("code_intervention", result.columns)
        self.assertIn("type_intervention", result.columns)
        self.assertIn("unit", result.columns)

        net_result = result[result["unit"] == "per ITN"].iloc[0]

        self.assertAlmostEqual(net_result["quantity"], expected_quantity)
        self.assertAlmostEqual(
            net_result["target_pop"],
            (
                self.mock_population_data["pop_0_5"][0]
                + self.mock_population_data["pop_pw"][0]
            ),
        )

    def test_itn_routine_quantification_custom_target_population(self):
        """Test that ItnRoutineQuantification returns expected results for a known code with custom target population."""

        quant = ItnRoutineQuantification(
            spatial_unit="adm2",
            assumptions={
                "itn_routine_coverage": 0.5,
                "itn_routine_buffer_mult": 1.1,
            },
        )
        scen_data = self.scen_data.copy()
        scen_data["target_population_columns_itn_routine"] = [
            ["pop_0_5_custom", "pop_pw_custom"]
        ]
        result = quant.get_quantification(scen_data, self.mock_population_data)

        expected_quantity = (
            (
                self.mock_population_data["pop_0_5_custom"][0]
                + self.mock_population_data["pop_pw_custom"][0]
            )
            * 0.5
            * 1.1
        )

        self.assertEqual(len(result), 1)
        self.assertIn("quantity", result.columns)
        self.assertIn("target_pop", result.columns)
        self.assertIn("code_intervention", result.columns)
        self.assertIn("type_intervention", result.columns)
        self.assertIn("unit", result.columns)

        net_result = result[result["unit"] == "per ITN"].iloc[0]

        self.assertAlmostEqual(net_result["quantity"], expected_quantity)
        self.assertAlmostEqual(
            net_result["target_pop"],
            (
                self.mock_population_data["pop_0_5_custom"][0]
                + self.mock_population_data["pop_pw_custom"][0]
            ),
        )

    def test_itn_routine_quantification_multiple_custom_target_population(self):
        """Test that ItnRoutineQuantification returns expected results for a known code with multiple custom target populations."""

        quant = ItnRoutineQuantification(
            spatial_unit="adm2",
            assumptions={
                "itn_routine_coverage": 0.5,
                "itn_routine_buffer_mult": 1.1,
            },
        )
        scen_data = self.scen_data.copy()
        scen_data["target_population_columns_itn_routine"] = [
            ["pop_0_5_custom", "pop_pw_custom", "pop_0_5_custom_2", "pop_pw_custom_2"]
        ]
        result = quant.get_quantification(scen_data, self.mock_population_data)

        expected_quantity = (
            (
                self.mock_population_data["pop_0_5_custom"][0]
                + self.mock_population_data["pop_pw_custom"][0]
                + self.mock_population_data["pop_0_5_custom_2"][0]
                + self.mock_population_data["pop_pw_custom_2"][0]
            )
            * 0.5
            * 1.1
        )

        self.assertEqual(len(result), 1)
        self.assertIn("quantity", result.columns)
        self.assertIn("target_pop", result.columns)
        self.assertIn("code_intervention", result.columns)
        self.assertIn("type_intervention", result.columns)
        self.assertIn("unit", result.columns)

        net_result = result[result["unit"] == "per ITN"].iloc[0]

        self.assertAlmostEqual(net_result["quantity"], expected_quantity)
        self.assertAlmostEqual(
            net_result["target_pop"],
            (
                self.mock_population_data["pop_0_5_custom"][0]
                + self.mock_population_data["pop_pw_custom"][0]
                + self.mock_population_data["pop_0_5_custom_2"][0]
                + self.mock_population_data["pop_pw_custom_2"][0]
            ),
        )

    def test_itn_routine_quantification_empty_base(self):
        """Test that ItnRoutineQuantification returns an empty DataFrame when base data is empty."""

        empty_scen_data = self.scen_data[self.scen_data["adm2"] == "Nonexistent LGA"]
        empty_population_data = self.mock_population_data[
            self.mock_population_data["adm2"] == "Nonexistent LGA"
        ]

        quant = ItnRoutineQuantification(
            spatial_unit="adm2",
            assumptions={
                "itn_routine_coverage": 0.5,
                "itn_routine_buffer_mult": 1,
            },
        )
        result = quant.get_quantification(empty_scen_data, empty_population_data)

        self.assertTrue(result.empty)

    def test_itn_routine_quantification_missing_assumption(self):
        """Test that ItnRoutineQuantification uses default coverage when specific coverage assumption is missing."""

        quant_missing_coverage = ItnRoutineQuantification(
            spatial_unit="adm2",
            assumptions={
                "itn_routine_buffer_mult": 1,
            },
        )
        with self.assertRaisesRegex(
            ValueError, r"Missing assumptions for itn_routine: itn_routine_coverage"
        ):
            quant_missing_coverage.get_quantification(
                self.scen_data, self.mock_population_data
            )

        quant_missing_buffer_mult = ItnRoutineQuantification(
            spatial_unit="adm2",
            assumptions={
                "itn_routine_coverage": 0.5,
            },
        )
        with self.assertRaisesRegex(
            ValueError, r"Missing assumptions for itn_routine: itn_routine_buffer_mult"
        ):
            quant_missing_buffer_mult.get_quantification(
                self.scen_data, self.mock_population_data
            )

    def test_itn_routine_quantification_different_code(self):
        """Test that ItnRoutineQuantification returns empty DataFrame when code does not match any column in scen_data."""

        quant = ItnRoutineQuantification(
            spatial_unit="adm2",
            assumptions={
                "itn_routine_coverage": 0.5,
                "itn_routine_buffer_mult": 1,
            },
        )
        result = quant.get_quantification(pd.DataFrame(), self.mock_population_data)

        self.assertTrue(result.empty)

    def test_itn_routine_quantification_missing_pop_column(self):
        """Test that ItnRoutineQuantification raises an error when population column is missing."""

        quant = ItnRoutineQuantification(
            spatial_unit="adm2",
            assumptions={
                "itn_routine_coverage": 0.5,
                "itn_routine_buffer_mult": 1,
            },
        )
        with self.assertRaisesRegex(
            ValueError,
            r"Target population DataFrame must contain columns: \['adm2', 'year', 'pop_0_5', 'pop_pw'\]",
        ):
            quant.get_quantification(self.scen_data, pd.DataFrame())
