import pandas as pd

from snt_malaria_budgeting.core.quantification_functions.base_quantification import (
    BaseQuantification,
)


class VaccQuantification(BaseQuantification):
    def __init__(self, spatial_unit, assumptions={}):
        super().__init__(
            "vacc",
            spatial_unit,
            assumptions=assumptions,
            default_pop_col=["pop_vaccine_5_36_months"],
            required_assumptions=[
                "vacc_coverage",
                "vacc_doses_per_child",
                "vacc_buffer_mult",
            ],
        )

    def get_quantification(self, scen_data, target_population):
        """
        Calculate quantification metrics for vaccination interventions.
        This method computes the required doses and target child population for a vaccination
        intervention based on scenario data, coverage assumptions, and dosing parameters.
        Args:
            scen_data: Scenario data containing relevant parameters and context for the calculation.
            target_population: The target population segment for which to calculate quantification.
        Returns:
            pd.DataFrame: A long-format DataFrame containing quantification results with the following columns:
                - All columns from the base dataframe (except those starting with "quant_")
                - unit: The unit of measurement ("per dose" or "per child")
                - quantity: The calculated quantity value
                - target_pop: Target population count (equals quant_child)
                - code_intervention: The intervention code identifier
                - type_intervention: The type of intervention
        Raises:
            Returns an empty DataFrame if the base dataframe is empty.
        Notes:
            - Uses assumptions for coverage, doses per child, and buffer multiplier
            - Converts wide format (quant_doses, quant_child) to long format for easier analysis
            - Buffer multiplier accounts for waste and contingency in dose calculations
        """

        df = self._get_base_df_(scen_data, target_population)
        if df.empty:
            return pd.DataFrame()

        self._validate_assumptions_()

        target_pop_raw = self._get_sum_target_population_(df)

        df = df.assign(
            quant_doses=target_pop_raw
            * self.assumptions[f"{self.code}_coverage"]
            * self.assumptions[f"{self.code}_doses_per_child"]
            * self.assumptions[f"{self.code}_buffer_mult"],
            quant_child=target_pop_raw * self.assumptions[f"{self.code}_coverage"],
        ).assign(
            target_pop=lambda x: x.quant_child,
            code_intervention=self.code,
            type_intervention=df[f"type_{self.code}"],
        )
        df_long = df.melt(
            id_vars=[c for c in df.columns if not c.startswith("quant_")],
            value_vars=["quant_doses", "quant_child"],
            var_name="unit",
            value_name="quantity",
        )
        df_long["unit"] = df_long["unit"].map(
            {"quant_doses": "per dose", "quant_child": "per child"}
        )

        return df_long
