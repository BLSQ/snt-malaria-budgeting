from pydantic import BaseModel, Field
from typing import List, Union

DEFAULT_COST_ASSUMPTIONS = {
    "itn_campaign_divisor": 1.8,  # people per net
    "itn_campaign_bale_size": 50,
    "itn_campaign_buffer_mult": 1.1,
    "itn_campaign_coverage": 1.0,
    "itn_routine_coverage": 0.3,
    "itn_routine_buffer_mult": 1.1,
    "iptp_anc_coverage": 0.8,
    "iptp_doses_per_pw": 3,
    "iptp_buffer_mult": 1.1,
    "smc_age_string": "0.18,0.77",  # proportion of population 3-11 months, 12-59 months
    "smc_pop_prop_3_11": 0.18,
    "smc_pop_prop_12_59": 0.77,
    "smc_coverage": 1.0,
    "smc_monthly_rounds": 4,
    "smc_buffer_mult": 1.1,
    "pmc_coverage": 0.85,
    "pmc_touchpoints": 4,
    "pmc_tablet_factor": 0.75,
    "pmc_buffer_mult": 1.1,
    "vacc_coverage": 0.84,
    "vacc_doses_per_child": 4,
    "vacc_buffer_mult": 1.1,
    "iptp_type": "SP",
    "smc_type": "SP+AQ",
    "pmc_type": "SP",
    "irs_type": "Sumishield",
    "lsm_type": "Bti",
    "vacc_type": "R21",
}


class InterventionDetailModel(BaseModel):
    type: str
    code: str
    places: List[Union[str, int]]


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
    interventions: List[InterventionDetailModel] = Field(default_factory=list)
    assumptions: dict = DEFAULT_COST_ASSUMPTIONS
    costs: List[CostItems] = []
    country: str = "NGA"
