from typing import Dict, List, Any, Optional
import pandas as pd
from ..models import InterventionDetailModel, CostItems
from .PATH_generate_budget import generate_budget


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

    if budget_currency is None:
        budget_currency = local_currency

    try:
        places = population_df[spatial_planning_unit].drop_duplicates().values.tolist()

        ######################################
        # convert from json input to dataframe
        ######################################
        scen_data = pd.DataFrame(places, columns=[spatial_planning_unit])
        scen_data["year"] = year  # Set a default year for the scenario

        def set_intervention_code(intervention_name, column_name):
            #################################################################################
            # for setting intervention code and type base on intervention's places from input
            #################################################################################
            interventions = [
                intervention
                for intervention in interventions_input
                if intervention.name == intervention_name
            ]
            # to handle the case where no interventions are provided
            if len(interventions) == 0:
                scen_data[column_name] = None
                scen_data[column_name.replace("code", "type")] = None
                return

            for intervention in interventions:
                intervention_places = intervention.places
                intervention_type = intervention.type
                code_column = column_name
                type_column = column_name.replace("code", "type")
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

        # for CM
        set_intervention_code("cm", "code_cm_public")

        # for Iptp
        set_intervention_code("iptp", "code_iptp")

        # for SMC
        set_intervention_code("smc", "code_smc")

        # for PMC
        set_intervention_code("pmc", "code_pmc")

        # for Vaccination
        set_intervention_code("vacc", "code_vacc")

        # for IRS
        set_intervention_code("irsx1", "code_irs")

        # for LSM
        scen_data["code_lsm"] = 1  # Assuming a type for LSM
        scen_data["type_lsm"] = "Bti"

        # for ITN Routine
        set_intervention_code("itn_routine", "code_itn_routine")

        # for ITN Campaign
        set_intervention_code("itn_campaign", "code_itn_campaign")

        # for ITN Urban
        scen_data["code_itn_urban"] = 0

        # for CM private
        scen_data["code_cm_private"] = 1

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

        def get_cost_class_data(code, currency, year, cost_class):
            """
            Helper function to get the total cost for a specific intervention, currency, year and cost class.
            """
            cost = budget[
                (budget["code_intervention"] == code)
                & (budget["currency"] == currency.upper())
                & (budget["year"] == year)
                & (budget["cost_class"] == cost_class)
            ]["cost_element"].sum()
            pop = budget[
                (budget["code_intervention"] == code)
                & (budget["currency"] == currency.upper())
                & (budget["year"] == year)
                & (budget["cost_class"] == cost_class)
            ]["target_pop"].sum()

            return {"cost": cost, "pop": pop}

        # Create the budget JSON structure
        # Create a DataFrame summarizing total costs for each intervention
        interventions = [
            "iptp",
            "smc",
            "pmc",
            "vacc",
            "itn_routine",
            "itn_campaign",
        ]

        intervention_costs = {
            "year": year,
            "interventions": [],
        }

        for code, name in zip(interventions, interventions):
            costs = []
            cost_classes = budget["cost_class"].unique()
            total_cost = 0
            total_pop = 0
            for cost_class in cost_classes:
                cost_class_data = get_cost_class_data(
                    code, budget_currency, year, cost_class
                )
                if cost_class_data["cost"] > 0:
                    costs.append(
                        {
                            "name": name,
                            "cost_class": cost_class,
                            "cost": cost_class_data["cost"],
                        }
                    )
                total_cost += cost_class_data["cost"]
                total_pop += cost_class_data["pop"]
            intervention_costs["interventions"].append(
                {
                    "name": name,
                    "total_cost": total_cost,
                    "total_pop": total_pop,
                    "cost_breakdown": costs,
                }
            )

        return intervention_costs
    except Exception as e:
        print(f"Error generating budget: {e}")
        raise e
