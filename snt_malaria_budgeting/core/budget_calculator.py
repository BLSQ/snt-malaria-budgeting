from typing import Dict, List, Any, Optional

import pandas as pd
from ..models import InterventionDetailModel, CostItems
from .PATH_generate_budget import generate_budget

INTERVENTION_BUDGET_CODES = (
    "itn_campaign",
    "itn_routine",
    "iptp",
    "smc",
    "pmc",
    "vacc",
    # Coming soon:
    # "irs",
    # "lsm",
)


class BudgetCalculator:
    def __init__(
        self,
        interventions_input: List[InterventionDetailModel],
        settings: Dict[str, Any],
        cost_df: pd.DataFrame,
        population_df: pd.DataFrame,
        local_currency: str,
        spatial_planning_unit: str,
        budget_currency: str = "",
        cost_overrides: Optional[List[CostItems]] = None,
    ):
        self.interventions_input = interventions_input
        self.settings = settings
        self.cost_df = cost_df
        self.population_df = population_df
        self.local_currency = local_currency
        self.spatial_planning_unit = spatial_planning_unit
        self.budget_currency = budget_currency if budget_currency else local_currency
        self.cost_overrides = cost_overrides if cost_overrides is not None else []
        self.places = (
            population_df[spatial_planning_unit].drop_duplicates().values.tolist()
        )

        self.intervention_types_and_codes = [
            [i.type, i.code] for i in self.interventions_input
        ]

        self.budgets = {}

    def calculate_budget(self, year):
        if year in self.budgets:
            return self.budgets.get(year)

        scen_data = self._get_scenario_data(year)
        self._merge_cost_overrides()
        self._normalize_cost_dataframe()
        costs_for_year = self.cost_df[self.cost_df["cost_year_for_analysis"] == year]
        pop_for_year = self.population_df[self.population_df["year"] == year]
        budget = generate_budget(
            scen_data=scen_data,
            cost_data=costs_for_year,
            target_population=pop_for_year,
            assumptions=self.settings,
            spatial_planning_unit=self.spatial_planning_unit,
            local_currency_symbol=self.local_currency.upper(),
        )

        self.budgets[year] = budget

        return budget

    def get_interventions_costs(self, year):
        budget = self.calculate_budget(year)
        # Filter budget for desired currency (it has two currencies: local and USD)
        budget_filtered = budget[budget["currency"] == self.budget_currency.upper()]

        # Get cost classes once
        cost_classes = budget_filtered["cost_class"].unique()

        # Get total costs per intervention and cost_class
        costs_grouped = budget_filtered.groupby(
            ["type_intervention", "code_intervention", "cost_class"]
        )["cost_element"].sum()

        # Group by intervention type and code to get populations
        # Drop duplicates per spatial unit before summing target_pop
        pop_grouped = (
            budget_filtered.drop_duplicates(
                subset=[
                    "type_intervention",
                    "code_intervention",
                    self.spatial_planning_unit,
                ]
            )
            .groupby(["type_intervention", "code_intervention"])["target_pop"]
            .sum()
        )

        interventions_costs = []
        # Create a dict summarizing the total costs per intervention _type_
        for intervention_type, code in self.intervention_types_and_codes:
            costs = []
            total_cost = 0

            for cost_class in cost_classes:
                cost = costs_grouped.get((intervention_type, code, cost_class), 0)
                if cost > 0:
                    costs.append({"cost_class": cost_class, "cost": cost})
                    total_cost += cost

            interventions_costs.append(
                {
                    "type": intervention_type,
                    "code": code,
                    "total_cost": total_cost,
                    "total_pop": pop_grouped.get((intervention_type, code), 0),
                    "cost_breakdown": costs,
                }
            )
        return interventions_costs

    def get_places_costs(self, year):
        budget = self.calculate_budget(year)
        # Filter budget for desired currency (it has two currencies: local and USD)
        budget_filtered_by_currency = budget[
            budget["currency"] == self.budget_currency.upper()
        ]

        # Group to have cost per place and intervention type and code
        grouped_per_place_and_intervention = (
            budget_filtered_by_currency.groupby(
                [self.spatial_planning_unit, "type_intervention", "code_intervention"]
            )
            .sum()
            .reset_index()
        )

        # get total costs per place
        place_totals = budget_filtered_by_currency.groupby(self.spatial_planning_unit)[
            "cost_element"
        ].sum()

        place_costs = []
        for place in self.places:
            place_interventions = grouped_per_place_and_intervention[
                grouped_per_place_and_intervention[self.spatial_planning_unit] == place
            ]

            interventions_list = []

            for _, row in place_interventions.iterrows():
                if row["cost_element"] > 0:
                    interventions_list.append(
                        {
                            "type": row["type_intervention"],
                            "code": row["code_intervention"],
                            "total_cost": row["cost_element"],
                        }
                    )
            place_costs.append(
                {
                    "place": place,
                    "total_cost": place_totals.get(place, 0),
                    "interventions": interventions_list,
                }
            )
        return place_costs

    def _get_scenario_data(
        self,
        year: int,
    ):
        ######################################
        # Convert from json input to dataframe
        ######################################
        scen_data = pd.DataFrame(self.places, columns=[self.spatial_planning_unit])
        scen_data["year"] = year  # Set a default year for the scenario

        #################################################################################
        # Set intervention code and type base on intervention's places from input for all
        # available intervention categories.
        # Using vectorized operations for performance
        #################################################################################
        # Pre-group interventions by code to avoid repeated filtering
        interventions_by_code = {}
        for intervention in self.interventions_input:
            if intervention.code not in interventions_by_code:
                interventions_by_code[intervention.code] = []
            interventions_by_code[intervention.code].append(intervention)

        for budget_code in INTERVENTION_BUDGET_CODES:
            interventions = interventions_by_code.get(budget_code, [])

            code_column = f"code_{budget_code}"
            type_column = f"type_{budget_code}"

            for intervention in interventions:
                intervention_places = intervention.places
                intervention_type = intervention.type

                # Use vectorized operations instead of apply()
                mask = scen_data[self.spatial_planning_unit].isin(intervention_places)
                scen_data.loc[mask, code_column] = 1
                scen_data.loc[mask, type_column] = intervention_type

        return scen_data

    def _merge_cost_overrides(
        self,
    ) -> pd.DataFrame:
        input_costs_dict = [cost.dict() for cost in self.cost_overrides]
        if len(input_costs_dict) > 0:
            validation = self.cost_df.merge(
                pd.DataFrame(input_costs_dict),
                on=["code_intervention", "type_intervention", "cost_class", "unit"],
                how="inner",
                suffixes=("", "_y"),
            )

            if len(validation) != len(input_costs_dict):
                raise ValueError("Cost data override validation failed.")

            self.cost_df = self.cost_df.merge(
                pd.DataFrame(input_costs_dict),
                on=["code_intervention", "type_intervention", "cost_class", "unit"],
                how="left",
                suffixes=("", "_y"),
            )
            self.cost_df["usd_cost"] = self.cost_df["usd_cost_y"].combine_first(
                self.cost_df["usd_cost"]
            )
        return self.cost_df

    def _normalize_cost_dataframe(self) -> pd.DataFrame:
        # Normalize cost_df columns as required by generate_budget
        if (
            "local_currency_cost" not in self.cost_df.columns
            and f"{self.local_currency.lower()}_cost" in self.cost_df.columns
        ):
            self.cost_df["local_currency_cost"] = self.cost_df[
                f"{self.local_currency.lower()}_cost"
            ]
        if (
            "cost_year_for_analysis" not in self.cost_df.columns
            and "cost_year" in self.cost_df.columns
        ):
            self.cost_df["cost_year_for_analysis"] = self.cost_df["cost_year"]
        return self.cost_df


