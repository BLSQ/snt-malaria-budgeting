import itertools

import pandas as pd


class BaseQuantification:
    def __init__(
        self,
        code,
        spatial_unit="adm1",
        assumptions={},
        default_pop_col=["pop_total"],
        required_assumptions=[],
    ):
        self.code = code
        self.join_keys = [spatial_unit] + ["year"]
        self.assumptions = assumptions
        self.default_pop_col = default_pop_col
        self.required_assumptions = required_assumptions

    def get_quantification(self, scen_data, target_population, all_quantifications):
        raise NotImplementedError("Subclasses must implement this method")

    def _get_base_df_(self, scen_data, target_population):
        """
        Retrieves and processes base dataframe by filtering scenario data and merging with target population.
        This method filters the scenario data based on the intervention code, ensures the target population
        columns are properly defined, validates that required columns exist in the target population dataframe,
        and performs a merge operation.
        Parameters
        ----------
        scen_data : pd.DataFrame
            Scenario data dataframe containing a column named `code_{self.code}` with binary values (0 or 1).
            Should also optionally contain a `target_population_columns` column with list values specifying
            which columns from target_population to use for the merge.
        target_population : pd.DataFrame
            Target population dataframe containing columns specified in `self.join_keys` and any columns
            referenced in the `target_population_columns` field from scen_data.
        Returns
        -------
        pd.DataFrame
            Merged dataframe containing rows from scen_data where `code_{self.code}` equals 1, combined with
            corresponding rows from target_population based on join_keys. Returns an empty DataFrame if:
            - The code column does not exist in scen_data
            - No rows match the filter condition (code_{self.code} == 1)
        Raises
        ------
        ValueError
            If target_population does not contain all required columns (self.join_keys + target_population_columns).
        """

        if f"code_{self.code}" not in scen_data.columns:
            return pd.DataFrame()

        df = scen_data[scen_data[f"code_{self.code}"] == 1].copy()
        if df.empty:
            return pd.DataFrame()

        # Dataframe might or might not have a target_population_columns column that can vary depending on the intervention.
        # We need to set that target_population_columns column using the predefine default_pop_col if it's not already in the dataframe.
        if f"target_population_columns_{self.code}" not in df.columns:
            df[f"target_population_columns_{self.code}"] = None

        df[f"target_population_columns_{self.code}"] = df[
            f"target_population_columns_{self.code}"
        ].apply(lambda x: x if x is not None else self.default_pop_col)

        # Get all columns from target_population_columns
        target_population_columns = list(
            dict.fromkeys(
                itertools.chain.from_iterable(
                    df[f"target_population_columns_{self.code}"]
                )
            )
        )

        if not all(
            col in target_population.columns
            for col in self.join_keys + list(target_population_columns)
        ):
            raise ValueError(
                f"Target population DataFrame must contain columns: {self.join_keys + list(target_population_columns)}"
            )

        # Step 1: Filter target_population to only keep relevant columns for the merge
        target_population_filtered = target_population[
            self.join_keys + list(target_population_columns)
        ]

        # Step 2: Merge on the code column
        df = pd.merge(
            df,
            target_population_filtered,
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

    def _get_sum_target_population_(self, base_df):
        return base_df.apply(
            lambda row: sum(
                row[pop_col]
                for pop_col in row[f"target_population_columns_{self.code}"]
            ),
            axis=1,
        )

    def _get_target_population_df_(self, base_df):
        return base_df.apply(
            lambda row: row[row[f"target_population_columns_{self.code}"]],
            axis=1,
        )
