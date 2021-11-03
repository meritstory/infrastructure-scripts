#!/usr/bin/env python3
import json
import os
import argparse
import sys
import subprocess

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
    print(f'Environment file "{args.env_file}" does not exist')
    sys.exit()

# Get the parameters from AWS SSM as JSON
profile = f"--profile {args.aws_profile}" if args.aws_profile is not None else "";
command = f'aws {profile} ssm get-parameters-by-path --path {args.ssm_path} --query "Parameters[*].{{Name:Name,Value:Value}}" --with-decryption --no-paginate'
pipe = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
jsons,err = pipe.communicate()
if (pipe.returncode != 0):
    print(err)
    sys.exit()
json = json.loads(jsons)

# Create a new environment and extend it with fetched SSM variables
myenv = os.environ.copy()
for item in json:
    itemName = item['Name'].split("/")[-1]
    myenv[itemName] = item['Value']

# Usage of envsubst from https://stackoverflow.com/a/61538920/1442776
envSubstCommand = f'originalfile="{args.env_file}"; \
                    tmpfile=$(mktemp); \
                    cp --attributes-only --preserve $originalfile $tmpfile; \
                    cat $originalfile | envsubst > $tmpfile && mv $tmpfile $originalfile;'
ret = subprocess.run(envSubstCommand, capture_output=True, shell=True, env=myenv)
if ret.returncode == 0:
    print("Environment variables were successfully substituted from AWS SSM")
else:
    print("Error: " + ret.stderr.decode())
