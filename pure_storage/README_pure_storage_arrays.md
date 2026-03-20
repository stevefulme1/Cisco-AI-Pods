# Pure Storage Array's Deployment Guide

## Top Level Documents
* [Cisco AI Pods Runbook](../guide_cisco_ai_pods_runbook.md#cisco-ai-pods-runbook)
* [Main README](../README.md)
* [Prepare the Environment](../guide_prepare_the_environment.md)

## Table of Contents
* [Overview](#overview)
* [Prerequisite Checklist](#prerequisite-checklist)
* [Best Practices](#best-practices)
* [Deployment](#deployment)
* [Troubleshooting](#troubleshooting)

## Overview
This guide covers the configuration of Pure Storage FlashArray and FlashBlade systems using Ansible automation.

⚠️ **CRITICAL DEPLOYMENT ORDER:** You **MUST** complete the following phases first:
- **Phase 1:** Network Foundation (complete)

**Do not proceed** with Pure Storage configuration until network infrastructure is fully deployed and operational.

## Prerequisite Checklist

- [ ] Ansible 2.17+ installed
- [ ] Pure Storage API access and credentials
- [ ] Network connectivity to storage arrays

### [<ins>Back to Table of Contents<ins>](#table-of-contents)

## Best Practices

### Security
- Use trusted certificates for portal access
- Use API tokens instead of username/password
- Rotate API tokens regularly
- Limit API token permissions
- Use encrypted connections (HTTPS)

### Performance
- Configure multiple paths for redundancy
- Use appropriate block sizes for workloads
- Monitor and tune performance policies
- Implement proper QoS settings within the network end-to-end

### Data Protection
- Configure regular snapshots
- Set up protection groups for critical data
- Test restore procedures regularly
- Document recovery procedures

### Monitoring
- Set up monitoring dashboards
- Configure alerts for capacity and performance
- Monitor array health regularly
- Track performance trends

### [<ins>Back to Table of Contents<ins>](#table-of-contents)

## Deployment

⚠️ **Prepare the Environment:** Be Sure you have followed the steps in prepare the environment, prior to moving forward here.

* [Prepare the Environment](../guide_prepare_the_environment.md)

### Step 1: Enter the Python Virtual Environment

* Make sure you are in the Python virtual environment created during the `Prepare the Environment` steps.

* **Linux**

   ```bash
   source .venv/bin/activate
   ```

* **Example output**

   ```bash
   tyscott@rich.ciscolabs.com@lnx2:~/scotttyso$ source .venv/bin/activate
   (.venv) tyscott@rich.ciscolabs.com@lnx2:~/scotttyso$ cd FlashStack-AI/pure_storage/
   (.venv) tyscott@rich.ciscolabs.com@lnx2:~/scotttyso/FlashStack-AI/pure_storage$
   ```

### Step 2: Load sensitive environment variables

* **Linux**

   ```bash
   export pure_api_token_1='my_user_api_token'
   # LDAP binding password
   export binding_parameters_password_1='secure_password'
   # Local User Password
   export local_user_password_2="secure_password"
   export snmp_auth_passphrase_1="secure_password"
   export snmp_auth_passphrase_2="secure_password"
   export snmp_privacy_passphrase_1="secure_password"
   export snmp_privacy_passphrase_2="secure_password"
   ```

### Step 3: Run Deployment Playbook

* **Change into the Directory**

   ```bash
   cd FlashStack-AI/pure_storage/
   ```

* **Run configuration playbook**

   ```bash
   ansible-playbook main.yaml
   ```

### 1. FlashArray Verification

Connect to the FlashArray/FlashBlade management interface

```bash
https://your-flasharray-ip
```

Validate that the expected configuration settings were applied.

Verify via CLI (if available)
```bash
ansible flasharray -i inventory -m shell -a "purearray list --host"
```

### [<ins>Back to Table of Contents<ins>](#table-of-contents)

## Troubleshooting

### API Connection Issues

Test API Connectivity

```bash
curl -k https://your-flasharray-ip/api/api_version
```

Verify API token

```bash
ansible flasharray -i inventory -m purefa_info -a "gather_subset=minimum"
```

### Module Import Errors

Reinstall Pure Storage Collection

```bash
ansible-galaxy collection install purestorage.flasharray --force
```

Check Python module installation

```bash
python3 -c "import purestorage; print('Success')"
```

### Performance Issues
1. Check network connectivity between hosts and arrays
2. Verify multipathing configuration
3. Check for ethernet configuration issues
4. Review Pure Storage performance metrics

### [<ins>Back to Table of Contents<ins>](#table-of-contents)

---

**Note:** This guide covers Pure Storage specific configuration. Ensure that the networking environment is up and operational before attempting this section.

