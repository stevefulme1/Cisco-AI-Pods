# OpenShift GitOps File Generator

This directory contains the Ansible workflow that prepares GitOps content for OpenShift cluster add-on operators used by Cisco AI Pods. The playbook copies the local Helm and OLM catalog trees into a destination Git repository structure, then renders Argo CD Application manifests and supporting YAML from Jinja2 templates.

## Table of Contents

- [OpenShift GitOps File Generator](#openshift-gitops-file-generator)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [What the Playbook Does](#what-the-playbook-does)
  - [Directory Structure](#directory-structure)
  - [Prerequisites](#prerequisites)
  - [Quick Start](#quick-start)
  - [Variables Reference](#variables-reference)
    - [Core Variables](#core-variables)
    - [GitOps Settings](#gitops-settings)
    - [Operator Selection](#operator-selection)
    - [NVIDIA Network Operator Mac VLAN Settings](#nvidia-network-operator-mac-vlan-settings)
  - [Render Rules](#render-rules)
  - [Generated Output](#generated-output)
  - [Validation Tips](#validation-tips)
  - [Troubleshooting](#troubleshooting)

## Overview

The main entry point is `generate_openshift_gitops_files.yaml`. It reads variables from `script_vars/vars.ezcai.yaml`, copies the bundled `helm/` and `olm-catalog/` directories into `openshift.destination_directory`, and renders additional files from `templates/`.

This workflow is used to build the GitOps repository content that OpenShift GitOps consumes later.

[Back to Table of Contents](#table-of-contents)

## What the Playbook Does

Running the playbook performs these actions:

- Loads variables from `script_vars/vars.ezcai.yaml`
- Creates the destination directory if it does not already exist
- Copies the local `helm/` and `olm-catalog/` trees into the destination directory
- Ensures `olm-catalog/operators/` exists in the destination directory
- Always renders the LLDP DaemonSet application manifest to `olm-catalog/operators/lldp-daemonset.yaml`
- Renders one operator application manifest per entry in `openshift.operators.operators_to_install`
- Renders two additional AAP resources when `ansible-automation-platform` is selected
- Renders one Macvlan policy file per `openshift.operators.nvidia_network_operator.mac_vlan` entry when `nvidia-network-operator` is selected

[Back to Table of Contents](#table-of-contents)

## Directory Structure

- `generate_openshift_gitops_files.yaml`: Main playbook
- `script_vars/vars.ezcai.example.yaml`: Example variable file to copy and customize
- `templates/`: Jinja2 templates used to render Argo CD Applications and related resources
- `helm/`: Helm content copied into the destination GitOps directory
- `olm-catalog/`: OLM and operator content copied into the destination GitOps directory

Current template stems include:

- `ansible-automation-platform.yaml.j2`
- `ansible_automation_platform.yaml.j2`
- `console-link-aap.yaml.j2`
- `external-secrets-operator.yaml.j2`
- `gpu-operator.yaml.j2`
- `infrastructure-operators.yaml.j2`
- `kubernetes-nmstate-operator.yaml.j2`
- `lldpd-daemonset.yaml.j2`
- `mac-vlan.yaml.j2`
- `node-feature-discovery-operator.yaml.j2`
- `nvidia-gpu-operator.yaml.j2`
- `nvidia-network-operator.yaml.j2`
- `observability-operators.yaml.j2`
- `openshift-virtualization.yaml.j2`
- `rhoai-application.yaml.j2`
- `scaling-operators.yaml.j2`

[Back to Table of Contents](#table-of-contents)

## Prerequisites

- Ansible is installed and available in your shell
- You have write access to the destination directory defined in the variables file
- You have a GitOps repository URL to use in generated Argo CD `repoURL` fields
- You have created `script_vars/vars.ezcai.yaml` from the example file in this folder

[Back to Table of Contents](#table-of-contents)

## Quick Start

1. Create the active variables file.

```bash
cp script_vars/vars.ezcai.example.yaml script_vars/vars.ezcai.yaml
```

2. Edit `script_vars/vars.ezcai.yaml` and define at least:

- `openshift.destination_directory`
- `openshift.base_domain`
- `openshift.cluster_name`
- `openshift.file_storage_class`
- `openshift.operators.openshift_gitops.gitops_repo_url`
- `openshift.operators.operators_to_install`

3. Run the playbook from this directory.

```bash
ansible-playbook generate_openshift_gitops_files.yaml
```

4. Review the generated content in your destination directory before committing it to your GitOps repository.

[Back to Table of Contents](#table-of-contents)

## Variables Reference

Top-level object: `openshift`

### Core Variables

- `destination_directory`: Output path where `helm/`, `olm-catalog/`, and generated files are written
- `base_domain`: Cluster base DNS domain
- `cluster_name`: OpenShift cluster name used by the AAP console link template
- `file_storage_class`: StorageClass referenced by the AAP custom resource template

### GitOps Settings

Path: `openshift.operators.openshift_gitops`

- `gitops_repo_url`: Repository URL used in generated Argo CD Application manifests
- `prune`: Value written to `spec.syncPolicy.automated.prune`
- `self_heal`: Value written to `spec.syncPolicy.automated.selfHeal`

### Operator Selection

Path: `openshift.operators.operators_to_install`

Each list item is rendered to:

- `<destination>/olm-catalog/operators/<item>.yaml`

Each value must match a template stem in `templates/`, for example:

- `ansible-automation-platform`
- `external-secrets-operator`
- `gpu-operator`
- `infrastructure-operators`
- `kubernetes-nmstate-operator`
- `node-feature-discovery-operator`
- `nvidia-gpu-operator`
- `nvidia-network-operator`
- `observability-operators`
- `openshift-virtualization`
- `rhoai-application`
- `scaling-operators`

### NVIDIA Network Operator Mac VLAN Settings

Path: `openshift.operators.nvidia_network_operator.mac_vlan`

Each list item supports:

- `master_interface`: Parent NIC, for example `ens201f0np0`
- `ip_range`: CIDR block used by Whereabouts IPAM
- `exclude_ips`: List of excluded IPs in CIDR notation

[Back to Table of Contents](#table-of-contents)

## Render Rules

- `lldp-daemonset.yaml` is always generated, regardless of the operator list
- Every value in `operators_to_install` attempts to render `templates/<value>.yaml.j2`
- When `ansible-automation-platform` is selected, the playbook also renders:
  - `<destination>/olm-catalog/ansible-automation-platform/04-ansible-automation-platform.yaml`
  - `<destination>/olm-catalog/ansible-automation-platform/04-console-link-aap.yaml`
- The AAP extra custom resource comes from `ansible_automation_platform.yaml.j2`, while the operator application uses `ansible-automation-platform.yaml.j2`
- When `nvidia-network-operator` is selected, the playbook loops through `mac_vlan` entries and renders one file per interface

[Back to Table of Contents](#table-of-contents)

## Generated Output

After a successful run, the destination directory contains at least:

- `<destination>/helm/`
- `<destination>/olm-catalog/`
- `<destination>/olm-catalog/operators/lldp-daemonset.yaml`
- `<destination>/olm-catalog/operators/<operator>.yaml` for each selected operator

Additional conditional output:

- `<destination>/olm-catalog/ansible-automation-platform/04-ansible-automation-platform.yaml`
- `<destination>/olm-catalog/ansible-automation-platform/04-console-link-aap.yaml`
- `<destination>/helm/gpu-operator-installation/templates/configs/05-mac-vlan-policy-<master_interface>.yaml`

[Back to Table of Contents](#table-of-contents)

## Validation Tips

Validate the generated content before committing it:

```bash
find <destination>/olm-catalog/operators -maxdepth 1 -name '*.yaml' | sort
```

```bash
grep -R "repoURL:" <destination>/olm-catalog
```

```bash
grep -R "MacvlanNetwork" <destination>/helm/gpu-operator-installation/templates/configs
```

[Back to Table of Contents](#table-of-contents)

## Troubleshooting

- Playbook fails loading variables:
  - Confirm `script_vars/vars.ezcai.yaml` exists. The playbook does not read the example file directly.
- Files are written to the wrong location:
  - Verify `openshift.destination_directory` in `script_vars/vars.ezcai.yaml`.
- Missing template error during the operator loop:
  - Ensure every entry in `operators_to_install` has a matching `templates/<name>.yaml.j2` file.
- No Macvlan files are created:
  - Ensure `nvidia-network-operator` is present in `operators_to_install`.
  - Ensure `openshift.operators.nvidia_network_operator.mac_vlan` contains one or more entries.
- AAP operator application exists but the extra AAP resources do not:
  - Ensure `ansible-automation-platform` is included in `operators_to_install`.

[Back to Table of Contents](#table-of-contents)
