#!/bin/bash
# $1 is the service account key file path
terraform init
terraform apply -var-file="main.tfvars" -auto-approve -lock=false
source push_image.sh $1
