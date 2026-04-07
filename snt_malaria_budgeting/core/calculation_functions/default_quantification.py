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
        df = self.__get_base_df__(scen_data, target_population)
        if df.empty:
            return pd.DataFrame()

        coverage = self.assumptions.get(
            f"{self.code}_coverage", self.assumptions.get("default_coverage", 0.8)
        )

        df = df.assign(
            quantity=(df[self.pop_col[0]] * coverage),
            target_pop=df[self.pop_col[0]],
            code_intervention=self.code,
            type_intervention=df[f"type_{self.code}"],
            unit="none",  # This is a tricky one, it is used to know which cost class we should use but for default, we don't have any
        )

        return df
