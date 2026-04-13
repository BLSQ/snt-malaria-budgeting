from typing import Dict, List

import pandas as pd

# TODO We should get rid of the label pop column here.
# Assumptions should have directly smth like pop_col: List[str] = ["pop_total"], and not this weird mapping we then need to do in the code.
# Should also make sure this can be scoped per assignment, e.g., we might want to use different pop columns for the same intervention in different assignments.


class BaseQuantification:
    def __init__(
        self,
        code,
        spatial_unit="adm1",
        assumptions={},
        label_pop_col="Total population",
        default_pop_col=["pop_total"],
        required_assumptions=[],
    ):
        self.code = code
        self.join_keys = [spatial_unit] + ["year"]
        self.assumptions = assumptions
        self.pop_col = self._get_pop_column_(
            label_pop_col, default_pop_col, assumptions=assumptions
        )
        self.required_assumptions = required_assumptions

    def get_quantification(self, scen_data, target_population, all_quantifications):
        raise NotImplementedError("Subclasses must implement this method")

    def _get_base_df_(self, scen_data, target_population):
        if f"code_{self.code}" not in scen_data.columns:
            return pd.DataFrame()

        df = scen_data[scen_data[f"code_{self.code}"] == 1].copy()
        if df.empty:
            return pd.DataFrame()

        if not all(
            col in target_population.columns for col in self.join_keys + self.pop_col
        ):
            raise ValueError(
                f"Target population DataFrame must contain columns: {self.join_keys + self.pop_col}"
            )

        df = pd.merge(
            df,
            target_population[self.join_keys + self.pop_col],
            on=self.join_keys,
        )

        return df

    def _validate_assumptions_(self):
        missing_assumptions = [
            assumption
            for assumption in self.required_assumptions
            if assumption not in self.assumptions
        ]
        if missing_assumptions:
            raise ValueError(
                f"Missing assumptions for {self.code}: {', '.join(missing_assumptions)}"
            )

    # TODO: This part is weird, label can be: ITN Campaign: target population, etc ...
    # So we try to get it from provided assumptions, which I guess look like something like {"ITN Campaign: target population": "Total population"},
    # and then we have a mapping of what those labels mean in terms of pop columns, e.g., Total population => pop_total, Children under 5 => pop_0_5, etc ...
    # But this doesn't allow to target other populations than hardcoded one from the parent class or the mapping.
    # IMO we should just directly pass the pop columns we want to use as assumptions, and not have this mapping at all.
    # This will be more flexible and less error prone.
    # We can still have a default value if the assumption is not provided, but it should be the actual column name(s) in the pop DF, not some label that we then need to map to column names.
    def _get_pop_column_(
        self, label: str, default_col: List[str], assumptions: Dict[str, float]
    ) -> List[str]:
        pop_assumption = assumptions.get(label)
        if not pop_assumption:
            return default_col
        mapping = {
            "Total population": ["pop_total"],
            "Children under 5": ["pop_0_5"],
            "Children under 5 and pregnant women": ["pop_0_5", "pop_pw"],
            "Children under 10": ["pop_0_5", "pop_5_10"],
            "Children 0-1": ["pop_0_1"],
            "Children 1-2": ["pop_1_2"],
            "Pregnant women": ["pop_pw"],
        }
        return mapping.get(str(pop_assumption), default_col)
