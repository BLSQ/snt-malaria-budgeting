import unittest

import pandas as pd

from snt_malaria_budgeting.core.quantification_functions.default_quantification import (
    DefaultQuantification,
)


class TestDefaultQuantification(unittest.TestCase):
    def setUp(cls):
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
                "scenario_name": ["Scenario with unknown intervention code"],
                "scenario_description": ["Test with only unknown intervention code"],
                "code_something": [1],
                "type_something": ["SMTH"],
            }
        )

        cls.mock_population_data = pd.DataFrame(
            {
                "adm1": [admin1],
                "adm2": [admin2],
                "year": [year],
                "pop_total": [342988.7383],
            }
        )

        cls.cost_data = pd.DataFrame(
            {
                "code_intervention": [
                    "something",
                ],
                "type_intervention": [
                    "SMTH",
                ],
                "unit": [
                    "Other",
                ],
                "cost_class": ["Commodity"],
                "cost_year_for_analysis": 2025,
                "usd_cost": [
                    1.0,
                ],
                "local_currency_cost": [
                    584.0,
                ],
                "cost_name": ["test"],
            }
        )

    def test_default_quantification(self):
        """Test that DefaultQuantification returns expected results for a known code."""

        quant = DefaultQuantification(
            code="something",
            spatial_unit="adm2",
            assumptions={"something_coverage": 0.5},
        )
        result = quant.get_quantification(self.scen_data, self.mock_population_data)

        expected_quantity = self.mock_population_data["pop_total"][0] * 0.5

        self.assertEqual(len(result), 1)
        self.assertIn("quantity", result.columns)
        self.assertIn("target_pop", result.columns)
        self.assertIn("code_intervention", result.columns)
        self.assertIn("type_intervention", result.columns)
        self.assertIn("unit", result.columns)

        self.assertAlmostEqual(result["quantity"].iloc[0], expected_quantity)
        self.assertAlmostEqual(
            result["target_pop"].iloc[0], self.mock_population_data["pop_total"][0]
        )
        self.assertEqual(result["code_intervention"].iloc[0], "something")
        self.assertEqual(result["type_intervention"].iloc[0], "SMTH")
        self.assertEqual(result["unit"].iloc[0], "Other")

    def test_default_quantification_empty_base(self):
        """Test that DefaultQuantification returns an empty DataFrame when base data is empty."""

        empty_scen_data = self.scen_data[self.scen_data["adm2"] == "Nonexistent LGA"]
        empty_population_data = self.mock_population_data[
            self.mock_population_data["adm2"] == "Nonexistent LGA"
        ]

        quant = DefaultQuantification(
            code="something",
            spatial_unit="adm2",
            assumptions={"something_coverage": 0.5},
        )
        result = quant.get_quantification(empty_scen_data, empty_population_data)

        self.assertTrue(result.empty)

    def test_default_quantification_no_coverage_assumption(self):
        """Test that DefaultQuantification uses default coverage when specific coverage assumption is missing."""

        quant = DefaultQuantification(
            code="something",
            spatial_unit="adm2",
            assumptions={"default_coverage": 0.3},
        )
        result = quant.get_quantification(self.scen_data, self.mock_population_data)

        expected_quantity = self.mock_population_data["pop_total"][0] * 0.3

        self.assertEqual(len(result), 1)
        self.assertAlmostEqual(result["quantity"].iloc[0], expected_quantity)

    def test_default_quantification_no_coverage_assumption_no_default(self):
        """Test that DefaultQuantification uses 1 as default coverage when no specific or default coverage assumption is provided."""

        quant = DefaultQuantification(
            code="something",
            spatial_unit="adm2",
            assumptions={},
        )
        result = quant.get_quantification(self.scen_data, self.mock_population_data)

        expected_quantity = self.mock_population_data["pop_total"][0] * 1

        self.assertEqual(len(result), 1)
        self.assertAlmostEqual(result["quantity"].iloc[0], expected_quantity)

    def test_default_quantification_different_code(self):
        """Test that DefaultQuantification returns empty DataFrame when code does not match any column in scen_data."""

        quant = DefaultQuantification(
            code="unknown_code",
            spatial_unit="adm2",
            assumptions={"unknown_code_coverage": 0.5},
        )
        result = quant.get_quantification(self.scen_data, self.mock_population_data)

        self.assertTrue(result.empty)

    def test_default_quantification_missing_pop_column(self):
        """Test that DefaultQuantification raises an error when population column is missing."""

        quant = DefaultQuantification(
            code="something",
            spatial_unit="adm2",
            assumptions={"something_coverage": 0.5},
        )
        with self.assertRaises(ValueError):
            quant.get_quantification(self.scen_data, pd.DataFrame())
