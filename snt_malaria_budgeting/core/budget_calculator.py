import pandas as pd
import numpy as np
from ..models.models import CostSettingItems


def generate_budget(
    scen_data: pd.DataFrame,
    cost_data: pd.DataFrame,
    settings: CostSettingItems,
    target_population: pd.DataFrame,
) -> pd.DataFrame:
    """
    Generates a detailed budget by quantifying needs for various health interventions
    and applying cost data.

    This function translates the R script's logic into Python using pandas. It calculates
    the required quantities for interventions like ITN campaigns, routine immunizations,
    SMC, PMC, etc., based on population data and specific programmatic assumptions.
    It then joins these quantifications with provided cost data to produce a final budget.

    Args:
        scen_data (pd.DataFrame): DataFrame containing scenario information, including
                                  which interventions are active in which administrative
                                  divisions (`adm1`, `adm2`) and year.
        cost_data (pd.DataFrame): DataFrame with cost information for different
                                  intervention components, including unit costs in
                                  multiple currencies.
        settings (CostSettingItems): Settings object containing various programmatic
                                     assumptions and parameters for quantification.
        target_population: pd.DataFrame: DataFrame with population data needed for quantifications.

    Returns:
        pd.DataFrame: A comprehensive budget DataFrame with costs broken down by
                      intervention, location, year, and currency.
    """

    # Print a summary of the interventions, similar to the R version's cat() output
    print("Costing scenario being generated for the following mix of interventions:")
    summary_df = (
        scen_data.melt(
            id_vars=["adm1", "adm2", "year", "scenario_name", "scenario_description"],
            value_vars=[col for col in scen_data.columns if col.startswith("code_")],
            var_name="intervention",
            value_name="included",
        )
        .assign(intervention=lambda df: df["intervention"].str.replace("code_", ""))
        .query("included == 1")
        .groupby(["intervention", "year"])
        .agg(
            states_targeted=("adm1", "nunique"),
            lgas_targeted=("adm2", "nunique"),
        )
        .reset_index()
    )
    print(summary_df.to_string(index=False))

    # --- Generate Quantifications ---

    # --- ITN CAMPAIGNS ---
    # Assumptions: pop / 1.8 nets; 50 nets per bale
    # 1.8 nets per person is a common assumption for ITN campaigns

    if (
        "code_itn_campaign" in scen_data.columns
        and scen_data["code_itn_campaign"].sum() > 0
    ):
        itn_q = scen_data[scen_data["code_itn_campaign"] == 1].merge(
            # target_population, left_on=['adm1', 'adm2', 'year'], right_on=['adm1', 'adm2', 'annee']
            # TODO: commented out year as there is only 2025 population data for now in Nigeria
            target_population,
            left_on=["adm1", "adm2"],
            right_on=["adm1", "adm2"],
            suffixes=("", "_right"),
        )
        itn_q["target_pop"] = itn_q["pop_total"] * settings.itn_campaign_coverage
        itn_q["quant_nets"] = (
            itn_q["target_pop"] / settings.itn_campaign_divisor
        ) * settings.itn_campaign_buffer
        itn_q["quant_bales"] = itn_q["quant_nets"] / settings.itn_campaign_bale_size
        itn_q_long = itn_q.melt(
            id_vars=[
                "adm1",
                "adm2",
                "year",
                "scenario_name",
                "scenario_description",
                "target_pop",
                "type_itn_campaign",
            ],
            value_vars=["quant_nets", "quant_bales"],
            var_name="unit",
            value_name="quantity",
        ).rename(columns={"type_itn_campaign": "type_intervention"})
        itn_q_long["unit"] = itn_q_long["unit"].replace(
            {"quant_nets": "per ITN", "quant_bales": "per bale"}
        )
        itn_q_long["code_intervention"] = "itn_campaign"
    else:
        itn_q_long = pd.DataFrame()

    # --- ITN ROUTINE ---
    if (
        "code_itn_routine" in scen_data.columns
        and scen_data["code_itn_routine"].sum() > 0
    ):
        itn_r_q = scen_data[scen_data["code_itn_routine"] == 1].merge(
            # target_population, left_on=['adm1', 'adm2', 'year'], right_on=['adm1', 'adm2', 'annee']
            # TODO: commented out year as there is only 2025 population data for now in Nigeria
            target_population,
            left_on=["adm1", "adm2"],
            right_on=["adm1", "adm2"],
            suffixes=("", "_right"),
        )
        # itn_r_q['target_pop'] = (itn_r_q['pop_0_5'] + itn_r_q['pop_femme_enceinte']) * settings.itn_routine_coverage
        itn_r_q["target_pop"] = (
            itn_r_q["pop_0_5"] + itn_r_q["pop_pw"]
        ) * settings.itn_routine_coverage
        itn_r_q["quant_nets"] = itn_r_q["target_pop"] * settings.itn_routine_buffer
        itn_r_q_long = itn_r_q.melt(
            id_vars=[
                "adm1",
                "adm2",
                "year",
                "scenario_name",
                "scenario_description",
                "target_pop",
                "type_itn_routine",
            ],
            value_vars=["quant_nets"],
            var_name="unit",
            value_name="quantity",
        ).rename(columns={"type_itn_routine": "type_intervention"})
        itn_r_q_long["unit"] = itn_r_q_long["unit"].replace({"quant_nets": "per ITN"})
        itn_r_q_long["code_intervention"] = "itn_routine"
    else:
        itn_r_q_long = pd.DataFrame()

    # --- IPTp ---
    # Assumptions: 3 doses, 80% ANC attendance, 10% buffer

    if "code_iptp" in scen_data.columns and scen_data["code_iptp"].sum() > 0:
        iptp_q = scen_data[scen_data["code_iptp"] == 1].merge(
            #
            # target_population, left_on=['adm1', 'adm2', 'year'], right_on=['adm1', 'adm2', 'annee']
            target_population,
            left_on=["adm1", "adm2"],
            right_on=["adm1", "adm2"],
            suffixes=("", "_right"),
        )
        # TODO: check difference between pop_pw and pop_femme_enceinte
        # iptp_q['target_pop'] = iptp_q['pop_femme_enceinte'] * settings.iptp_ANC_coverage
        iptp_q["target_pop"] = iptp_q["pop_pw"] * settings.iptp_ANC_coverage
        iptp_q["quant_sp_doses"] = (
            iptp_q["target_pop"] * settings.iptp_doses_per_pw
        ) * settings.iptp_buffer
        iptp_q_long = iptp_q.melt(
            id_vars=[
                "adm1",
                "adm2",
                "year",
                "scenario_name",
                "scenario_description",
                "target_pop",
                "type_iptp",
            ],
            value_vars=["quant_sp_doses"],
            var_name="unit",
            value_name="quantity",
        ).rename(columns={"type_iptp": "type_intervention"})
        iptp_q_long["unit"] = "per SP"
        iptp_q_long["code_intervention"] = "iptp"
    else:
        iptp_q_long = pd.DataFrame()

    # --- SMC ---
    # Assumptions are detailed in the R code comments
    # 4 - doses per child
    # 0.18 - proportion of children 3-11 months
    # 0.77 - proportion of children 12-59 months
    # 1.1 - buffer

    if "code_smc" in scen_data.columns and scen_data["code_smc"].sum() > 0:
        smc_monthly_rounds = settings.smc_monthly_rounds
        smc_pop_prop_3_11 = settings.smc_pop_prop_3_11
        smc_pop_prop_12_59 = settings.smc_pop_prop_12_59
        smc_buffer = settings.smc_buffer  # smc_buffer
        smc_coverage = settings.smc_coverage
        include_5_10 = settings.smc_include_5_10

        target_population.rename(columns={"annee": "year"})

        smc_q = scen_data[scen_data["code_smc"] == 1].merge(
            # target_population, left_on=['adm1', 'adm2', 'year'], right_on=['adm1', 'adm2', 'annee']
            # TODO: commented out year as there is only 2025 population data for now in Nigeria
            target_population,
            left_on=["adm1", "adm2"],
            right_on=["adm1", "adm2"],
            suffixes=("", "_right"),
        )
        smc_q["quant_smc_spaq_3_11_months"] = (
            (smc_q["pop_0_5"] * smc_pop_prop_3_11 * smc_coverage)
            * smc_monthly_rounds
            * smc_buffer
        )
        smc_q["quant_smc_spaq_12_59_months"] = (
            (smc_q["pop_0_5"] * smc_pop_prop_12_59 * smc_coverage)
            * smc_monthly_rounds
            * smc_buffer
        )
        smc_q["quant_smc_spaq_5_10_years"] = (
            (smc_q["pop_5_10"] * smc_coverage * smc_monthly_rounds * smc_buffer)
            if include_5_10 and "pop_5_10" in smc_q.columns
            else 0
        )

        pop_base = smc_q["pop_0_5"] * (smc_pop_prop_3_11 + smc_pop_prop_12_59)
        pop_extended = (
            (pop_base + smc_q["pop_5_10"])
            if include_5_10 and "pop_5_10" in smc_q.columns
            else pop_base
        )
        smc_q["target_pop"] = pop_extended * smc_coverage

        smc_q_long = smc_q.melt(
            id_vars=[
                "adm1",
                "adm2",
                "year",
                "scenario_name",
                "scenario_description",
                "target_pop",
                "type_smc",
            ],
            value_vars=[c for c in smc_q.columns if c.startswith("quant_smc")],
            var_name="unit",
            value_name="quantity",
        ).rename(columns={"type_smc": "type_intervention"})

        unit_map = {
            "quant_smc_spaq_3_11_months": "per SPAQ pack 3-11 month olds",
            "quant_smc_spaq_12_59_months": "per SPAQ pack 12-59 month olds",
            "quant_smc_spaq_5_10_years": "per SPAQ pack 12-59 month olds",  # Note: R code maps this to the same unit
        }
        smc_q_long["unit"] = smc_q_long["unit"].map(unit_map)
        smc_q_long["code_intervention"] = "smc"
    else:
        smc_q_long = pd.DataFrame()

    # --- PMC ---
    # Assumptions detailed in R code comments
    #     # 0.85 coverage
    #     # 4 is number of rounds / child
    #     # 0.75 underweight status for children
    #     # 1.1 is buffer
    #     # 2 is larger dose

    pmc_df = scen_data[scen_data["code_pmc"] == 1].copy()

    if not pmc_df.empty:
        # Select relevant population columns
        pop_cols_to_merge = ["adm1", "adm2", "year", "pop_0_1", "pop_1_2"]
        target_pop_pmc = target_population.rename(columns={"annee": "year"})[
            pop_cols_to_merge
        ]

        # Join with population data
        # pmc_df = pd.merge(pmc_df, target_pop_pmc, on=['adm1', 'adm2', 'year'], how='left', suffixes=('', '_right'))
        # TODO: update when more years are available
        pmc_df = pd.merge(
            pmc_df,
            target_pop_pmc,
            on=["adm1", "adm2"],
            how="left",
            suffixes=("", "_right"),
        )

        # Apply quantification formulas
        pmc_df["quant_pmc_sp_0_1_years"] = (
            pmc_df["pop_0_1"]
            * settings.pmc_coverage
            * settings.pmc_touchpoints  # Question: only for DRC? \
            * settings.pmc_tablet_factor  # Question: only for DRC? \
            * settings.pmc_buffer
        )
        pmc_df["quant_pmc_sp_1_2_years"] = (
            pmc_df["pop_1_2"]
            * settings.pmc_coverage
            * settings.pmc_touchpoints
            * 2  # 2 is for larger dose \
            * settings.pmc_tablet_factor
            * settings.pmc_buffer
        )
        pmc_df["quant_pmc_sp_total"] = (
            pmc_df["quant_pmc_sp_0_1_years"] + pmc_df["quant_pmc_sp_1_2_years"]
        )
        pmc_df["quant_pmc_child"] = (
            pmc_df["pop_0_1"] * settings.pmc_coverage
            + pmc_df["pop_1_2"] * settings.pmc_coverage
        )

        # Set target population and intervention codes
        pmc_df["target_pop"] = pmc_df["quant_pmc_child"]
        pmc_df["code_intervention"] = "pmc"
        pmc_df["type_intervention"] = pmc_df["type_pmc"]

        # Reshape the data from wide to long format
        pmc_quantification = pd.melt(
            pmc_df,
            id_vars=[
                "adm1",
                "adm2",
                "year",
                "scenario_name",
                "scenario_description",
                "code_intervention",
                "type_intervention",
                "target_pop",
            ],
            value_vars=["quant_pmc_sp_total", "quant_pmc_child"],
            var_name="unit",
            value_name="quantity",
        )

        # Clean up the 'unit' column
        pmc_quantification["unit"] = pmc_quantification["unit"].str.replace(
            "quant_pmc_", ""
        )

        # Map unit names to final display names
        unit_map = {"sp_total": "per SP", "child": "per child"}
        pmc_quantification["unit"] = pmc_quantification["unit"].map(unit_map)

    else:
        pmc_quantification = (
            pd.DataFrame()
        )  # Create empty dataframe if no PMC intervention

    # --- Vaccine ---
    # Assumptions: 84% coverage, 7% wastage, 4 doses per child

    if "code_vacc" in scen_data.columns and scen_data["code_vacc"].sum() > 0:
        vacc_q = scen_data[scen_data["code_vacc"] == 1].merge(
            # target_population, left_on=['adm1', 'adm2', 'year'], right_on=['adm1', 'adm2', 'year']
            # commented out year as there is only 2025 population data for now in Nigeria
            # TODO: update when more years are available
            # target_population, left_on=['adm1', 'adm2', 'year'], right_on=['adm1', 'adm2', 'year'], suffixes=('', '_right')
            target_population,
            left_on=["adm1", "adm2"],
            right_on=["adm1", "adm2"],
            suffixes=("", "_right"),
        )
        vacc_q["quant_child"] = (
            vacc_q["pop_vaccine_5_36_months"] * settings.vacc_coverage
        )
        vacc_q["quant_doses"] = (
            vacc_q["quant_child"]
            * settings.vacc_doses_per_child
            * settings.vacc_wastage_offset
        )
        vacc_q_long = vacc_q.melt(
            id_vars=[
                "adm1",
                "adm2",
                "year",
                "scenario_name",
                "scenario_description",
                "type_vacc",
            ],
            value_vars=["quant_doses", "quant_child"],
            var_name="unit",
            value_name="quantity",
        ).rename(columns={"type_vacc": "type_intervention"})
        vacc_q_long["code_intervention"] = "vacc"
        vacc_q_long = vacc_q_long.assign(
            unit=lambda df: df["unit"].replace(
                {"quant_doses": "per dose", "quant_child": "per child"}
            )
        )
    else:
        vacc_q_long = pd.DataFrame()

    # --- CASE MANAGEMENT ---
    try:
        case_management_quantification = pd.read_csv(
            "./nga-demo-data-pre-processed/cm-quant-data.csv"
        )
        case_management_quantification = case_management_quantification.assign(
            scenario_name=scen_data["scenario_name"].iloc[0],
            scenario_description=scen_data["scenario_description"].iloc[0],
            year=scen_data["year"].iloc[
                0
            ],  # Assumes a single year in scen_data for this part
            code_intervention="cm_public",
        )
        case_management_quantification = case_management_quantification.melt(
            id_vars=[
                "adm1",
                "adm2",
                "year",
                "scenario_name",
                "scenario_description",
                "code_intervention",
            ],
            value_vars=[
                col
                for col in case_management_quantification.columns
                if col.startswith("cm")
            ],
            var_name="unit",
            value_name="quantity",
        )
        type_intervention_conditions = [
            case_management_quantification["unit"] == "cm_rdt_kit_quantity",
            case_management_quantification["unit"] == "cm_act_packs_quantity",
            case_management_quantification["unit"] == "cm_iv_artesunate_quantity",
            case_management_quantification["unit"] == "cm_ras_quantity",
        ]
        type_intervention_choices = ["RDT kits", "AL", "Artesunate injections", "RAS"]
        case_management_quantification["type_intervention"] = np.select(
            type_intervention_conditions, type_intervention_choices, default="Other"
        )

        unit_conditions = [
            case_management_quantification["unit"] == "cm_rdt_kit_quantity",
            case_management_quantification["unit"] == "cm_act_packs_quantity",
            case_management_quantification["unit"] == "cm_iv_artesunate_quantity",
            case_management_quantification["unit"] == "cm_ras_quantity",
        ]
        unit_choices = ["per RDT kit", "per AL", "per 60mg powder", "per RAS"]
        case_management_quantification["unit"] = np.select(
            unit_conditions, unit_choices, default="Other"
        )

        # Add target_pop as NA for this section
        case_management_quantification["target_pop"] = np.nan

    except FileNotFoundError:
        print("Warning: Case management data file not found. Skipping this component.")
        case_management_quantification = pd.DataFrame()

    # --- Combine into one dataframe ---
    budget = pd.concat(
        [
            itn_q_long,
            itn_r_q_long,
            iptp_q_long,
            smc_q_long,
            pmc_quantification,
            vacc_q_long,
            case_management_quantification,
        ],
        ignore_index=True,
    )

    # Join with cost data
    budget = pd.merge(
        budget,
        cost_data,
        on=["code_intervention", "type_intervention", "unit"],
        how="left",
    )
    budget = budget.dropna(subset=["cost_class"])

    # Melt cost columns to handle currencies
    budget = budget.melt(
        id_vars=[col for col in budget.columns if not col.endswith("_cost")],
        value_vars=["usd_cost", "ngn_cost"],
        var_name="currency",
        value_name="unit_cost",
    )

    # Final calculations
    budget = budget.assign(
        cost_element=lambda df: df["quantity"] * df["unit_cost"],
        currency=lambda df: df["currency"].replace(
            {"usd_cost": "USD", "ngn_cost": "NGN"}
        ),
    )

    # Create 'intervention_nice' column
    conditions = [
        budget["code_intervention"] == "cm_public",
        budget["code_intervention"] == "cm_private",
        budget["code_intervention"] == "iptp",
        budget["code_intervention"] == "vacc",
        budget["code_intervention"] == "itn_routine",
        budget["code_intervention"] == "itn_campaign",
        budget["code_intervention"] == "smc",
        budget["code_intervention"] == "pmc",
        # budget["code_intervention"] == "irs",
        # budget["code_intervention"] == "lsm",
    ]
    choices = [
        "Case Management Public",
        "Case Management Private",
        "IPTp",
        "Vaccine",
        "ITN Routine",
        "ITN Campaign",
        "SMC",
        "PMC",
        # "IRS",
        # "LSM",
    ]
    budget["intervention_nice"] = np.select(
        conditions, choices, default=budget["code_intervention"]
    )

    # print(budget)

    return budget


