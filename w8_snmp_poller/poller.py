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
    if not isinstance(cfg, dict) : #if it is not a dict
        raise ValueError("Config must be a dict")

    if "targets" not in cfg:
        raise ValueError("targets are missing")

    if "defaults" not in cfg:
        raise ValueError("defaults are missing")

    value_defaults = cfg["defaults"]
    value_targets = cfg["targets"]

    if not isinstance(value_defaults, dict):
        raise ValueError("default is not a dict")

    if "oids" not in value_defaults:
        raise ValueError("No oids")

    default_oids = value_defaults["oids"]

    if not isinstance(default_oids, list) or len(default_oids) == 0:
        raise ValueError("defaults.oids must be a non-empty list")

    if not isinstance(value_targets, list):
        raise ValueError("targets is not a list")

    if len(value_targets) == 0:
        raise ValueError("List is empty")

    required_targets = ["ip", "name"]

    for target in required_targets:
        if target not in value_targets:
            raise ValueError(f"{target} is missing in target")

target in value_targets:
        if not isinstance(target, dict):
            raise ValueError("target is no a dict")

        if not isinstance(target["name"], str) or target["name"] == "":
            raise ValueError("name must be a non-empty string")

        if not isinstance(target["ip"], str) or target["ip"] == "":
            raise ValueError("ip must be a non-empty string")
        for target in 
print(validate_config(load_config("config.yml")))

#def merge_defaults(defaults, target):


#def build_snmpget_cmd():


#def run_snmpget():


#def poll_target():


#def main():

