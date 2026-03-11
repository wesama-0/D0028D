import argparse
import datetime
import json
import logging
import subprocess
import sys
import time
import yaml

# function: load_config
# description: Loads and parses the YAML configuration file.
# input: path (str) - path to the YAML configuration file.
# output: dict - parsed configuration dictionary.
# raises: ValueError if the configuration file is empty
def load_config(path): #reading the yaml file
    with open(path, "r", encoding="utf-8") as yml: #load and parse the YAML configuration file
        cfg = yaml.safe_load(yml)

    if cfg is None: #if the config file is empty
        raise ValueError("Config file is empty")

    return cfg

# function: validate_config
# description: validates the structure and content of the configuration. 
# ensures required fields exist, types are correct and numeric values are valid.
# input: cfg(dict) - configuration dictionary. 
# output: none
# raises: ValueError if the config is invalid
def validate_config(cfg): #validate config structure
    if not isinstance(cfg, dict) : #if config is not a dict
        raise ValueError("Config must be a dict")

    if "targets" not in cfg: #target have to be in the config
        raise ValueError("targets are missing")

    if "defaults" not in cfg: #defaults have to be in the config
        raise ValueError("defaults are missing")

    defaults = cfg["defaults"]
    targets = cfg["targets"]

#validate defaults
    if "timeout_s" not in defaults: #checking so timeouts are in defaults and that it is a number and biggger than 0
        raise ValueError("timeout_s are missing")
    if not isinstance(defaults["timeout_s"], (int, float)) or defaults["timeout_s"] <= 0: 
        raise ValueError("timeout_s must be a number > 0")
    
    if "target_budget_s" not in defaults: #checking so target budget/s are in defaults and that it is a number and bigger than 0
        raise ValueError("target_budget_s are missing")
    if not isinstance(defaults["target_budget_s"], (int, float)) or defaults["target_budget_s"] <= 0:
        raise ValueError("target_budget_s must be a number > 0")

    if defaults["target_budget_s"] < defaults["timeout_s"]: #budget must be >= timeout
        raise ValueError("target_budget_s has to be >= timeout_s")

    if "retries" not in defaults: #makeing sure retries is a whole positive number and are in defaults
        raise ValueError("retries are missing")   
    if not isinstance(defaults["retries"], int) or defaults["retries"] < 0:
        raise ValueError("retires have to be a whole and positive number")

    if "oids" not in defaults or not isinstance(defaults["oids"], list) or len(defaults["oids"]) == 0: #standard-OIDs
        raise ValueError("No oids in the default part")

#validate targets 
    if not isinstance(targets, list) or len(targets) == 0:
        raise ValueError("targets must be a non-empty list")


    required_field = ["ip", "name", "community"]

    for target in targets:
        #each targegt must be a dictionary
        if not isinstance(target, dict): 
                raise ValueError(f"{target} is not a dict")
        
        #validate required fields for each target             
        for field in required_field: #controls requierd fields
            if field not in target:
                raise ValueError(f"{field} is missing in target")
            if not isinstance(target[field], str):
                raise ValueError (f"{field} is not a string!")
            if target[field] == "":
                raise ValueError (f"{field} is empty!")
        
        #validate optional target-specific OIDs(override defaults)
        if "oids" in target:
            if not isinstance(target["oids"], list) or len(target["oids"]) == 0:
                raise ValueError("target.oids must be a non-empty list ")
                
# function: merge_defaults
# description: combines default config values
# target values override defaults when present
# input: defaults (dict), target (dict)
# output: dict - merged configuration dictionary
def merge_defaults(defaults, target): #merge defaults with target-specific overrides
    effective = defaults.copy() #a new dictionary is returned to avoid modifying the original one
    effective.update(target) #target-specific values override defaults
    return effective
    
# function: build_snmpget_cmd
# description: builds the SNMPGET command used to query an OID on a target device
# input: target(dict), oid (str)
# output: list - command arguments for subprocces.run().
def build_snmpget_cmd(target, oid): #build SNMP command
    cmd = []
    cmd.append("snmpget")
    cmd.append("-v2c") 
    cmd.append("-c")
    cmd.append(target["community"])
    cmd.append("-t") #timeout per request
    cmd.append(str(target["timeout_s"])) 
    cmd.append("-r") #SNMPGET retries 
    cmd.append("0") #SNMPGET must not retry
    cmd.append(target["ip"]) #target IP
    cmd.append(oid) #OID to get
    
    return cmd

# function: run_snmpget
# description: executes the SNMPGET command and captures the results
# input: cmd (list), timeout_s (float)
# output: tuple - (returncode, stdout, stderr)
def run_snmpget(cmd, timeout_s): #run SNMP command
    try:
        result = subprocess.run(
            cmd,
            capture_output=True, #saveing the program writing out in variables instead of writing it directly in the terminal
            text=True, #makeing the output to strings (text) instead of bytes
            timeout=timeout_s #interupts if it take longer time than timeout_s seconds
        )

        return result.returncode, result.stdout.strip(), result.stderr.strip() 

    except subprocess.TimeoutExpired: #Python-timeout (snmpget dosen´t respond on time)
        return 124, "", "timeout"

