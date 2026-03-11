# SNMP Poller


# About:
This application is a lightweight SNMP poller written in Python.

It reads a YAML configuration file that contains default settings and a list of network targets. For each target, the program performs SNMP GET requests and collects the results.

The poller includes retry handling, timeout control and a per-target time budget. Results are written as structured JSON output.

# Files:
poller.py
Main application. Handles configuration loading, validation, SNMP polling, retry logic, time-budget enforcement, JSON output, and exit codes.

config.yml
Configuration file defining default values (timeouts, retries, OIDs) and the list of SNMP targets.

test_config.py
Unit tests verifying configuration validation for valid and invalid configs. 

README.md
Documentation for installation, structure, and usage. 

# Methods:
load_config(path)
 * Input: file path (string)
 * Output: Python dictionary
 * Description: load and parses the YAML configuration file. Raises an error if the file is empty.

validate_config(cfg)
 * Input: configuration dictionary
 * Output: none (raises ValueError on invalid config)
 * Description: ensures that required fields exist, types are correct, numeric values are positive, and targets contain valid entries. This prevents the application from running with invalid settings.

merge_defaults(defaults, target)
 * Input: two dictionaries
 * Output: merged dictionary
 * Description: combines default settings with target-specific overrides. Target values replace defaults when present. 

build_snmpget_cmd(target, oid)
 * Input: target dictionary, OID string
 * Output: list of command argumetns
 * Description: constructs the snmpget command for a specific target and OID. SNMP retries are disabled (-r 0) because retry logic is handled in Python. 

run_snmpget(cmd, timeout_s)
 * Input: command list, timeout(float)
 * Output: (returncode, stdout, stderr)
 * Description: executes the SNMP command using subprocess.run(). Returns "timeout" on Python-level timeout. 

poll_target(merged_t)
 * Input: merged target dictionary  
 * Output: result dictionary for one target
 * Description: Polls all configured OIDs for a target device within a defined time budget.

The function handles:
 * retries when a timeout occurs
 * unreachable devices
 * authentication errors (stos polling immediately)
 * skipping remaining OIDs if the time budget is exceeded

It also collects the results and determines the final status of the target.

main()
 * Input: command-line arguments
 * Output: JSON file or stdout + exit code
 * Description: Coordinates the entire application. It parses CLI arguments, loads and validates config, polls all targets, writes JSON output, sets exit code (0/1/2) based on results.

# Installation:
Requirements:
 * Linux enviornment
 * Python 3.8+
 * Net-SNMP tools (snmpget)
 * Python package: pyyaml

Install dependencies:
```
 sudo apt-get update
 sudo apt-get install -y snmp python3 python3-venv
```

Create enviornment:
```
 python3 -m venv .venv
 source .venv/bin/activate
 pip install pyyaml
```

# Running:
Basic usage: 
```
python3 poller-py --config config.yml --out result.json
```
Output to stdout:
```
python3 poller.py --config config.yml --out -
```

Arguments:

--config

Specifies the path to the YAML configuration file.


--out

Defines the output location for the JSON results.
Use - to send the output to stdout instead of writing to a file.


--log-level
Controls the amount of logging information printed to the terminal


   * INFO: Normal runtime information such as when a targets start and finish polling. 
   * WARNING: Indicates potential issues such as timeouts or retries. 
   * ERROR: Serious problems such as authentication failures or invalid configuration.

Exit codes:

0 - all targets succeeded

1 - partial success (some OIDs failed)

2 - total failure or invalid configuration. 


# Program Flow

The application runs in the following order:

main

↓

load_config

↓

validate_config

↓

merge_defaults

↓

poll_target

↓

   build_snmpget_cmd
   
   ↓
   
   run_snmpget

↓

write JSON output

# Summary
This SNMP poller reads a YAML configuration file, polls network devices using SNMP GET requests, and outputs the results as structured JSON.

The application includes retry logic, timeout handling and configuration validation, making it suitable for automated monitoring and network diagnostics.
