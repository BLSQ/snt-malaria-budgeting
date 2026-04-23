from .base_quantification import BaseQuantification


class PMCQuantification(BaseQuantification):
    def __init__(self, spatial_unit, assumptions={}):
        super().__init__(
            "pmc",
            spatial_unit,
            assumptions=assumptions,
            default_pop_col=["pop_0_1", "pop_1_2"],
            required_assumptions=[
                "pmc_coverage",
                "pmc_touchpoints",
                "pmc_tablet_factor",
                "pmc_buffer_mult",
            ],
        )

    def _validate_df_(self, df):
        if (
            not df[f"target_population_columns_{self.code}"]
            .apply(lambda x: len(x) == 2)
            .all()
        ):
            raise ValueError(
                f"target_population_columns_{self.code} must contain exactly 2 items"
            )
        return super()._validate_assumptions_()

    def _get_quantification_(self, df):
        """
        Calculate the quantification of preventive medicine doses for malaria-affected populations.
        This method computes the required quantity of seasonal preventive chemotherapy (SP) tablets
        based on population segments (children 0-1 years and 1-2 years), coverage rates, touchpoints,
        and dosage factors.
        Args:
            df: DataFrame containing the filtered and merged scenario and target population data.
        Returns:
            pd.DataFrame: A dataframe with the following columns:
                - quantity: Total number of SP tablets required (sum of sp_0_1 and sp_1_2)
                - target_pop: Target population reached (covered population for both age groups)
                - code_intervention: Code identifier for this intervention (self.code)
                - type_intervention: Type of intervention from the scenario data
                - unit: Unit of measurement ("per SP")
            Returns an empty DataFrame if the base dataframe is empty.
        Notes:
            - Children 0-1 years receive 1 dose per touchpoint (sp_0_1)
            - Children 1-2 years receive 2 doses per touchpoint (sp_1_2)
            - Calculations include coverage, touchpoints, tablet_factor, and buffer multiplier assumptions
        """

        pop_df = self._get_target_population_df_(df)

        pop_0_1 = pop_df.iloc[:, 0]
        pop_1_2 = pop_df.iloc[:, 1]

        sp_0_1 = (
            pop_0_1
            * self.assumptions[f"{self.code}_coverage"]
            * self.assumptions[f"{self.code}_touchpoints"]
            * 1
            * self.assumptions[f"{self.code}_tablet_factor"]
            * self.assumptions[f"{self.code}_buffer_mult"]
        )
        sp_1_2 = (
            pop_1_2
            * self.assumptions[f"{self.code}_coverage"]
            * self.assumptions[f"{self.code}_touchpoints"]
            * 2
            * self.assumptions[f"{self.code}_tablet_factor"]
            * self.assumptions[f"{self.code}_buffer_mult"]
        )
        return df.assign(
            quantity=sp_0_1 + sp_1_2,
            target_pop=pop_0_1 * self.assumptions[f"{self.code}_coverage"]
            + pop_1_2 * self.assumptions[f"{self.code}_coverage"],
            code_intervention=self.code,
            type_intervention=df[f"type_{self.code}"],
            unit="per SP",
        )