# function: poll_target
# description: polls all configured OIDs for a target device within a time budget
# handles retries, timeouts, authentication errors and collects results
# input: merged_dt (dict) - merged target configuration
# output: dict - result object containing status, counts and OID results
def poll_target(merged_dt): #poll a single target within a time budget.
    
    results = []
    ok_count = 0
    fail_count = 0

    start_time = time.monotonic()
    budget_s = float(merged_dt["target_budget_s"])

    logging.info(f"Starting target {merged_dt['name']} ({merged_dt['ip']})")

    for oid in merged_dt["oids"]:
        #per-target budget check (stop if runing out of time)
        elapsed = time.monotonic() - start_time
        if elapsed >= budget_s: #record that stopped early due to budget
            logging.warning(f"{merged_dt['name']}: budget exceeded, skipping remaining OIDs")

            #marking all remaining OIDs as skipped
            remaining = merged_dt["oids"][merged_dt["oids"].index(oid):]
            for o in remaining:
                results.append({
                    "oid": o,
                    "status": "skipped",
                    "error": "target budget exceeded"
                })
            break

        cmd = build_snmpget_cmd(merged_dt, oid)
        
        #retry-loop (only timeout/unreachable)
        attempts = merged_dt["retries"] + 1
        for attempt in range(attempts):
            rc, output_text, error_text = run_snmpget(cmd, merged_dt["timeout_s"])

            err_l = (error_text or "").lower()
            is_timeout = (error_text == "timeout") or ("timeout" in err_l)

        if rc == 0: #if it is success
            ok_count += 1
            results.append({
                "oid": oid,
                "status": "ok",
                "value": output_text
            })
            break
        
        if is_timeout and attempt < attempts -1: #only retries at timeout/unreachable
            logging.warning(f"{merged_dt['name']} OID {oid}: timeout, retrying...")
            continue
        
        if "authentication" in err_l or "unknown user" in err_l: #fail-fast on auth
            logging.error(f"{merged_dt['name']}: authentication failure")
            fail_count += 1
            results.append({
                "oid": oid,
                "status": "fail",
                "error": error_text
            })
        #interupt the entire target directly
            duration_s = round(time.monotonic() - start_time, 3)
            return {
                "name": merged_dt["name"],
                "ip": merged_dt["ip"],
                "status": "failed",
                "ok_count": ok_count,
                "fail_count": fail_count,
                "duration_s": duration_s,
                "results": results,
            }
        
        #other fails (no retry)
        fail_count += 1
        results. append ({
            "oid": oid,
            "status": "fail",
            "error": error_text
        })
        break

    #target done
    duration_s = round(time.monotonic() - start_time, 3)

    #determine status
    if ok_count > 0 and fail_count == 0:
        status = "ok"
    elif ok_count > 0:
        status = "partial"
    else:
        status = "failed"
    
    logging.info(f"Finished target {merged_dt['name']} status={status} duration={duration_s}s")

    return {
        "name": merged_dt["name"],
        "ip": merged_dt["ip"],
        "status": status,
        "ok_count": ok_count,
        "fail_count": fail_count,
        "duration_s": duration_s,
        "results": results,
    }

# function: main
# description: entry point of the application
# handles CLI arguments, load and validates configuration, polls all targets, writes JSON output and sets exit codes. 
# input: command-line arguments (--config, --out, --log-level)
# output: JSON output + program exit code
def main(): #mainprogram
    #CLI, logging, doing all of the targets, JSON-output and exit codes
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()
    
    #basic logging setup
    logging.basicConfig(
        level=args.log_level.upper(),
        format="%(asctime)s %(levelname)s %(message)s"
    )
    #load and validate config
    try:
        cfg = load_config(args.config)
        validate_config(cfg)
    except ValueError as e:
        logging.error(f"Invalid configuration: {e}")
        sys.exit(2) #config error --> exit code 2
    
    defaults = cfg["defaults"]
    targets = cfg["targets"]
    
    logging.info(f"Starting run with {len(targets)} targets")

    run_start = time.time()
    all_results = []

    #poll all targets
    for target in targets:
        merged_dt = merge_defaults(defaults, target)

        #ensure OIDs exist (target override else defaults)
        if "oids" not in target:
            merged_dt["oids"] = defaults["oids"]
        
        result = poll_target(merged_dt)
        all_results.append(result)
    
    #exit code logic
    any_ok = any(t["ok_count"] > 0 for t in all_results)
    any_fail = any(t["fail_count"] > 0 for t in all_results)

    if any_ok and not any_fail:
        exit_code = 0
    elif any_ok and any_fail:
        exit_code = 1
    else:
        exit_code = 2
    
    #JSON output
    output = {
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        "config":args.config,
        "duration_s": round(time.time() - run_start, 3),
        "targets": all_results,
    }

    #writing JSON to file or stdout
    if args.out == "-":
        print(json.dumps(output, indent=2))
    else:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)
    
    logging.info(f"Run complete. Exit code {exit_code}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
