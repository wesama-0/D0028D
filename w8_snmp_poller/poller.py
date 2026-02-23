import argparse
import datetime
import json
import logging
import subprocess
import yaml

def load_config(path): #reading the yaml file
    with open(path, "r", encoding="utf-8") as yml: #load and parse the YAML configuration file
        cfg = yaml.safe_load(yml)

    if cfg is None: #if the config file is empty
        raise ValueError("Config file is empty")

    return cfg

def validate_config(cfg):
    if not isinstance(cfg, dict) : #if it is not a dict
        raise ValueError("Config must be a dict")

    if "targets" not in cfg:
        raise ValueError("targets are missing")

    if "defaults" not in cfg:
        raise ValueError("defaults are missing")

    defaults = cfg["defaults"]
    targets = cfg["targets"]
#validates default structure
    if not isinstance(defaults, dict):
        raise ValueError("default is not a dict")

    if "timeout_s" not in defaults:
        raise ValueError("timeout_s are missing")
    if not isinstance(defaults["timeout_s"], (int, float)):
        raise ValueError("timeout_s is supposed to be a number")

    if "oids" not in defaults:
        raise ValueError("No oids in the default part")

    default_oids = defaults["oids"]

    if not isinstance(default_oids, list) or len(default_oids) == 0:
        raise ValueError("defaults.oids must be a non-empty list")
#ensure all oids are valid strings
    for oid in default_oids:
        if not isinstance(oid, str):
            raise ValueError("oid is not a string")
        if len(oid) == 0:
            raise ValueError("oid is empty")
#validate targets list
    if not isinstance(targets, list):
        raise ValueError("targets is not a list")

    if len(targets) == 0:
        raise ValueError("List is empty")

    required_field = ["ip", "name", "community"]

    for target in targets:
        #each targegt must be a dictionary
        if not isinstance(target, dict): 
                raise ValueError(f"{target} is not a dict")
        #validate optional target-specific OIDs(override defaults)
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
        #validate required fields for each target             
        for field in required_field: #controls requierd fields
            if field not in target:
                raise ValueError(f"{field} is missing in target")
            if not isinstance(target[field], str):
                raise ValueError (f"{field} is not a string!")
            if target[field] == "":
                raise ValueError (f"{field} is empty!")         

def merge_defaults(defaults, target): #merge target configuration with defualts
    effective = defaults.copy() #a new dictionary is returned to avoid modifying the original one
    effective.update(target) #target-specific values override defaults
    return effective

def build_snmpget_cmd(target, oid):
    cmd = []
    cmd.append("snmpget")
    cmd.append("-v2c")
    cmd.append("-c")
    cmd.append(target["community"])
    cmd.append("-t")
    cmd.append(target["timeout_s"])
    cmd.append("-r")
    cmd.append(target["retries"])
    cmd.append(target["ip"])
    return cmd
  

#def run_snmpget(cmd, timeout_s):
  # subprocess.run([cmd])

#def poll_target(target):


def main():
    cfg = load_config(path)
    validate_config(cfg)

    defaults = cfg["defaults"]
    targets = cfg["targets"]

    for target in targets:
        effective = merge_defaults(defaults, target)
        if "oids" not in target:
            effective["oids"] = defaults["oids"]