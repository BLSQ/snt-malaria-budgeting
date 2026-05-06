import pandas as pd
from typing import Dict

from snt_malaria_budgeting.core.quantification_functions.smc import (
    SMC3Quantification,
    SMC4Quantification,
    SMC5Quantification,
)
from snt_malaria_budgeting.models import UnknownInterventionHandling

from .quantification_functions import (
    ItnCampaignQuantification,
    ItnSchoolQuantification,
    ItnRoutineQuantification,
    IPTPQuantification,
    PMCQuantification,
    SMCQuantification,
    VaccQuantification,
    DefaultQuantification,
)

INTERVENTION_QUANTIFICATION_CLASSES = {
    "code_itn_campaign": ItnCampaignQuantification,
    "code_itn_school": ItnSchoolQuantification,
    "code_itn_routine": ItnRoutineQuantification,
    "code_iptp": IPTPQuantification,
    "code_smc": SMCQuantification,
    "code_smc_3": SMC3Quantification,
    "code_smc_4": SMC4Quantification,
    "code_smc_5": SMC5Quantification,
    "code_pmc": PMCQuantification,
    "code_vacc": VaccQuantification,
}


def generate_budget(
    scen_df: pd.DataFrame,
    cost_df: pd.DataFrame,
    target_population: pd.DataFrame,
    assumptions: Dict[str, float],
    spatial_planning_unit: str,
    local_currency_symbol: str = "NGN",
    unknown_intervention_handling: UnknownInterventionHandling = UnknownInterventionHandling.IGNORE,
) -> pd.DataFrame:
    """
    Generates a detailed intervention budget from scenarios & costs.

    This function is a Python port of the R script detailed in the Partner
    Integration Guide, validated with sample data files.
    It quantifies commodity/service needs, applies unit costs, and returns a
    long-form budget dataset.

    Args:
        scen_df: DataFrame of implementation scenarios, from the 'Scenario template'.
        cost_df: DataFrame of unit costs, from the 'Unit Cost template'.
        target_population: DataFrame with population data by SPU and year.
        assumptions: Dictionary of overrides for default parameters.
        spatial_planning_unit:
            The identifier of the spatial planning unit, i.e. the join key to match
            the scen_df on the target_population dataframes.
            This can be a database ID, DHIS reference, combination of adm1 and adm2, etc.
        local_currency_symbol: Symbol for the local currency (e.g., "NGN").

    Returns:
        A long-format DataFrame containing the detailed budget.
    """

    # --- Cost Data Prep (Partner Guide: 4.1) ---
    cost_df_clean = cost_df.dropna(subset=["local_currency_cost"]).copy()
    cost_df_clean["cost_year_for_analysis"] = pd.to_numeric(
        cost_df_clean["cost_year_for_analysis"], errors="coerce"
    )

    unique_years = scen_df[["year"]].drop_duplicates()
    cost_df_expanded = pd.merge(unique_years, cost_df_clean, how="cross")

    cost_df_expanded["cost_year_for_analysis"] = cost_df_expanded[
        "cost_year_for_analysis"
    ].fillna(cost_df_expanded["year"])
    cost_df_expanded = cost_df_expanded[
        cost_df_expanded["cost_year_for_analysis"] == cost_df_expanded["year"]
    ]

    all_quantifications = []

    # --- Quantification by Intervention (Partner Guide: 4.3) ---
    for (
        code_column,
        quantification_class,
    ) in INTERVENTION_QUANTIFICATION_CLASSES.items():
        if code_column in scen_df.columns:
            quantification = quantification_class(
                spatial_unit=spatial_planning_unit, assumptions=assumptions
            ).get_quantification(
                scen_df,
                target_population,
            )
            all_quantifications.append(quantification)

    unknown_code_columns = [
        col.removeprefix("code_")
        for col in scen_df.columns
        if col.startswith("code_") and col not in INTERVENTION_QUANTIFICATION_CLASSES
    ]

    if (
        unknown_code_columns
        and unknown_intervention_handling == UnknownInterventionHandling.ERROR
    ):
        raise ValueError(
            f"Unknown intervention code columns found in scen_df: {unknown_code_columns}. "
            "Please add quantification logic for these interventions or adjust the unknown_intervention_handling parameter."
        )

    if (
        unknown_code_columns
        and unknown_intervention_handling == UnknownInterventionHandling.HANDLE
    ):
        print(
            f"Warning: Unknown intervention code columns found in scen_df: {unknown_code_columns}. "
            "Using default quantification for these interventions."
        )

        for col in unknown_code_columns:
            quantification = DefaultQuantification(
                code=col, spatial_unit=spatial_planning_unit, assumptions=assumptions
            ).get_quantification(
                scen_df,
                target_population,
            )
            all_quantifications.append(quantification)

    # --- Intervention Costing & Final Assembly (Partner Guide: 4.4, 4.5, 4.6) ---
    if not all_quantifications:
        return pd.DataFrame()

    budget = pd.concat(all_quantifications, ignore_index=True, sort=False)

    if budget.empty or cost_df_expanded.empty:
        return pd.DataFrame()

    budget = pd.merge(
        budget,
        cost_df_expanded.drop(columns=["year"]),
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

    fixed_budget = cost_df_expanded[
        cost_df_expanded["type_intervention"] == "Fixed cost"
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
        "itn_school": "School ITN",
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
