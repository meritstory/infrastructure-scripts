#!/usr/bin/env python3
import json
import os
import argparse
import sys
import subprocess
import boto3

# Define and parse the arguments supported by this tool
parser = argparse.ArgumentParser(description='This tool fetches paramters from a provided AWS SSM namespace and substitutes their values instead of placeholders in the specified environment variables file.')
parser.add_argument(dest='ssm_path', help="SSM path from which to fetch variables", type=str)
parser.add_argument(dest='env_file', help="Destination env file in which variable placeholders should be replaced", type=str)
parser.add_argument('--aws-profile', help="AWS profile to use. Will use the \"default\" profile if not specified.", type=str)
args=parser.parse_args()
if hasattr(args, "help"):
    parser.print_help()

# Validate arguments
if not os.path.exists(args.env_file):
    sys.exit(f'Environment file "{args.env_file}" does not exist')

# Create a new environment for storing the parameters
myenv = os.environ.copy()

# Get the parameters from AWS SSM and store them in the environment
session = boto3.session.Session() if args.aws_profile is None else boto3.session.Session(profile_name=args.aws_profile)
client = session.client('ssm')
paginator = client.get_paginator('get_parameters_by_path')
response_iterator = paginator.paginate(
    Path=args.ssm_path,
    Recursive=False,
    WithDecryption=True,
    PaginationConfig={
        'PageSize': 10
    }
)
for page in response_iterator:
    for param in page['Parameters']:
        itemName = param['Name'].split("/")[-1]
        myenv[itemName] = param['Value']

# Usage of envsubst from https://stackoverflow.com/a/61538920/1442776
envSubstCommand = f'originalfile="{args.env_file}"; \
                    tmpfile=$(mktemp); \
                    cp --attributes-only --preserve $originalfile $tmpfile; \
                    cat $originalfile | envsubst > $tmpfile && mv $tmpfile $originalfile;'
ret = subprocess.run(envSubstCommand, capture_output=True, shell=True, env=myenv)
if ret.returncode == 0:
    print("Environment variables were successfully substituted from AWS SSM")
else:
    sys.exit("Error: " + ret.stderr.decode())
