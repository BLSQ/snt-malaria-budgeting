import pandas as pd

from .base_quantification import BaseQuantification


class PMCQuantification(BaseQuantification):
    def __init__(self, spacial_unit, assumptions={}):
        super().__init__(
            "pmc",
            spacial_unit,
            assumptions=assumptions,
            label_pop_col="PMC: target population",
            default_pop_col=["pop_0_1", "pop_1_2"],
        )

    def get_quantification(self, scen_data, target_population):
        df = self.__get_base_df__(scen_data)
        if df.empty:
            return pd.DataFrame()

        df = pd.merge(
            df, target_population[self.join_keys + self.pop_col], on=self.join_keys
        )

        # TODO Loop through pop columns instead of hardcoding pop_0_1 and pop_1_2, and pass in the age groups as arguments instead of hardcoding them here.
        # TODO Not sure as we need to double the value if 1_2 since these children will receive 2 SP doses
        sp_0_1 = (
            df[
                "pop_0_1"
            ]  # TODO: This shouldn't be hardcoded here, but rather passed in as an argument. Same for pop_1_2
            * self.assumptions[f"{self.code}_coverage"]
            * self.assumptions[f"{self.code}_touchpoints"]
            * 1
            * self.assumptions[f"{self.code}_tablet_factor"]
            * self.assumptions[f"{self.code}_buffer_mult"]
        )
        sp_1_2 = (
            df[
                "pop_1_2"
            ]  # TODO: This shouldn't be hardcoded here, but rather passed in as an argument. Same for pop_0_1
            * self.assumptions[f"{self.code}_coverage"]
            * self.assumptions[f"{self.code}_touchpoints"]
            * 2
            * self.assumptions[f"{self.code}_tablet_factor"]
            * self.assumptions[f"{self.code}_buffer_mult"]
        )
        df = df.assign(
            quantity=sp_0_1 + sp_1_2,
            target_pop=df["pop_0_1"] * self.assumptions[f"{self.code}_coverage"]
            + df["pop_1_2"] * self.assumptions[f"{self.code}_coverage"],
            code_intervention=self.code,
            type_intervention=df[f"type_{self.code}"],
            unit="per SP",
        )

        return df
