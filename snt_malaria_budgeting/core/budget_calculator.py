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
        interventions_costs = []
        # Create a dict summarizing the total costs per intervention _type_
        for intervention_type, code in self.intervention_types_and_codes:
            costs = []
            cost_classes = budget["cost_class"].unique()
            total_cost = 0
            total_pop = self._get_total_population(
                budget, code, intervention_type, self.budget_currency
            )
            for cost_class in cost_classes:
                cost = self._get_cost(
                    budget, code, intervention_type, self.budget_currency, cost_class
                )
                if cost > 0:
                    costs.append(
                        {
                            "cost_class": cost_class,
                            "cost": cost,
                        }
                    )
                total_cost += cost

            interventions_costs.append(
                {
                    "type": intervention_type,
                    "code": code,
                    "total_cost": total_cost,
                    "total_pop": total_pop,
                    "cost_breakdown": costs,
                }
            )
        return interventions_costs

    def get_places_costs(self, year):
        budget = self.calculate_budget(year)

        place_costs = []
        for place in self.places:
            place_budget = budget[budget[self.spatial_planning_unit] == place]

            total_place_cost = place_budget[
                (place_budget["currency"] == self.budget_currency.upper())
            ]["cost_element"].sum()

            place_interventions = []
            for intervention_type, code in self.intervention_types_and_codes:
                intervention_cost = place_budget[
                    (place_budget["type_intervention"] == intervention_type)
                    & (place_budget["currency"] == self.budget_currency.upper())
                ]["cost_element"].sum()
                if intervention_cost > 0:
                    place_interventions.append(
                        {
                            "type": intervention_type,
                            "code": code,
                            "total_cost": intervention_cost,
                        }
                    )

            place_costs.append(
                {
                    "place": place,
                    "total_cost": total_place_cost,
                    "interventions": place_interventions,
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
        #################################################################################
        for budget_code in INTERVENTION_BUDGET_CODES:
            interventions = [
                intervention
                for intervention in self.interventions_input
                if intervention.code == budget_code
            ]

            for intervention in interventions:
                intervention_places = intervention.places
                intervention_type = intervention.type
                code_column = f"code_{budget_code}"
                type_column = f"type_{budget_code}"
                # Update the intervention code column in scen_data DataFrame
                scen_data[code_column] = scen_data.apply(
                    lambda row: 1
                    if row[self.spatial_planning_unit] in intervention_places
                    else row[code_column]
                    if code_column in row and pd.notnull(row[code_column])
                    else None,
                    axis=1,
                )
                # Update the intervention type column in scen_data DataFrame
                scen_data[type_column] = scen_data.apply(
                    lambda row: intervention_type
                    if row[self.spatial_planning_unit] in intervention_places
                    else row[type_column]
                    if type_column in row and pd.notnull(row[type_column])
                    else None,
                    axis=1,
                )
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

    def _get_cost(
        self, budget, intervention_code, intervention_type, currency, cost_class
    ):
        """
        Helper function to get the total cost for a specific intervention, currency, cost class.
        """

        cost = budget[
            (budget["type_intervention"] == intervention_type)
            & (budget["code_intervention"] == intervention_code)
            & (budget["currency"] == currency.upper())
            & (budget["cost_class"] == cost_class)
        ]["cost_element"].sum()

        return cost

    def _get_total_population(
        self, budget, intervention_code, intervention_type, currency
    ):
        total_pop = (
            budget[
                (budget["code_intervention"] == intervention_code)
                & (budget["type_intervention"] == intervention_type)
                & (budget["currency"] == currency.upper())
            ]
            .drop_duplicates(subset=[self.spatial_planning_unit])["target_pop"]
            .sum()
        )
        return total_pop


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
        #################################################################################
        for budget_code in INTERVENTION_BUDGET_CODES:
            interventions = [
                intervention
                for intervention in interventions_input
                if intervention.code == budget_code
            ]

            for intervention in interventions:
                intervention_places = intervention.places
                intervention_type = intervention.type
                code_column = f"code_{budget_code}"
                type_column = f"type_{budget_code}"
                # Update the intervention code column in scen_data DataFrame
                scen_data[code_column] = scen_data.apply(
                    lambda row: 1
                    if row[spatial_planning_unit] in intervention_places
                    else row[code_column]
                    if code_column in row and pd.notnull(row[code_column])
                    else None,
                    axis=1,
                )
                # Update the intervention type column in scen_data DataFrame
                scen_data[type_column] = scen_data.apply(
                    lambda row: intervention_type
                    if row[spatial_planning_unit] in intervention_places
                    else row[type_column]
                    if type_column in row and pd.notnull(row[type_column])
                    else None,
                    axis=1,
                )

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

        def get_cost_class_data(intervention_type, currency, year, cost_class):
            """
            Helper function to get the total cost for a specific intervention, currency, year and cost class.
            """
            cost = budget[
                (budget["type_intervention"] == intervention_type)
                & (budget["currency"] == currency.upper())
                & (budget["year"] == year)
                & (budget["cost_class"] == cost_class)
            ]["cost_element"].sum()
            pop = budget[
                (budget["type_intervention"] == intervention_type)
                & (budget["currency"] == currency.upper())
                & (budget["year"] == year)
                & (budget["cost_class"] == cost_class)
            ]["target_pop"].sum()

            return {"cost": cost, "pop": pop}

        intervention_costs = {
            "year": year,
            "interventions": [],
        }

        intervention_types_and_codes = [[i.type, i.code] for i in interventions_input]

        # Create a dict summarizing the total costs per intervention _type_
        for intervention_type, code in intervention_types_and_codes:
            costs = []
            cost_classes = budget["cost_class"].unique()
            total_cost = 0
            total_pop = 0
            for cost_class in cost_classes:
                cost_class_data = get_cost_class_data(
                    intervention_type, budget_currency, year, cost_class
                )
                if cost_class_data["cost"] > 0:
                    costs.append(
                        {
                            "cost_class": cost_class,
                            "cost": cost_class_data["cost"],
                        }
                    )
                total_cost += cost_class_data["cost"]
                total_pop += cost_class_data["pop"]

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
