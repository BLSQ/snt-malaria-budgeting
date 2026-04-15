import pandas as pd

from .base_quantification import BaseQuantification


class DefaultQuantification(BaseQuantification):
    def __init__(self, code, spatial_unit, assumptions={}):
        super().__init__(
            code,
            spatial_unit,
            assumptions=assumptions,
            default_pop_col=["pop_total"],
        )

    def _get_quantification_(self, df):
        """
        Calculate quantification for an intervention based on scenario data and target population.

        This method retrieves base data, applies coverage assumptions, and returns a DataFrame
        with calculated quantities and metadata for the intervention.

        Args:
            df: DataFrame containing the filtered and merged scenario and target population data.

        Returns:
            pd.DataFrame: A DataFrame containing quantification results with columns:
                - quantity: Calculated quantity (population * coverage)
                - target_pop: Target population value
                - code_intervention: Intervention code identifier
                - type_intervention: Type of intervention
                - unit: Unit type (default: "none", used for cost class classification)
                Returns an empty DataFrame if base data is empty.

        Notes:
            - Coverage is retrieved from assumptions using the pattern "{code}_coverage",
              falling back to "default_coverage" (default: 0.8) if not found.
            - The unit field defaults to "none" and is used internally for cost class determination.
        """
        coverage = self.assumptions.get(
            f"{self.code}_coverage", self.assumptions.get("default_coverage", 1)
        )

        target_pop_sum = self._get_sum_target_population_(df)

        return df.assign(
            quantity=target_pop_sum * coverage,
            target_pop=target_pop_sum,
            code_intervention=self.code,
            type_intervention=df[f"type_{self.code}"],
            unit="Other",  # This is a tricky one, it is used to know which cost class we should use but for default, we don't have any
        )
