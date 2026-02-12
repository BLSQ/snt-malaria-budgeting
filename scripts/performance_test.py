"""
Performance test for BudgetCalculator.

Usage: python performance_test.py
"""

import time
import pandas as pd
from snt_malaria_budgeting.core.budget_calculator import BudgetCalculator
from snt_malaria_budgeting.models import (
    DEFAULT_COST_ASSUMPTIONS,
    InterventionDetailModel,
)

POP_TOTAL = 250000
POP_PW = 12500
POP_0_5 = 45000
POP_0_1 = 10000
POP_1_2 = 10000
POP_VACCINE_5_36_MONTHS = 8000


def create_large_dataset(num_places, num_years):
    data = []
    base_key = 2000
    for place_idx in range(num_places):
        key = base_key + place_idx
        multiplier = (place_idx % 5) + 1
        for year_idx in range(num_years):
            year = 2025 + year_idx
            data.append(
                {
                    "key": key,
                    "year": year,
                    "pop_total": POP_TOTAL * multiplier,
                    "pop_pw": POP_PW * multiplier,
                    "pop_0_5": POP_0_5 * multiplier,
                    "pop_0_1": POP_0_1 * multiplier,
                    "pop_1_2": POP_1_2 * multiplier,
                    "pop_vaccine_5_36_months": POP_VACCINE_5_36_MONTHS * multiplier,
                }
            )
    return pd.DataFrame(data)


def create_cost_data(num_years):
    data = []
    intervention_types = [
        ("iptp", "SP", "per SP", "Commodity"),
        ("iptp", "SP", "per SP", "Distribution"),
        ("smc", "SP+AQ", "per SPAQ pack 3-11 month olds", "Commodity"),
        ("smc", "SP+AQ", "per SPAQ pack 12-59 month olds", "Commodity"),
        ("smc", "SP+AQ", "per SPAQ pack 3-11 month olds", "Distribution"),
        ("smc", "SP+AQ", "per SPAQ pack 12-59 month olds", "Distribution"),
        ("pmc", "SP", "per SP", "Commodity"),
        ("pmc", "SP", "per SP", "Distribution"),
        ("itn_routine", "PBO", "per ITN", "Procurement"),
        ("itn_routine", "PBO", "per ITN", "Distribution"),
        ("itn_routine", "Standard Pyrethroid", "per ITN", "Procurement"),
        ("itn_routine", "Standard Pyrethroid", "per ITN", "Distribution"),
        ("itn_campaign", "Dual AI", "per ITN", "Procurement"),
        ("itn_campaign", "Dual AI", "per ITN", "Distribution"),
        ("itn_campaign", "Dual AI", "per bale", "Distribution"),
        ("vacc", "R21", "per dose", "Commodity"),
        ("vacc", "R21", "per dose", "Distribution"),
        ("vacc", "RTS,S", "per dose", "Commodity"),
        ("vacc", "RTS,S", "per dose", "Distribution"),
    ]
    for year_idx in range(num_years):
        year = 2025 + year_idx
        for code, type_int, unit, cost_class in intervention_types:
            base_usd = 0.5 + (year_idx * 0.1)
            base_ngn = 800 + (year_idx * 50)
            data.append(
                {
                    "code_intervention": code,
                    "type_intervention": type_int,
                    "unit": unit,
                    "cost_class": cost_class,
                    "cost_year_for_analysis": year,
                    "usd_cost": base_usd,
                    "ngn_cost": base_ngn,
                    "cost_name": f"{type_int} - {cost_class}",
                }
            )
    return pd.DataFrame(data)


def create_interventions(num_places):
    base_key = 2000
    places = [base_key + i for i in range(num_places)]
    third = num_places // 3
    return [
        InterventionDetailModel(code="iptp", type="SP", places=places),
        InterventionDetailModel(code="smc", type="SP+AQ", places=places[:third]),
        InterventionDetailModel(
            code="pmc", type="SP", places=places[third : third * 2]
        ),
        InterventionDetailModel(
            code="itn_routine", type="PBO", places=places[: third * 2]
        ),
        InterventionDetailModel(
            code="itn_routine", type="Standard Pyrethroid", places=places[third * 2 :]
        ),
        InterventionDetailModel(code="itn_campaign", type="Dual AI", places=places),
        InterventionDetailModel(code="vacc", type="R21", places=places[:third]),
        InterventionDetailModel(
            code="vacc", type="RTS,S", places=places[third : third * 2]
        ),
    ]


def benchmark(method, *args):
    start = time.time()
    result = method(*args)
    return time.time() - start, result


def run_performance_test(num_places, num_years):
    population_df = create_large_dataset(num_places, num_years)
    cost_df = create_cost_data(num_years)
    interventions = create_interventions(num_places)

    calculator = BudgetCalculator(
        interventions_input=interventions,
        settings=DEFAULT_COST_ASSUMPTIONS,
        cost_df=cost_df,
        population_df=population_df,
        local_currency="ngn",
        spatial_planning_unit="key",
        budget_currency="usd",
    )

    t_interventions = 0
    t_places = 0
    for year in range(2025, 2025 + num_years):
        t, _ = benchmark(calculator.get_interventions_costs, year)
        t_interventions += t
        t, _ = benchmark(calculator.get_places_costs, year)
        t_places += t

    return t_interventions, t_places


def main():
    configs = [("100 places", 100, 5), ("500 places", 500, 5)]

    print(
        f"{'Config':<12} {'interv_costs':>12} {'places_costs':>12} {'total (5Ys)':>8} {'avg/yr':>8}"
    )
    print("-" * 56)

    for label, num_places, num_years in configs:
        t_int, t_pl = run_performance_test(num_places, num_years)
        total = t_int + t_pl
        avg = total / num_years
        print(f"{label:<12} {t_int:>11.3f}s {t_pl:>11.3f}s {total:>7.3f}s {avg:>7.3f}s")


if __name__ == "__main__":
    main()
