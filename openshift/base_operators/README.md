# Base Operators Overview

This folder contains base operator installation automation for OpenShift.

Use this page as a high-level index, then open the README in each sub-folder for full prerequisites, variables, run commands, and validation steps.

**Back to OpenShift README:** [OpenShift Deployment Order](../README.md)

## Operator Guides

- Gitea Operator: [gitea/README.md](gitea/README.md)
- OpenShift GitOps Operator: [openshift-gitops/README.md](openshift-gitops/README.md)

## Gitea Note

Use Gitea to create an internal Git source for onboarding repositories only when an existing Git service is not available.

It is not recommended to use public Git repositories for this workflow, because much of the repository content is specific to each customer environment and can include sensitive infrastructure configuration details.

## Scope

These playbooks are intended to bootstrap foundational operator capabilities before higher-level platform and workload automation.

## Troubleshooting

- Operator subscriptions do not install:
	- Check cluster OperatorHub/catalog sources and confirm namespace/operatorgroup prerequisites are present.
	- Validate pull access and image registry reachability from cluster nodes.
- CRDs are missing after install:
	- Wait for CSV to reach `Succeeded`, then re-check CRD registration.
	- Use the subfolder runbooks for operator-specific verification steps.
- GitOps bootstrap dependencies fail:
	- Ensure the OpenShift GitOps base operator is healthy before running higher-level GitOps content generation.
	- See [openshift-gitops/README.md](openshift-gitops/README.md).
