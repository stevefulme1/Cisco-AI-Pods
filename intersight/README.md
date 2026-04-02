# Cisco AI Pods Intersight Deployment Guide

This folder deploys Cisco Intersight organizations, pools, policies, and profiles/templates using Terraform and Cisco Terraform modules.

## Top Level Documents

- [Cisco AI Pods Runbook](../guide_cisco_ai_pods_runbook.md)
- [Main README](../README.md)
- [Prepare the Environment](../guide_prepare_the_environment.md)

## Table of Contents

- [Cisco AI Pods Intersight Deployment Guide](#cisco-ai-pods-intersight-deployment-guide)
  - [Top Level Documents](#top-level-documents)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Folder Structure](#folder-structure)
  - [Prerequisites](#prerequisites)
  - [Configuration Model](#configuration-model)
    - [Global Settings](#global-settings)
    - [Data Merge Behavior](#data-merge-behavior)
  - [Authentication and Sensitive Variables](#authentication-and-sensitive-variables)
    - [Required Environment Variables](#required-environment-variables)
    - [Common Sensitive Variables](#common-sensitive-variables)
  - [Deployment Steps](#deployment-steps)
  - [Validation](#validation)
  - [Troubleshooting](#troubleshooting)
    - [Authentication Failures](#authentication-failures)
    - [Model Not Applied](#model-not-applied)
    - [Provider or Module Issues](#provider-or-module-issues)
    - [State Conflicts](#state-conflicts)
  - [Next Steps](#next-steps)

## Overview

Deployment in this folder is Terraform-based and uses:

- Provider: `CiscoDevNet/intersight`
- Data merge helper: `netascode/utils`
- Terraform modules:
  - `terraform-cisco-modules/organizations/intersight`
  - `terraform-cisco-modules/pools/intersight`
  - `terraform-cisco-modules/policies/intersight`
  - `terraform-cisco-modules/profiles/intersight`

The deployment merges all `*.ezi.yaml` model files from this folder and from selected subfolders into one model, then applies modules conditionally based on content.

[Back to Table of Contents](#table-of-contents)

## Folder Structure

Key files:

- `main.tf`: module orchestration and YAML merge
- `provider.tf`: Terraform providers and Intersight auth config
- `locals.tf`: model/sensitive variable mapping
- `variables.tf`: provider and policy sensitive variable definitions
- `outputs.tf`: module outputs
- `global_settings.ezi.yaml`: global settings including `intersight_fqdn` and tags

Model folders:

- `organizations/`
- `pools/`
- `policies/`
- `profiles/`
- `templates/`

[Back to Table of Contents](#table-of-contents)

## Prerequisites

- Terraform `>= 1.3.0`
- Network connectivity to Intersight SaaS or appliance endpoint
- Intersight API key ID and secret key
- Environment prepared per [Prepare the Environment](../guide_prepare_the_environment.md)

Optional but recommended:

- `jq` for output parsing
- version-controlled `.ezi.yaml` model files per organization

[Back to Table of Contents](#table-of-contents)

## Configuration Model

### Global Settings

Edit `global_settings.ezi.yaml`:

```yaml
global_settings:
  intersight_fqdn: intersight.com
```

For appliance deployments, set `intersight_fqdn` to your appliance FQDN.

### Data Merge Behavior

`main.tf` merges model files from:

- `*.ezi.yaml` in this directory
- `o*/*.ezi.yaml`
- `p*/*.ezi.yaml`
- `t*/*.ezi.yaml`

Keep model data in these paths so Terraform picks it up automatically.

[Back to Table of Contents](#table-of-contents)

## Authentication and Sensitive Variables

### Required Environment Variables

```bash
export TF_VAR_intersight_api_key_id="<apikeyid>"
export TF_VAR_intersight_secret_key="/absolute/path/to/SecretKey.pem"
```

Important:

- `TF_VAR_intersight_api_key_id` must match the format validated in `variables.tf`:
  - `24hex/24hex/24hex`
- `TF_VAR_intersight_secret_key` can be a file path or inline PEM text.

### Common Sensitive Variables

Depending on your policy model, export additional variables such as:

```bash
export TF_VAR_cco_password="<secure_password>"
export TF_VAR_binding_parameters_password="<ldap_bind_password>"
export TF_VAR_local_user_password_1="<secure_password>"
export TF_VAR_snmp_auth_password_1="<secure_password>"
export TF_VAR_snmp_privacy_password_1="<secure_password>"
```

See `variables.tf` and `locals.tf` for full supported variable names.

[Back to Table of Contents](#table-of-contents)

## Deployment Steps

1. Change into this folder.

```bash
cd Cisco-AI-Pods/intersight
```

2. Initialize Terraform.

```bash
terraform init
```

3. Validate configuration.

```bash
terraform validate
```

4. Create plan.

```bash
terraform plan -out main.plan
```

5. Apply plan.

```bash
terraform apply main.plan
```

[Back to Table of Contents](#table-of-contents)

## Validation

Check module outputs:

```bash
terraform output
```

Inspect created state objects:

```bash
terraform state list
```

Optional output checks:

```bash
terraform output organizations
terraform output pools
terraform output policies
terraform output profiles
```

In Intersight UI, confirm objects under:

- Organizations and Resource Groups
- Pools
- Policies
- Templates and Profiles

[Back to Table of Contents](#table-of-contents)

## Troubleshooting

### Authentication Failures

- Verify `TF_VAR_intersight_api_key_id` format (`24hex/24hex/24hex`).
- Verify `TF_VAR_intersight_secret_key` path exists and is readable.
- Ensure endpoint in `global_settings.ezi.yaml` is correct.

### Model Not Applied

- Confirm model files are in recognized paths (`*.ezi.yaml`, `o*/`, `p*/`, `t*/`).
- Run `terraform plan` and check for zero-change output due to missing model keys.

### Provider or Module Issues

```bash
terraform init -upgrade
terraform providers
terraform version
```

### State Conflicts

Use with care:

```bash
terraform state rm <resource>
terraform import <resource> <id>
```

[Back to Table of Contents](#table-of-contents)

## Next Steps

After successful Intersight deployment:

1. Continue storage workflow using [pure_storage/README.md](../pure_storage/README.md).
2. Continue with OpenShift and platform operator deployment phases from the runbook.

[Back to Table of Contents](#table-of-contents)
