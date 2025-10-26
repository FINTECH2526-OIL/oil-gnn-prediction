# Requirements
1. Docker Desktop
2. Terraform
3. GCloud CLI (For triggering cloud run deployment)
4. GH CLI (For auto-syncing variables)

# Deployment Setup (Outside of main email used)
1. Create a Service Acocunt (take note of the unique id) and grant it the below mentioned roles
    - Compute Network Admin
    - Cloud Run Admin
    - Cloud Run Source Developer
    - Artifact Registry Administrator 
    - Create Service Account
    - Service Account User
2. Login into GCP (`gcloud auth login`)
3. Run the below command to enable the required APIs (If any are missed out, please raise an issue)
```bash
gcloud services enable cloudresourcemanager.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable iam
gcloud services enable redis.googleapis.com
```
4. From the service account, create a key in JSON
5. Run the following script to obtain a minifed json output
```bash
python -c 'import json, sys;output="";output=json.dumps(json.load(sys.stdin), indent=None,separators=(",",":"));sys.stdout.write(output.replace("\"","\\\"").replace("\\n","\\\\n"))' < {INSERT_JSON_FILE_HERE}

(For Adding as a Repo Env Variable into Github Repo)
python -c 'import json, sys;output="";output=json.dumps(json.load(sys.stdin), indent=None,separators=(",",":"));sys.stdout.write(output)' < {INSERT_JSON_FILE_HERE}

```
6. Put the output into a var file (ex. main.tfvars) as credentials and fill in the rest of the required variables

Template of tfvars file
```terraform
credentials        = "INSERT_CRED_OUTPUT_HERE"
project_id         = "INSERT_PROJECT_ID"
project_region     = "INSERT_PROJECT_REGION"
service_account_id = "INSERT_ACCOUNT_ID"
docker_repo_name   = "INSERT_REPO_NAME"
service_name       = "INSERT_CLOUD_RUN_SERVICE_NAME"

```
7. Fill in the required fields in `push_image.sh`
8. Run the below command to deploy

Note: The below script will <strong>auto-deploy</strong> the infrastructure

```bash
bash ./deploy.sh
```

## CI / CD Deployment Setup (Assuming most of the setup is done on Deployment Setup)
1. Sync terraform variables to your github repo using `sync_var.sh {TFVARS_FILE} {REPO_NAME}` 

Example:
```bash 
sync_var.sh test.tfvars Derrick-Png/oil-gnn-prediction
```
2. Add secret (`credentials`) into github repository's secrets

# Github Repo Variables and Secrets Setup
## Secrets
1. GCLOUD_CREDENTIALS
2. TF_API_TOKEN
3. TF_VAR_CREDENTIALS

## Variables
1. TF_VAR_DOCKER_BUILD_PATH
2. TF_VAR_DOCKER_REPO_NAME
3. TF_VAR_PROJECT_ID
4. TF_VAR_PROJECT_REGION
5. TF_VAR_SERVICE_ACCOUNT_ID
6. TF_VAR_SERVICE_NAME




