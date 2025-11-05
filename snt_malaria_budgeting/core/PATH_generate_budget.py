import pandas as pd
from typing import Dict, List


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
    # --- Environment & Inputs (Partner Guide: 4.1) ---
    join_keys = [spatial_planning_unit] + ["year"]

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

    def get_pop_column(label: str, default_col: List[str]) -> List[str]:
        pop_assumption = assumptions.get(label)
        if not pop_assumption:
            return default_col
        mapping = {
            "Total population": ["pop_total"],
            "Children under 5": ["pop_0_5"],
            "Children under 5 and pregnant women": ["pop_0_5", "pop_pw"],
            "Children under 10": ["pop_0_5", "pop_5_10"],
            "Children 0-1": ["pop_0_1"],
            "Children 1-2": ["pop_1_2"],
            "Pregnant women": ["pop_pw"],
        }
        return mapping.get(str(pop_assumption), default_col)

    itn_campaign_pop_col = get_pop_column(
        "ITN Campaign: target population", ["pop_total"]
    )
    itn_routine_pop_col = get_pop_column(
        "ITN Routine: target population", ["pop_0_5", "pop_pw"]
    )
    smc_pop_col = get_pop_column("SMC: target population", ["pop_0_5"])

    all_quantifications = []

    # --- Quantification by Intervention (Partner Guide: 4.3) ---

    # 4.3.1 ITN — Campaign
    if "code_itn_campaign" in scen_data.columns:
        df = scen_data[scen_data["code_itn_campaign"] == 1].copy()
        if not df.empty:
            df = pd.merge(
                df,
                target_population[list(set(join_keys + itn_campaign_pop_col))],
                on=join_keys,
            )
            df["target_pop_raw"] = df[itn_campaign_pop_col].sum(axis=1)
            df = df.assign(
                quant_nets=(
                    (df["target_pop_raw"] * assumptions["itn_campaign_coverage"])
                    / assumptions["itn_campaign_divisor"]
                )
                * assumptions["itn_campaign_buffer_mult"],
                target_pop=df["target_pop_raw"] * assumptions["itn_campaign_coverage"],
                code_intervention="itn_campaign",
                type_intervention=df["type_itn_campaign"],
            ).assign(
                quant_bales=lambda x: x.quant_nets
                / assumptions["itn_campaign_bale_size"]
            )
            df_long = df.melt(
                id_vars=[c for c in df.columns if not c.startswith("quant_")],
                value_vars=["quant_nets", "quant_bales"],
                var_name="unit",
                value_name="quantity",
            )
            df_long["unit"] = df_long["unit"].map(
                {"quant_nets": "per ITN", "quant_bales": "per bale"}
            )
            all_quantifications.append(df_long)

    # 4.3.2 ITN — Routine
    if "code_itn_routine" in scen_data.columns:
        df = scen_data[scen_data["code_itn_routine"] == 1].copy()
        if not df.empty:
            df = pd.merge(
                df,
                target_population[list(set(join_keys + itn_routine_pop_col))],
                on=join_keys,
            )
            df["target_pop"] = df[itn_routine_pop_col].sum(axis=1)
            df = df.assign(
                quantity=(df["target_pop"] * assumptions["itn_routine_coverage"])
                * assumptions["itn_routine_buffer_mult"],
                code_intervention="itn_routine",
                type_intervention=df["type_itn_routine"],
                unit="per ITN",
            )
            all_quantifications.append(df)

    # 4.3.3 IPTp
    if "code_iptp" in scen_data.columns:
        df = scen_data[scen_data["code_iptp"] == 1].copy()
        if not df.empty:
            df = pd.merge(df, target_population[join_keys + ["pop_pw"]], on=join_keys)
            df = df.assign(
                quantity=(
                    (df["pop_pw"] * assumptions["iptp_anc_coverage"])
                    * assumptions["iptp_doses_per_pw"]
                )
                * assumptions["iptp_buffer_mult"],
                target_pop=df["pop_pw"],
                code_intervention="iptp",
                type_intervention=df["type_iptp"],
                unit="per SP",
            )
            all_quantifications.append(df)

    # 4.3.4 SMC
    if "code_smc" in scen_data.columns:
        df = scen_data[scen_data["code_smc"] == 1].copy()
        if not df.empty:
            df = pd.merge(
                df, target_population[list(set(join_keys + smc_pop_col))], on=join_keys
            )
            df = df.assign(
                quant_smc_3_11_months=(
                    (df["pop_0_5"] * assumptions["smc_pop_prop_3_11"])
                    * assumptions["smc_coverage"]
                )
                * assumptions["smc_monthly_rounds"]
                * assumptions["smc_buffer_mult"],
                quant_smc_12_59_months=(
                    (df["pop_0_5"] * assumptions["smc_pop_prop_12_59"])
                    * assumptions["smc_coverage"]
                )
                * assumptions["smc_monthly_rounds"]
                * assumptions["smc_buffer_mult"],
                target_pop=(
                    df["pop_0_5"]
                    * (
                        assumptions["smc_pop_prop_3_11"]
                        + assumptions["smc_pop_prop_12_59"]
                    )
                )
                * assumptions["smc_coverage"],
                code_intervention="smc",
                type_intervention=df["type_smc"],
            )
            df_long = df.melt(
                id_vars=[c for c in df.columns if not c.startswith("quant_")],
                value_vars=["quant_smc_3_11_months", "quant_smc_12_59_months"],
                var_name="unit",
                value_name="quantity",
            )
            unit_map = {
                "quant_smc_3_11_months": "per SPAQ pack 3-11 month olds",
                "quant_smc_12_59_months": "per SPAQ pack 12-59 month olds",
            }
            df_long["unit"] = df_long["unit"].map(unit_map)
            all_quantifications.append(df_long)

    # 4.3.5 PMC
    if "code_pmc" in scen_data.columns:
        df = scen_data[scen_data["code_pmc"] == 1].copy()
        if not df.empty:
            df = pd.merge(
                df, target_population[join_keys + ["pop_0_1", "pop_1_2"]], on=join_keys
            )
            sp_0_1 = (
                df["pop_0_1"]
                * assumptions["pmc_coverage"]
                * assumptions["pmc_touchpoints"]
                * 1
                * assumptions["pmc_tablet_factor"]
                * assumptions["pmc_buffer_mult"]
            )
            sp_1_2 = (
                df["pop_1_2"]
                * assumptions["pmc_coverage"]
                * assumptions["pmc_touchpoints"]
                * 2
                * assumptions["pmc_tablet_factor"]
                * assumptions["pmc_buffer_mult"]
            )
            df = df.assign(
                quantity=sp_0_1 + sp_1_2,
                target_pop=df["pop_0_1"] * assumptions["pmc_coverage"]
                + df["pop_1_2"] * assumptions["pmc_coverage"],
                code_intervention="pmc",
                type_intervention=df["type_pmc"],
                unit="per SP",
            )
            all_quantifications.append(df)

    # 4.3.6 Vaccine
    if "code_vacc" in scen_data.columns:
        df = scen_data[scen_data["code_vacc"] == 1].copy()
        if not df.empty:
            df = pd.merge(
                df,
                target_population[join_keys + ["pop_vaccine_5_36_months"]],
                on=join_keys,
            )
            df = df.assign(
                quant_doses=df["pop_vaccine_5_36_months"]
                * assumptions["vacc_coverage"]
                * assumptions["vacc_doses_per_child"]
                * assumptions["vacc_buffer_mult"],
                quant_child=df["pop_vaccine_5_36_months"]
                * assumptions["vacc_coverage"],
            ).assign(
                target_pop=lambda x: x.quant_child,
                code_intervention="vacc",
                type_intervention=df["type_vacc"],
            )
            df_long = df.melt(
                id_vars=[c for c in df.columns if not c.startswith("quant_")],
                value_vars=["quant_doses", "quant_child"],
                var_name="unit",
                value_name="quantity",
            )
            df_long["unit"] = df_long["unit"].map(
                {"quant_doses": "per dose", "quant_child": "per child"}
            )
            all_quantifications.append(df_long)

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
