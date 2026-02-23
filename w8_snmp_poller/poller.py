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

    if "targets" not in cfg: #target have to be in the config
        raise ValueError("targets are missing")

    if "defaults" not in cfg: #defaults have to be in the config
        raise ValueError("defaults are missing")

    defaults = cfg["defaults"]
    targets = cfg["targets"]
#validates default structure
    if not isinstance(defaults, dict):
        raise ValueError("default is not a dict")

    if "timeout_s" not in defaults: #checking so timeouts are in defaults and that it is a number
        raise ValueError("timeout_s are missing")
    if not isinstance(defaults["timeout_s"], (int, float)) or defaults["timeout_s"] <= 0:
        raise ValueError("timeout_s must be a number > 0")
    
    if "target_budget_s" not in defaults: #checking so timeouts are in defaults and that it is a number
        raise ValueError("target_budget_s are missing")
    if not isinstance(defaults["target_budget_s"], (int, float)) or defaults["target_budget_s"] <= 0:
        raise ValueError("target_budget_s must be a number > 0")

    if defaults["target_budget_s"] < defaults["timeout_s"]:
        raise ValueError("target_budget_s has to be >= timeout_s")

    if "retries" not in defaults: #makeing sure retries is a whole positive number and are in defaults
        raise ValueError("retries are missing")   
    if not isinstance(defaults["retries"], int) or defaults["retries"] < 0:
        raise ValueError("retires have to be a whole and positive number")

    if "oids" not in defaults:
        raise ValueError("No oids in the default part")

    default_oids = defaults["oids"]

    if not isinstance(default_oids, list) or len(default_oids) == 0:
        raise ValueError("defaults.oids must be a non-empty list")
#ensure all oids are valid strings
    for oid in default_oids:
        if not isinstance(oid, str):
            raise ValueError("oid is not a string")
        if oid == "":
            raise ValueError("oid is empty")

#check OID format (numeric OR symbolic)
        if oid.startswith(".") or oid.endswith("."):
            raise ValueError(f"Invalid OID format: {oid}")
        if " " in oid:
            raise ValueError(f"Invalid OID format: {oid}")

        if oid[0].isdigit():
#numeric OID: digits separated by dots
            parts = oid.split(".")
            if "" in parts:
                raise ValueError(f"Invalid OID format: {oid}")
            for part in parts:
                if not part.isdigit():
                    raise ValueError(f"Invalid OID format: {oid}")
        else:
            #symbolic OID: require at least one dot (e.g. sysUpTime.0)
            if "." not in oid:
                raise ValueError(f"Invalid OID format: {oid}")

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
                
            #check OID format (numeric OR symbolic)
                if oid.startswith(".") or oid.endswith("."):
                    raise ValueError(f"Invalid OID format: {oid}")
                if " " in oid:
                    raise ValueError(f"Invalid OID format: {oid}")
                if oid[0].isdigit():
             #numeric OID: digits separated by dots
                    parts = oid.split(".")
                    if "" in parts:
                        raise ValueError(f"Invalid OID format: {oid}")
                    for part in parts:
                        if not part.isdigit():
                            raise ValueError(f"Invalid OID format: {oid}")
                else:
             #symbolic OID: require at least one dot (e.g. sysUpTime.0)
                    if "." not in oid:
                        raise ValueError(f"Invalid OID format: {oid}")

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
    cmd.append(str(target["timeout_s"]))
    cmd.append("-r")
    cmd.append(str(target["retries"]))
    cmd.append(target["ip"])
    cmd.append(oid)
    
    return cmd
def run_snmpget(cmd, timeout_s):
    try:
        snmp_result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_s
        )
        stdout = (snmp_result.stdout or "").strip()
        stderr = (snmp_result.stderr or "").strip()
        return snmp_result.returncode, stdout, stderr
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    

#def poll_target(target):


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Path to configuration file")
    args = parser.parse_args()
   
    cfg = load_config(args.config)
    validate_config(cfg)

    defaults = cfg["defaults"]
    targets = cfg["targets"]

    for target in targets:
        effective = merge_defaults(defaults, target)
        if "oids" not in target:
            effective["oids"] = defaults["oids"]
        for oid in effective["oids"]:
            cmd = build_snmpget_cmd(effective, oid)
            rc, output_text, error_text = run_snmpget(cmd, effective["timeout_s"])
            print("CMD:", cmd)
            print("RC:", rc)
            print("OUT:", output_text)
            print("ERR:", error_text)
            print("---")

if __name__ == "__main__":
    main()