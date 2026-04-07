import pandas as pd

from .base_quantification import BaseQuantification


class IPTPQuantification(BaseQuantification):
    def __init__(self, spacial_unit, assumptions={}):
        super().__init__(
            "iptp",
            spacial_unit,
            assumptions=assumptions,
            label_pop_col="IPTp: target population",
            default_pop_col=["pop_pw"],
        )

    def get_quantification(self, scen_data, target_population):
        df = self.__get_base_df__(scen_data, target_population)
        if df.empty:
            return pd.DataFrame()

        df = df.assign(
            quantity=(
                (df["pop_pw"] * self.assumptions[f"{self.code}_anc_coverage"])
                * self.assumptions[f"{self.code}_doses_per_pw"]
            )
            * self.assumptions[f"{self.code}_buffer_mult"],
            target_pop=df["pop_pw"],
            code_intervention=self.code,
            type_intervention=df[f"type_{self.code}"],
            unit="per SP",
        )

        return df