def get_budget(
    year: int,
    interventions_input: List[InterventionDetailModel],
    settings: Dict[str, Any],
    cost_df: pd.DataFrame,
    population_df: pd.DataFrame,
    local_currency: str,
    spatial_planning_unit: str,
    budget_currency: str = "",
    cost_overrides: Optional[List[CostItems]] = None,
) -> Dict[str, Any]:
    if cost_overrides is None:
        cost_overrides = []

    if not budget_currency:
        budget_currency = local_currency

    try:
        places = population_df[spatial_planning_unit].drop_duplicates().values.tolist()

        ######################################
        # Convert from json input to dataframe
        ######################################
        scen_data = pd.DataFrame(places, columns=[spatial_planning_unit])
        scen_data["year"] = year  # Set a default year for the scenario

        #################################################################################
        # Set intervention code and type base on intervention's places from input for all
        # available intervention categories.
        # Using vectorized operations for performance.
        #################################################################################
        interventions_by_code = {}
        for intervention in interventions_input:
            if intervention.code not in interventions_by_code:
                interventions_by_code[intervention.code] = []
            interventions_by_code[intervention.code].append(intervention)

        for budget_code in INTERVENTION_BUDGET_CODES:
            interventions = interventions_by_code.get(budget_code, [])

            for intervention in interventions:
                mask = scen_data[spatial_planning_unit].isin(intervention.places)
                scen_data.loc[mask, f"code_{budget_code}"] = 1
                scen_data.loc[mask, f"type_{budget_code}"] = intervention.type

        ######################################
        # merge cost_df with cost_overrides
        ######################################
        input_costs_dict = [cost.dict() for cost in cost_overrides]

        if input_costs_dict.__len__() > 0:
            validation = cost_df.merge(
                pd.DataFrame(input_costs_dict),
                on=["code_intervention", "type_intervention", "cost_class", "unit"],
                how="inner",
                suffixes=("", "_y"),
            )

            if validation.__len__() != input_costs_dict.__len__():
                raise ValueError("Cost data override validation failed.")

            cost_df = cost_df.merge(
                pd.DataFrame(input_costs_dict),
                on=["code_intervention", "type_intervention", "cost_class", "unit"],
                how="left",
                suffixes=("", "_y"),
            )
            cost_df["usd_cost"] = cost_df["usd_cost_y"].combine_first(
                cost_df["usd_cost"]
            )

        # Normalize cost_df columns as required by generate_budget
        if (
            "local_currency_cost" not in cost_df.columns
            and f"{local_currency.lower()}_cost" in cost_df.columns
        ):
            cost_df["local_currency_cost"] = cost_df[f"{local_currency.lower()}_cost"]
        if (
            "cost_year_for_analysis" not in cost_df.columns
            and "cost_year" in cost_df.columns
        ):
            cost_df["cost_year_for_analysis"] = cost_df["cost_year"]

        budget = generate_budget(
            scen_data=scen_data,
            cost_data=cost_df,
            target_population=population_df,
            assumptions=settings,
            spatial_planning_unit=spatial_planning_unit,
            local_currency_symbol=local_currency.upper(),
        )

        # Filter budget by currency and year once
        budget_filtered = budget[
            (budget["currency"] == budget_currency.upper()) & (budget["year"] == year)
        ]

        # Group by intervention type and cost class to get all costs in one operation
        costs_grouped = (
            budget_filtered.groupby(["type_intervention", "cost_class"])[
                ["cost_element", "target_pop"]
            ]
            .sum()
            .reset_index()
        )

        intervention_costs = {
            "year": year,
            "interventions": [],
        }

        intervention_types_and_codes = [[i.type, i.code] for i in interventions_input]

        # Create a dict summarizing the total costs per intervention _type_
        for intervention_type, code in intervention_types_and_codes:
            costs = []
            total_cost = 0
            total_pop = 0

            # Filter grouped data for this intervention type
            intervention_data = costs_grouped[
                costs_grouped["type_intervention"] == intervention_type
            ]

            for _, row in intervention_data.iterrows():
                cost_class = row["cost_class"]
                cost = row["cost_element"]
                pop = row["target_pop"]

                if cost > 0:
                    costs.append({"cost_class": cost_class, "cost": cost})
                total_cost += cost
                total_pop += pop

            intervention_costs["interventions"].append(
                {
                    "type": intervention_type,
                    "code": code,
                    "total_cost": total_cost,
                    "total_pop": total_pop,
                    "cost_breakdown": costs,
                }
            )

        return intervention_costs
    except Exception as e:
        print(f"Error generating budget: {e}")
        raise e
