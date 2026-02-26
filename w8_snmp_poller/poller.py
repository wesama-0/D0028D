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
        result = subprocess.run(
            cmd,
            capture_output=True, #saveing the program writing out in variables instead of writing it directly in the terminal
            text=True, #makeing the output to strings (text) instead of bytes
            timeout=timeout_s #interupts if it take longer time than timeout_s seconds
        )

        return (
            result.returncode,
            result.stdout.strip(),
            result.stderr.strip() 
            )
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    
def poll_target(merged_dt): #poll a single target within a time budget.
    
    results = []
    ok_count = 0
    fail_count = 0

    start_time = time.monotonic()
    budget_s = float(merged_dt["target_budget_s"])

    for oid in merged_dt["oids"]:
        #per-target budget check (stop if runing out of time)
        elapsed = time.monotonic() - start_time
        if elapsed >= budget_s: #record that stopped early due to budget
            results.appen({
                "oid": oid,
                "status": "skipped",
                "error": "target budget exceeded"
            })
            break

        cmd = build_snmpget_cmd(merged_dt, oid)
        rc, out, err = run_snmpget(cmd, merged_dt["timeout_s"])

        if rc == 0: #if it is ok
            ok_count += 1
            results.append({
                "oid": oid,
                "status": "ok",
                "value": out
            })
        
        else: #if it fails
            fail_count += 1
            results.append({
                "oid": oid,
                "status": "fail",
                "error": err,
                "rc": rc,
            })

    duration_s = time.monotonic() - start_time

    if ok_count > 0 and fail_count == 0:
        status = "ok"
    
    if ok_count > 0 and fail_count > 0:
        status = "partial"
        
    if ok_count == 0:
        status = "failed"
        
    return {
        "name": merged_dt.get("name"),
        "ip": merged_dt.get("ip"),
        "status": status,
        "ok_count": ok_count,
        "fail_count": fail_count,
        "duration_s": round(duration_s, 3),
        "results": results,
    }

def main():
    parser1 = argparse.ArgumentParser()
    parser1.add_argument("--config", required=True, help="Path to configuration file")
    args = parser1.parse_args()
   
    cfg = load_config(args.config)
    validate_config(cfg)

    defaults = cfg["defaults"]
    targets = cfg["targets"]

    for target in targets:
        merged_dt = merge_defaults(defaults, target)
        if "oids" not in target:
            merged_dt["oids"] = defaults["oids"]
        result = poll_target(merged_dt)
        for oid in merged_dt["oids"]:
            cmd = build_snmpget_cmd(merged_dt, oid)
            rc, output_text, error_text = run_snmpget(cmd, merged_dt["timeout_s"])
            print("CMD:", cmd)
            print("RC:", rc)
            print("OUT:", output_text)
            print("ERR:", error_text)
            print("---")

if __name__ == "__main__":
    main()