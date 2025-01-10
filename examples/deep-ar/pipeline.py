import sagemaker
from sagemaker.workflow.steps import ProcessingStep, TrainingStep, ProcessingJob
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.processing import ScriptProcessor, ProcessingOutput, ProcessingInput
from sagemaker.estimator import Estimator
from sagemaker.inputs import TrainingInput
from sagemaker.workflow.parameters import ParameterString
from sagemaker.amazon.amazon_estimator import get_image_uri

# Define SageMaker session and role
session = sagemaker.Session()
role = sagemaker.get_execution_role()
# bucket = session.default_bucket()
bucket_uri = "s3://stock-86589a88-8765-41e7-9019-865601"


# Parameters for pipeline
input_data_uri = ParameterString(
    name="InputDataUri",
    default_value=f"{bucket_uri}/AAPL.csv",
)

# Processing step
processor = ScriptProcessor(
    role=role,
    image_uri="763104351884.dkr.ecr.us-west-2.amazonaws.com/sagemaker-scikit-learn:1.2-1-cpu-py3",
    instance_count=1,
    instance_type="ml.m5.large",
    command=["python3"],
)

processing_step = ProcessingStep(
    name="TimeSeriesDataProcessing",
    processor=processor,
    inputs=[
        ProcessingInput(
            source=input_data_uri,
            destination="/opt/ml/processing/input/",
            input_name="input_data",
        )
    ],
    outputs=[
        ProcessingOutput(
            output_name="processed_data", source="/opt/ml/processing/output"
        )
    ],
    code="scripts/processing.py",
)
print(processing_step)

# Training step using DeepAR
estimator = Estimator(
    image_uri=get_image_uri(session.boto_region_name, "forecasting-deepar"),
    role=role,
    instance_count=1,
    instance_type="ml.m5.large",
    output_path=f"{bucket_uri}/output",
    hyperparameters={
        "time_freq": "H",
        "context_length": "40",
        "prediction_length": "20",
        "num_cells": "40",
        "num_layers": "2",
        "likelihood": "gaussian",
        "epochs": "100",
        "mini_batch_size": "32",
        "learning_rate": "0.001",
    },
)

training_step = TrainingStep(
    name="TimeSeriesTraining",
    estimator=estimator,
    inputs={
        "train": TrainingInput(
            s3_data="s3://stock-86589a88-8765-41e7-9019-865601/processed_data",
        )
    },
)

# Creating the pipeline
pipeline = Pipeline(name="TimeSeriesPipeline", steps=[processing_step, training_step])

if __name__ == "__main__":
    pipeline.upsert(role_arn=role)
    execution = pipeline.start(parameters={"InputDataUri": f"{bucket_uri}/AAPL.csv"})
    execution.wait()
