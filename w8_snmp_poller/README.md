About the application:
This application is a lightweight SNMP polling tool written in Python. It reads a YAML configuration file containgning default settings and a list of network targets, polls each target  within a defined time budget, handles retries on timeouts, performs fail-fast on authentication error, and outputs structured JSON results. The program is designed to behave predictably under network delays, unreachable devices, and misconfigurations.

Files:
*Poller.py
The main application. Handles configuration loading, validation, SNMP polling, retry logic, time-budget enforcement, JSON output, and exit codes.

*config.yml
The configuration file defining default values (timeouts, retries, OIDs) and the list of SNMP targets to poll.

*test_config.py
Unit tests verifying that the configuration validation behaves correctly for valid and invalid YAML files. 

*README.md
Documentation describing the application, structure, methods, installation, and usage. 

Methods:
load_config(path)
Input: file path (string)
Output: Python dictionary
Description: load and parses the YAML configuration file. Raises an error if the file is empty.

validate_config(cfg)
Input: configuration dictionary
Output: none (raises ValueError on invalid config)
Description: ensures that required fields exist, types are correct, numeric values are positive, and targets contain valid entries. Prevents the application from running with invalid settings.

merge_defaults(defaults, target)
Input: two dictionaries
Output: merged dictionary
Description: combines default settings with target-specific overrides. Target values replace defaults when present. 

build_snmpget_cmd(target, oid)
Input: target dictionary, OID string
Output: list of command argumetns
Description: constructs the snmpget command for a specific target and OID. SNMP retries are disabled (-r 0) because retry logic is handled in Python. 

run_snmpget(cmd, timeout_s)
Input: command list, timeout(float)
Output: (returncode, stdout, stderr)
Description: executes the SNMP command using subprocess.run(). Returns "timeout" on Python-level timeout. 

poll_target(merged_dt)
Input: merged target dictionary.
Output: result dictionary for one target.
Description: polls all OIDs for a target within a time budget. Handles: retries on timeout/unreachable, fail-fast on authentication errors, marking remaining OIDs as skipped wgen budget is exceeded, collecting results and determining target status. 
Dependencices: uses build_snmpget_cmd(), run_snmpget(), and time-budget logic. 

main()
Input: command-line arguments
Output: JSON file or stdout + exit code
Description: Coordinates the entire application. It parses CLI arguments, loads and validates config, polls all targets, writes JSON output, sets exit code (0/1/2) based on results.

Installation:
Requirements are Linux enviornment, Python 3.8 or newer, Net-SNMP tools (snmpget), Python package: pyyaml

Install dependencies
sudo apt-get update
sudo apt-get install -y snmp python3 python3-venv

python3 -m venv .venv
source .venv/bin/activate
pip install pyyaml

Running:
Basic usage: python3 poller-py --config config.yml --out result.json
Output to stdout: python3 poller.py --config config.yml --out -
Change log level: python3 poller.py --config config.yml --out result.json --log-level DEBUG

Exit codes:
0 - all targets succeeded
1 - partial success (some OIDs failed)
2 - total failure or invalid configuration. 