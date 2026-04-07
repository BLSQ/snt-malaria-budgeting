import pandas as pd

from snt_malaria_budgeting.core.calculation_functions.base_quantification import (
    BaseQuantification,
)


class VaccQuantification(BaseQuantification):
    def __init__(self, spacial_unit, assumptions={}):
        super().__init__(
            "vacc",
            spacial_unit,
            assumptions=assumptions,
            label_pop_col="Vaccine: target population",
            default_pop_col=["pop_vaccine_5_36_months"],
        )

    def get_quantification(self, scen_data, target_population):
        df = self.__get_base_df__(scen_data, target_population)
        if df.empty:
            return pd.DataFrame()
        df = df.assign(
            quant_doses=df[self.pop_col[0]]  # TODO ain't sure about this
            * self.assumptions[f"{self.code}_coverage"]
            * self.assumptions[f"{self.code}_doses_per_child"]
            * self.assumptions[f"{self.code}_buffer_mult"],
            quant_child=df[self.pop_col[0]]  # TODO ain't sure about this neither
            * self.assumptions[f"{self.code}_coverage"],
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
