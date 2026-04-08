import unittest

import pandas as pd

from snt_malaria_budgeting.core.quantification_functions import (
    ItnCampaignQuantification,
)


class TestItnCampaignQuantification(unittest.TestCase):
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
                "scenario_name": ["Scenario with itn campaign intervention code"],
                "scenario_description": [
                    "Test with only itn campaign intervention code"
                ],
                "code_itn_campaign": [1],
                "type_itn_campaign": ["ITN_CAMPAIGN"],
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
                    "itn_campaign",
                    "itn_campaign",
                ],
                "type_intervention": [
                    "ITN_CAMPAIGN",
                    "ITN_CAMPAIGN",
                ],
                "unit": ["per ITN", "per bale"],
                "cost_class": ["Commodity"] * 2,
                "cost_year_for_analysis": 2025,
                "usd_cost": [1.0, 1.1],
                "local_currency_cost": [584.0, 642.4],
                "cost_name": ["test"] * 2,
            }
        )

    def test_itn_campaign_quantification(self):
        """Test that ItnCampaignQuantification returns expected results for a known code."""

        quant = ItnCampaignQuantification(
            spacial_unit="adm2",
            assumptions={
                "itn_campaign_coverage": 0.5,
                "itn_campaign_divisor": 1.5,
                "itn_campaign_buffer_mult": 1.1,
                "itn_campaign_bale_size": 10,
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

    def test_itn_campaign_quantification_empty_base(self):
        """Test that ItnCampaignQuantification returns an empty DataFrame when base data is empty."""

        empty_scen_data = self.scen_data[self.scen_data["adm2"] == "Nonexistent LGA"]
        empty_population_data = self.mock_population_data[
            self.mock_population_data["adm2"] == "Nonexistent LGA"
        ]

        quant = ItnCampaignQuantification(
            spacial_unit="adm2",
            assumptions={
                "itn_campaign_coverage": 0.5,
                "itn_campaign_divisor": 1,
                "itn_campaign_buffer_mult": 1,
                "itn_campaign_bale_size": 10,
            },
        )
        result = quant.get_quantification(empty_scen_data, empty_population_data)

        self.assertTrue(result.empty)

    def test_itn_campaign_quantification_missing_assumption(self):
        """Test that ItnCampaignQuantification uses default coverage when specific coverage assumption is missing."""

        quant_missing_coverage = ItnCampaignQuantification(
            spacial_unit="adm2",
            assumptions={
                "itn_campaign_divisor": 1,
                "itn_campaign_buffer_mult": 1,
            },
        )
        with self.assertRaises(ValueError):
            quant_missing_coverage.get_quantification(
                self.scen_data, self.mock_population_data
            )

        quant_missing_divisor = ItnCampaignQuantification(
            spacial_unit="adm2",
            assumptions={
                "itn_campaign_coverage": 0.5,
                "itn_campaign_buffer_mult": 1,
            },
        )
        with self.assertRaises(ValueError):
            quant_missing_divisor.get_quantification(
                self.scen_data, self.mock_population_data
            )

        quant_missing_divisor = ItnCampaignQuantification(
            spacial_unit="adm2",
            assumptions={
                "itn_campaign_coverage": 0.5,
                "itn_campaign_buffer_mult": 1,
            },
        )
        with self.assertRaises(ValueError):
            quant_missing_divisor.get_quantification(
                self.scen_data, self.mock_population_data
            )

        quant_missing_buffer = ItnCampaignQuantification(
            spacial_unit="adm2",
            assumptions={
                "itn_campaign_coverage": 0.5,
                "itn_campaign_divisor": 1,
            },
        )
        with self.assertRaises(ValueError):
            quant_missing_buffer.get_quantification(
                self.scen_data, self.mock_population_data
            )

    def test_itn_campaign_quantification_different_code(self):
        """Test that ItnCampaignQuantification returns empty DataFrame when code does not match any column in scen_data."""

        quant = ItnCampaignQuantification(
            spacial_unit="adm2",
            assumptions={
                "itn_campaign_coverage": 0.5,
                "itn_campaign_divisor": 1,
                "itn_campaign_buffer_mult": 1,
            },
        )
        result = quant.get_quantification(pd.DataFrame(), self.mock_population_data)

        self.assertTrue(result.empty)

    def test_itn_campaign_quantification_missing_pop_column(self):
        """Test that ItnCampaignQuantification raises an error when population column is missing."""

        quant = ItnCampaignQuantification(
            spacial_unit="adm2",
            assumptions={
                "itn_campaign_coverage": 0.5,
                "itn_campaign_divisor": 1,
                "itn_campaign_buffer_mult": 1,
            },
        )
        with self.assertRaises(ValueError):
            quant.get_quantification(self.scen_data, pd.DataFrame())
