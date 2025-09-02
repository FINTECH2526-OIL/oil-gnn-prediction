# Deployment Setup (Outside of main email used)
1. Create a Service Acocunt (take note of the unique id) and grant it the below mentioned roles
    - Cloud Run Admin
    - Cloud Build Creator
    - Storage Object Creator
    - Storage Object Viewer
    - Create Service Account
    - Service Account User
2. From the service account, create a key in JSON
3. Run the following script to obtain a minifed json output
```bash
python -c 'import json, sys;output="";output=json.dumps(json.load(sys.stdin), indent=None,separators=(",",":"));sys.stdout.write(output.replace("\"","\\\"").replace("\\n","\\\\n"))' < {INSERT_JSON_FILE_HERE}
```
4. Put the output into a var file (ex. main.tfvars) as credentials
5. Fill in the rest of the required variables (ex. project id and region)
6. Enable the following APIs via CLI
```bash
gcloud services enable iam  
```

# To plan

# To Deploy

```bash
terraform apply -var-file="{INSERT_VAR_FILE_HERE}"
```

Include `-auto-approve` to allow for deployment without confirmation 

