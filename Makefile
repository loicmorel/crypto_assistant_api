### GCP AI Platform - - - - - - - - - - - - - - - - - - - -

##### Machine configuration
PYTHON_VERSION=3.7
RUNTIME_VERSION=1.15

##### Package params
PACKAGE_LOC=app
FILENAME=main

# choose your region from https://cloud.google.com/storage/docs/locations#available_locations
REGION=$(shell python ${PACKAGE_LOC}/config.py 'REGION')

##### GCP Storage
BUCKET_NAME=$(shell python ${PACKAGE_LOC}/config.py 'BUCKET_NAME')

# will store the packages uploaded to GCP for the training
BUCKET_TRAINING_FOLDER=$(shell python ${PACKAGE_LOC}/config.py 'BUCKET_TRAINING_FOLDER')

##### GCS API job name
JOB_NAME=$(shell python ${PACKAGE_LOC}/config.py 'JOB_NAME')_$(shell date +'%Y%m%d_%H%M%S')

install_requirements_amd64:
	@pip install --upgrade pip
	@pip install -r requirements_amd64

install_requirements_for_macosm1:
	@pip install --upgrade pip
	@pip install -r requirements_macosm1.txt

run_notebook:
	@jupyter notebook notebooks

get_all_data:
	@python ${PACKAGE_LOC}/data_mgt/datamgt.py 'get_all_data'

data_collection:
	@python ${PACKAGE_LOC}/data_mgt/datamgt.py 'data_collection'

run_locally:
	@python -m ${PACKAGE_LOC}.${FILENAME}

count_lignes:
	@git ls-files -z | xargs -0 wc -l

gcp_submit_training:
	gcloud ai-platform jobs submit training ${JOB_NAME} \
		--job-dir gs://${BUCKET_NAME}/${BUCKET_TRAINING_FOLDER} \
		--package-path ${PACKAGE_LOC} \
		--module-name ${PACKAGE_LOC}.${FILENAME} \
		--python-version=${PYTHON_VERSION} \
		--runtime-version=${RUNTIME_VERSION} \
		--region ${REGION}
##		--stream-logs

clean:
	@rm -f */version.txt
	@rm -f .coverage
	@rm -fr */__pycache__ __pycache__
	@rm -fr build dist *.dist-info *.egg-info
	@rm -fr */*.pyc
	@rm -fr raw_data

# ----------------------------------
#      UPLOAD PACKAGE TO PYPI
# ----------------------------------
PYPI_USERNAME=<AUTHOR>
build:
	@python setup.py sdist bdist_wheel

pypi_test:
	@twine upload -r testpypi dist/* -u $(PYPI_USERNAME)

pypi:
	@twine upload dist/* -u $(PYPI_USERNAME)

# ----------------------------------
#      BUCKET CREATION ON GCSP
# ----------------------------------

# GCP project id
PROJECT_ID=$(shell python ${PACKAGE_LOC}/config.py 'PROJECT_ID')

set_project:
	@gcloud config set project ${PROJECT_ID}

create_bucket:
	@gsutil mb -l ${REGION} -p ${PROJECT_ID} gs://${BUCKET_NAME}

set_google_credentials:
	@echo run in the terminal before executing python: GOOGLE_APPLICATION_CREDENTIALS=./le-wagon-bootcamp-348503-5c7068200bc6.json

# ----------------------------------
#      BUCKET UPLOAD ON GCSP
# ----------------------------------

# path to the file to upload to GCP (the path to the file should be absolute or should match the directory where the make command is ran)
# replace with your local path to the `train_1k.csv` and make sure to put the path between quotes
LOCAL_PATH="setup.sh"

# bucket directory in which to store the uploaded file (`data` is an arbitrary name that we choose to use)
BUCKET_FOLDER=data

# name for the uploaded file inside of the bucket (we choose not to rename the file that we upload)
BUCKET_FILE_NAME=$(shell basename ${LOCAL_PATH})

upload_data:
# @gsutil cp train_1k.csv gs://wagon-ml-my-bucket-name/data/train_1k.csv
	@gsutil cp ${LOCAL_PATH} gs://${BUCKET_NAME}/${BUCKET_FOLDER}/${BUCKET_FILE_NAME}


# ----------------------------------
#      DOCKER CREATION
# ----------------------------------

DOCKER_NAME=$(shell python ${PACKAGE_LOC}/config.py 'PROJECT_NAME')_image

docker_build:
# @docker build --tag=${DOCKER_NAME}_macosm1 -f Dockerfile.macosm1 .
# @echo "docker image: ${DOCKER_NAME}_macosm1"
	@docker build --tag=${DOCKER_NAME}_amd64 --platform linux/amd64 -f Dockerfile.amd64 .
	@echo "docker image: ${DOCKER_NAME}_amd64"

docker_run:
	@docker run \
		-e PORT=8000 \
		-p 8000:8000 \
		-e "GOOGLE_APPLICATION_CREDENTIALS=/google_credentials.json" \
		${DOCKER_NAME}_amd64

docker_name:
	@echo "docker image: ${DOCKER_NAME}_macosm1"
	@echo "docker image: ${DOCKER_NAME}_amd64"

# ----------------------------------
#      DEPLOY ON GOOGLE CLOUD
# ----------------------------------

deploy_to_google:
	@gcloud config set project ${PROJECT_ID}
	@docker build -t eu.gcr.io/${PROJECT_ID}/${DOCKER_NAME}_amd64 --platform linux/amd64 -f Dockerfile.amd64 .
	@docker push eu.gcr.io/${PROJECT_ID}/${DOCKER_NAME}_amd64
	@gcloud run deploy \
    --image eu.gcr.io/${PROJECT_ID}/${DOCKER_NAME}_amd64 \
    --platform managed \
    --region ${REGION} \
    --set-env-vars "GOOGLE_APPLICATION_CREDENTIALS=/google_credentials.json"


# ----------------------------------
#      API MANAGEMENT
# ----------------------------------

run_api:
	uvicorn api.ca_api:ca_api --reload  # load web server with code autoreload
