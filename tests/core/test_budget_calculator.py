import unittest
from unittest.mock import patch
import pandas as pd
from snt_malaria_budgeting.core.budget_calculator import generate_budget


class TestGenerateBudget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up mock dataframes and settings once for all tests."""
        # cls.settings = MockCostSettings()
        cls.settings = {}

        def get_assumption(label, default):
            return cls.settings.get(label, default)

        cls.settings["itn_campaign_divisor"] = get_assumption(
            "ITN Campaign: people per net", 1.8
        )
        cls.settings["itn_campaign_bale_size"] = get_assumption(
            "ITN Campaign: nets per bale", 50
        )
        cls.settings["itn_campaign_buffer_mult"] = 1 + get_assumption(
            "ITN Campaign: buffer (%)", 0.10
        )
        cls.settings["itn_campaign_coverage"] = get_assumption(
            "ITN Campaign: target population coverage", 1.00
        )
        cls.settings["itn_routine_coverage"] = get_assumption(
            "ITN Routine: target population coverage", 0.30
        )
        cls.settings["itn_routine_buffer_mult"] = 1 + get_assumption(
            "ITN Routine: buffer (%)", 0.10
        )
        cls.settings["iptp_anc_coverage"] = get_assumption("IPTp: ANC attendance", 0.80)
        cls.settings["iptp_doses_per_pw"] = get_assumption("IPTp: contact points", 3)
        cls.settings["iptp_buffer_mult"] = 1 + get_assumption(
            "IPTp: drug supply buffer", 0.10
        )
        cls.settings["smc_age_string"] = get_assumption(
            "SMC: age targeting", "0.18,0.77"
        )
        cls.settings["smc_pop_prop_3_11"], cls.settings["smc_pop_prop_12_59"] = [
            float(x) for x in cls.settings["smc_age_string"].split(",")
        ]
        cls.settings["smc_coverage"] = get_assumption(
            "SMC: target population coverage", 1.00
        )
        cls.settings["smc_monthly_rounds"] = get_assumption("SMC: cycles", 4)
        cls.settings["smc_buffer_mult"] = 1 + get_assumption(
            "SMC: drug supply buffer", 0.10
        )
        cls.settings["pmc_coverage"] = get_assumption("PMC: coverage", 0.85)
        cls.settings["pmc_touchpoints"] = get_assumption("PMC: contact points", 4)
        cls.settings["pmc_tablet_factor"] = get_assumption(
            "PMC: nutrition scaling factor", 0.75
        )
        cls.settings["pmc_buffer_mult"] = 1 + get_assumption(
            "PMC: drug supply buffer", 0.10
        )
        cls.settings["vacc_coverage"] = get_assumption("Vaccine: coverage", 0.84)
        cls.settings["vacc_doses_per_child"] = get_assumption(
            "Vaccine: number of doses", 4
        )
        cls.settings["vacc_buffer_mult"] = 1 + get_assumption(
            "Vaccine: supply buffer", 0.10
        )

        cls.scen_data = pd.DataFrame(
            {
                "adm1": ["State A"],
                "adm2": ["LGA 1"],
                "year": [2025],
                "scenario_name": ["Full Scenario"],
                "scenario_description": ["Test with all interventions"],
                "code_itn_campaign": [1],
                "type_itn_campaign": ["Dual AI"],
                "code_itn_routine": [1],
                "type_itn_routine": ["Dual AI"],
                "code_iptp": [1],
                "type_iptp": ["SP"],
                "code_smc": [1],
                "type_smc": ["SP+AQ"],
                "code_pmc": [1],
                "type_pmc": ["SP"],
                "code_vacc": [1],
                "type_vacc": ["R21"],
                "code_cm_public": [1],  # Case management is handled differently
            }
        )

        cls.mock_population_data = pd.DataFrame(
            {
                "adm1": ["State A"],
                "adm2": ["LGA 1"],
                "year": [2025],
                "pop_total": [342988.7383],
                "pop_pw": [17149.43692],
                "pop_0_5": [63109.92785],
                "pop_0_1": [13719.54953],
                "pop_1_2": [13719.54953],
                "pop_vaccine_5_36_months": [10975.63963],
                "pop_vaccine_5_36_mois": [10975.63963],
            }
        )

        cls.mock_cm_data = pd.DataFrame(
            {
                "adm1": ["State A"],
                "adm2": ["LGA 1"],
                "cm_rdt_kit_quantity": [500],
                "cm_act_packs_quantity": [400],
                "cm_iv_artesunate_quantity": [50],
                "cm_ras_quantity": [20],
            }
        )

        cls.cost_data = pd.DataFrame(
            {
                "code_intervention": [
                    "itn_campaign",
                    "itn_campaign",
                    "itn_routine",
                    "iptp",
                    "smc",
                    "smc",
                    "smc",
                    "pmc",
                    "pmc",
                    "vacc",
                    "vacc",
                    "cm_public",
                    "cm_public",
                    "cm_public",
                    "cm_public",
                ],
                "type_intervention": [
                    "Dual AI",
                    "Dual AI",
                    "Dual AI",
                    "SP",
                    "SP+AQ",
                    "SP+AQ",
                    "SP+AQ",
                    "SP",
                    "SP",
                    "R21",
                    "R21",
                    "RDT kits",
                    "AL",
                    "Artesunate injections",
                    "RAS",
                ],
                "unit": [
                    "per ITN",
                    "per bale",
                    "per ITN",
                    "per SP",
                    "per SPAQ pack 3-11 month olds",
                    "per SPAQ pack 12-59 month olds",
                    "per child",
                    "per SP",
                    "per child",
                    "per dose",
                    "per child",
                    "per RDT kit",
                    "per AL",
                    "per 60mg powder",
                    "per RAS",
                ],
                "cost_class": ["Commodity"] * 15,
                "cost_year_for_analysis": 2025,
                "usd_cost": [
                    3.490605554,
                    6.25,
                    3.490605554,
                    0.50558094,
                    0.24375,
                    0.271875,
                    1.33,
                    0.204375,
                    0.08125,
                    4.0,
                    1.0,
                    0.4625,
                    1.22,
                    2.003125,
                    0.439375,
                ],
                "local_currency_cost": [
                    5584.968886,
                    10000,
                    5584.968886,
                    808.929504,
                    390.0,
                    435.0,
                    2128.0,
                    327.0,
                    130.0,
                    5800.0,
                    584.0,
                    740.0,
                    1952.0,
                    3205.0,
                    703.0,
                ],
                "cost_name": ["test"] * 15,
            }
        )

    @patch("pandas.read_csv")
    @patch("pandas.read_excel")
    def run_generate_budget(self, mock_read_excel, mock_read_csv):
        """Helper method to run generate_budget with mocked file reads."""
        mock_read_excel.return_value = self.mock_population_data
        mock_read_csv.return_value = self.mock_cm_data
        return generate_budget(
            self.scen_data, self.cost_data, self.mock_population_data, self.settings
        )

    def test_itn_campaign_quantification(self):
        """Verify ITN Campaign quantities."""
        result = self.run_generate_budget()
        df = result[result["code_intervention"] == "itn_campaign"]
        # Expected nets = 342988.7383 pop * 1.0 coverage * 10% buffer / 1.8 = 209604.229
        expected_nets = 342988.7383 * 1.0 * 1.1 / 1.8
        self.assertAlmostEqual(
            df[df["unit"] == "per ITN"]["quantity"].iloc[0], expected_nets, 2
        )
        # Expected bales = 190549.2991 / 50 = 3810.985982
        self.assertAlmostEqual(
            df[df["unit"] == "per bale"]["quantity"].iloc[0], expected_nets / 50, 2
        )

    def test_itn_routine_quantification(self):
        """Verify ITN Routine quantities."""
        result = self.run_generate_budget()
        df = result[result["code_intervention"] == "itn_routine"]

        # Expected nets = (17149.43692 pw + 63109.92785 u5) * 0.3 * 1.1 buffer = 26485.59037
        self.assertAlmostEqual(df["quantity"].iloc[0], 26485.59037, 2)

    def test_iptp_quantification(self):
        """Verify IPTp quantities."""
        result = self.run_generate_budget()
        df = result[result["code_intervention"] == "iptp"]
        # Expected doses = 17149.43692 pw * 0.8 ANC * 3 doses * 1.1 buffer = 528
        self.assertAlmostEqual(df["quantity"].iloc[0], 45274.5134688, 2)

    def test_smc_quantification(self):
        """Verify SMC quantities."""
        result = self.run_generate_budget()
        df = result[result["code_intervention"] == "smc"]
        # Expected 3-11m packs = 63109.9279 u5 * 0.18 * 4 rounds * 1.1 buffer = 792
        self.assertAlmostEqual(
            df[df["unit"].str.contains("3-11")]["quantity"].iloc[0], 49983.0629, 2
        )
        # Expected 12-59m packs = 63109.9279 u5 * 0.77 * 4 rounds * 1.1 buffer = 3388
        self.assertAlmostEqual(
            df[df["unit"].str.contains("12-59")]["quantity"].iloc[0], 213816.4356, 2
        )

    def test_pmc_quantification(self):
        """Verify PMC quantities."""
        result = self.run_generate_budget()
        df = result[result["code_intervention"] == "pmc"]
        # Expected SP doses = (13719.54953 u1 * 0.85 * 4 * 0.75 * 1.1) + (13719.54953 u2 * 0.85 * 4 * 2 * 0.75 * 1.1)
        # 561 + 1122 = 1683
        self.assertAlmostEqual(
            df[df["unit"] == "per SP"]["quantity"].iloc[0], 115450.0093, 2
        )

    def test_vaccine_quantification(self):
        """Verify Vaccine quantities."""
        result = self.run_generate_budget()
        df = result[result["code_intervention"] == "vacc"]
        # Expected doses = 10975.63963 pop * 0.84 cov * 1.1 wastage * 4 doses = 40565.96406
        self.assertAlmostEqual(
            df[df["unit"] == "per dose"]["quantity"].iloc[0], 40565.96406, 2
        )

    # def test_case_management_quantification(self):
    #     """Verify Case Management quantities are loaded correctly."""
    #     result = self.run_generate_budget()
    #     df = result[result['code_intervention'] == 'cm_public']
    #     self.assertAlmostEqual(df[df['unit'] == 'per RDT kit']['quantity'].iloc[0], 500.0)
    #     self.assertAlmostEqual(df[df['unit'] == 'per AL']['quantity'].iloc[0], 400.0)

    def test_final_cost_calculation(self):
        """Verify a final cost_element calculation."""
        result = self.run_generate_budget()
        # IPTp: 45274.5134688 doses * $0.50558094/dose = $22889.93108
        iptp_cost = result[
            (result["code_intervention"] == "iptp") & (result["currency"] == "USD")
        ]["cost_element"].sum()
        self.assertAlmostEqual(iptp_cost, 22889.93108, 2)

        # ITN Campaign: 209604.229 nets * 3.490605554 USD/net = 731645.6858 USD
        # ITN Campaign: 4192.0846 bales * 6.25 USD/bale = 26200.5287 USD
        itn_campaign_cost_usd = result[
            (result["code_intervention"] == "itn_campaign")
            & (result["currency"] == "USD")
        ]["cost_element"].sum()
        self.assertAlmostEqual(itn_campaign_cost_usd, 731645.6858 + 26200.5287, 2)

        # ITN Routine: 26485.59037 nets * 5584.968886 NGN/net = 147921198.2 NGN
        itn_routine_cost_ngn = result[
            (result["code_intervention"] == "itn_routine")
            & (result["currency"] == "NGN")
        ]["cost_element"].sum()
        self.assertAlmostEqual(itn_routine_cost_ngn, 147921198.2, 1)

        # ITN Routine: 26485.59037 nets *  3.490605554 USD/net = 92450.74886
        itn_routine_cost_ngn = result[
            (result["code_intervention"] == "itn_routine")
            & (result["currency"] == "USD")
        ]["cost_element"].sum()
        self.assertAlmostEqual(itn_routine_cost_ngn, 92450.74886, 1)

        # Vaccine: 40565.96406 doses * $4.0/dose = $162263.85624
        # Vaccine: 9219.53 operational cost per child = $9219.537
        vacc_cost = result[
            (result["code_intervention"] == "vacc") & (result["currency"] == "USD")
        ]["cost_element"].sum()
        self.assertAlmostEqual(vacc_cost, 171483.393579, 2)

        # SMC 3-11m: 49983.062857 packs * $0.24375/pack = $12183.375
        # SMC 12-59m: 213816.435556 packs * $0.271875/pack = $58131.3434

        smc_cost = result[
            (result["code_intervention"] == "smc") & (result["currency"] == "USD")
        ]["cost_element"].sum()
        self.assertAlmostEqual(smc_cost, 12183.375 + 58131.3434, 2)

        # PMC: 115450.009295 doses * $0.204375/dose = $23595.09
        pmc_cost = result[
            (result["code_intervention"] == "pmc") & (result["currency"] == "USD")
        ]["cost_element"].sum()
        self.assertAlmostEqual(pmc_cost, 23595.0956, 2)

    def test_output_structure_and_completeness(self):
        """Verify the final DataFrame contains all expected interventions and columns."""
        result = self.run_generate_budget()
        self.assertIn("cost_element", result.columns)
        self.assertIn("intervention_nice", result.columns)

        expected_interventions = [
            "itn_campaign",
            "itn_routine",
            "iptp",
            "smc",
            "pmc",
            "vacc",
        ]
        present_interventions = result["code_intervention"].unique()
        for intervention in expected_interventions:
            self.assertIn(intervention, present_interventions)


if __name__ == "__main__":
    unittest.main(argv=["first-arg-is-ignored"], exit=False)
