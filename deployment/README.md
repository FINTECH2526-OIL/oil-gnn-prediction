# Requirements
1. Docker Desktop
2. Terraform
3. GCloud CLI (For triggering cloud run deployment)

# Deployment Setup (Outside of main email used)
1. Create a Service Acocunt (take note of the unique id) and grant it the below mentioned roles
    - Cloud Run Admin
    - Cloud Run Source Developer
    - Artifact Registry Administrator 
    - Create Service Account
    - Service Account User
2. Run the below command to enable the required APIs (If any are missed out, please raise an issue)
```bash
gcloud services enable cloudresourcemanager.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable iam  
```
2. From the service account, create a key in JSON
3. Run the following script to obtain a minifed json output
```bash
python -c 'import json, sys;output="";output=json.dumps(json.load(sys.stdin), indent=None,separators=(",",":"));sys.stdout.write(output.replace("\"","\\\"").replace("\\n","\\\\n"))' < {INSERT_JSON_FILE_HERE}

(For Adding as a Repo Env Variable into Github Repo)
python -c 'import json, sys;output="";output=json.dumps(json.load(sys.stdin), indent=None,separators=(",",":"));sys.stdout.write(output)' < {INSERT_JSON_FILE_HERE}

```
4. Put the output into a var file (ex. main.tfvars) as credentials and fill in the rest of the required variables

Template of tfvars file
```terraform
credentials        = "INSERT_CRED_OUTPUT_HERE"
project_id         = "INSERT_PROJECT_ID"
project_region     = "INSERT_PROJECT_REGION"
service_account_id = "INSERT_ACCOUNT_ID"
docker_repo_name   = "INSERT_REPO_NAME"
service_name       = "INSERT_CLOUD_RUN_SERVICE_NAME"

```
5. Fill in the required fields in `push_image.sh`
6. Run the below command to deploy

Note: The below script will <strong>auto-deploy</strong> the infrastructure

```bash
bash ./deploy.sh
```

