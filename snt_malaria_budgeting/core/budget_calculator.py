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
