
### Service Setup

1. Open a terminal and navigate to the root of the repository.

2. Create a new virtual environment named 'venv': `python -m venv venv`

3. Activate the virtual environment by running the following command in linux `source venv/bin/activate`. 
In windows, the command is `venv\Scripts\activate`

4. Install the required dependencies:
```
cd budgetingService
pip install -r requirements.txt
```

5. Set the following environment variables:
- `PYTHONPATH=%PYTHONPATH%;C:\Your\Project\Root`

6. Run the application in the service folder: 
- `uvicorn main:app  --port 5001`
