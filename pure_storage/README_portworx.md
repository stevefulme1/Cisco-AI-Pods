# Portworx Deployment with Pure Storage

This guide covers the Portworx-specific flow in this folder:

1. Generate `pure.json` credentials using Pure APIs.
2. Install Portworx Operator and StorageCluster on OpenShift.
3. Create Portworx storage classes from template values.

**Back to OpenShift README:** [OpenShift Deployment Order](../openshift/README.md)

## Table of Contents

- [Prerequisites](#prerequisites)
- [Configuration Inputs](#configuration-inputs)
- [Step 1: Create pure.json](#step-1-create-purejson)
- [Step 2: Install Portworx](#step-2-install-portworx)
- [Step 3: Validate Portworx and Storage Classes](#step-3-validate-portworx-and-storage-classes)
- [Step 4: Test PVC Provisioning](#step-4-test-pvc-provisioning)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- Ansible collections installed from `requirements.yaml`
- Python dependencies installed from `requirements.txt`
- OpenShift cluster access (`oc`) with sufficient privileges
- Pure API tokens for every array/blade listed in variables

Install dependencies:

```bash
ansible-galaxy collection install -r requirements.yaml
pip install -r requirements.txt
```

[Back to Table of Contents](#table-of-contents)

## Configuration Inputs

Primary variable file:

- `script_vars/vars.ezcai.yaml`

Important keys:

- `pure_storage.flash_arrays[]` and `pure_storage.flash_blades[]`
- `pure_storage.portworx.namespace`
- `pure_storage.portworx.cluster_name`
- `pure_storage.portworx.operator_source`
- `pure_storage.portworx.storage_classes[]`
- `pure_storage.portworx.version`

Environment variables used by playbooks:

```bash
# One token per api_token_id used in vars file
export pure_api_token_1="<flasharray_token>"
export pure_api_token_2="<flashblade_token>"

# OpenShift access (for install_portworx.yaml)
export openshift_api_url="https://api.<cluster>.<domain>:6443"
export openshift_token_id="<token>"
```

[Back to Table of Contents](#table-of-contents)

## Step 1: Create pure.json

Generate the Portworx credential payload:

```bash
ansible-playbook create_pure_json.yaml
```

What this does:

- Creates/rotates a Portworx API user (`pure_storage.portworx.array_user`) on each FlashArray and FlashBlade.
- Collects generated API tokens.
- Renders `pure.json` from `templates/pure.json.j2`.

Expected output:

- `pure.json` file in this folder

[Back to Table of Contents](#table-of-contents)

## Step 2: Install Portworx

Deploy the operator and storage components:

```bash
ansible-playbook install_portworx.yaml
```

What this does:

1. Logs in to OpenShift.
2. Creates namespace from `pure_storage.portworx.namespace`.
3. Creates secret `px-pure-secret` from local `pure.json` (if it does not already exist).
4. Creates Portworx subscription `portworx-certified` in `openshift-operators`.
5. Waits for deployment `portworx-operator` to become ready.
6. Prompts for confirmation before deploying StorageCluster.
7. Applies `templates/storage-cluster.yaml.j2`.
8. Applies one StorageClass per entry in `pure_storage.portworx.storage_classes` using `templates/storage-classes.yaml.j2`.

[Back to Table of Contents](#table-of-contents)

## Step 3: Validate Portworx and Storage Classes

```bash
oc get pods -n openshift-operators | grep portworx
oc get pods -n <portworx-namespace>
oc get storagecluster -n <portworx-namespace>
oc get storageclass
```

Replace `<portworx-namespace>` with the value in `pure_storage.portworx.namespace` (default example is `portworx`).

[Back to Table of Contents](#table-of-contents)

## Step 4: Test PVC Provisioning

Example manifests are in `examples/`.

```bash
cd examples
oc apply -f pvc/
oc get pvc -A
```

Confirm PVCs bind successfully and backing volumes are created.

[Back to Table of Contents](#table-of-contents)

## Troubleshooting

- `pure.json` not generated:
  - Ensure every `api_token_id` in variables has a matching `pure_api_token_<id>` environment variable.
- Portworx operator not ready:
  - Check subscription and CSV in `openshift-operators`.
- Secret already exists with stale data:
  - Delete and recreate `px-pure-secret` or update it from regenerated `pure.json`.
- StorageCluster not progressing:
  - Check events and describe the StorageCluster resource.

Helpful commands:

```bash
oc get subscription -n openshift-operators | grep portworx
oc get csv -n openshift-operators | grep -i portworx
oc describe storagecluster -n <portworx-namespace>
oc get events -n <portworx-namespace> --sort-by=.metadata.creationTimestamp
```

[Back to Table of Contents](#table-of-contents)
