# OpenShift GitOps File Generator

This directory contains an Ansible workflow that builds OpenShift GitOps application manifests and supporting Helm/OLM content for AI Pods cluster add-on operators.

## Table of Contents

- [What This Generates](#what-this-generates)
- [Directory Structure](#directory-structure)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Variables Reference](#variables-reference)
- [Render Rules and Conditions](#render-rules-and-conditions)
- [Validation Tips](#validation-tips)
- [Troubleshooting](#troubleshooting)

## What This Generates

Running the generator playbook will:

- Create the destination GitOps working directory
- Copy the local helm and olm-catalog trees into that destination
- Build operator Argo CD Application manifests from Jinja templates
- Build optional NVIDIA Network Operator MacvlanNetwork manifests from variable input
- Build AAP-specific extra manifests when ansible-automation-platform is selected

[Back to Table of Contents](#table-of-contents)

## Directory Structure

- generate_openshift_gitops_files.yaml: Main playbook
- script_vars/vars.ezcai.yaml: Active variable file consumed by the playbook
- script_vars/vars.ezcai.example.yaml: Example variable file
- templates/: Jinja2 templates for generated Argo CD Application YAML and related resources
- helm/: Helm content copied to the destination GitOps repository path
- olm-catalog/: OLM/operator application content copied to the destination GitOps repository path

[Back to Table of Contents](#table-of-contents)

## Prerequisites

- Ansible installed
- Write access to the destination directory defined in variables
- A reachable Git repository URL for Argo CD source.repoURL values

[Back to Table of Contents](#table-of-contents)

## Quick Start

1. Set variables in script_vars/vars.ezcai.yaml.
2. Run the playbook from this directory:

```bash
ansible-playbook generate_openshift_gitops_files.yaml
```

3. Review generated files under your destination directory:

- <destination>/helm
- <destination>/olm-catalog
- <destination>/olm-catalog/operators/*.yaml
- <destination>/helm/gpu-operator-installation/templates/configs/05-mac-vlan-policy-*.yaml (if NVIDIA Network Operator is enabled)

[Back to Table of Contents](#table-of-contents)

## Variables Reference

Top-level object: openshift

### Core

- base_domain: Cluster base DNS domain
- cluster_name: OpenShift cluster name
- destination_directory: Output location where helm and olm-catalog are copied and generated files are written
- file_storage_class: StorageClass used by templates that reference shared storage

### GitOps Behavior

Path: openshift.operators.openshift_gitops

- gitops_repo_url: Repository URL used in generated Argo CD Application manifests
- prune: Argo CD automated prune setting
- self_heal: Argo CD automated selfHeal setting

### Operator Selection

Path: openshift.operators.operators_to_install

This list controls which operator application manifests are rendered to:

- <destination>/olm-catalog/operators/<item>.yaml

Each list item must match a template filename stem in templates/.yaml.j2.

Common entries include:

- ansible-automation-platform
- external-secrets-operator
- kubernetes-nmstate-operator
- node-feature-discovery-operator
- nvidia-gpu-operator
- nvidia-network-operator
- openshift-virtualization
- gpu-operator
- infrastructure-operators
- observability-operators
- rhoai-application
- scaling-operators

### NVIDIA Network Operator Mac VLAN

Path: openshift.operators.nvidia_network_operator.mac_vlan

Each list item supports:

- master_interface: Parent NIC (for example ens201f0np0)
- ip_range: CIDR range for Whereabouts IPAM
- exclude_ips: List of excluded IPs in CIDR notation

When nvidia-network-operator is selected, one MacvlanNetwork manifest is generated per entry at:

- <destination>/helm/gpu-operator-installation/templates/configs/05-mac-vlan-policy-<master_interface>.yaml

[Back to Table of Contents](#table-of-contents)

## Render Rules and Conditions

- ansible-automation-platform in operators_to_install additionally renders:
  - <destination>/olm-catalog/ansible-automation-platform/04-ansible-automation-platform.yaml
  - <destination>/olm-catalog/ansible-automation-platform/04-console-link-aap.yaml
- Every value in operators_to_install attempts to render templates/<value>.yaml.j2
- nvidia-network-operator in operators_to_install enables Mac VLAN template rendering loop

[Back to Table of Contents](#table-of-contents)

## Validation Tips

After generation, validate before committing:

```bash
find <destination>/olm-catalog/operators -name '*.yaml' -maxdepth 1 | wc -l
```

```bash
grep -R "repoURL:" <destination>/olm-catalog/operators
```

```bash
grep -R "MacvlanNetwork" <destination>/helm/gpu-operator-installation/templates/configs
```

[Back to Table of Contents](#table-of-contents)

## Troubleshooting

- Missing template error:
  - Ensure every operators_to_install value has a matching templates/<name>.yaml.j2 file.
- No MacvlanNetwork files generated:
  - Ensure nvidia-network-operator is present in operators_to_install.
  - Ensure openshift.operators.nvidia_network_operator.mac_vlan contains at least one entry.
- Files written to an unexpected path:
  - Verify openshift.destination_directory in script_vars/vars.ezcai.yaml.

[Back to Table of Contents](#table-of-contents)
