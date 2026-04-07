import pandas as pd
from .base_quantification import BaseQuantification


class ItnRoutineQuantification(BaseQuantification):
    def __init__(self, code="itn_routine", spacial_unit="adm1", assumptions={}):
        super().__init__(
            code,
            spacial_unit,
            assumptions=assumptions,
            label_pop_col="ITN Routine: target population",
            default_pop_col=["pop_0_5", "pop_pw"],
        )

    def get_quantification(self, scen_data, target_population):
        # --- Quantification (Partner Guide: 4.3) ---
        # Get population of interest (e.g., children under 5 or pregnant
        df = self.__get_base_df__(scen_data)
        if df.empty:
            return pd.DataFrame()

        df = pd.merge(
            df,
            target_population[list(set(self.join_keys + self.pop_col))],
            on=self.join_keys,
        )
        df["target_pop"] = df[self.pop_col].sum(axis=1)
        df = df.assign(
            quantity=(df["target_pop"] * self.assumptions[f"{self.code}_coverage"])
            * self.assumptions[f"{self.code}_buffer_mult"],
            code_intervention=self.code,
            type_intervention=df[f"type_{self.code}"],
            unit="per ITN",
        )

        return df
