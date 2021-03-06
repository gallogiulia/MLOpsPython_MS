import os
import sys
import argparse
from azureml.core import Workspace
from azureml.core.image import ContainerImage, Image
from azureml.core.model import Model
sys.path.append(os.path.abspath("./ml_service/util"))  # NOQA: E402
from env_variables import Env

e = Env()

# Get Azure machine learning workspace
ws = Workspace.get(
    name=e.workspace_name,
    subscription_id=e.subscription_id,
    resource_group=e.resource_group
)

parser = argparse.ArgumentParser("create scoring image")
parser.add_argument(
    "--output_image_location_file",
    type=str,
    help=("Name of a file to write image location to, "
          "in format REGISTRY.azurecr.io/IMAGE_NAME:IMAGE_VERSION")
)
args = parser.parse_args()

model = Model(ws, name=e.model_name, version=e.model_version)
sources_dir = e.sources_directory_train
if (sources_dir is None):
    sources_dir = 'diabetes_regression'
path_to_scoring = os.path.join(".", sources_dir, "scoring")
cwd = os.getcwd()
os.chdir(path_to_scoring)

image_config = ContainerImage.image_configuration(
    execution_script=e.score_script,
    runtime="python",
    conda_file="conda_dependencies.yml",
    description="Image with ridge regression model",
    tags={"area": "diabetes", "type": "regression"},
)

image = Image.create(
    name=e.image_name, models=[model], image_config=image_config, workspace=ws
)

os.chdir(cwd)

image.wait_for_creation(show_output=True)

if image.creation_state != "Succeeded":
    raise Exception("Image creation status: {image.creation_state}")

print("{}(v.{} [{}]) stored at {} with build log {}".format(
    image.name,
    image.version,
    image.creation_state,
    image.image_location,
    image.image_build_log_uri,
)
)

# Save the Image Location for other AzDO jobs after script is complete
if args.output_image_location_file is not None:
    print("Writing image location to %s" % args.output_image_location_file)
    with open(args.output_image_location_file, "w") as out_file:
        out_file.write(str(image.image_location))
