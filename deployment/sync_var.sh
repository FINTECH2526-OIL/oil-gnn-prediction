#!/bin/bash

# This is for syncing terraform variables / secrets automatically on the repository
# NOTE: DEFAULT REPO IS THE REPO THIS SCRIPT IS IN
# THIS SCRIPT ONLY SYNCS VAR BECAUSE THERE IS DIFFICULTY SYNCING SECRETS

IGNORE_VARS="credentials some_other_vars"
TFVARS_FILE=$1
GITHUB_REPO=$2


# Read variables from the tfvars file, ignoring specified ones
while IFS='=' read -r var_name var_value; do
    # Remove leading/trailing whitespace and quotes
    var_name=$(echo "$var_name" | xargs)
    var_value=$(echo "$var_value" | (xargs || true) | sed 's/^"//;s/"$//')

    # Check if the variable should be ignored
    if [[ ! " ${IGNORE_VARS[@]} " =~ " ${var_name} " ]]; then
        echo "Syncing variable '$var_name' to value: $var_value"
        # You can use these variables in your script, e.g., export "$var_name=$var_value"
        gh variable set TF_VAR_$var_name --body "$var_value" --repo $GITHUB_REPO
    fi
done < "$TFVARS_FILE"