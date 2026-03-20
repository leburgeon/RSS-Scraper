FROM public.ecr.aws/lambda/python:3.13

COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt

COPY metrics.py ${LAMBDA_TASK_ROOT}
COPY report.py ${LAMBDA_TASK_ROOT}

CMD ["report.lambda_handler"]