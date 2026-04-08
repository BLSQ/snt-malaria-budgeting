import unittest

import pandas as pd

from snt_malaria_budgeting.core.quantification_functions import IPTPQuantification


class TestIPTPQuantification(unittest.TestCase):
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
                "scenario_name": ["Scenario with iptp intervention code"],
                "scenario_description": ["Test with only iptp intervention code"],
                "code_iptp": [1],
                "type_iptp": ["IPTP"],
            }
        )

        cls.mock_population_data = pd.DataFrame(
            {
                "adm1": [admin1],
                "adm2": [admin2],
                "year": [year],
                "pop_pw": [342988.7383],
            }
        )

        cls.cost_data = pd.DataFrame(
            {
                "code_intervention": [
                    "iptp",
                ],
                "type_intervention": [
                    "IPTP",
                ],
                "unit": [
                    "per SP",
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

    def test_iptp_quantification(self):
        """Test that IPTPQuantification returns expected results for a known code."""

        quant = IPTPQuantification(
            spacial_unit="adm2",
            assumptions={
                "iptp_anc_coverage": 0.5,
                "iptp_doses_per_pw": 1.5,
                "iptp_buffer_mult": 1.1,
            },
        )
        result = quant.get_quantification(self.scen_data, self.mock_population_data)

        expected_quantity = self.mock_population_data["pop_pw"][0] * 0.5 * 1.5 * 1.1

        self.assertEqual(len(result), 1)
        self.assertIn("quantity", result.columns)
        self.assertIn("target_pop", result.columns)
        self.assertIn("code_intervention", result.columns)
        self.assertIn("type_intervention", result.columns)
        self.assertIn("unit", result.columns)

        self.assertAlmostEqual(result["quantity"].iloc[0], expected_quantity)
        self.assertAlmostEqual(
            result["target_pop"].iloc[0], self.mock_population_data["pop_pw"][0]
        )
        self.assertEqual(result["code_intervention"].iloc[0], "iptp")
        self.assertEqual(result["type_intervention"].iloc[0], "IPTP")
        self.assertEqual(result["unit"].iloc[0], "per SP")

    def test_iptp_quantification_empty_base(self):
        """Test that IPTPQuantification returns an empty DataFrame when base data is empty."""

        empty_scen_data = self.scen_data[self.scen_data["adm2"] == "Nonexistent LGA"]
        empty_population_data = self.mock_population_data[
            self.mock_population_data["adm2"] == "Nonexistent LGA"
        ]

        quant = IPTPQuantification(
            spacial_unit="adm2",
            assumptions={
                "iptp_anc_coverage": 0.5,
                "iptp_doses_per_pw": 1,
                "iptp_buffer_mult": 1,
            },
        )
        result = quant.get_quantification(empty_scen_data, empty_population_data)

        self.assertTrue(result.empty)

    def test_iptp_quantification_missing_assumption(self):
        """Test that IPTPQuantification uses default coverage when specific coverage assumption is missing."""

        quant_missing_anc = IPTPQuantification(
            spacial_unit="adm2",
            assumptions={
                "iptp_doses_per_pw": 1,
                "iptp_buffer_mult": 1,
            },
        )
        with self.assertRaises(ValueError):
            quant_missing_anc.get_quantification(
                self.scen_data, self.mock_population_data
            )

        quant_missing_doses = IPTPQuantification(
            spacial_unit="adm2",
            assumptions={
                "iptp_anc_coverage": 0.5,
                "iptp_buffer_mult": 1,
            },
        )
        with self.assertRaises(ValueError):
            quant_missing_doses.get_quantification(
                self.scen_data, self.mock_population_data
            )

        quant_missing_buffer = IPTPQuantification(
            spacial_unit="adm2",
            assumptions={
                "iptp_anc_coverage": 0.5,
                "iptp_doses_per_pw": 1,
            },
        )
        with self.assertRaises(ValueError):
            quant_missing_buffer.get_quantification(
                self.scen_data, self.mock_population_data
            )

    def test_iptp_quantification_different_code(self):
        """Test that IPTPQuantification returns empty DataFrame when code does not match any column in scen_data."""

        quant = IPTPQuantification(
            spacial_unit="adm2",
            assumptions={
                "iptp_anc_coverage": 0.5,
                "iptp_doses_per_pw": 1,
                "iptp_buffer_mult": 1,
            },
        )
        result = quant.get_quantification(pd.DataFrame(), self.mock_population_data)

        self.assertTrue(result.empty)

    def test_iptp_quantification_missing_pop_column(self):
        """Test that IPTPQuantification raises an error when population column is missing."""

        quant = IPTPQuantification(
            spacial_unit="adm2",
            assumptions={
                "iptp_anc_coverage": 0.5,
                "iptp_doses_per_pw": 1,
                "iptp_buffer_mult": 1,
            },
        )
        with self.assertRaises(ValueError):
            quant.get_quantification(self.scen_data, pd.DataFrame())
