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

    for oid in default_oids:
        if not isinstance(oid, str):
            raise ValueError("oid is not a string")
        if len(oid) == 0:
            raise ValueError("oid is empty")

    if not isinstance(value_targets, list):
        raise ValueError("targets is not a list")

    if len(value_targets) == 0:
        raise ValueError("List is empty")

    required_field = ["ip", "name"]

    for target in value_targets:
        if not isinstance(target, dict): #controlls that target is a dict
                raise ValueError(f"{target} is not a dict")
        if "oids" in target:
            if not isinstance(target["oids"], list):
                raise ValueError("oids is not a list")
            if len(target["oids"]) == 0:
                raise ValueError("the list of oids is empty")
            for oid in target["oids"]:
                 if not isinstance(oid, str):
                    raise ValueError("oids is not a string")
                 if oid == "":
                      raise ValueError("oids is empty")
                     
        for field in required_field: #controls requierd fields
            if field not in target:
                raise ValueError(f"{field} is missing in target")
            if not isinstance(target[field], str):
                raise ValueError (f"{field} is not a string!")
            if target[field] == "":
                raise ValueError (f"{field} is empty!")
            


print(validate_config(load_config("config.yml")))

#def merge_defaults(defaults, target):


#def build_snmpget_cmd():


#def run_snmpget():


#def poll_target():


#def main():

