import unittest

import pandas as pd

from snt_malaria_budgeting.core.quantification_functions import (
    VaccQuantification,
)


class TestVaccQuantification(unittest.TestCase):
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
                "scenario_name": ["Scenario with vaccination intervention code"],
                "scenario_description": [
                    "Test with only vaccination intervention code"
                ],
                "code_vacc": [1],
                "type_vacc": ["VACC"],
            }
        )

        self.mock_population_data = pd.DataFrame(
            {
                "adm1": [admin1],
                "adm2": [admin2],
                "year": [year],
                "pop_vaccine_5_36_months": [32988.7383],
                "pop_vaccine_5_36_months_custom": [32088.7383],
                "pop_vaccine_5_36_months_custom_2": [30988.7383],
            }
        )

        self.cost_data = pd.DataFrame(
            {
                "code_intervention": [
                    "vacc",
                    "vacc",
                ],
                "type_intervention": [
                    "VACC",
                    "VACC",
                ],
                "unit": ["per dose", "per child"],
                "cost_class": ["Commodity", "Commodity"],
                "cost_year_for_analysis": 2025,
                "usd_cost": [1.0, 1.23],
                "local_currency_cost": [584.0, 584.0],
                "cost_name": ["test", "test"],
            }
        )

    def test_vacc_quantification(self):
        """Test that VaccQuantification returns expected results for a known code."""

        quant = VaccQuantification(
            spatial_unit="adm2",
            assumptions={
                "vacc_coverage": 0.5,
                "vacc_buffer_mult": 1.1,
                "vacc_doses_per_child": 3,
            },
        )
        result = quant.get_quantification(self.scen_data, self.mock_population_data)

        expected_quantity_per_dose = (
            self.mock_population_data["pop_vaccine_5_36_months"][0] * 0.5 * 1.1 * 3
        )

        expected_quantity_per_child = (
            self.mock_population_data["pop_vaccine_5_36_months"][0] * 0.5
        )

        self.assertEqual(len(result), 2)
        self.assertIn("quantity", result.columns)
        self.assertIn("target_pop", result.columns)
        self.assertIn("code_intervention", result.columns)
        self.assertIn("type_intervention", result.columns)
        self.assertIn("unit", result.columns)

        dose_result = result[result["unit"] == "per dose"].iloc[0]

        self.assertAlmostEqual(dose_result["quantity"], expected_quantity_per_dose)
        self.assertAlmostEqual(
            dose_result["target_pop"],
            expected_quantity_per_child,
        )

        child_result = result[result["unit"] == "per child"].iloc[0]
        self.assertAlmostEqual(child_result["quantity"], expected_quantity_per_child)
        self.assertAlmostEqual(child_result["target_pop"], expected_quantity_per_child)

    def test_vacc_quantification_custom_target_population(self):
        """Test that VaccQuantification returns expected results for a known code."""

        quant = VaccQuantification(
            spatial_unit="adm2",
            assumptions={
                "vacc_coverage": 0.5,
                "vacc_buffer_mult": 1.1,
                "vacc_doses_per_child": 3,
            },
        )
        scen_data = self.scen_data.copy()
        scen_data["target_population_columns_vacc"] = [
            ["pop_vaccine_5_36_months_custom"]
        ]
        result = quant.get_quantification(scen_data, self.mock_population_data)

        expected_quantity_per_dose = (
            self.mock_population_data["pop_vaccine_5_36_months_custom"][0]
            * 0.5
            * 1.1
            * 3
        )

        expected_quantity_per_child = (
            self.mock_population_data["pop_vaccine_5_36_months_custom"][0] * 0.5
        )

        self.assertEqual(len(result), 2)
        self.assertIn("quantity", result.columns)
        self.assertIn("target_pop", result.columns)
        self.assertIn("code_intervention", result.columns)
        self.assertIn("type_intervention", result.columns)
        self.assertIn("unit", result.columns)

        dose_result = result[result["unit"] == "per dose"].iloc[0]

        self.assertAlmostEqual(dose_result["quantity"], expected_quantity_per_dose)
        self.assertAlmostEqual(
            dose_result["target_pop"],
            expected_quantity_per_child,
        )

        child_result = result[result["unit"] == "per child"].iloc[0]
        self.assertAlmostEqual(child_result["quantity"], expected_quantity_per_child)
        self.assertAlmostEqual(child_result["target_pop"], expected_quantity_per_child)

    def test_vacc_quantification_multiple_custom_target_population(self):
        """Test that VaccQuantification returns expected results for a known code."""

        quant = VaccQuantification(
            spatial_unit="adm2",
            assumptions={
                "vacc_coverage": 0.5,
                "vacc_buffer_mult": 1.1,
                "vacc_doses_per_child": 3,
            },
        )
        scen_data = self.scen_data.copy()
        scen_data["target_population_columns_vacc"] = [
            ["pop_vaccine_5_36_months_custom", "pop_vaccine_5_36_months_custom_2"]
        ]
        result = quant.get_quantification(scen_data, self.mock_population_data)
        target_pop_sum = (
            self.mock_population_data["pop_vaccine_5_36_months_custom"][0]
            + self.mock_population_data["pop_vaccine_5_36_months_custom_2"][0]
        )
        expected_quantity_per_dose = target_pop_sum * 0.5 * 1.1 * 3

        expected_quantity_per_child = target_pop_sum * 0.5

        self.assertEqual(len(result), 2)
        self.assertIn("quantity", result.columns)
        self.assertIn("target_pop", result.columns)
        self.assertIn("code_intervention", result.columns)
        self.assertIn("type_intervention", result.columns)
        self.assertIn("unit", result.columns)

        dose_result = result[result["unit"] == "per dose"].iloc[0]

        self.assertAlmostEqual(dose_result["quantity"], expected_quantity_per_dose)
        self.assertAlmostEqual(
            dose_result["target_pop"],
            expected_quantity_per_child,
        )

        child_result = result[result["unit"] == "per child"].iloc[0]
        self.assertAlmostEqual(child_result["quantity"], expected_quantity_per_child)
        self.assertAlmostEqual(child_result["target_pop"], expected_quantity_per_child)

    def test_vacc_quantification_empty_base(self):
        """Test that VaccQuantification returns an empty DataFrame when base data is empty."""

        empty_scen_data = self.scen_data[self.scen_data["adm2"] == "Nonexistent LGA"]
        empty_population_data = self.mock_population_data[
            self.mock_population_data["adm2"] == "Nonexistent LGA"
        ]

        quant = VaccQuantification(
            spatial_unit="adm2",
            assumptions={
                "vacc_coverage": 0.5,
                "vacc_buffer_mult": 1.1,
                "vacc_doses_per_child": 3,
            },
        )
        result = quant.get_quantification(empty_scen_data, empty_population_data)

        self.assertTrue(result.empty)

    def test_vacc_quantification_missing_assumption(self):
        """Test that VaccQuantification uses default coverage when specific coverage assumption is missing."""

        quant_missing_coverage = VaccQuantification(
            spatial_unit="adm2",
            assumptions={
                "vacc_buffer_mult": 1.1,
                "vacc_doses_per_child": 3,
            },
        )
        with self.assertRaisesRegex(
            ValueError, r"Missing assumptions for vacc: vacc_coverage"
        ):
            quant_missing_coverage.get_quantification(
                self.scen_data, self.mock_population_data
            )

        quant_missing_buffer_mult = VaccQuantification(
            spatial_unit="adm2",
            assumptions={
                "vacc_coverage": 0.5,
                "vacc_doses_per_child": 3,
            },
        )

        with self.assertRaisesRegex(
            ValueError, r"Missing assumptions for vacc: vacc_buffer_mult"
        ):
            quant_missing_buffer_mult.get_quantification(
                self.scen_data, self.mock_population_data
            )

        quant_missing_dose_per_child = VaccQuantification(
            spatial_unit="adm2",
            assumptions={
                "vacc_coverage": 0.5,
                "vacc_buffer_mult": 1.1,
            },
        )
        with self.assertRaisesRegex(
            ValueError, r"Missing assumptions for vacc: vacc_doses_per_child"
        ):
            quant_missing_dose_per_child.get_quantification(
                self.scen_data, self.mock_population_data
            )

    def test_vacc_quantification_different_code(self):
        """Test that VaccQuantification returns empty DataFrame when code does not match any column in scen_data."""

        quant = VaccQuantification(
            spatial_unit="adm2",
            assumptions={
                "vacc_coverage": 0.5,
                "vacc_buffer_mult": 1,
                "vacc_doses_per_child": 3,
            },
        )
        result = quant.get_quantification(pd.DataFrame(), self.mock_population_data)

        self.assertTrue(result.empty)

    def test_vacc_quantification_missing_pop_column(self):
        """Test that VaccQuantification raises an error when population column is missing."""

        quant = VaccQuantification(
            spatial_unit="adm2",
            assumptions={
                "vacc_coverage": 0.5,
                "vacc_buffer_mult": 1,
            },
        )
        with self.assertRaisesRegex(
            ValueError,
            r"Target population DataFrame must contain columns: \['adm2', 'year', 'pop_vaccine_5_36_months'\]",
        ):
            quant.get_quantification(self.scen_data, pd.DataFrame())
