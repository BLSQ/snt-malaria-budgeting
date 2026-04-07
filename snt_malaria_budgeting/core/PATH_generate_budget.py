import pandas as pd
from typing import Dict

from .calculation_functions import (
    ItnCampaignQuantification,
    ItnRoutineQuantification,
    IPTPQuantification,
    PMCQuantification,
    SMCQuantification,
    VaccQuantification,
)

INTERVENTION_QUANTIFICATION_CLASSES = {
    "code_itn_campaign": ItnCampaignQuantification,
    "code_itn_routine": ItnRoutineQuantification,
    "code_iptp": IPTPQuantification,
    "code_smc": SMCQuantification,
    "code_pmc": PMCQuantification,
    "code_vacc": VaccQuantification,
}


def generate_budget(
    scen_data: pd.DataFrame,
    cost_data: pd.DataFrame,
    target_population: pd.DataFrame,
    assumptions: Dict[str, float],
    spatial_planning_unit: str,
    local_currency_symbol: str = "NGN",
) -> pd.DataFrame:
    """
    Generates a detailed intervention budget from scenarios & costs.

    This function is a Python port of the R script detailed in the Partner
    Integration Guide, validated with sample data files.
    It quantifies commodity/service needs, applies unit costs, and returns a
    long-form budget dataset.

    Args:
        scen_data: DataFrame of implementation scenarios, from the 'Scenario template'.
        cost_data: DataFrame of unit costs, from the 'Unit Cost template'.
        target_population: DataFrame with population data by SPU and year.
        assumptions: Dictionary of overrides for default parameters.
        spatial_planning_unit:
            The identifier of the spatial planning unit, i.e. the join key to match
            the scen_data on the target_population dataframes.
            This can be a database ID, DHIS reference, combination of adm1 and adm2, etc.
        local_currency_symbol: Symbol for the local currency (e.g., "NGN").

    Returns:
        A long-format DataFrame containing the detailed budget.
    """

    # --- Cost Data Prep (Partner Guide: 4.1) ---
    cost_data_clean = cost_data.dropna(subset=["local_currency_cost"]).copy()
    cost_data_clean["cost_year_for_analysis"] = pd.to_numeric(
        cost_data_clean["cost_year_for_analysis"], errors="coerce"
    )

    unique_years = scen_data[["year"]].drop_duplicates()
    cost_data_expanded = pd.merge(unique_years, cost_data_clean, how="cross")

    cost_data_expanded["cost_year_for_analysis"] = cost_data_expanded[
        "cost_year_for_analysis"
    ].fillna(cost_data_expanded["year"])
    cost_data_expanded = cost_data_expanded[
        cost_data_expanded["cost_year_for_analysis"] == cost_data_expanded["year"]
    ]

    all_quantifications = []

    # --- Quantification by Intervention (Partner Guide: 4.3) ---
    for (
        code_column,
        quantification_class,
    ) in INTERVENTION_QUANTIFICATION_CLASSES.items():
        if code_column in scen_data.columns:
            quantification = quantification_class(
                spacial_unit=spatial_planning_unit, assumptions=assumptions
            ).get_quantification(
                scen_data,
                target_population,
            )
            all_quantifications.append(quantification)

    # --- Intervention Costing & Final Assembly (Partner Guide: 4.4, 4.5, 4.6) ---
    if not all_quantifications:
        return pd.DataFrame()

    budget = pd.concat(all_quantifications, ignore_index=True, sort=False)

    budget = pd.merge(
        budget,
        cost_data_expanded.drop(columns=["year"]),
        left_on=["code_intervention", "type_intervention", "unit", "year"],
        right_on=[
            "code_intervention",
            "type_intervention",
            "unit",
            "cost_year_for_analysis",
        ],
        how="left",
    )

    budget = budget.melt(
        id_vars=[
            c for c in budget.columns if c not in ["local_currency_cost", "usd_cost"]
        ],
        value_vars=["local_currency_cost", "usd_cost"],
        var_name="currency",
        value_name="unit_cost",
    )

    budget["cost_element"] = budget["quantity"] * budget["unit_cost"]
    budget["currency"] = budget["currency"].map(
        {"local_currency_cost": local_currency_symbol, "usd_cost": "USD"}
    )

    fixed_budget = cost_data_expanded[
        cost_data_expanded["type_intervention"] == "Fixed cost"
    ].copy()
    if not fixed_budget.empty:
        fixed_budget = fixed_budget.melt(
            id_vars=[c for c in fixed_budget.columns if not c.endswith("_cost")],
            value_vars=["local_currency_cost", "usd_cost"],
            var_name="currency",
            value_name="unit_cost",
        )
        fixed_budget = fixed_budget.assign(
            currency=lambda x: x["currency"].map(
                {"local_currency_cost": local_currency_symbol, "usd_cost": "USD"}
            ),
            quantity=1,
            cost_element=lambda x: x["unit_cost"] * x["quantity"],
        )
        budget = pd.concat([budget, fixed_budget], ignore_index=True, sort=False)

    intervention_map = {
        "iptp": "IPTp",
        "vacc": "Vaccine",
        "itn_routine": "Routine ITN",
        "itn_campaign": "Campaign ITN",
        "smc": "SMC",
        "pmc": "PMC",
        "irs": "IRS",
        "lsm": "LSM",
    }

    budget["intervention_nice"] = (
        budget["code_intervention"]
        .map(intervention_map)
        .fillna(budget["code_intervention"])
    )
    budget = budget[budget["cost_element"].notna() & (budget["cost_element"] != 0)]

    assumption_summary = (
        "; ".join([f"{k} = {v}" for k, v in assumptions.items()])
        if assumptions
        else "default values"
    )
    budget = budget.assign(
        assumptions_changes=assumption_summary,
        assumption_type=(
            "adjusted assumptions" if assumptions else "baseline assumptions"
        ),
    )

    final_cols = [
        spatial_planning_unit,
        "year",
        "code_intervention",
        "type_intervention",
        "target_pop",
        "unit",
        "quantity",
        "cost_class",
        "currency",
        "unit_cost",
        "cost_element",
        "intervention_nice",
        "assumptions_changes",
        "assumption_type",
    ]
    return budget.reindex(columns=final_cols)
