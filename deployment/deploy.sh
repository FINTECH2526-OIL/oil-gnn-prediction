#!/bin/bash
terraform init
terraform apply -var-file="main.tfvars" -auto-approve -lock=false
source push_image.sh
