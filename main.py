import uvicorn

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette import status
from models.models import InterventionCostModel

from budgetController import get_country_budgets

app = FastAPI()


@app.post("/get_budgets", status_code=status.HTTP_200_OK)
async def get_budgets(data: InterventionCostModel):
    """Endpoint to get budget estimates based on intervention cost model.
    Example: /get_budgets
                    {
        "startYear": 2025,
        "endYear": 2025,
        "settings": {
            "smc_buffer": 1.5,
            "vacc_doses_per_child": 4,
            "currency": "NGN"
        },
        "interventions": [
            {
            "name": "smc",
            "type": "SP+AQ",
            "places": [
                "Tshopo:Opala"
            ]
            },
            {
            "name": "vacc",
            "type": "R21",
            "places": [
                "Tshopo:Opala"
            ]
            },
            {
            "name": "iptp",
            "type": "SP",
            "places": [
                "Tshopo:Opala"
            ]
            }
        ],
        "country": "drc"
        }
    """

    try:
        return get_country_budgets(data)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/test")
async def run():
    output = "test success"
    return {"output": output}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5001)
