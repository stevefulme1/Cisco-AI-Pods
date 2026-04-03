# Configure Active Directory LDAP Authentication for OpenShift

Ansible playbook that configures OpenShift OAuth to authenticate against Active Directory via LDAP/LDAPS, creates the `ldap-sync` project, deploys the LDAP group synchronization secret, RBAC, service account, and a CronJob that runs every hour to keep OpenShift groups in sync with AD.

**Reference:** [OpenShift LDAP Configuration](https://examples.openshift.pub/cluster-configuration/authentication/activedirectory-ldap/)

**Back to OpenShift README:** [OpenShift Deployment Order](../README.md)

---

## Table of Contents

- [Directory Structure](#directory-structure)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Variables Reference](#variables-reference)
- [What the Playbook Does](#what-the-playbook-does)
- [Post-Deployment Steps](#post-deployment-steps)
- [Troubleshooting / Testing LDAP](#troubleshooting--testing-ldap)
- [Manual Method](#manual-method)

---

## Directory Structure

```
oath_ldap/
├── configure_oath_ldap.yaml          # Main Ansible playbook
├── ca.crt                            # PEM bundle of LDAP CA certificates (provide your own)
├── script_vars/
│   └── vars.ezcai.example.yaml       # Example variables file
└── templates/                        # Jinja2 templates
    ├── active-directory.yaml.j2      # OpenShift OAuth identity provider config
    ├── ldap-sync.yaml.j2             # LDAPSyncConfig for group synchronization
    ├── ldap-cron.yaml.j2             # CronJob manifest (runs `oc adm groups sync` hourly)
    ├── project.yaml.j2               # ldap-sync namespace manifest
    ├── rbac-ldap-group-sync.yaml.j2  # ClusterRole for ldap-sync service account
    └── whitelist.txt.j2              # Group DN whitelist for ldap-sync
```

---

## Prerequisites

- Ansible with the `kubernetes.core` collection installed (`ansible-galaxy collection install kubernetes.core`)
- The `oc` CLI binary available on the Ansible controller host
- An OpenShift cluster token with `cluster-admin` privileges
- An Active Directory service account with read access to the relevant OUs
- **For LDAPS:** a `ca.crt` PEM bundle containing the certificate chain of the LDAP server(s)

Obtain the LDAP server certificate chain:

```bash
openssl s_client -showcerts -connect ldap-server.example.com:636 </dev/null 2>/dev/null \
  | awk '/BEGIN CERTIFICATE/,/END CERTIFICATE/' > ca.crt
```

---

## Quick Start

1. **Copy and edit the variables file:**

   ```bash
   cp script_vars/vars.ezcai.example.yaml script_vars/vars.yaml
   # edit script_vars/vars.yaml with your environment values
   ```

2. **Export sensitive credentials as environment variables** — the playbook reads these at runtime and never writes them to disk:

   ```bash
   export ldap_bind_password="<bind_password>"
   export openshift_api_url="https://api.<cluster>.<domain>:6443"
   export openshift_token_id="<token>"
   ```

   Obtain the token from the OpenShift web console:
   - Click your username (top-right) → **Copy login command** → **Display Token**

   ![Copy Login Command](../../images/copy_login_command.png)
   ![Display Token](../../images/display_token.png)

3. **Run the playbook:**

   ```bash
   ansible-playbook configure_oath_ldap.yaml
   ```

4. **Trigger the first sync manually** (LDAP groups must exist before assigning cluster roles):

   In the OpenShift console go to **Workloads → CronJobs**, find `ldap-group-sync`, click the three-dot menu, and select **Create Job**. Wait for the job to complete.

5. **Grant cluster-admin to your AD group(s):**

   ```bash
   oc adm policy add-cluster-role-to-group cluster-admin <ldap-group-name>
   ```

---

## Variables Reference

All variables live under the top-level `ldap:` key in `script_vars/vars.yaml`.

| Key | Required | Description |
|-----|----------|-------------|
| `base_dn` | Yes | LDAP base distinguished name (e.g. `DC=example,DC=com`) |
| `bind_dn` | Yes | DN of the service account used to bind to LDAP |
| `certificate_file_name` | Yes | Filename of the CA cert PEM bundle relative to the playbook directory (e.g. `ca.crt`) |
| `cluster_admins` | Yes | List of OpenShift group names to grant `cluster-admin` (added after first sync) |
| `group_uid_mappings` | Yes | Map of AD group DNs to short OpenShift group names, used in `ldap-sync.yaml` and `whitelist.txt` |
| `secure_ldap` | Yes | `true` to use LDAPS with CA verification; `false` for plain LDAP |
| `sync_url` | Yes | LDAP URL used by the sync CronJob (e.g. `ldaps://ad.example.com:636`) |
| `url` | Yes | Full LDAP search URL for the OAuth identity provider including base DN, attribute, scope, and filter |

### Example `vars.yaml`

```yaml
ldap:
  base_dn: DC=example,DC=com
  bind_dn: CN=Service Account,OU=Service Accounts,DC=example,DC=com
  certificate_file_name: ca.crt
  cluster_admins:
    - lab-admins
  group_uid_mappings:
    "CN=Lab Admin,OU=Cisco Employees,DC=example,DC=com": lab-admins
  secure_ldap: true
  sync_url: ldaps://ad.example.com:636
  url: "ldaps://ad.example.com:636/DC=example,DC=com?sAMAccountName?sub?(&(objectclass=*)((memberOf=CN=Domain Admins,OU=Users,DC=example,DC=com)))"
```

---

## What the Playbook Does

The playbook executes the following steps in order:

1. Loads variables from `script_vars/`
2. Logs in to OpenShift using the token and API URL from environment variables
3. Creates the `ldap-bind-password` Secret in `openshift-config`
4. Creates the `ldap-ca-cert` ConfigMap in `openshift-config` (LDAPS only)
5. Applies the `OAuth` identity provider config (`active-directory.yaml.j2`)
6. Creates the `ldap-sync` namespace
7. Renders `ldap-sync.yaml` and `whitelist.txt` locally from templates
8. Creates the `ldap-sync` Secret (with or without CA cert depending on `secure_ldap`)
9. Applies the `ldap-group-sync` ClusterRole and ClusterRoleBinding
10. Creates the `ldap-sync` ServiceAccount and grants it the `ldap-group-sync` ClusterRole
11. Deploys the `ldap-group-sync` CronJob (runs `oc adm groups sync` every hour)
12. Removes the locally rendered `ldap-sync.yaml` and `whitelist.txt` files

---

## Post-Deployment Steps

After the first CronJob sync completes, grant cluster-admin to the groups defined in `cluster_admins`:

```bash
oc adm policy add-cluster-role-to-group cluster-admin <ldap-group-name>
```

---

## Troubleshooting / Testing LDAP

### Update the ldap-sync Secret

If you need to correct the sync configuration after deployment:

```bash
oc set data secret/ldap-sync -n ldap-sync \
  --from-file=ldap-sync.yaml=<path-to-ldap-sync.yaml>

oc set data secret/ldap-sync -n ldap-sync \
  --from-file=whitelist.txt=<path-to-whitelist.txt>

oc set data secret/ldap-sync -n ldap-sync \
  --from-file=ca.crt=<path-to-ca.crt>
```

### List members of a group (transitive)

```bash
ldapsearch -W -H ldaps://ad.example.com:636 \
  -D 'CN=Administrator,OU=Users,DC=example,DC=com' \
  -xLL -b "DC=example,DC=com" \
  "(memberof:1.2.840.113556.1.4.1941:=CN=Domain Admins,OU=Users,DC=example,DC=com)" dn
```

- `-b` — base DN
- `-D` — bind DN
- `-W` — prompt for bind password

### Look up a user's attributes and group memberships

```bash
ldapsearch -x -H ldaps://ad.example.com:636 \
  -D 'CN=Administrator,OU=Users,DC=example,DC=com' \
  -b "DC=example,DC=com" \
  -W '(sAMAccountName=<username>)'
```

### Run the sync manually from the CLI

```bash
oc adm groups sync \
  --whitelist=whitelist.txt \
  --sync-config=ldap-sync.yaml \
  --confirm
```

---

## Manual Method

If you prefer to apply resources manually without Ansible:

```bash
# Bind password secret
oc create secret generic ldap-bind-password \
  --from-literal=bindPassword='<bind_password>' \
  -n openshift-config

# CA cert ConfigMap (LDAPS only)
oc create configmap ldap-ca-cert \
  --from-file=ca.crt=./ca.crt \
  -n openshift-config

# OAuth identity provider
oc apply -f active-directory.yaml

# Grant cluster-admin after first sync
oc adm policy add-cluster-role-to-group cluster-admin <ldap-group-name>
```

### LDAP Synchronization Project and Secret

```bash
oc new-project ldap-sync

# With CA (LDAPS)
oc create secret generic ldap-sync \
  --from-file=ldap-sync.yaml=ldap-sync.yaml \
  --from-file=whitelist.txt=whitelist.txt \
  --from-file=ca.crt=ca.crt \
  -n ldap-sync

# Without CA (plain LDAP)
oc create secret generic ldap-sync \
  --from-file=ldap-sync.yaml=ldap-sync.yaml \
  --from-file=whitelist.txt=whitelist.txt \
  -n ldap-sync
```

### Example LDAP Search URL Format

```
ldaps://ad.example.com:636/DC=example,DC=com?sAMAccountName?sub?(&(objectclass=*)(memberOf=CN=Domain Admins,OU=Users,DC=example,DC=com))
```
