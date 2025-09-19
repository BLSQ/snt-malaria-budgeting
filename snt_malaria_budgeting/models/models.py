from pydantic import BaseModel
from typing import List


# Input parameter
class InputInterventionPackage(BaseModel):
    name: str
    places: List[str]


class InputScenario(BaseModel):
    scenario: str
    interventionPackage: List[InputInterventionPackage]
    # coverage: int
    insecticideResistance: int
    vaccineEfficacy: int


class InputConfigurationModel(BaseModel):
    scenarios: List[InputScenario]


class InterventionDetailModel(BaseModel):
    name: str
    type: str
    places: List[str]


class CostSettingItems(BaseModel):
    itn_campaign_net_needed_radio: float = 1.8
    itn_campaign_nets_per_bale: float = 50
    itn_campaign_coverage: float = 0.8
    itn_campaign_divisor: float = 1.8
    itn_campaign_buffer: float = 1.1
    itn_campaign_bale_size: float = 50

    itn_routine_coverage: float = 0.3
    itn_routine_buffer: float = 1.1

    iptp_ANC_coverage: float = 0.8
    iptp_doses_per_pw: float = 3
    iptp_buffer: float = 1.1
    iptp_type: str = "SP"

    smc_monthly_rounds: int = 4
    smc_pop_prop_3_11: float = 0.18
    smc_pop_prop_12_59: float = 0.77
    smc_buffer: float = 1.1
    smc_coverage: float = 1
    smc_include_5_10: bool = False  # TODO: what is default value for each country
    smc_type: str = "SP+AQ"

    pmc_touchpoints: float = 4
    pmc_tablet_factor: float = 0.75
    pmc_coverage: float = 0.85
    pmc_rounds_per_child: int = 4
    pmc_underweight_status: float = 0.75
    pmc_buffer: float = 1.1
    pmc_larger_dose_factor: float = 2
    pmc_type: str = "SP"

    irs_type: str = "Sumishield"

    lsm_type: str = "Bti"

    vacc_coverage: float = 0.84
    vacc_wastage_offset: float = 1.07
    vacc_doses_per_child: int = 4
    vacc_type: str = "R21"

    currency: str = "USD"


class CostItems(BaseModel):
    code_intervention: str
    type_intervention: str
    cost_class: str
    unit: str
    ngn_cost: float = 0
    usd_cost: float = 0
    cost_year: int = 0


class InterventionCostModel(BaseModel):
    startYear: int
    endYear: int
    # coverage: int
    interventions: List[InterventionDetailModel] = []
    settings: CostSettingItems
    costs: List[CostItems] = []
    country: str = "NGA"
