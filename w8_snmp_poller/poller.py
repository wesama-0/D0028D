import argparse
import datetime
import json
import logging
import subprocess
import yaml

def load_config(path): #reading the yaml file
    with open(path, "r", encoding="utf-8") as yml:
        cfg = yaml.safe_load(yml)

    if cfg is None:
        raise ValueError("Config file is empty")

    return cfg

def validate_config(cfg):
    if not isinstance(cfg, dict) : #if it is not a dictionary
        raise ValueError("Config must be a dictionary")

    if "targets" not in cfg:
        raise ValueError("targets are missing")

    if "defaults" not in cfg:
        raise ValueError("defaults are missing")

    value_defaults = cfg["defaults"]
    value_targets = cfg["targets"]

    if not isinstance(value_defaults, dict):
        raise ValueError("default is not a directory")

    if not isinstance(value_targets, list):
        raise ValueError("targets is not a list")

    for target in value_targets:
        if not isinstance(target, dict):
            raise ValueError("target is no a dict")

    if "name" not in target:
        raise ValueError("name is not in target")

    if "ip" not in target:
        raise ValueError("ip is not in target")

#def merge_defaults(defaults, target):


#def build_snmpget_cmd():


#def run_snmpget():


#def poll_target():


#def main():

