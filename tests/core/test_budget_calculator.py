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

        cls.settings["itn_campaign_divisor"] = get_assumption("ITN Campaign: people per net", 1.8)
        cls.settings["itn_campaign_bale_size"] = get_assumption("ITN Campaign: nets per bale", 50)
        cls.settings["itn_campaign_buffer_mult"] = 1 + get_assumption("ITN Campaign: buffer (%)", 0.10)
        cls.settings["itn_campaign_coverage"] = get_assumption("ITN Campaign: target population coverage", 1.00)
        cls.settings["itn_routine_coverage"] = get_assumption("ITN Routine: target population coverage", 0.30)
        cls.settings["itn_routine_buffer_mult"] = 1 + get_assumption("ITN Routine: buffer (%)", 0.10)
        cls.settings["iptp_anc_coverage"] = get_assumption("IPTp: ANC attendance", 0.80)
        cls.settings["iptp_doses_per_pw"] = get_assumption("IPTp: contact points", 3)
        cls.settings["iptp_buffer_mult"] = 1 + get_assumption("IPTp: drug supply buffer", 0.10)
        cls.settings["smc_age_string"] = get_assumption("SMC: age targeting", "0.18,0.77")
        cls.settings["smc_pop_prop_3_11"], cls.settings["smc_pop_prop_12_59"] = [float(x) for x in cls.settings["smc_age_string"].split(',')]
        cls.settings["smc_coverage"] = get_assumption("SMC: target population coverage", 1.00)
        cls.settings["smc_monthly_rounds"] = get_assumption("SMC: cycles", 4)
        cls.settings["smc_buffer_mult"] = 1 + get_assumption("SMC: drug supply buffer", 0.10)
        cls.settings["pmc_coverage"] = get_assumption("PMC: coverage", 0.85)
        cls.settings["pmc_touchpoints"] = get_assumption("PMC: contact points", 4)
        cls.settings["pmc_tablet_factor"] = get_assumption("PMC: nutrition scaling factor", 0.75)
        cls.settings["pmc_buffer_mult"] = 1 + get_assumption("PMC: drug supply buffer", 0.10)
        cls.settings["vacc_coverage"] = get_assumption("Vaccine: coverage", 0.84)
        cls.settings["vacc_doses_per_child"] = get_assumption("Vaccine: number of doses", 4)
        cls.settings["vacc_buffer_mult"] = 1 + get_assumption("Vaccine: supply buffer", 0.10)

        cls.scen_data = pd.DataFrame({
            'adm1': ['State A'], 'adm2': ['LGA 1'], 'year': [2025],
            'scenario_name': ['Full Scenario'], 'scenario_description': ['Test with all interventions'],
            'code_itn_campaign': [1], 'type_itn_campaign': ['Standard'],
            'code_itn_routine': [1], 'type_itn_routine': ['Standard'],
            'code_iptp': [1], 'type_iptp': ['SP'],
            'code_smc': [1], 'type_smc': ['SP+AQ'],
            'code_pmc': [1], 'type_pmc': ['SP'],
            'code_vacc': [1], 'type_vacc': ['R21'],
            'code_cm_public': [1] # Case management is handled differently
        })

        cls.mock_population_data = pd.DataFrame({
            'adm1': ['State A'], 'adm2': ['LGA 1'], 'year': [2025],
            'pop_total': [10000], 'pop_pw': [200], 'pop_0_5': [1000],
            'pop_0_1': [200], 'pop_1_2': [200], 'pop_vaccine_5_36_months': [800],
            'pop_vaccine_5_36_mois': [800]
        })

        cls.mock_cm_data = pd.DataFrame({
            'adm1': ['State A'], 'adm2': ['LGA 1'],
            'cm_rdt_kit_quantity': [500], 'cm_act_packs_quantity': [400],
            'cm_iv_artesunate_quantity': [50], 'cm_ras_quantity': [20]
        })

        cls.cost_data = pd.DataFrame({
            'code_intervention': [
                'itn_campaign', 'itn_campaign', 'itn_routine', 'iptp',
                'smc', 'smc', 'smc',
                'pmc', 'pmc', 'vacc', 'vacc',
                'cm_public', 'cm_public', 'cm_public', 'cm_public'
            ],
            'type_intervention': [
                'Standard', 'Standard', 'Standard', 'SP',
                'SP+AQ', 'SP+AQ', 'SP+AQ',
                'SP', 'SP', 'R21', 'R21',
                'RDT kits', 'AL', 'Artesunate injections', 'RAS'
            ],
            'unit': [
                'per ITN', 'per bale', 'per ITN', 'per SP',
                'per SPAQ pack 3-11 month olds', 'per SPAQ pack 12-59 month olds', 'per child',
                'per SP', 'per child', 'per dose', 'per child',
                'per RDT kit', 'per AL', 'per 60mg powder', 'per RAS'
            ],
            'cost_class': ['Commodity'] * 15,
            'cost_year_for_analysis': 2025,
            'usd_cost': [2.0, 100.0, 2.1, 0.5, 1.0, 1.0, 0.0, 0.6, 0.0, 4.0, 0.0, 0.2, 1.5, 5.0, 3.0],
            'local_currency_cost': [1800, 90000, 1890, 450, 900, 900, 0, 540, 0, 3600, 0, 180, 1350, 4500, 2700],
            'cost_name': ['test'] * 15
        })

    @patch('pandas.read_csv')
    @patch('pandas.read_excel')
    def run_generate_budget(self, mock_read_excel, mock_read_csv):
        """Helper method to run generate_budget with mocked file reads."""
        mock_read_excel.return_value = self.mock_population_data
        mock_read_csv.return_value = self.mock_cm_data
        return generate_budget(self.scen_data, self.cost_data, self.mock_population_data, self.settings) 
                               

    def test_itn_campaign_quantification(self):
        """Verify ITN Campaign quantities."""
        result = self.run_generate_budget()
        df = result[result['code_intervention'] == 'itn_campaign']
        # Expected nets = 10000 pop * 1.0 coverage * 1.1 buffer / 1.8 = 5555.55
        expected_nets = 10000 * 1.0 * 1.1 / 1.8
        self.assertAlmostEqual(df[df['unit'] == 'per ITN']['quantity'].iloc[0], expected_nets, 2)
        # Expected bales = 5555.55 / 50 = 111.11
        self.assertAlmostEqual(df[df['unit'] == 'per bale']['quantity'].iloc[0], expected_nets / 50, 2)

    def test_itn_routine_quantification(self):
        """Verify ITN Routine quantities."""
        result = self.run_generate_budget()
        df = result[result['code_intervention'] == 'itn_routine']
        # Expected nets = (200 pw + 1000 u5) * 0.3 * 1.1 buffer = 396
        self.assertAlmostEqual(df['quantity'].iloc[0], 396.0)

    def test_iptp_quantification(self):
        """Verify IPTp quantities."""
        result = self.run_generate_budget()
        df = result[result['code_intervention'] == 'iptp']
        # Expected doses = 200 pw * 0.8 ANC * 3 doses * 1.1 buffer = 528
        self.assertAlmostEqual(df['quantity'].iloc[0], 528.0)

    def test_smc_quantification(self):
        """Verify SMC quantities."""
        result = self.run_generate_budget()
        df = result[result['code_intervention'] == 'smc']
        # Expected 3-11m packs = 1000 u5 * 0.18 * 4 rounds * 1.1 buffer = 792
        self.assertAlmostEqual(df[df['unit'].str.contains('3-11')]['quantity'].iloc[0], 792.0)
        # Expected 12-59m packs = 1000 u5 * 0.77 * 4 rounds * 1.1 buffer = 3388
        self.assertAlmostEqual(df[df['unit'].str.contains('12-59')]['quantity'].iloc[0], 3388.0)

    def test_pmc_quantification(self):
        """Verify PMC quantities."""
        result = self.run_generate_budget()
        df = result[result['code_intervention'] == 'pmc']
        # Expected SP doses = (200 u1 * 0.85 * 4 * 0.75 * 1.1) + (200 u2 * 0.85 * 4 * 2 * 0.75 * 1.1)
        # 561 + 1122 = 1683
        self.assertAlmostEqual(df[df['unit'] == 'per SP']['quantity'].iloc[0], 1683.0)

    def test_vaccine_quantification(self):
        """Verify Vaccine quantities."""
        result = self.run_generate_budget()
        df = result[result['code_intervention'] == 'vacc']
        # Expected doses = 800 pop * 0.84 cov * 1.1 wastage * 4 doses = 2956.8
        self.assertAlmostEqual(df[df['unit'] == 'per dose']['quantity'].iloc[0], 2956.8)

    # def test_case_management_quantification(self):
    #     """Verify Case Management quantities are loaded correctly."""
    #     result = self.run_generate_budget()
    #     df = result[result['code_intervention'] == 'cm_public']
    #     self.assertAlmostEqual(df[df['unit'] == 'per RDT kit']['quantity'].iloc[0], 500.0)
    #     self.assertAlmostEqual(df[df['unit'] == 'per AL']['quantity'].iloc[0], 400.0)

    def test_final_cost_calculation(self):
        """Verify a final cost_element calculation."""
        result = self.run_generate_budget()
        # IPTp: 528 doses * $0.5/dose = $264
        iptp_cost = result[(result['code_intervention'] == 'iptp') & (result['currency'] == 'USD')]['cost_element'].iloc[0]
        self.assertAlmostEqual(iptp_cost, 264.0)
        # ITN Routine: 360 nets * 1890 NGN/net *1.1 buffer = 748,440 NGN
        itn_routine_cost_ngn = result[(result['code_intervention'] == 'itn_routine') & (result['currency'] == 'NGN')]['cost_element'].iloc[0]
        self.assertAlmostEqual(itn_routine_cost_ngn, 748440.0)

    def test_output_structure_and_completeness(self):
        """Verify the final DataFrame contains all expected interventions and columns."""
        result = self.run_generate_budget()
        self.assertIn('cost_element', result.columns)
        self.assertIn('intervention_nice', result.columns)
        
        expected_interventions = [
            'itn_campaign', 'itn_routine', 'iptp', 'smc', 'pmc', 'vacc'
        ]
        present_interventions = result['code_intervention'].unique()
        for intervention in expected_interventions:
            self.assertIn(intervention, present_interventions)


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
