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
