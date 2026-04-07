# Cisco AI Pods Pure Storage Overview

This folder contains Pure Storage automation used by Cisco AI Pods for two main workflows:

- Pure Storage array configuration (FlashArray and FlashBlade)
- Portworx integration and deployment on OpenShift

## Table of Contents

- [Runbook Documents](#runbook-documents)
- [Folder Contents](#folder-contents)
- [Prerequisites](#prerequisites)
- [Deployment Order](#deployment-order)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)

## Runbook Documents

- Array deployment guide: [README_pure_storage_arrays.md](README_pure_storage_arrays.md)
- Portworx deployment guide: [README_portworx.md](README_portworx.md)

[Back to Table of Contents](#table-of-contents)

## Folder Contents

- `configure_pure_storage_arrays.yaml`: Configures FlashArray and FlashBlade using settings in `script_vars`
- `create_pure_json.yaml`: Creates `pure.json` used by the Portworx secret
- `install_portworx.yaml`: Installs Portworx operator and deploys StorageCluster/storage classes
- `pure.json`: Generated credentials payload for `px-pure-secret`
- `script_vars/vars.ezcai.yaml`: Active configuration values
- `script_vars/vars.ezcai.example.yaml`: Example configuration values
- `tasks/`: Task files for FlashArray, FlashBlade, and Portworx workflows
- `templates/`: Templates for `pure.json`, StorageCluster, and storage classes
- `examples/`: Example manifests for validation and testing

[Back to Table of Contents](#table-of-contents)

## Prerequisites

Install required Ansible collections from the repository root requirements file by following:

- [Prepare the Environment](../guide_prepare_the_environment.md#install-ansible-on-ubuntu)

Example:

```bash
cd ..
ansible-galaxy collection install -r requirements.yaml
cd pure_storage
```

Install required Python dependencies:

```bash
cd ..
pip install -r requirements.txt
cd pure_storage
```

[Back to Table of Contents](#table-of-contents)

## Deployment Order

Use this order to avoid dependency issues:

1. Configure Pure arrays (FlashArray/FlashBlade) if needed.
2. Generate `pure.json` for Portworx authentication.
3. Install Portworx and StorageCluster on OpenShift.

Detailed procedures are documented in:

- [README_pure_storage_arrays.md](README_pure_storage_arrays.md)
- [README_portworx.md](README_portworx.md)

[Back to Table of Contents](#table-of-contents)

## Quick Start

1. Update configuration values in `script_vars/vars.ezcai.yaml`.
2. Export required API tokens and OpenShift credentials.
3. Run playbooks in order:

```bash
ansible-playbook configure_pure_storage_arrays.yaml
ansible-playbook create_pure_json.yaml
ansible-playbook install_portworx.yaml
```

[Back to Table of Contents](#table-of-contents)

## Environment Variables

Common variables used in this folder:

```bash
# Pure API tokens (match api_token_id values in script_vars)
export pure_api_token_1="<flasharray_token>"
export pure_api_token_2="<flashblade_token>"

# OpenShift access for install_portworx.yaml
export openshift_api_url="https://api.<cluster>.<domain>:6443"
export openshift_token_id="<token>"
```

Note: Additional sensitive variables may be required depending on your array security settings in `script_vars/vars.ezcai.yaml`.

[Back to Table of Contents](#table-of-contents)
