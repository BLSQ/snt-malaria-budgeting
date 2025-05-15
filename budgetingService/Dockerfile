FROM python:3.9


# 
RUN mkdir /app
RUN mkdir /app/budgetingService
WORKDIR /app/budgetingService

# 
COPY ./requirements.txt /app/budgetingService/requirements.txt

# 
RUN pip install --no-cache-dir --upgrade -r /app/budgetingService/requirements.txt

# 
COPY ./ /app/budgetingService

#
ENV PYTHONPATH=/app

# Run all unit tests
RUN python -m unittest budgetingService.budgetController_test

# 
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5001"]

# for debugging
#CMD ["tail", "-f", "/dev/null"]

