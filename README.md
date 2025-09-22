# SNT Malaria Budgeting

A Python library for calculating malaria intervention budgets across different countries and time periods.

## Installation

Install the package and its dependencies:

```bash
pip install -r requirements.txt
```

## Example usage

To fetch budgets for a given country and years:

```python
from snt_malaria_budgeting import get_budget

country = "DRC"
start_year = 2025
end_year = 2027
interventions = [
    {"name": "smc", "type": "SP+AQ", "places": ["Tshopo:Opala"]},
    {"name": "vacc", "type": "R21", "places": ["Tshopo:Opala"]},
    {"name": "iptp", "type": "SP", "places": ["Tshopo:Opala"]},
]
settings = {
    "smc_buffer": 1.5,
    "vacc_doses_per_child": 4,
    "currency": "NGN",
}

budgets = []

for year in range(start_year, end_year + 1):
    print(f"Fetching budget for year: {year}")
    budgets.append(
        get_budget(
            country=country,
            year=year,
            interventions_input=interventions,
            settings=settings,
            cost_df=cost_df,
            population_df=population_df,
            cost_overrides=[], # optional
        )
    )

print(budgets)
```

## Development

### Running Tests

```bash
pip install pytest pytest-cov
```

Run the test suite:

```bash
pytest
pytest -v # verbose output
pytest --cov=snt_malaria_budgeting --cov-report=html # with coverage report

# specific test files or methods:
pytest tests/core/test_budget_calculator.py
pytest tests/core/test_budget_calculator.py::TestBudgetCalculator::test_iptp_quantification
```
