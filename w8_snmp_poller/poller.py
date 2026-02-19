import argparse
import datetime
import json
import logging
import subprocess
import yaml

def load_config(file): #reading the yaml file
    with open(file, "r", encoding="utf-8") as yml:
        yaml_config = yaml.safe_load(yml)

    if yaml_config is None:
        raise ValueError("Config file is empty")

    return yaml_config

def validate_config():


#def merge_defaults():


#def build_snmpget_cmd():


#def run_snmpget():


#def poll_target():


#def main():

