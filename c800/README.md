# Cisco AI Pods UCS C800-Series Server Configuration Guide

## Top Level Documents

- [Cisco AI Pods Runbook](../guide_cisco_ai_pods_runbook.md)
- [Main README](../README.md)
- [Prepare the Environment](../guide_prepare_the_environment.md)

## Table of Contents

- [Overview](#overview)
- [Supported Platforms](#supported-platforms)
- [Prerequisite Checklist](#prerequisite-checklist)
- [Folder Contents](#folder-contents)
- [Deployment](#deployment)
- [Sensitive Variables Reference](#sensitive-variables-reference)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

## Overview

This folder provides the Redfish/BMC automation configuration for Cisco UCS C800-series rack servers deployed in Cisco AI Pods.

Configuration is applied via `ucs_bmc.py` from the `intersight-tools` toolkit against the `main.fsai.yaml` model file in this folder. The tool connects to each server BMC using the Redfish API and applies BIOS, networking, NTP, LDAP, local user, and device connector settings defined in the model.

⚠️ **DEPLOYMENT ORDER:** BMC configuration can be performed any time after network connectivity to the BMC management interfaces is confirmed.

[Back to Table of Contents](#table-of-contents)

## Supported Platforms

This configuration folder supports the following Cisco UCS servers:

| Platform | CPU | Role |
|----------|-----|------|
| UCS C845 M8 | AMD EPYC | GPU-optimized AI/ML compute |
| UCS C885A M8 | AMD EPYC | High-density GPU AI/ML compute (HGX) |
| UCS C880 M7 | Intel Xeon | High-memory AI/ML compute |

All three platforms use the same `ucs_bmc.py` workflow and `c800:` model structure. Platform-specific BIOS and hardware settings are controlled through the `shared_settings.bios` block in `main.fsai.yaml`.

[Back to Table of Contents](#table-of-contents)

## Prerequisite Checklist

- [ ] Network connectivity to each server's BMC management interface confirmed
- [ ] Python virtual environment prepared per [Prepare the Environment](../guide_prepare_the_environment.md)
- [ ] `intersight-tools` repo cloned alongside this repo
- [ ] BMC credentials available for each host

[Back to Table of Contents](#table-of-contents)

## Folder Contents

- `main.fsai.yaml`: Model file defining hosts, BIOS, network, NTP, LDAP, and user settings
- `README.md`: This guide

### main.fsai.yaml Structure

```
c800:
  hosts:                         # List of servers to configure
    - hostname: <fqdn>
      api: <bmc-ip>
      ipv4_address: <bmc-ip>
  shared_settings:
    bios: ...                    # BIOS tuning (AMD or Intel specific)
    boot_order: true
    device_connector:            # Intersight device connector claim settings
      intersight:
        organization: <org>
        resource_group: <rg>
    ethernet_interfaces:         # BMC in-band NIC settings
    ldap:                        # LDAP/AD integration
    local_user:                  # Local BMC user accounts
    ntp:                         # NTP servers and timezone
  username: root
```

[Back to Table of Contents](#table-of-contents)

## Deployment

### Step 1: Activate Python Virtual Environment

```bash
source .venv/bin/activate
```

### Step 2: Change to intersight-tools directory

```bash
cd intersight-tools
```

### Step 3: Export sensitive environment variables

```bash
# Intersight API credentials (for device connector claim)
export intersight_api_key_id="<api-key-id>"
export intersight_secret_key="~/Downloads/SecretKeyv3.txt"

# BMC LDAP bind password
export binding_parameters_password="<ldap-bind-password>"

# BMC local user passwords (number matches local_user password index in vars)
export local_user_password_1="<secure-password>"
export local_user_password_2="<secure-password>"

# SNMP credentials
export snmp_auth_password_1="<secure-password>"
export snmp_auth_password_2="<secure-password>"
export snmp_privacy_password_1="<secure-password>"
export snmp_privacy_password_2="<secure-password>"
```

### Step 4: Run the BMC configuration tool

**Linux:**

```bash
./ucs_bmc.py -y ../Cisco-AI-Pods/c800/main.fsai.yaml
```

**Windows:**

```powershell
python .\ucs_bmc.py -y ..\Cisco-AI-Pods\c800\main.fsai.yaml
```

[Back to Table of Contents](#table-of-contents)

## Sensitive Variables Reference

The following environment variables are consumed by `ucs_bmc.py`. Only export the variables relevant to the settings defined in your `main.fsai.yaml`.

| Variable | Used For |
|----------|----------|
| `intersight_api_key_id` | Device connector Intersight claim |
| `intersight_secret_key` | Device connector Intersight claim |
| `binding_parameters_password` | LDAP bind password |
| `local_user_password_1` | BMC local user (index 1) |
| `local_user_password_2` | BMC local user (index 2) |
| `snmp_auth_password_1` | SNMP auth password (index 1) |
| `snmp_privacy_password_1` | SNMP privacy password (index 1) |

[Back to Table of Contents](#table-of-contents)

## Verification

After the tool completes, confirm configuration was applied on each BMC:

```bash
# Confirm BMC reachability
ping <bmc-ip>

# Verify Redfish endpoint
curl -k -s https://<bmc-ip>/redfish/v1 | python3 -m json.tool

# Check NTP settings
curl -k -s https://<bmc-ip>/redfish/v1/Managers/bmc \
  --user root:<password> | python3 -m json.tool | grep -i ntp

# Check BIOS settings
curl -k -s https://<bmc-ip>/redfish/v1/Systems/1/Bios \
  --user root:<password> | python3 -m json.tool
```

For C885A HGX nodes, verify GPU BMC synchronization:

```bash
curl -k -X POST \
  "https://<bmc-ip>/redfish/v1/Managers/bmc/Actions/Oem/OemManager.SyncGpuDateTime" \
  --user "root:<password>" \
  --header "Content-Type: application/json" \
  --data '{"ActionType": "SyncImmediately"}'
```

[Back to Table of Contents](#table-of-contents)

## Troubleshooting

- Redfish connection refused or timeout:
  - Verify BMC IP is reachable and fully booted.
  - Confirm management network connectivity.
- Authentication failure:
  - Check BMC username in `main.fsai.yaml` (`username:` key).
  - Verify password indexes match exported environment variables.
- LDAP not applying:
  - Confirm `binding_parameters_password` is exported.
  - Verify LDAP server is reachable from BMC network.
- Device connector not claiming:
  - Confirm `intersight_api_key_id` and `intersight_secret_key` are exported and valid.
  - Confirm the organization and resource group names in `main.fsai.yaml` match your Intersight tenant.

Useful diagnostic commands:

```bash
# BMC system event log
curl -k https://<bmc-ip>/redfish/v1/Systems/1/LogServices/EventLog/Entries \
  --user root:<password>

# BMC manager log
curl -k https://<bmc-ip>/redfish/v1/Managers/bmc/LogServices/Log1/Entries \
  --user root:<password>
```

[Back to Table of Contents](#table-of-contents)
