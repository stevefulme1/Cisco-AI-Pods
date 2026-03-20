# Cisco AI Pods Intersight Deployment Guide

## Top Level Documents
* [Cisco AI Pods Runbook](../guide_cisco_ai_pods_runbook.md#cisco-ai-pods-runbook)
* [Main README](../README.md)
* [Prepare the Environment](../guide_prepare_the_environment.md)

## Table of Contents
* [Overview](#overview)
* [Prerequisites Checklist](#prerequisites-checklist)
* [Prerequisite Steps](#prerequisite-steps)
* [Security Best Practices](#prerequisite-steps)
* [Deployment Steps](#deployment-steps)
* [Post-Deployment Validation](#post-deployment-validation)
* [Next Steps](#next-steps)
* [Troubleshooting / Quick Fixes](#troubleshooting--quick-fixes)

### [<ins>Back to Cisco AI Pods Runbook - C885A<ins>](../guide_cisco_ai_pods_runbook.md#cisco-ai-pods-c885a-m8-server-deployment-guide)

## Overview

This guide provides step-by-step instructions for deploying Cisco Intersight infrastructure using the `Cisco Terraform Easy-IMM` module.

## Prerequisites Checklist

- [ ] Terraform v1.3.0+ installed
- [ ] VS Code with YAML schema support
- [ ] Network connectivity to Intersight (SaaS/CVA/PVA)

## Prerequisite Steps

⚠️ **CRITICAL:** Before continuing make sure you have completed the steps in `network deployment` and `Prepare the Environment`.

* [Prepare the Environment](../guide_prepare_the_environment.md#prepare-the-environment)

### [<ins>Back to Table of Contents<ins>](#table-of-contents)

## Security Best Practices

1. **File Permissions:**
   ```bash
   # Ensure secret key files have restrictive permissions
   chmod 600 ./auth/*.pem
   
   # Verify no other users can read the files
   ls -la ./auth/
   ```

2. **Environment Variable Security:**

* **Add to your Shell profile for persistence**
   ```bash
   # ~/.bash_profile or ~/.zshrc
   cat >> ~/.bash_profile << 'EOF'
   export TF_VAR_intersight_api_key_id="your-api-key-id"
   export TF_VAR_intersight_secret_key="./auth/SecretKey.pem"
   EOF
   ```

* **Reload profile**
   ```bash
   source ~/.bash_profile
   ```

3. **API Key Rotation:**
   - Plan for regular API key rotation (every 90 to 180 days recommended)
   - Test new keys before decommissioning old ones
   - Update environment variables and secret files accordingly

### [<ins>Back to Table of Contents<ins>](#table-of-contents)

## Deployment Steps

⚠️ **IMPORTANT:** Follow the [Deployment Execution Order](../cisco-ai-pods-runbook.md#️-environment-deployment-execution-order) from the main runbook. Intersight deployment is **Phase 2** and requires **Phase 1 (Network Foundation)** to be complete first.

### 1. Prepare Environment

**Step 1a: Navigate to Intersight Directory**
```bash
cd FlashStack-AI/intersight
```

### Step 1: Prepare Global Settings

* If you are not using the SaaS version of intersight update the `global_settings.ezi.yaml` to point to your local instance.

1. **Update `global_settings.ezi.yaml`:**
   ```yaml
   global_settings:
     intersight_fqdn: <local-intersight-instance-fully-qualified-hostname>
   ```

### Step 2: Configure Intersight Authentication

Proper authentication setup is critical for successful Terraform deployment to Intersight. Follow these detailed steps:

1. **Generate API Key in Intersight Portal:**
   - Login to https://intersight.com or your local appliance https://[local-intersight-instance-fully-qualified-hostname]
   - **permissions** make sure you are logged in administrative credentials
   - Navigate to **Settings > API Keys**
   - Click **Generate API Key**
   - **Key Name:** Enter descriptive name (e.g., "terraform-deployment-key")
   - **copy api key:** Save in a secure location
   - **Download:** Save the generated **SecretKey.pem** file to a secure location

2. **Set Environment Variables:**

* **API Key ID (from Intersight portal)**
   ```bash
   export TF_VAR_intersight_api_key_id="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
   ```
   
* **Path to secret key file (adjust path as needed)**
   ```bash
   export TF_VAR_intersight_secret_key="/home/tyscott/Downloads/SecretKey.pem"
   ```

* **Policy Sensitive Variables**
   ```bash
   export TF_VAR_cco_password='secure_password'
   export TF_VAR_local_user_password_1='secure_password'
   export TF_VAR_snmp_auth_password_1='secure_password'
   export TF_VAR_snmp_auth_password_2='secure_password'
   export TF_VAR_snmp_privacy_password_1='secure_password'
   export TF_VAR_snmp_privacy_password_2='secure_password'
   ```


   
3. **Verify and Protect Secret Key File:**

   ```bash
   # Check file exists and has correct permissions
   ls -la ~/Downloads/SecretKey.pem
   
   # Verify file format (should start with -----BEGIN RSA PRIVATE KEY-----)
   head -1 ~/Downloads/SecretKey.pem
   
   # Should show: -rw------- (600 permissions)
   # If not, fix permissions:
   chmod 600 ~/Downloads/SecretKey.pem
   ```

4. **Test Connectivity:**

* **Test network connectivity**
   
   ```bash
   ping <intersight-saas-or-your-private-appliance-fqdn>
   ```
   
* **Test HTTPS connectivity**
   ```bash
   curl -k https://<intersight-saas-or-your-private-appliance-fqdn>/api/v1/organizations/Organizations
   ```
   
### 2. Initialize and Deploy

* **Initialize Terraform**

    ```bash
    terraform init
    ```

* **Validate configuration**

    ```bash
    terraform validate
    ```

* **Plan deployment**

    ```bash
    terraform plan -out="main.plan"
    ```

* **Apply configuration**

    ```bash
    terraform apply "main.plan"
    ```

### 3. Verify Deployment

* **Check deployed resources**

    ```bash
    terraform state list
    ```

* **View outputs**

    ```bash
    terraform output
    ```

### [<ins>Back to Table of Contents<ins>](#table-of-contents)

## Post-Deployment Validation

### Check Organizations
```bash
terraform output organizations
```

### Login to the intersight environment

* Check that the pools are created `Configure: Pools` in the left navigation pane
    * example pools:
        * IP
        * MAC
        * UUID

* Check that the policies are created `Configure: Policies` in the left navigation pane
    * example policies:
        * BIOS
        * Boot Order
        * Firmware
        * LAN Connectivity
        * NTP
        * Network Connectivity (DNS)
        * SNMP
        * Storage
        * Syslog
        * Virtual KVM
        * Virtual Media

* Check that the templates are created `Configure: Templates` in the left navigation pane
    * example templates:
        * UCS Server Profile Templates

* Check that the templates are created `Configure: Templates` in the left navigation pane
    * example profiles:
        * UCS Chassis Profiles
        * UCS Domain Profiles
        * UCS Server Profiles


## Next Steps

1. [Deploy C885A GPU Nodes](../c885/README.md#cisco-c885a-m8-server-configuration-guide)
2. [Deploy Pure Storage configuration](../pure_storage/README.md#cisco-ai-pods-pure-storage-configuration-guide)

### [<ins>Back to Table of Contents<ins>](#table-of-contents)

## Troubleshooting / Quick Fixes

### Authentication Issues

**Problem:** API Key Authentication Errors

#### Verify API key format (should be UUID)

```bash
echo $TF_VAR_intersight_api_key_id
```

The output should be similar to:

```bash
tyscott@TYSCOTT-DESKTOP:~$ echo $TF_VAR_intersight_api_key_id
987654321987654321987654/987654321987654321987654/987654321987654321987654
tyscott@TYSCOTT-DESKTOP:~$
```

#### Verify secret key file format

```bash
head -1 $TF_VAR_intersight_secret_key
```

Should start with: -----BEGIN RSA PRIVATE KEY-----

```bash
tyscott@TYSCOTT-DESKTOP:~$ head -1 $intersight_secret_key
-----BEGIN EC PRIVATE KEY-----
tyscott@TYSCOTT-DESKTOP:~$
```

* Note: The above command may fail if you are using relative paths in the variable

#### Check secret key file exists and has the correct permissions

```bash
echo $TF_VAR_intersight_secret_key
ll <output>
```

```bash
tyscott@TYSCOTT-DESKTOP:~$ echo $TF_VAR_intersight_secret_key
~/Downloads/SecretKeyv3.txt
tyscott@TYSCOTT-DESKTOP:~$ ll ~/Downloads/SecretKeyv3.txt
-rw------- 1 tyscott tyscott 248 Jun  4 14:21 /home/tyscott/Downloads/SecretKeyv3.txt
tyscott@TYSCOTT-DESKTOP:~$
```

Should show: -rw------- (600 permissions)

#### Fix environment variable if needed

```bash
export $TF_VAR_intersight_secret_ke="<correct-file-location>"
```

**Problem:** "Authentication failed" errors

Test API key in Intersight portal
* Login to Intersight
* Go to Settings > API Keys  
* Verify key exists and has correct permissions
* Regenerate key if necessary
 
For CVA/PVA, test connectivity

```bash
ping <intersight-appliance>
curl -k https://<intersight-appliance>/api/v1/organizations/Organizations
```

**Problem:** Permission denied errors

* Check API key organizational access
* Ensure the API key has required permissions:
    * Resource Group access
    * Domain Policy permissions
    * Pool and Policy management rights

### Execution Order Issues

**Problem:** Deploying out of sequence

* Always verify Phase 1 (Network) is complete first
* Reference: Main runbook deployment execution order
* Do not proceed with Intersight until network foundation is ready

### Resource Conflicts

* **Remove conflicting state**

    ```bash
    terraform state rm <resource>
    ```

* **Re-importing existing resources**

    ```bash
    terraform import <resource> <id>
    ```

### Module Version Issues

* **Update modules**

    ```bash
    terraform init -upgrade
    ```

* **Check module versions**

    ```bash
    terraform version
    ```

### [<ins>Back to Table of Contents<ins>](#table-of-contents)

---

**Note:** This guide covers X-Series specific configuration. Ensure that the networking environment is up and operational before attempting this section.

### [<ins>Back to Cisco AI Pods Runbook - C885A<ins>](../guide_cisco_ai_pods_runbook.md#cisco-ai-pods-c885a-m8-server-deployment-guide)
