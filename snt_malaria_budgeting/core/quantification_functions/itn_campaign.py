from .base_quantification import BaseQuantification


class ItnCampaignQuantification(BaseQuantification):
    def __init__(self, spatial_unit, assumptions={}):
        super().__init__(
            "itn_campaign",
            spatial_unit,
            assumptions=assumptions,
            default_pop_col=["pop_total"],
            required_assumptions=[
                "itn_campaign_coverage",
                "itn_campaign_divisor",
                "itn_campaign_buffer_mult",
                "itn_campaign_bale_size",
            ],
        )

    def _get_quantification_(self, df):
        """
        Calculate ITN (Insecticide-Treated Net) quantification based on scenario data and target population.

        This method computes the required quantity of nets and bales needed to meet coverage targets,
        applying coverage rates, divisor factors, and buffer multipliers from assumptions.

        Args:
            df: DataFrame containing the filtered and merged scenario and target population data.

        Returns:
            pd.DataFrame: A long-format DataFrame containing quantification data with columns:
                - All id_vars from the base dataframe (non-quantification columns)
                - unit: The unit of measurement ('per ITN' or 'per bale')
                - quantity: The calculated quantity value for the given unit
                Returns an empty DataFrame if the base dataframe is empty.

        Notes:
            - Calculates both net quantities and bale quantities
            - Applies coverage assumptions and buffer multipliers to target population
            - Converts net quantities to bale quantities using the bale_size assumption
            - Uses assumption keys: `{code}_coverage`, `{code}_divisor`, `{code}_buffer_mult`, `{code}_bale_size`
        """

        target_pop_raw = self._get_sum_target_population_(df)

        df = df.assign(
            quant_nets=(
                (target_pop_raw * self.assumptions[f"{self.code}_coverage"])
                / self.assumptions[f"{self.code}_divisor"]
            )
            * self.assumptions[f"{self.code}_buffer_mult"],
            target_pop=target_pop_raw * self.assumptions[f"{self.code}_coverage"],
            code_intervention=self.code,
            type_intervention=df[f"type_{self.code}"],
        ).assign(
            quant_bales=lambda x: x.quant_nets
            / self.assumptions[f"{self.code}_bale_size"]
        )
        df_long = df.melt(
            id_vars=[c for c in df.columns if not c.startswith("quant_")],
            value_vars=["quant_nets", "quant_bales"],
            var_name="unit",
            value_name="quantity",
        )
        df_long["unit"] = df_long["unit"].map(
            {"quant_nets": "per ITN", "quant_bales": "per bale"}
        )

        return df_long
