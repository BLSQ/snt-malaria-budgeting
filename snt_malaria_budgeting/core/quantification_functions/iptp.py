import pandas as pd

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

    def get_quantification(self, scen_data, target_population):
        """
        Calculate the quantification of IPTp (Intermittent Preventive Treatment in pregnancy) doses.

        Computes the required quantity of SP (Sulfadoxine-Pyrimethamine) based on population coverage,
        doses per pregnant women, and buffer multiplier assumptions.

        Args:
            scen_data: Scenario data containing relevant assumptions and parameters.
            target_population: Target population class or identifier for which to calculate quantification.

        Returns:
            pd.DataFrame: DataFrame with calculated quantification including columns:
                - quantity: Calculated number of SP doses accounting for coverage, doses per pregnant woman, and buffer
                - target_pop: Target population value
                - code_intervention: Code identifier for the intervention (IPTp)
                - type_intervention: Type classification of the intervention
                - unit: Unit of measurement ("per SP")

            Returns an empty DataFrame if base data is empty.
        """
        df = self._get_base_df_(scen_data, target_population)
        if df.empty:
            return pd.DataFrame()

        self._validate_assumptions_()

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
