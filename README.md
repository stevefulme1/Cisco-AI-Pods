# Cisco AI Pods Repository Guide

This repository contains automation and runbooks for Cisco AI Pods infrastructure across Intersight, storage, OpenShift, and observability workflows.

## Table of Contents

- [Cisco AI Pods Repository Guide](#cisco-ai-pods-repository-guide)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Primary Workstreams](#primary-workstreams)
  - [Repository Layout](#repository-layout)
  - [Runbook Documents](#runbook-documents)
  - [Environment Preparation](#environment-preparation)
  - [Quick Start Workflow](#quick-start-workflow)
  - [Common Commands](#common-commands)
  - [Troubleshooting and Operations](#troubleshooting-and-operations)

## Overview

Current repository workflows are primarily:

- Python-based automation for Intersight/UCS configuration
- Ansible-based automation for Everpure, OpenShift, and observability integrations

Legacy Terraform references were removed from this guide to reflect the current model.

## Primary Workstreams

1. Intersight and UCS deployment
- Guide: [intersight/README.md](intersight/README.md)
- Entry point: `intersight/deploy_intersight_ucs.py`

2. Everpure storage and Portworx
- Guide: [everpure/README.md](everpure/README.md)
- Array and Portworx specifics: [everpure/README_everpure_arrays.md](everpure/README_everpure_arrays.md), [everpure/README_portworx.md](everpure/README_portworx.md)

3. OpenShift lifecycle modules
- Guide: [openshift/README.md](openshift/README.md)

4. Splunk observability integration
- Guide: [splunk-ai-pods/README.md](splunk-ai-pods/README.md)

5. NetApp/Trident assets
- Guide: [netapp/README.md](netapp/README.md)

## Repository Layout

Top-level structure (abbreviated):

```text
Cisco-AI-Pods/
  best_practices/
  everpure/
  intersight/
  netapp/
  openshift/
  playbooks/
  roles/
  schema/
  splunk-ai-pods/
  guide_cisco_ai_pods_runbook.md
  guide_prepare_the_environment.md
  guide_troubleshooting.md
  requirements.txt
  requirements.yaml
```

## Runbook Documents

- Main runbook: [guide_cisco_ai_pods_runbook.md](guide_cisco_ai_pods_runbook.md)
- Environment preparation: [guide_prepare_the_environment.md](guide_prepare_the_environment.md)
- Troubleshooting: [guide_troubleshooting.md](guide_troubleshooting.md)
- Best-practice phases index: [best_practices/README.md](best_practices/README.md)

## Environment Preparation

Prepare tools and dependencies first:

1. Follow [guide_prepare_the_environment.md](guide_prepare_the_environment.md).
2. Install Python dependencies from [requirements.txt](requirements.txt).
3. Install Ansible collections from [requirements.yaml](requirements.yaml).

## Quick Start Workflow

1. Prepare environment and credentials.
2. Run Intersight/UCS automation:

```bash
cd intersight
python3 deploy_intersight_ucs.py
```

3. Run Everpure workflows as needed:

```bash
cd everpure
ansible-playbook configure_everpure_arrays.yaml
ansible-playbook create_pure_json.yaml
```

4. Run OpenShift modules in order documented in [openshift/README.md](openshift/README.md).

5. Deploy observability components if required via [splunk-ai-pods/README.md](splunk-ai-pods/README.md).

## Common Commands

Install Python requirements:

```bash
python3 -m pip install -r requirements.txt
```

Install Ansible collections:

```bash
ansible-galaxy collection install -r requirements.yaml
```

Run the Intersight deployment in check mode:

```bash
cd intersight
python3 deploy_intersight_ucs.py -c
```

## Troubleshooting and Operations

- Use [guide_troubleshooting.md](guide_troubleshooting.md) for cross-component triage.
- For component-specific issues, start with the README in the corresponding top-level folder.
- Keep model files and runbook documentation synchronized as workflows evolve.