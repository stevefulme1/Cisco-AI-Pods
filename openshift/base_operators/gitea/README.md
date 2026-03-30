# Ansible Playbook Outline to Install Red Hat Gitea on OpenShift 4.21

## Prerequisites:

* Ansible 6.7 or later installed on the installer host.
* Python 3 and required Python modules (openshift Ansible module).
* Access to the OpenShift 4.2X cluster with `oc` CLI configured.

### Load the Variables to Environment

Obtain the API token and url by logging into OpenShift > User > Copy Login

![Copy Login Command](../images/copy_login_command.png)

![Display Token](../images/display_token.png)

```bash
export openshift_api_url="api_url"
export openshift_token_id="token_value"
```

### How to Run

1. Run the playbook:

```bash
ansible-playbook install_gitea.yaml
```

2. Verify the installation:

```bash
oc get pods -n gitea-operator
```

## Notes:

* This playbook creates the namespace, subscribes to the Gitea Operator from the Red Hat Operator Catalog, and waits for the operator to be ready.
* Adjust the subscription channel and source as per your OpenShift environment.
* Ensure the k8s Ansible module is installed (`pip install openshift`).
* For full automation, integrate this playbook into your existing OpenShift installation automation.
