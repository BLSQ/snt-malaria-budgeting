from .base_quantification import BaseQuantification


class SMCBaseQuantification(BaseQuantification):
    def __init__(self, code, spatial_unit, assumptions={}):
        super().__init__(
            code,
            spatial_unit,
            assumptions=assumptions,
            default_pop_col=["pop_0_5"],
            required_assumptions=[
                f"{code}_coverage",
                f"{code}_monthly_rounds",
                f"{code}_buffer_mult",
                f"{code}_pop_prop_3_11",
                f"{code}_pop_prop_12_59",
            ],
        )

    def _get_quantification_(self, df):
        """
        Calculate SMC (Seasonal Malaria Chemoprevention) quantification requirements.
        This method computes the required quantities of SPAQ (Sulfadoxine-Pyrimethamine + Amodiaquine)
        packs for different age groups based on population data, coverage assumptions, and monthly
        rounds of treatment.
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame containing the filtered and merged scenario and target population data.
        Returns
        -------
        pd.DataFrame
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

        target_pop_raw = self._get_sum_target_population_(df)

        df = df.assign(
            **{
                f"quant_{self.code}_3_11_months": (
                    (target_pop_raw * self.assumptions[f"{self.code}_pop_prop_3_11"])
                    * self.assumptions[f"{self.code}_coverage"]
                )
                * self.assumptions[f"{self.code}_monthly_rounds"]
                * self.assumptions[f"{self.code}_buffer_mult"],
                f"quant_{self.code}_12_59_months": (
                    (target_pop_raw * self.assumptions[f"{self.code}_pop_prop_12_59"])
                    * self.assumptions[f"{self.code}_coverage"]
                )
                * self.assumptions[f"{self.code}_monthly_rounds"]
                * self.assumptions[f"{self.code}_buffer_mult"],
                "target_pop": (
                    target_pop_raw
                    * (
                        self.assumptions[f"{self.code}_pop_prop_3_11"]
                        + self.assumptions[f"{self.code}_pop_prop_12_59"]
                    )
                )
                * self.assumptions[f"{self.code}_coverage"],
                "code_intervention": self.code,
                "type_intervention": df[f"type_{self.code}"],
            }
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


class SMCQuantification(SMCBaseQuantification):
    def __init__(self, spatial_unit, assumptions={}):
        super().__init__("smc", spatial_unit, assumptions)


class SMC3Quantification(SMCBaseQuantification):
    def __init__(self, spatial_unit, assumptions={}):
        super().__init__("smc_3", spatial_unit, assumptions)


class SMC4Quantification(SMCBaseQuantification):
    def __init__(self, spatial_unit, assumptions={}):
        super().__init__("smc_4", spatial_unit, assumptions)


class SMC5Quantification(SMCBaseQuantification):
    def __init__(self, spatial_unit, assumptions={}):
        super().__init__("smc_5", spatial_unit, assumptions)
