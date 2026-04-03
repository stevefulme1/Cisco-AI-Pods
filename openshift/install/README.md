# OpenShift Install — Manifest Generation

This directory contains an Ansible playbook and supporting files to generate the manifests needed to deploy a bare-metal OpenShift cluster via **Cisco iServer** and the **OpenShift Assisted Installer**. It also includes a Python module for generating more complex output artifacts.

**Back to OpenShift README:** [OpenShift Deployment Order](../README.md)

## Table of Contents

- [OpenShift Install — Manifest Generation](#openshift-install--manifest-generation)
  - [Table of Contents](#table-of-contents)
  - [Directory Structure](#directory-structure)
  - [Prerequisites](#prerequisites)
  - [Quick Start](#quick-start)
  - [Python Module Usage](#python-module-usage)
    - [Example: export sensitive variables and validate only](#example-export-sensitive-variables-and-validate-only)
    - [Example: export sensitive variables and generate output](#example-export-sensitive-variables-and-generate-output)
  - [Variables Reference](#variables-reference)
    - [`openshift.install.bare_metal`](#openshiftinstallbare_metal)
    - [`fabric_interconnects[]`](#fabric_interconnects)
    - [`iso_web_server`](#iso_web_server)
    - [`servers[]`](#servers)
    - [`openshift.operators`](#openshiftoperators)
    - [`proxy` (optional)](#proxy-optional)
  - [Feature Flags](#feature-flags)
  - [Generated Output](#generated-output)
  - [Security Notes](#security-notes)

---

## Directory Structure

```
install/
├── create_install_manifest_files.yaml   # Main Ansible playbook
├── generate_server_and_nmstate_templates.py  # Python module for complex assisted-installer output generation
├── script_vars/
│   └── vars.ezcai.example.yaml          # Example variables file
├── tasks/
│   ├── cilium.yaml                      # Cilium CNI manifest tasks
│   ├── persistent_net_rules.yaml        # NVIDIA Network Operator udev rule tasks
│   └── proxy.yaml                       # HTTP/HTTPS proxy manifest tasks
├── templates/                           # Jinja2 templates
│   ├── cilium-config.yaml.j2            # CiliumConfig custom resource
│   ├── cilium-network.yaml.j2           # Cluster network config (kube-proxy replacement)
│   ├── cilium-subscription.yaml.j2      # Cilium operator subscription
│   ├── iserver-cluster.json.j2          # iServer cluster manifest
│   ├── iserver-proxy.json.j2            # iServer proxy manifest
│   ├── iserver-web.json.j2              # iServer ISO web server manifest
│   ├── 70-machine-config-udev-network.yaml.j2
│   ├── 70-persistent-net.rules.j2
│   ├── 99-kernel-arguments.yaml.j2
│   ├── 99-kubelet-config-memory.yaml.j2
│   ├── 99-node-disruption-policy.j2
│   ├── 99-nvme-nqn-generate.yaml.j2
│   └── 99-portworx-multipathd-config.yaml.j2
└── assisted-installer/                  # Generated output directory
    ├── cluster.json
    ├── ssh.pub
    ├── web_server.json
    └── manifests/                       # OpenShift manifests for Assisted Installer
```

[Back to Table of Contents](#table-of-contents)

---

## Prerequisites

- Ansible installed with the following collections:
  - `ansible.builtin`
  - `community.general` (for `json_query` filter)
- Use the iServer executable downloaded from the datacenter/iserver GitHub releases to manage the target UCS Server inventory
- An ISO web server reachable from the target nodes
- An SSH key pair for cluster node access

[Back to Table of Contents](#table-of-contents)

---

## Quick Start

1. **Copy the example variables file** and populate it with your environment's values:

   ```bash
   cp script_vars/vars.ezcai.example.yaml script_vars/vars.yaml
   ```

2. **Edit `script_vars/vars.yaml`** — at a minimum configure:
   - `openshift.install.bare_metal.cluster_name`
   - `openshift.install.bare_metal.base_dns_domain`
   - `openshift.install.bare_metal.cluster_version`
   - `openshift.install.bare_metal.cluster_networking` (API VIP, Ingress VIP, machine network, DNS)
   - `openshift.install.bare_metal.fabric_interconnects` (iServer inventory, if using servers with `fabric_interconnect`)
   - `openshift.install.bare_metal.iso_web_server` (IP, image URL, upload directory)
   - `openshift.install.bare_metal.servers` (hostnames, roles, interfaces, MACs)

3. **Run the playbook**:

   ```bash
   ansible-playbook create_install_manifest_files.yaml
   ```

4. **Run the Python module** to generate `server.json` and `nmstate_*.yaml` in `assisted-installer/`:

  ```bash
  cd openshift/install
  export redfish_password_1='replace-with-secret-1'
  export redfish_password_2='replace-with-secret-2'
  export fi_password_1='replace-with-fi-secret-1'
  export fi_password_2='replace-with-fi-secret-2'

  # Validate credentials only
  python generate_server_and_nmstate_templates.py --check-env

  # Generate outputs
  python generate_server_and_nmstate_templates.py
  ```

5. **Prepare the iServer environment**, following:  **🔗 [iServer Console Setup](https://github.com/datacenter/iserver/blob/main/doc/ocp/Console.md)**

6. **Run iServer from the `assisted-installer/` directory**.

  First, check the data:

  ```bash
  iserver create ocp cluster bm --dir ./ --mode check
  ```

  Then run:

  ```bash
  iserver create ocp cluster bm --dir ./ --mode install
  ```

[Back to Table of Contents](#table-of-contents)

---

## Python Module Usage

Run the Python module as a required step to generate `server.json`, `nmstate_*.yaml`, and extract the iServer Linux release asset into `assisted-installer/`.

### Example: export sensitive variables and validate only

```bash
cd openshift/install

export redfish_password_1='replace-with-secret-1'
export redfish_password_2='replace-with-secret-2'
export fi_password_1='replace-with-fi-secret-1'
export fi_password_2='replace-with-fi-secret-2'

# Optional: helps avoid GitHub API rate-limit issues when downloading release metadata/assets
export GITHUB_TOKEN='replace-with-github-token'

python generate_server_and_nmstate_templates.py --check-env
```

### Example: export sensitive variables and generate output

```bash
cd openshift/install

export redfish_password_1='replace-with-secret-1'
export redfish_password_2='replace-with-secret-2'
export fi_password_1='replace-with-fi-secret-1'
export fi_password_2='replace-with-fi-secret-2'
export GITHUB_TOKEN='replace-with-github-token'  # optional

python generate_server_and_nmstate_templates.py
```

[Back to Table of Contents](#table-of-contents)

---

## Variables Reference

All variables live under the top-level `openshift:` key in your variables file. The table below describes the most important fields.

### `openshift.install.bare_metal`

| Key | Required | Description |
|-----|----------|-------------|
| `cluster_name` | Yes | Short name of the cluster (e.g. `ai-pods`) |
| `base_dns_domain` | Yes | Base DNS domain (e.g. `example.com`) |
| `cluster_version` | Yes | OpenShift version to install (e.g. `4.20.16`) |
| `cluster_networking.api.v4` | Yes (multi-node) | API VIP address |
| `cluster_networking.ingress.v4` | Yes (multi-node) | Ingress VIP address |
| `cluster_networking.cluster_network.v4_cidr` | Yes | Pod network CIDR |
| `cluster_networking.cluster_network.v4_host_prefix` | Yes | Per-node subnet prefix length |
| `cluster_networking.service_network.v4_cidr` | Yes | Service network CIDR |
| `cluster_networking.machine_network_gateway.v4_gateway` | Yes | Node network gateway in CIDR notation |
| `cluster_networking.dns_servers` | Yes | List of DNS server IPs |
| `cluster_networking.cni` | No | CNI plugin (`OVNKubernetes` or `Cilium`); defaults to `OVNKubernetes` |
| `ntp_servers` | No | List of NTP server addresses |
| `ssh_public_key_file` | Yes | Path to SSH public key file for node access |
| `fabric_interconnects` | Conditional | List of iServer Fabric Interconnect entries (required when any `servers[]` entry uses `fabric_interconnect`) |
| `iso_web_server` | Yes | ISO web server configuration (see below) |
| `servers` | Yes | List of cluster node definitions (see below) |
| `proxy` | No | HTTP/HTTPS proxy settings (see below) |

### `fabric_interconnects[]`

| Key | Description |
|-----|-------------|
| `ip` | Management IP of the Fabric Interconnect |
| `inventory_id` | iServer inventory identifier |
| `username` / `password` | iServer credentials (use Ansible Vault for passwords) |

### `iso_web_server`

| Key | Description |
|-----|-------------|
| `ip` | IP or hostname of the web server |
| `image_base_url` | Base URL used by iServer to download ISOs |
| `image_upload_directory` | Local path on the web server to upload ISOs |
| `username` | (Optional) Username for SSH-based upload |
| `ssh_public_key_file` | (Optional) SSH public key for passwordless upload |
| `password` | (Optional) Environment variable suffix for password lookup |

### `servers[]`

Each entry describes one cluster node:

| Key | Description |
|-----|-------------|
| `hostname` | Node hostname |
| `role` | `master` or `worker` |
| `fabric_interconnect.id` | Index into the `fabric_interconnects` list |
| `fabric_interconnect.inventory_id` | iServer inventory ID for this node |
| `redfish.ip` / `.username` / `.password` / `.type` | Redfish BMC settings (alternative to FI-based boot). `password` is an environment variable suffix, not a plain-text secret. |
| `interfaces.ethernet[]` | Ethernet interface definitions (name, MAC, IPv4, MTU, LLDP) |
| `interfaces.bond[]` | Bond interface definitions |

### `openshift.operators`

| Key | Description |
|-----|-------------|
| `cilium.cluster_network.v4_cidr` | Pod CIDR to configure in CiliumConfig |
| `cilium.cluster_network.v4_host_prefix` | Per-node prefix size for Cilium IPAM |
| `cilium.enable_kube_proxy_replacement` | Enable full kube-proxy replacement in Cilium |
| `cilium.enable_hubble_metrics` | Enable extended Hubble flow metrics |
| `cilium.download_url` | URL to the Cilium/Clife operator tarball |
| `nvidia_network_operator.persistent_net_rules` | Per-host interface-to-MAC mappings for udev renaming |
| `portworx.enabled` | Generate Portworx multipathd MachineConfig manifests |

### `proxy` (optional)

| Key | Description |
|-----|-------------|
| `http_proxy` | HTTP proxy URL |
| `https_proxy` | HTTPS proxy URL |
| `no_proxy` | Comma-separated no-proxy list |
| `username` | Proxy username (injected into the URL) |
| `password` | Environment variable suffix for proxy password lookup |

[Back to Table of Contents](#table-of-contents)

---

## Feature Flags

The playbook conditionally generates additional manifests based on the variables provided:

| Condition | Manifests generated |
|-----------|---------------------|
| `openshift.operators.cilium.download_url` is set | Downloads Cilium tarball, renders `ciliumconfig.yaml` |
| `cilium.enable_kube_proxy_replacement: true` | Also renders `subscription.yaml` and `cluster-network-02-config-local.yaml` |
| `cilium.enable_hubble_metrics: true` | Enables extended Hubble metrics in `CiliumConfig` |
| `nvidia_network_operator.persistent_net_rules` is set | Renders `70-machine-config-udev-network.yaml` udev MachineConfig |
| `portworx.enabled: true` | Renders `99-portworx-multipathd-config-{master,worker}.yaml` |
| `openshift_install.proxy` is set | Renders `proxy.json` for iServer |

[Back to Table of Contents](#table-of-contents)

---

## Generated Output

After the playbook runs, the `assisted-installer/` directory will contain:

| File | Description |
|------|-------------|
| `cluster.json` | iServer cluster creation payload |
| `server.json` | Assisted Installer server inventory generated from `openshift.install.bare_metal.servers` |
| `nmstate_*.yaml` | Generated unique nmstate network profiles referenced by `server.json` |
| `ssh.pub` | SSH public key for node access |
| `web_server.json` | iServer ISO web server payload |
| `proxy.json` | iServer proxy payload (if proxy is configured) |
| `manifests/` | MachineConfig and operator manifests injected at install time |

When running `generate_server_and_nmstate_templates.py` (without `--check-env`), the script also downloads the latest Linux `.tar.gz` asset from [datacenter/iserver releases](https://github.com/datacenter/iserver/releases) and extracts it into `assisted-installer/`. If an iServer Linux `.tar.gz` archive already exists in `assisted-installer/`, the script reuses that local archive and skips downloading from GitHub.

[Back to Table of Contents](#table-of-contents)

---

## Acknowledgments

Special credit to GitHub user **akaliwod** for extensive work on the iServer project:

- [datacenter/iserver](https://github.com/datacenter/iserver)

[Back to Table of Contents](#table-of-contents)

---

## Security Notes

- **Never commit plain-text passwords.** Use [Ansible Vault](https://docs.ansible.com/ansible/latest/vault_guide/index.html) to encrypt sensitive values in your variables file.
- Proxy passwords and ISO web server passwords are resolved at runtime from environment variables (e.g., `export iso_web_server_password_<suffix>=...`), keeping credentials out of the YAML.
- Redfish/BMC passwords are required at runtime via environment variables using this format: `redfish_password_<suffix>`.
- Fabric interconnect passwords are required at runtime via environment variables using this format: `fi_password_<suffix>`.
- The `<suffix>` comes from `servers[].redfish.password` for redfish hosts, or the resolved `fabric_interconnects[].password` value for FI-backed hosts.
- You can define as many suffixes as needed (for example: `redfish_password_1`, `redfish_password_2`, `fi_password_1`, `fi_password_17`, ...).
- Example: if `password: 1` in YAML, set `export redfish_password_1='your-redfish-secret'` or `export fi_password_1='your-fi-secret'` (depending on host type) before running the generator.
- The nmstate/server generator exits with an error if a required `redfish_password_*` or `fi_password_*` environment variable is missing.
- To validate only required credential env vars without generating files, run: `python generate_server_and_nmstate_templates.py --check-env`
- If GitHub API rate limits are encountered during release download, set `GITHUB_TOKEN` to increase API limits.
- The ISO web server template disables TLS verification when `https://` is detected in `image_base_url`. Use a trusted certificate in production environments.

[Back to Table of Contents](#table-of-contents)

