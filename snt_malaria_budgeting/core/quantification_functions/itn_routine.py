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
            required_assumptions=[
                f"{code}_coverage",
                f"{code}_buffer_mult",
            ],
        )

    def get_quantification(self, scen_data, target_population):
        """
        Calculate the quantification of ITN (Insecticide-Treated Net) interventions.
        This method computes the number of ITNs needed based on target population,
        coverage assumptions, and buffer multipliers. It follows Partner Guide section 4.3.
        Parameters
        ----------
        scen_data : dict or pd.DataFrame
            Scenario data containing relevant parameters and assumptions for the calculation.
        target_population : str
            The population segment of interest (e.g., 'children_under_5', 'pregnant_women').
        Returns
        -------
        pd.DataFrame
            A DataFrame with the following columns:
            - target_pop : int
                Total target population for the intervention.
            - quantity : float
                Calculated quantity of ITNs needed (target_pop * coverage * buffer_multiplier).
            - code_intervention : str
                The code identifier for the intervention.
            - type_intervention : str
                The type of intervention.
            - unit : str
                Unit of measurement ("per ITN").
            Returns an empty DataFrame if the base data is empty.
        Notes
        -----
        The quantification calculation applies:
        1. Coverage rate from assumptions
        2. Buffer multiplier to account for waste/loss
        3. Summation of target population across relevant dimensions
        """

        # --- Quantification (Partner Guide: 4.3) ---
        # Get population of interest (e.g., children under 5 or pregnant
        df = self.__get_base_df__(scen_data, target_population)
        if df.empty:
            return pd.DataFrame()

        self.__validate_assumptions__()

        df["target_pop"] = df[self.pop_col].sum(axis=1)
        return df.assign(
            quantity=(df["target_pop"] * self.assumptions[f"{self.code}_coverage"])
            * self.assumptions[f"{self.code}_buffer_mult"],
            code_intervention=self.code,
            type_intervention=df[f"type_{self.code}"],
            unit="per ITN",
        )
