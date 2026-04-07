import pandas as pd

from .base_quantification import BaseQuantification


class SMCQuantification(BaseQuantification):
    def __init__(self, spacial_unit, assumptions={}):
        super().__init__(
            "smc",
            spacial_unit,
            assumptions=assumptions,
            label_pop_col="SMC: target population",
            default_pop_col=["pop_0_5"],
        )

    def get_quantification(self, scen_data, target_population):
        df = self.__get_base_df__(scen_data)
        if df.empty:
            return pd.DataFrame()

        df = pd.merge(
            df,
            target_population[list(set(self.join_keys + self.pop_col))],
            on=self.join_keys,
        )
        df = df.assign(
            quant_smc_3_11_months=(
                (df["pop_0_5"] * self.assumptions[f"{self.code}_pop_prop_3_11"])
                * self.assumptions[f"{self.code}_coverage"]
            )
            * self.assumptions[f"{self.code}_monthly_rounds"]
            * self.assumptions[f"{self.code}_buffer_mult"],
            quant_smc_12_59_months=(
                (df["pop_0_5"] * self.assumptions[f"{self.code}_pop_prop_12_59"])
                * self.assumptions[f"{self.code}_coverage"]
            )
            * self.assumptions[f"{self.code}_monthly_rounds"]
            * self.assumptions[f"{self.code}_buffer_mult"],
            target_pop=(
                df["pop_0_5"]
                * (
                    self.assumptions[f"{self.code}_pop_prop_3_11"]
                    + self.assumptions[f"{self.code}_pop_prop_12_59"]
                )
            )
            * self.assumptions[f"{self.code}_coverage"],
            code_intervention=self.code,
            type_intervention=df[f"type_{self.code}"],
        )
        df_long = df.melt(
            id_vars=[c for c in df.columns if not c.startswith("quant_")],
            value_vars=[
                f"quant_{self.code}_3_11_months",
                f"quant_{self.code}_12_59_months",
            ],
            var_name="unit",
            value_name="quantity",
        )
        unit_map = {
            f"quant_{self.code}_3_11_months": "per SPAQ pack 3-11 month olds",
            f"quant_{self.code}_12_59_months": "per SPAQ pack 12-59 month olds",
        }
        df_long["unit"] = df_long["unit"].map(unit_map)
        return df_long
