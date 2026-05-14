# Cisco AI Pods Intersight Deployment Guide

This folder deploys Cisco UCS GPU Servers (C885A/C880A), Intersight organizations, pools, policies, templates, and profiles using the Python-based deployment workflow.

## Top Level Documents

- [Cisco AI Pods Runbook](../guide_cisco_ai_pods_runbook.md)
- [Main README](../README.md)
- [Best Practices README](../best_practices/README.md)
- [Prepare the Environment](../guide_prepare_the_environment.md)

## Best Practices Phase Navigation

- [Best Practices Index](../best_practices/README.md)
- [Phase 1: Planning and Design](../best_practices/phase-1-planning-and-design.md)
- [Phase 2: Hardware Staging](../best_practices/phase-2-hardware-staging.md)
- [Phase 3: Fabric Configuration](../best_practices/phase-3-fabric-configuration.md)
- [Phase 4A: Compute Provisioning](../best_practices/phase-4-compute-provisioning.md)
- [Phase 4B: GPU Runtime Configuration](../best_practices/phase-4-gpu-configuration.md)
- [Phase 5: Storage Provisioning](../best_practices/phase-5-storage-provisioning.md)
- [Phase 6: Orchestration and Workload](../best_practices/phase-6-orchestration-and-workload.md)

[Back to Table of Contents](#table-of-contents) | [Back to Main README](../README.md)

## Table of Contents

- [Cisco AI Pods Intersight Deployment Guide](#cisco-ai-pods-intersight-deployment-guide)
  - [Top Level Documents](#top-level-documents)
  - [Best Practices Phase Navigation](#best-practices-phase-navigation)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Folder Structure](#folder-structure)
  - [Prerequisites](#prerequisites)
  - [Configuration Model](#configuration-model)
  - [Authentication and Sensitive Variables](#authentication-and-sensitive-variables)
  - [Deployment Steps](#deployment-steps)
  - [C885A-M8/C880A-M8 BMC Configuration](#c885a-m8c880a-m8-bmc-configuration)
    - [When to Run It](#when-to-run-it)
    - [How to Run It](#how-to-run-it)
  - [Validation](#validation)
  - [Docs Guidance](#docs-guidance)
    - [Policy Template Guidance](#policy-template-guidance)
    - [Name Prefix and Suffix Conventions](#name-prefix-and-suffix-conventions)
  - [Troubleshooting](#troubleshooting)
  - [Next Steps](#next-steps)

## Overview

Deployment in this folder is Python-based and uses:

- Entrypoint: `deploy_intersight_ucs.py`
- Orchestration: `src/initialize.py` and `src/intersight/configure.py`
- Helpers: `src/shared_functions.py`, template rendering, and sensitive-variable validation
- Model and schema: YAML models validated with `schema/cisco-ai-pods.json`

This deployment reads model files, validates schema/sensitive variables, and then applies changes through Intersight APIs.

[Back to Table of Contents](#table-of-contents) | [Back to Main README](../README.md) | [Back to Best Practices README](../best_practices/README.md)

## Folder Structure

Key files and folders:

- `deploy_intersight_ucs.py`: Python CLI entrypoint
- `src/`: deployment logic and API interactions
- `templates/`: Jinja templates used to build API payloads
- `examples/`: sample model files (`*.ezai.yaml`)
- `docs/`: policy template guidance and naming conventions
- `QA/`: environment-specific test models

[Back to Table of Contents](#table-of-contents) | [Back to Main README](../README.md) | [Back to Best Practices README](../best_practices/README.md)

## Prerequisites

- Python 3.9+ (recommended)
- Network connectivity to Intersight SaaS or appliance endpoint
- Intersight API key ID and secret key
- Environment prepared per [Prepare the Environment](../guide_prepare_the_environment.md)

Install required Python packages (example):

```bash
python3 -m pip install dotmap jinja2 pyyaml requests stringcase json-ref-dict
```

[Back to Table of Contents](#table-of-contents) | [Back to Main README](../README.md) | [Back to Best Practices README](../best_practices/README.md)

## Configuration Model

- Primary model format is `*.ezai.yaml`
- Schema source is `../schema/cisco-ai-pods.json`
- Place environment and policy/profile models under `configuration/`, or your chosen directory passed with `-d`

Common execution pattern:

```bash
python3 deploy_intersight_ucs.py
```

[Back to Table of Contents](#table-of-contents) | [Back to Main README](../README.md) | [Back to Best Practices README](../best_practices/README.md)

## Authentication and Sensitive Variables

Required environment variables:

```bash
export intersight_api_key_id="<apikeyid>"
export intersight_secret_key="/absolute/path/to/SecretKey.pem"
```

Additional sensitive values are discovered from the model and validated during load. Typical examples include local user, LDAP bind, and SNMP credential variables.

[Back to Table of Contents](#table-of-contents) | [Back to Main README](../README.md) | [Back to Best Practices README](../best_practices/README.md)

## Deployment Steps

1. Change into this folder.

```bash
cd Cisco-AI-Pods/intersight
```

2. Run a normal deployment.

```bash
python3 deploy_intersight_ucs.py
```

3. Run in check mode (compare only, no changes).

```bash
python3 deploy_intersight_ucs.py -c
```

4. Optional flags:

```bash
python3 deploy_intersight_ucs.py -d configuration/ -ni -dl 5
```

Where:

- `-d` sets the configuration folder name
- `-ni` runs non-interactive mode
- `-dl` sets debug level
- `-i` ignores TLS server certificate verification

[Back to Table of Contents](#table-of-contents) | [Back to Main README](../README.md) | [Back to Best Practices README](../best_practices/README.md)

## C885A-M8/C880A-M8 BMC Configuration

### When to Run It

Run BMC pre-stage after BMC management interfaces are reachable. It is commonly used to apply BIOS, BMC networking, LDAP, NTP, local user, and device connector settings.

Example:

```bash
examples/C885A/configuration.ezai.yaml
```

### How to Run It

```bash
python3 deploy_intersight_ucs.py -d examples/C885A
```

The above command would run against the `examples/C885A` directory.


[Back to Table of Contents](#table-of-contents) | [Back to Main README](../README.md) | [Back to Best Practices README](../best_practices/README.md)

## Validation

Validation occurs in two places:

- Schema/model load validation before execution
- Sensitive variable validation against required model fields

After execution, confirm object state in Intersight UI:

- Organizations and Resource Groups
- Pools
- Policies
- Templates and Profiles

[Back to Table of Contents](#table-of-contents) | [Back to Main README](../README.md) | [Back to Best Practices README](../best_practices/README.md)

## Docs Guidance

### Policy Template Guidance

Use these references when selecting template names in policy models:

- [BIOS templates](docs/intersight_policy_templates/README_bios_templates.md)
- [Ethernet adapter templates](docs/intersight_policy_templates/README_ethernet_adapter_templates.md)
- [Fibre Channel adapter templates](docs/intersight_policy_templates/README_fibre_channel_adapter_templates.md)
- [Storage templates](docs/intersight_policy_templates/README_storage_templates.md)

### Name Prefix and Suffix Conventions

For naming conventions across pools, policies, profiles, and templates, see:

- [Name prefix and suffix support](docs/README_prefix_suffix.md)

[Back to Table of Contents](#table-of-contents) | [Back to Main README](../README.md) | [Back to Best Practices README](../best_practices/README.md)

## Troubleshooting

- Authentication failure:
  - Verify `intersight_api_key_id` and `intersight_secret_key` are set and valid.
- TLS/connectivity issues:
  - Confirm endpoint reachability and, when needed, use `-i` to bypass cert verification for test environments.
- Missing sensitive variables:
  - Export the missing variable names printed by the validator.
- No changes applied:
  - Confirm your model files are under the directory passed by `-d` and use the expected schema keys.

[Back to Table of Contents](#table-of-contents) | [Back to Main README](../README.md) | [Back to Best Practices README](../best_practices/README.md)

## Next Steps

After successful Intersight deployment:

1. Continue storage workflow using [everpure/README.md](../everpure/README.md).
2. Continue with OpenShift and platform operator deployment phases from the runbook.

[Back to Table of Contents](#table-of-contents)
