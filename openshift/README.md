# OpenShift Deployment Order

Use this guide to run the OpenShift workflow in the correct sequence.

Top-level project README:
- [Cisco-AI-Pods README](../README.md)

## Run Order

1. Install
- Generates base Assisted Installer payloads (`cluster.json`, `web_server.json`, `ssh.pub`) and, via the Python module, creates `server.json` plus `nmstate_*.yaml` profiles used for host networking and inventory mapping to be consumed with `iserver` module.
- [install README](install/README.md)

2. Certificates
- Applies trust bundle, ingress wildcard certificate, and API server certificate updates, then validates certificate rollout/state on the cluster.
- [certificates README](certificates/README.md)

3. Pure Storage Portworx Install
- Prepares Pure credentials, installs Portworx Operator/StorageCluster, and creates StorageClasses for persistent workload storage.
- [Pure Storage Portworx README](../pure_storage/README_portworx.md)

4. OATH LDAP (Optional for Active Directory Authentication)
- Configures OpenShift OAuth/LDAP integration for AD sign-in and deploys group sync resources (including scheduled synchronization).
- [oath_ldap README](oath_ldap/README.md)

5. Base Operators
- Installs foundational operators needed before higher-level platform automation.
- [base_operators README](base_operators/README.md)
- Note: Gitea is only required if another Git service is not available.
- [base_operators/gitea README](base_operators/gitea/README.md)

6. OpenShift GitOps
- Generates and stages GitOps repository content (Helm/OLM trees and rendered Argo CD applications) consumed by OpenShift GitOps.
- [openshift-gitops README](openshift-gitops/README.md)

Back to top-level:
- [Cisco-AI-Pods README](../README.md)
