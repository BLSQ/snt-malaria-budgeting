from typing import Dict, List


class BaseQuantification:
    def __init__(
        self,
        code,
        spacial_unit="adm1",
        assumptions={},
        label_pop_col="Total population",
        default_pop_col=["pop_total"],
    ):
        self.code = code
        self.join_keys = [spacial_unit] + ["year"]
        self.assumptions = assumptions
        self.pop_col = self.__get_pop_column__(
            label_pop_col, default_pop_col, assumptions=assumptions
        )

    def get_quantification(self, scen_data, target_population, all_quantifications):
        raise NotImplementedError("Subclasses must implement this method")

    def __get_base_df__(self, scen_data):
        return scen_data[scen_data[f"code_{self.code}"] == 1].copy()

    # TODO: not sure this makes sense, only two of them are used and default is the same as mapping.
    def __get_pop_column__(
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
