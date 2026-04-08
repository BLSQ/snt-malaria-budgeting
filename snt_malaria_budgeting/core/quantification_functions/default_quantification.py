import pandas as pd

from .base_quantification import BaseQuantification


class DefaultQuantification(BaseQuantification):
    def __init__(self, code, spacial_unit, assumptions={}):
        super().__init__(
            code,
            spacial_unit,
            assumptions=assumptions,
            default_pop_col=["pop_total"],
        )

    def get_quantification(self, scen_data, target_population):
        """
        Calculate quantification for an intervention based on scenario data and target population.

        This method retrieves base data, applies coverage assumptions, and returns a DataFrame
        with calculated quantities and metadata for the intervention.

        Args:
            scen_data: Scenario data containing information needed to build the base DataFrame.
            target_population: Target population parameters for quantification calculation.

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
        df = self.__get_base_df__(scen_data, target_population)
        if df.empty:
            return pd.DataFrame()

        coverage = self.assumptions.get(
            f"{self.code}_coverage", self.assumptions.get("default_coverage", 0.8)
        )

        return df.assign(
            quantity=(df[self.pop_col[0]] * coverage),
            target_pop=df[self.pop_col[0]],
            code_intervention=self.code,
            type_intervention=df[f"type_{self.code}"],
            unit="none",  # This is a tricky one, it is used to know which cost class we should use but for default, we don't have any
        )