def get_budget(data, country, year, settings):
    cost_file = f"./data/{country.lower()}-demo-data-pre-processed/costs.xlsx"
    pop_file = f"./data/{country.lower()}-demo-data-pre-processed/data-needs-not-user-defined.xlsx"

    try:
        pop_data = pd.read_excel(pop_file, sheet_name="population")
        places = pop_data[["adm1", "adm2"]].drop_duplicates().values.tolist()

        ######################################
        # convert from json input to dataframe
        ######################################
        settings = data.settings

        scen_data = pd.DataFrame(places, columns=["adm1", "adm2"])
        scen_data["adm0"] = (
            country  # Add a new column 'adm0' and set its value to "Nigeria"
        )
        scen_data["year"] = year  # Set a default year for the scenario
        scen_data["scenario_name"] = "Test Scenario"
        scen_data["scenario_description"] = "test"

        def set_intervention_code(intervention_name, column_name):
            ########################################################################
            # for setting intervention code base on intervention's places from input
            ########################################################################
            intervention = [
                intervention
                for intervention in data.interventions
                if intervention.name == intervention_name
            ]
            intervention_places = (
                intervention[0].places if len(intervention) > 0 else []
            )
            scen_data[column_name] = scen_data.apply(
                lambda row: 1
                if (f"{row['adm1']}:{row['adm2']}" in intervention_places)
                else 0,
                axis=1,
            )

        def set_intervention_type(intervention_name, column_name):
            ################################################################
            # for setting intervention type base on intervention from input
            ################################################################
            intervention = [
                intervention
                for intervention in data.interventions
                if intervention.name == intervention_name
            ]
            scen_data[column_name] = (
                intervention[0].type if len(intervention) > 0 else ""
            )

        # for CM
        set_intervention_code("cm", "code_cm_public")

        # for Iptp
        set_intervention_code("iptp", "code_iptp")
        set_intervention_type("iptp", "type_iptp")

        # for SMC
        set_intervention_code("smc", "code_smc")
        set_intervention_type("smc", "type_smc")

        # for PMC
        set_intervention_code("pmc", "code_pmc")
        set_intervention_type("pmc", "type_pmc")

        # for Vaccination
        set_intervention_code("vacc", "code_vacc")
        set_intervention_type("vacc", "type_vacc")

        # for IRS
        set_intervention_code("irsx1", "code_irs")
        set_intervention_type("irsx1", "type_irs")

        # for LSM
        scen_data["code_lsm"] = 1  # Assuming a type for LSM
        scen_data["type_lsm"] = "Bti"

        # for ITN Routine
        # Todo: for now, let's map that to IG2
        set_intervention_code("ig2", "code_itn_routine")
        set_intervention_type("ig2", "type_itn_routine")

        # for ITN Campaign
        set_intervention_code("pyr", "code_itn_campaign")
        set_intervention_type("pyr", "type_itn_campaign")

        # for ITN Urban
        scen_data["code_itn_urban"] = 0

        # for CM private
        scen_data["code_cm_private"] = 1

        # todo: for now, cost data is read from a file
        cost_data = pd.read_excel(cost_file, sheet_name=0)

        input_costs_dict = [cost.dict() for cost in data.costs]

        ######################################
        # merge cost_data with data.costs
        ######################################
        if input_costs_dict.__len__() > 0:
            validation = cost_data.merge(
                pd.DataFrame(input_costs_dict),
                on=["code_intervention", "type_intervention", "cost_class", "unit"],
                how="inner",
                suffixes=("", "_y"),
            )

            if validation.__len__() != input_costs_dict.__len__():
                raise ValueError("Cost data override validation failed.")

            cost_data = cost_data.merge(
                pd.DataFrame(input_costs_dict),
                on=["code_intervention", "type_intervention", "cost_class", "unit"],
                how="left",
                suffixes=("", "_y"),
            )
            cost_data["usd_cost"] = cost_data["usd_cost_y"].combine_first(
                cost_data["usd_cost"]
            )

            # TODO: need a better way to support different country
            if country == "NGA":
                cost_data["ngn_cost"] = cost_data["ngn_cost_y"].combine_first(
                    cost_data["ngn_cost"]
                )
            elif country == "CDF":  # DRC
                cost_data["cdf_cost"] = cost_data["cdf_cost_y"].combine_first(
                    cost_data["cdf_cost"]
                )

        budget = generate_budget(scen_data, cost_data, settings, pop_data)

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
            #   "cm_public", "iptp", "smc", "pmc", "vacc", "irs", "lsm", "itn_routine", "itn_campaign"
            "iptp",
            "smc",
            "pmc",
            "vacc",
            "itn_routine",
            "itn_campaign",
        ]

        intervention_costs = {"year": year, "interventions": [], "scenairo_name": ""}

        for code, name in zip(interventions, interventions):
            costs = []
            cost_classes = budget["cost_class"].unique()
            total_cost = 0
            total_pop = 0
            for cost_class in cost_classes:
                cost_class_data = get_cost_class_data(
                    code, settings.currency, year, cost_class
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


def get_country_budgets(data):
    """Fetches budgets for a given country and time range."""
    try:
        if data.startYear is None or data.endYear is None:
            raise ValueError("Start year and end year must be provided.")
        if data.startYear > data.endYear:
            raise ValueError("Start year cannot be greater than end year.")
        if data.country is None or data.country.strip() == "":
            raise ValueError("Country must be provided.")

        budgets = []

        for year in range(data.startYear, data.endYear + 1):
            print(f"Fetching budget for year: {year}")
            budgets.append(get_budget(data, data.country, year, data.settings))

        return {"budgets": budgets}

    except Exception as e:
        print(f"Error fetching budgets: {e}")
        raise e
