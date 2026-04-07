# Cisco AI Pods Runbook Index

## Table of Contents
* [Overview](#overview)
* [Best Practices](#best-practices)
* [Runbook Components](#runbook-components)
* [Prepare the Environment](#️---critical-prepare-the-environment)
* [Quick Start Workflow](#quick-start-workflow)
* [Repository Structure Reference](#repository-structure-reference)
* [Key Configuration Files](#key-configuration-files)
* [Support and Escalation](#support-and-escalation)
* [Quick Commands Reference](#quick-commands-reference)
* [Updates and Maintenance](#updates-and-maintenance)

## Overview
This directory contains comprehensive documentation for the Cisco AI Pods infrastructure. The runbook is organized into focused guides for each component and operational procedure. This is a living document.

## Best Practices

### Documentation
- Keep runbooks updated with any customizations
- Document all deviations from standard procedures
- Maintain change logs for configuration modifications
- Regular review and validation of procedures

### Security
- Rotate API tokens and credentials regularly
- Use encrypted connections for all management
- Implement proper access controls
- Regular security audits and updates

### Operations
- Regular health checks and monitoring
- Scheduled maintenance windows
- Automated backup procedures
- Performance monitoring and optimization

### [<ins>Back to Table of Contents<ins>](#table-of-contents)

## Runbook Components

### 🌐 [Network Deployment](network/README.md)
**Network infrastructure deployment guide**
- Cisco Nexus switch configuration
- VLAN and routing setup
- Integration with compute and storage
- Monitoring and maintenance

### 🖥️ [C800 Configuration Automation](c800/README.md)
**Automation for C845A/C880A/C885A GPU server deployment**
- Cisco C8XX M8 GPU server deployment
- Redfish API configuration procedures
- GPU-optimized BIOS settings
- Integration with main AI Pods infrastructure

### 🚀 [Intersight Automation](intersight/README.md)
**Automation for Cisco Intersight deployment**
- Essential setup steps
- Key configuration files
- Common troubleshooting
- Verification procedures

### 📚 [Cisco AI Pods Runbook](cisco-ai-pods-runbook.md)
**Complete deployment guide covering all components**
- Prerequisites and planning
- End-to-end deployment procedures  
- Integration steps
- Post-deployment validation

### 💾 [Pure Storage Automation](pure_storage/README.md)
**Automation for Pure Storage deployment**
- FlashArray/FlashBlade configuration
- Ansible automation procedures
- Host integration steps
- Performance optimization

### 🔧 [Troubleshooting Guide](troubleshooting.md)
**Comprehensive troubleshooting reference**
- Common issues and resolutions
- Performance troubleshooting
- Recovery procedures
- Escalation processes

## ⚠️ - **CRITICAL** Prepare the Environment

Follow the Steps to [Prepare the Environment](guide_prepare_the_environment.md#prepare-the-environment)

### [<ins>Back to Table of Contents<ins>](#table-of-contents)

## Quick Start Workflow

⚠️ **CRITICAL:** Always follow the [Deployment Execution Order](cisco-ai-pods-runbook.md#️-environment-deployment-execution-order) defined in the main runbook.

### For New Deployments
1. **Planning Phase:**
   - Review [Main Runbook - Pre-Deployment Planning](cisco-ai-pods-runbook.md#pre-deployment-planning)
   - Review [Deployment Execution Order](cisco-ai-pods-runbook.md#deployment-execution-order)
   - Complete network and IP planning
   - Gather all required credentials

2. **Phase 1 - Foundation Setup (FIRST):**
   - Follow [Network Configuration - Phase 1](network/README.md) for management network
   - Establish basic network connectivity **before any automation**
   - **Checkpoint:** Verify management network connectivity

3. **Phase 2 - Infrastructure Deployment:**
   - Use [Intersight Automation](intersight/README.md) for compute infrastructure
   - **Checkpoint:** Validate Intersight deployment before proceeding

4. **Phase 3 - C845A/C880A/C885A M8 GPU Servers:**
   - Follow [C845A/C880A/C885A Configuration Guide](c800/README.md) for additional GPU infrastructure
   - Configure using Redfish API for GPU-specific features
   - **Checkpoint:** Validate GPU functionality and DateTime sync

5. **Phase 4 - Storage Configuration:**
   - Follow [Pure Storage Configuration](pure_storage/README.md) for storage
   - **Checkpoint:** Verify storage connectivity

6. **Phase 5 - OpenShift Deployment:**
   - Complete [OpenShift Deployment - Phase 5](openshift/README.md)
   - **Checkpoint:** End-to-end connectivity validation

7. **Phase 6 - Integration & Validation:**
   - Run verification procedures from each guide
   - Perform end-to-end testing
   - Document any customizations

8. **Phase 7 - Application Platform:**
   - Deploy OpenShift/Kubernetes
   - Configure container orchestration

### Troubleshooting

1. **Identify Component:**
   - C845/C880/C885 issues → [Troubleshooting C885 issues](c800/README.md#troubleshooting-c885-issues)
   - Compute issues → [Troubleshooting Quick Fixes](intersight/README.md#troubleshooting-quick-fixes)
   - Network issues → [Troubleshooting Common Issues](network/README.md#troubleshooting-common-issues)
   - Pure Storage issues → [Troubleshooting](pure_storage/README.md#troubleshooting)
   - OpenShift issues → See Individual READMEs
     - OpenShift Installatin → [Troubleshooting](openshift/install/README.md#trou)
     - OpenShift - Base Operators → [Troubleshooting](openshift/base_operators/gitea/)

2. **Follow Procedures:**
   - Use [Troubleshooting Guide](guide_troubleshooting.md) for comprehensive procedures
   - Check component-specific guides for detailed steps
   - Escalate following documented procedures

### [<ins>Back to Table of Contents<ins>](#table-of-contents)

## Repository Structure Reference

```
Cisco-AI-Pods
├── c885/                        # Cisco C885A automation
│   ├── main.fsai.yaml           # C885 configuration data model
├── intersight/                  # Cisco Intersight automation
│   ├── global_settings.ezi.yaml # Global Parameters
│   ├── main.tf                  # Main Terraform module
│   ├── organizations/           # Organization data model
│   ├── policies/                # Policy data model
│   ├── pools/                   # Pool data model
│   ├── provider.tf              # Provider Attributes
│   ├── templates/               # Templates data model
│   └── variables.tf             # Terraform sensitive variables
├── network/                     # Network Device Configurations
│   └── *.txt                    # Switch configuration templates
├── openshift/                   # Cisco Intersight automation
│   ├── global_settings.ezi.yaml # Global Parameters
│   ├── main.tf                  # Main Terraform module
│   ├── organizations/           # Organization data model
│   ├── policies/                # Policy data model
└── pure_storage/                # Pure Storage automation
    ├── tasks/                   # Ansible playbooks
    ├── vars/                    # Ansible vars
    ├── configure_pure_storage_arrays.yaml                # Top-level Ansible Playbook
    └── requirements.yaml        # Ansible Requirements
```

### [<ins>Back to Table of Contents<ins>](#table-of-contents)

## Key Configuration Files

### Intersight Global Settings
- **Location:** `Cisco-AI-Pods/Intersight/global_settings.ezi.yaml`
- **Purpose:** Central configuration for Intersight deployment
- **Key Settings:** Intersight FQDN, tags, global parameters

### Pure Storage Inventory Files  
- **Location:** `Cisco-AI-Pods/pure_storage/vars/main.fsai.yaml`
- **Purpose:** Ansible inventory for storage automation
- **Content:** Storage array IPs, credentials, connection details

### Network Templates
- **Location:** `Cisco-AI-Pods/network/*.txt`
- **Purpose:** Switch configuration templates
- **Usage:** Customize and apply to network devices

### [<ins>Back to Table of Contents<ins>](#table-of-contents)

## Support and Escalation

### Internal Support
- **Level 1:** Infrastructure team → Component-specific guides
- **Level 2:** Senior engineers → [Troubleshooting Guide](troubleshooting.md)
- **Level 3:** Vendor support → Escalation procedures

### Vendor Support
- **Cisco TAC:** Intersight, UCS, and network issues
- **Pure Storage:** Storage array and performance issues
- **DevNet Community:** Terraform and Ansible community support

### [<ins>Back to Table of Contents<ins>](#table-of-contents)

## Quick Commands Reference

### Terraform Operations

```bash
terraform init          # Initialize working directory
terraform validate      # Validate configuration
terraform plan          # Preview changes
terraform apply         # Apply changes
terraform destroy       # Destroy infrastructure
```

### Ansible Operations

```bash
ansible-galaxy collection install -r requirements.yaml
ansible-playbook main.yml    # Run Pure Storage setup
```

For full environment and dependency setup, see [Prepare the Environment](guide_prepare_the_environment.md#install-ansible-on-ubuntu).

### Network Operations

```bash
copy running-config startup-config  # Save configuration
ping                                # Basic connectivity tests
show bgp ipv4 unicast               # See the BGP IPv4 unicasting table
show interface brief                # Interface status
show ip route                       # IP Routing Table
show vlan brief                     # VLAN configuration
show version                        # Software version
traceroute                          # Path validation
```

## Updates and Maintenance

### [<ins>Back to Table of Contents<ins>](#table-of-contents)

### Runbook Updates
- Review quarterly for accuracy
- Update after major infrastructure changes
- Validate procedures after software updates
- Incorporate lessons learned from incidents

### Infrastructure Updates
- Follow change management procedures
- Test in non-production first
- Document all changes
- Update runbooks accordingly

---

**Document Information**
- **Created:** June 13, 2025
- **Version:** 1.2
- **Last Updated:** July 12, 2025
- **Maintained By:** Infrastructure Automation Team

For questions or updates to this runbook, please contact the Infrastructure team or submit an issue in the repository.