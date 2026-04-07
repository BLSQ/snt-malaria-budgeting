import pandas as pd
from .base_quantification import BaseQuantification


class ItnCampaignQuantification(BaseQuantification):
    def __init__(self, spacial_unit, assumptions={}):
        super().__init__(
            "itn_campaign",
            spacial_unit,
            assumptions=assumptions,
            # TODO I think we can get rid of this
            label_pop_col="ITN Campaign: target population",
            default_pop_col=["pop_total"],
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
        df["target_pop_raw"] = df[self.pop_col].sum(axis=1)

        df = df.assign(
            quant_nets=(
                (df["target_pop_raw"] * self.assumptions[f"{self.code}_coverage"])
                / self.assumptions[f"{self.code}_divisor"]
            )
            * self.assumptions[f"{self.code}_buffer_mult"],
            target_pop=df["target_pop_raw"] * self.assumptions[f"{self.code}_coverage"],
            code_intervention=self.code,
            type_intervention=df[f"type_{self.code}"],
        ).assign(
            quant_bales=lambda x: x.quant_nets
            / self.assumptions[f"{self.code}_bale_size"]
        )
        df_long = df.melt(
            id_vars=[c for c in df.columns if not c.startswith("quant_")],
            value_vars=["quant_nets", "quant_bales"],
            var_name="unit",
            value_name="quantity",
        )
        df_long["unit"] = df_long["unit"].map(
            {"quant_nets": "per ITN", "quant_bales": "per bale"}
        )

        return df_long
