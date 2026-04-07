# Pure Storage Arrays Deployment Guide

This guide covers Day 0 automation for Pure Storage FlashArray and FlashBlade configuration in this folder.

## Table of Contents

- [Scope](#scope)
- [Prerequisites](#prerequisites)
- [Configuration Files](#configuration-files)
- [Environment Variables](#environment-variables)
- [Run the Array Configuration Playbook](#run-the-array-configuration-playbook)
- [What Gets Configured](#what-gets-configured)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

## Scope

The array workflow configures settings on FlashArray and FlashBlade using task sets under:

- `tasks/flash_array/`
- `tasks/flash_blade/`

This includes network, security/access, system, users, and (for FlashBlade) optional notification integrations based on the values you provide.

[Back to Table of Contents](#table-of-contents)

## Prerequisites

- Ansible collections installed from the repository root `requirements.yaml` (see [Prepare the Environment](../guide_prepare_the_environment.md#install-ansible-on-ubuntu))
- Python dependencies installed from the repository root `requirements.txt` (see [Prepare the Environment](../guide_prepare_the_environment.md#install-ansible-on-ubuntu))
- Network connectivity from Ansible host to all array management endpoints
- API tokens for each array entry in your variables

Install dependencies:

```bash
cd ..
ansible-galaxy collection install -r requirements.yaml
pip install -r requirements.txt
cd pure_storage
```

[Back to Table of Contents](#table-of-contents)

## Configuration Files

Current files in this folder:

- `script_vars/vars.ezcai.yaml`: main variable definitions
- `script_vars/vars.ezcai.example.yaml`: sample input
- `configure_pure_storage_arrays.yaml`: array configuration playbook

Important note:

- `configure_pure_storage_arrays.yaml` currently loads variables from `{{ playbook_dir }}/vars`.
- If your active data is in `script_vars/vars.ezcai.yaml`, copy or mirror it into a `vars/` location before running, or update the playbook path in your local workflow.

[Back to Table of Contents](#table-of-contents)

## Environment Variables

Set one API token per `api_token_id` used in your variable file.

Example:

```bash
export pure_api_token_1="<flasharray_token>"
export pure_api_token_2="<flashblade_token>"
```

Additional environment variables may be required by your selected security/system options, for example bind or service account passwords referenced via lookups in task files.

[Back to Table of Contents](#table-of-contents)

## Run the Array Configuration Playbook

From this folder:

```bash
ansible-playbook configure_pure_storage_arrays.yaml
```

[Back to Table of Contents](#table-of-contents)

## What Gets Configured

Based on your variable content, the playbook iterates through:

- `pure_storage.flash_arrays[]`
- `pure_storage.flash_blades[]`

FlashArray tasks include:

- Settings: network
- Settings: access/security
- Settings: system

FlashBlade tasks include:

- Settings: network
- Settings: security
- Settings: system
- Notifications (if `pure_storage.notifications` is defined)

[Back to Table of Contents](#table-of-contents)

## Verification

Validate expected changes in Pure UI or via API/CLI checks.

Suggested checks:

```bash
# Example API version check
curl -k https://<array-management-endpoint>/api/api_version
```

```bash
# Re-run facts gathering in check mode style (optional pattern)
ansible localhost -m purestorage.flasharray.purefa_info -a "fa_url=<flasharray_fqdn> api_token=$pure_api_token_1 gather_subset=minimum" -c local
```

```bash
ansible localhost -m purestorage.flashblade.purefb_info -a "fb_url=<flashblade_fqdn> api_token=$pure_api_token_2" -c local
```

[Back to Table of Contents](#table-of-contents)

## Troubleshooting

- Authentication errors:
  - Confirm `pure_api_token_<id>` environment variable names match `api_token_id` values.
- Variable load failures:
  - Confirm the variables path expected by the playbook (`vars/`) is present or adjust the playbook to your chosen location.
- Module import errors:
  - Reinstall required collections and Python packages from the repository root `requirements.yaml` and `requirements.txt`.
  - See [Prepare the Environment](../guide_prepare_the_environment.md#install-ansible-on-ubuntu).
- Task skipped unexpectedly:
  - Check conditional keys like `pure_storage.settings.network`, `pure_storage.settings.security`, `pure_storage.settings.system`, and `pure_storage.notifications`.

[Back to Table of Contents](#table-of-contents)
