from typing import Dict, List, Any, Optional

import pandas as pd
from ..models import InterventionDetailModel, CostItems, UnknownInterventionHandling
from .PATH_generate_budget import generate_budget


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
        unknown_intervention_handling: UnknownInterventionHandling = UnknownInterventionHandling.IGNORE,
    ):
        self.interventions_input = interventions_input
        self.settings = settings
        self.cost_df = cost_df
        self.population_df = population_df
        self.local_currency = local_currency
        self.spatial_planning_unit = spatial_planning_unit
        self.budget_currency = budget_currency if budget_currency else local_currency
        self.cost_overrides = cost_overrides if cost_overrides is not None else []
        self.unknown_intervention_handling = unknown_intervention_handling
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

        scen_df = self._get_scenario_dataframe(year)
        self._merge_cost_overrides()
        self._normalize_cost_dataframe()
        costs_for_year = self.cost_df[self.cost_df["cost_year_for_analysis"] == year]
        pop_for_year = self.population_df[self.population_df["year"] == year]
        budget = generate_budget(
            scen_df=scen_df,
            cost_df=costs_for_year,
            target_population=pop_for_year,
            assumptions=self.settings,
            spatial_planning_unit=self.spatial_planning_unit,
            local_currency_symbol=self.local_currency.upper(),
            unknown_intervention_handling=self.unknown_intervention_handling,
        )

        self.budgets[year] = budget

        return budget

    def get_interventions_costs(self, year):
        budget = self.calculate_budget(year)
        if budget.empty:
            return []

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
        if budget.empty:
            return []

        budget_filtered_by_currency = budget[
            budget["currency"] == self.budget_currency.upper()
        ]

        # Group to have cost per place, intervention type/code, and cost_class
        grouped_per_place_intervention_class = budget_filtered_by_currency.groupby(
            [
                self.spatial_planning_unit,
                "type_intervention",
                "code_intervention",
                "cost_class",
            ]
        )["cost_element"].sum()

        # get total costs per place
        place_totals = budget_filtered_by_currency.groupby(self.spatial_planning_unit)[
            "cost_element"
        ].sum()

        places_with_data = set(
            grouped_per_place_intervention_class.index.get_level_values(0)
        )

        place_costs = []
        for place in self.places:
            interventions_list = []
            if place in places_with_data:
                place_data = grouped_per_place_intervention_class[place]
                interventions_dict = {}
                for (
                    type_intervention,
                    code_intervention,
                    cost_class,
                ), cost in place_data.items():
                    key = (type_intervention, code_intervention)
                    if key not in interventions_dict:
                        interventions_dict[key] = {
                            "type": type_intervention,
                            "code": code_intervention,
                            "total_cost": 0,
                            "cost_breakdown": [],
                        }
                    if cost > 0:
                        interventions_dict[key]["total_cost"] += cost
                        interventions_dict[key]["cost_breakdown"].append(
                            {"cost_class": cost_class, "cost": cost}
                        )
                interventions_list = [
                    v for v in interventions_dict.values() if v["total_cost"] > 0
                ]

            place_costs.append(
                {
                    "place": place,
                    "total_cost": place_totals.get(place, 0),
                    "interventions": interventions_list,
                }
            )

        return place_costs

    def _set_intervention_scen_data(self, budget_code, interventions, scen_df):
        code_column = f"code_{budget_code}"
        type_column = f"type_{budget_code}"
        intervention_target_population_column = (
            f"target_population_columns_{budget_code}"
        )

        for intervention in interventions:
            intervention_places = intervention.places
            intervention_type = intervention.type

            # Use vectorized operations instead of apply()
            mask = scen_df[self.spatial_planning_unit].isin(intervention_places)
            scen_df.loc[mask, code_column] = 1
            scen_df.loc[mask, type_column] = intervention_type
            scen_df.loc[mask, intervention_target_population_column] = None

            if intervention.target_population_columns:
                scen_df.loc[mask, intervention_target_population_column] = pd.Series(
                    [intervention.target_population_columns] * len(scen_df[mask]),
                    index=scen_df[mask].index,
                )

    def _get_scenario_dataframe(
        self,
        year: int,
    ):
        ######################################
        # Convert from json input to dataframe
        ######################################
        scen_df = pd.DataFrame(self.places, columns=[self.spatial_planning_unit])
        scen_df["year"] = year  # Set a default year for the scenario

        #################################################################################
        # Set intervention code and type base on intervention's places from input for all
        # available intervention categories.
        # Using vectorized operations for performance
        #################################################################################
        # Pre-group interventions by code to avoid repeated filtering
        interventions_by_code = {}
        budget_codes = set()
        for intervention in self.interventions_input:
            code = intervention.code
            if code not in interventions_by_code:
                interventions_by_code[code] = []
                budget_codes.add(code)
            interventions_by_code[code].append(intervention)

        for budget_code in budget_codes:
            interventions = interventions_by_code.get(budget_code, [])
            self._set_intervention_scen_data(budget_code, interventions, scen_df)

        return scen_df

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
