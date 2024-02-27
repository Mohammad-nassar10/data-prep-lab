import os
import sys

from data_processing.ray import TransformLauncher
from data_processing.utils import ParamsUtils
from schema_modification_implementation import SchemaTransformConfiguration


# create launcher
launcher = TransformLauncher(transform_runtime_config=SchemaTransformConfiguration())
# create parameters
s3_cred = {
    "access_key": os.environ.get("COS_ACCESS_KEY", "access"),
    "secret_key": os.environ.get("COS_SECRET_KEY", "secret"),
    "cos_url": "https://s3.us-east.cloud-object-storage.appdomain.cloud",
}
s3_conf = {
    "input_folder": "cos-optimal-llm-pile/sanity-test/input/dataset=text/",
    "output_folder": "cos-optimal-llm-pile/boris-da-test/",
}
worker_options = {"num_cpus": 0.8}
code_location = {"github": "github", "commit_hash": "12345", "path": "path"}
params = {
    "run_locally": True,
    "max_files": -1,
    "s3_cred": ParamsUtils.convert_to_ast(s3_cred),
    "s3_config": ParamsUtils.convert_to_ast(s3_conf),
    "worker_options": ParamsUtils.convert_to_ast(worker_options),
    "num_workers": 3,
    "checkpointing": False,
    "pipeline_id": "pipeline_id",
    "job_id": "job_id",
    "creation_delay": 0,
    "code_location": ParamsUtils.convert_to_ast(code_location),
    "doc_column": "contents",
    "id_column": "id_column",
    "int_id_column": "int_id_column"
}
sys.argv = ParamsUtils.dict_to_req(d=params)

# launch
launcher.launch()