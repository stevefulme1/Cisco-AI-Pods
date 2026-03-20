# Configure OATH LDAP Authentication for OpenShift

## Source URL

[OpenShift LDAP Configuration](https://examples.openshift.pub/cluster-configuration/authentication/activedirectory-ldap/)

## Table of Content

  * [Prerequisites](#prerequisites): Prepare for deployment.
  * [Active Directory OAuth Ansible Module](#execute-the-active-directory-oauth-ansible-module): Deploy Active Directory OAuth integration with ansible module.
  * [Troubleshooting / Testing LDAP](#troubleshooting--updates--testing-ldap)`: Tools/Methods to troubleshooting LDAP.
  * [Run the Portworx install module](#manual-method)`: Deploy Active Directory OAuth integration manually.

## Prerequisites

* If using secure LDAP, build `ca.crt` with the required PEM certificates from the LDAP servers.  Can contain multiple PEM certificates.

* Obtain LDAP Server Certificates

```bash
openssl s_client -showcerts -connect ldap-server.example.com:636
```

### [Back to Table of Content](#table-of-content)

## Execute the Active Directory OAuth Ansible Module

1. Fill out the variables in the `script_vars/vars.ezcai.yaml` folder/file according to your environment.

2. Load Sensitive Variables into the Environment.

![Copy Login Command](../../images/copy_login_command.png)

![Display Token](../../images/display_token.png)

```bash
export ldap_bind_password="bind_password"
export openshift_api_url="api_url"
export openshift_token_id="token_value"
```

3. Execute the ansible script.

```bash
ansible-playbook main.yaml
```

* The LDAP Groups need to synchronize before you can add group/groups to the cluster-admin role.

4. Run the CronJob.

* Go to `Workloads` > `CronJobs`
* Run the `ldap-grou-sync` CronJob from the 3 dots: `Start Job`

5. After the 1st CronJob completes, add any groups necessary to the cluster-admin role.

```bash
oc adm policy add-cluster-role-to-group cluster-admin <ldap-group-name>
```

### [Back to Table of Content](#table-of-content)

## Troubleshooting / Updates / Testing LDAP

If you need to make corrections to the ldap-sync secret.

```bash
oc set data secret/ldap-sync -n ldap-sync --from-file=ldap-sync.yaml=<path-to-ldap-sync.yaml>
oc set data secret/ldap-sync -n ldap-sync --from-file=whitelist.txt=<path-to-whitelist.txt>
oc set data secret/ldap-sync -n ldap-sync --from-file=ca.crt=<path-to-ca.crt>
```

### Testing LDAP

* Get Members of a Group

```bash
ldapsearch -W -H ldap://ad.example.com:389 \
  -D 'CN=Administrator,OU=Users,DC=example,DC=com' \
  -xLL -b "DC=example,DC=com" "(memberof:1.2.840.113556.1.4.1941:=CN=Domain Admins,OU=Users,DC=example,DC=com)" dn
```

1. `-b`: base_dn
2. `-D`: bind_dn
3. `-W`: prompt for password.

* Lookup user attributes/memberships

```bash
ldapsearch -x -H ldap://ad.example.com:389 \
  -D 'CN=Administrator,OU=Users,DC=example,DC=com' \
  -b "DC=example,DC=com" \
  -W '(sAMAccountName=Administrator)'
```

1. `-b`: base_dn.
2. `-D`: bind_dn.
3. `-W`: prompt for password.

### [Back to Table of Content](#table-of-content)

## Manual Method

```bash
oc create secret generic ldap-bind-password --from-literal=bindPassword='' -n openshift-config
oc create configmap ldap-ca-cert --from-file=ca.crt=./ca.crt -n openshift-config
oc apply -f <ldap-config-file>.yaml
oc adm policy add-cluster-role-to-group cluster-admin <ldap-group-name>
```

### LDAP Config File

```yaml
apiVersion: config.openshift.io/v1
kind: OAuth
metadata:
  name: cluster
spec:
  identityProviders:
    - name: ActiveDirectory
      mappingMethod: claim
      type: LDAP
      ldap:
        attributes:
          email: [mail]
          id: [sAMAccountName]
          name: [cn]
          preferredUsername: [sAMAccountName]
        bindDN: <bind_dn>
        bindPassword:
          name: ldap-bind-password # Name of a secret containing the bind password
        ca:
          name: ldap-ca-cert # Name of the ConfigMap with the CA certificate
        insecure: false
        url: <ldap_search_url>
```

### Example Input

* ldap_search_url: ldaps://ldap1.example.com:636/DC=example,DC=com?sub?(&(objectclass=*))(|(memberOf=CN=Users,DC=example,DC=com))

### LDAP Synchronization

```bash
oc new-project ldap-sync
oc create secret generic ldap-sync \
    --from-file=ldap-sync.yaml=ldap-sync.yaml \
    --from-file=whitelist.txt=whitelist.txt \
    --from-file=ca.crt=ldap-ca.crt
```

### Example LDAP Sync File

```yaml
kind: LDAPSyncConfig
apiVersion: v1
url: <ldap_url>
bindDN: <bind_dn>
bindPassword: '<bind_password>'
insecure: false # If URL is Secure
ca: /ldap-sync/ca.crt # If URL is Secure
groupUIDNameMapping:
  <list_of_group_mappings>
augmentedActiveDirectory:
    groupsQuery:
        derefAliases: never
        pageSize: 0
    groupUIDAttribute: dn
    groupNameAttributes: [ cn ]
    usersQuery:
        baseDN: "<base_dn>"
        derefAliases: never
        filter: (objectclass=person)
        pageSize: 0
        scope: sub
        timeout: 0
    userNameAttributes: [ sAMAccountName ]
    groupMembershipAttributes: [ "memberOf:1.2.840.113556.1.4.1941:" ]
```

### Example LDAP CronJob Sync file

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: ldap-group-sync
  namespace: ldap-sync
spec:
  # Format: https://en.wikipedia.org/wiki/Cron
  schedule: '@hourly'
  suspend: false
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: ldap-sync
          restartPolicy: Never
          containers:
            - name: oc-cli
              command:
                - /bin/oc
                - adm
                - groups
                - sync
                - --whitelist=/ldap-sync/whitelist.txt
                - --sync-config=/ldap-sync/ldap-sync.yaml
                - --confirm
              image: registry.redhat.io/openshift4/ose-cli
              imagePullPolicy: Always
              volumeMounts:
              - mountPath: /ldap-sync/
                name: config
                readOnly: true
          volumes:
          - name: config
            secret:
              defaultMode: 420
              secretName: ldap-sync
```

### [Back to Table of Content](#table-of-content)
