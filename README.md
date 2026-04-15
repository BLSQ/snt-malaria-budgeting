# SNT Malaria Budgeting

A Python library for calculating malaria intervention budgets across different countries and time periods.

## Installation

Install from PyPI:

```bash
pip install snt-malaria-budgeting
```

### Development Installation

For development, clone the repository and install with development dependencies:

```bash
pip install -e .[dev]
```

This installs the package in editable mode along with all development tools (pytest, ruff, mypy, etc.).

## Example usage

To fetch budgets for a given country and years:

```python
from snt_malaria_budgeting.core.budget_calculator import get_budget
from snt_malaria_budgeting.models import (
    DEFAULT_COST_ASSUMPTIONS,
    InterventionDetailModel,
)

start_year = 2025
end_year = 2027
# places are a list of ids
interventions = [InterventionDetailModel(code="iptp", type="SP", places=[1001])]
settings = DEFAULT_COST_ASSUMPTIONS

budgets = []
budget_calculator = BudgetCalculator(
    interventions_input=interventions_input,
    settings=settings,
    cost_df=cost_df, # refer to unit tests for an example
    population_df=population_df, # refer to unit tests for an example
    local_currency="EUR",
    spatial_planning_unit="key",
    cost_overrides=[], # optional
    unknown_intervention_handling="ignore", #optional can be: ignore, handle or error

)

for year in range(start_year, end_year + 1):
    print(f"Fetching budget for year: {year}")
    interventions_costs = budget_calculator.get_interventions_costs(year)
    places_costs = budget_calculator.get_places_costs(year)
    budgets.append({
        "year": year,
        "interventions": interventions_costs,
        "org_units_costs": places_costs
    })

print(budgets)

```


## Input Definitions

### 1. `interventions_input` (List of `InterventionDetailModel`)
- **code**: Intervention code (e.g., "iptp", "smc", etc.)
- **type**: Unique identifier for the intervention within a code (e.g., "SP", "SP+AQ")
- **places**: List of place IDs assigned to the intervention
- **target_population_columns**: (Optional) List of population columns to use for quantification (e.g., ["pop_total"], ["pop_0_5", "pop_pw"])


**Default target population columns by intervention:**

**Default Target Population & Required Cost Units by Intervention:**

| Intervention Code | Default Target Population Column(s) | Required Cost Unit(s)                |
|-------------------|--------------------------------------|--------------------------------------|
| itn_campaign      | pop_total                            | per ITN, per bale                    |
| itn_routine       | pop_0_5, pop_pw                      | per ITN                              |
| iptp              | pop_pw                               | per SP                               |
| smc               | pop_0_5                              | per SPAQ pack 3-11 month olds,<br>per SPAQ pack 12-59 month olds |
| pmc               | pop_0_1, pop_1_2                     | per SP                               |
| vacc              | pop_vaccine_5_36_months              | per dose, per child                  |
| default           | pop_total                            | Other                                |

> **Note:**
> - The `unit` column in your `cost_df` must match the required cost unit(s) for each intervention code above.
> - Some interventions (like SMC and Vacc) require multiple units for different age groups or quantification types.

> **Note:**
> - The `unit` column in your `cost_df` must match the required cost unit(s) for each intervention code above.
> - Some interventions (like SMC and Vacc) require multiple units for different age groups or quantification types.



### 2. `settings` (Dictionary)
Dictionary of cost and quantification assumptions. Defaults are provided in `DEFAULT_COST_ASSUMPTIONS` (see models.py).

### 3. `cost_df` (DataFrame)
DataFrame of unit costs, with columns such as:
- code_intervention
- type_intervention
- cost_class
- unit
- ngn_cost
- usd_cost
- cost_year

### 4. `population_df` (DataFrame)
DataFrame with population data by place and year, with columns:
- org_unit_id: Place ID
- year: Year
- Population columns: e.g., pop_total, pop_0_5, pop_pw, etc.

If `target_population_columns` is not specified in the intervention, the default columns above are used.

### 5. `local_currency` (str)
The local currency symbol (e.g., "NGN", "EUR").

### 6. `spatial_planning_unit` (str)
The column name in `population_df` that identifies the spatial unit (e.g., "org_unit_id").

### 7. `budget_currency` (str, optional)
The currency for the budget output. Defaults to `local_currency`.

### 8. `cost_overrides` (Optional[List[CostItems]])
List of cost override items (see `CostItems` model).

### 9. `unknown_intervention_handling` (str, optional)
How to handle unknown interventions: "ignore", "handle", or "error".

## Development

### Running Tests

After installing with development dependencies, run the test suite:

```bash
pytest
pytest -v # verbose output
pytest --cov=snt_malaria_budgeting --cov-report=html # with coverage report

# specific test files or methods:
pytest tests/core/test_budget_calculator.py
pytest tests/core/test_budget_calculator.py::TestGetBudget::test_get_budget_iptp
```

## Acknowledgements

This library is a Python port of the [PATH Budget Generation Function](https://github.com/PATH-Global-Health/budget-generation-function) (R implementation).
