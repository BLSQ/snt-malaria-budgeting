import pandas as pd

from .base_quantification import BaseQuantification


class SMCQuantification(BaseQuantification):
    def __init__(self, spatial_unit, assumptions={}):
        super().__init__(
            "smc",
            spatial_unit,
            assumptions=assumptions,
            label_pop_col="SMC: target population",
            default_pop_col=["pop_0_5"],
            required_assumptions=[
                "smc_coverage",
                "smc_monthly_rounds",
                "smc_buffer_mult",
                "smc_pop_prop_3_11",
                "smc_pop_prop_12_59",
            ],
        )

    def get_quantification(self, scen_data, target_population):
        """
        Calculate SMC (Seasonal Malaria Chemoprevention) quantification requirements.
        This method computes the required quantities of SPAQ (Sulfadoxine-Pyrimethamine + Amodiaquine)
        packs for different age groups based on population data, coverage assumptions, and monthly
        rounds of treatment.
        Parameters
        ----------
        scen_data : dict or DataFrame
            Scenario data containing population and intervention-related information.
        target_population : int or str
            The target population identifier or value used to filter/process scenario data.
        Returns
        -------
        pd.DataFrame
            A long-format DataFrame with the following columns:
            - All non-quantification columns from the base dataframe
            - unit : str
                The age group and unit type ("per SPAQ pack 3-11 month olds" or "per SPAQ pack 12-59 month olds")
            - quantity : float
                The calculated quantification requirement for the specified unit
            - code_intervention : str
                The intervention code
            - type_intervention : str
                The type of intervention
            - target_pop : float
                The target population covered
            Returns an empty DataFrame if base data is empty.
        Notes
        -----
        The quantification calculation includes:
        - Population proportion by age group (3-11 months and 12-59 months)
        - Coverage assumptions
        - Number of monthly rounds
        - Buffer multiplier for safety stock
        """

        df = self._get_base_df_(scen_data, target_population)
        if df.empty:
            return pd.DataFrame()

        self._validate_assumptions_()

        df = df.assign(
            quant_smc_3_11_months=(
                (df[self.pop_col[0]] * self.assumptions[f"{self.code}_pop_prop_3_11"])
                * self.assumptions[f"{self.code}_coverage"]
            )
            * self.assumptions[f"{self.code}_monthly_rounds"]
            * self.assumptions[f"{self.code}_buffer_mult"],
            quant_smc_12_59_months=(
                (df[self.pop_col[0]] * self.assumptions[f"{self.code}_pop_prop_12_59"])
                * self.assumptions[f"{self.code}_coverage"]
            )
            * self.assumptions[f"{self.code}_monthly_rounds"]
            * self.assumptions[f"{self.code}_buffer_mult"],
            target_pop=(
                df[self.pop_col[0]]
                * (
                    self.assumptions[f"{self.code}_pop_prop_3_11"]
                    + self.assumptions[f"{self.code}_pop_prop_12_59"]
                )
            )
            * self.assumptions[f"{self.code}_coverage"],
            code_intervention=self.code,
            type_intervention=df[f"type_{self.code}"],
        )
        df_long = df.melt(
            id_vars=[c for c in df.columns if not c.startswith("quant_")],
            value_vars=[
                f"quant_{self.code}_3_11_months",
                f"quant_{self.code}_12_59_months",
            ],
            var_name="unit",
            value_name="quantity",
        )
        unit_map = {
            f"quant_{self.code}_3_11_months": "per SPAQ pack 3-11 month olds",
            f"quant_{self.code}_12_59_months": "per SPAQ pack 12-59 month olds",
        }
        df_long["unit"] = df_long["unit"].map(unit_map)
        return df_long
