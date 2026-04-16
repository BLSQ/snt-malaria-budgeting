from .base_quantification import BaseQuantification


class IPTPQuantification(BaseQuantification):
    def __init__(self, spatial_unit, assumptions={}):
        super().__init__(
            "iptp",
            spatial_unit,
            assumptions=assumptions,
            default_pop_col=["pop_pw"],
            required_assumptions=[
                "iptp_anc_coverage",
                "iptp_doses_per_pw",
                "iptp_buffer_mult",
            ],
        )

    def _get_quantification_(self, df):
        """
        Calculate the quantification of IPTp (Intermittent Preventive Treatment in pregnancy) doses.

        Computes the required quantity of SP (Sulfadoxine-Pyrimethamine) based on population coverage,
        doses per pregnant women, and buffer multiplier assumptions.

        Args:
            df: DataFrame containing the filtered and merged scenario and target population data.

        Returns:
            pd.DataFrame: DataFrame with calculated quantification including columns:
                - quantity: Calculated number of SP doses accounting for coverage, doses per pregnant woman, and buffer
                - target_pop: Target population value
                - code_intervention: Code identifier for the intervention (IPTp)
                - type_intervention: Type classification of the intervention
                - unit: Unit of measurement ("per SP")

            Returns an empty DataFrame if base data is empty.
        """

        sum_target_pop = self._get_sum_target_population_(df)

        return df.assign(
            quantity=(
                (sum_target_pop * self.assumptions[f"{self.code}_anc_coverage"])
                * self.assumptions[f"{self.code}_doses_per_pw"]
            )
            * self.assumptions[f"{self.code}_buffer_mult"],
            target_pop=sum_target_pop,
            code_intervention=self.code,
            type_intervention=df[f"type_{self.code}"],
            unit="per SP",
        )
