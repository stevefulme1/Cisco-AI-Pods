# Prepare the Environment

⚠️ **CRITICAL:** Make sure to complete all tasks below for environment preparation.

## Top Level Documents
* [Main README](README.md)

## Table of Contents
* [Module Dependencies](#module-dependencies)
* [Install Git](#install-git)
* [Configure Git Credentials](#configure-git-credentials)
* [Clone Repositories](#clone-repositories)
* [Install Visual Studio Code](#install-visual-studio-code)
* [Install Visual Studio Code Extensions](#install-visual-studio-code-extensions)
* [Install Python](#install-python)
* [Create a Virtual Environment through Visual Studio Code](#create-a-virtual-environment-through-visual-studio-code)
* [YAML Schema for auto-completion, Help, and Error Validation](#yaml-schema-for-auto-completion-help-and-error-validation)
* [Install Ansible](#install-ansible-on-ubuntu)
* [Install Terraform](#install-terraform-on-ubuntu)

## Module Dependencies

| Component | Minimum Version | Recommended | Notes |
|-----------|----------------|-------------|-------|
| Ansible | 2.15.0 | 2.17+ | Storage automation |
| Terraform | 1.3.0 | 1.14+ | Core automation |
| Intersight Terraform Provider | 1.0.64 | Latest | SaaS compatible |
| Everpure Collection | 1.35 | Latest | Install from repository root `requirements.yaml` |
| Python | 3.9 | 3.9+ | Ansible and OpenShift dependency |
| Python Modules | N/A | Latest | Install from repository root `requirements.txt` |

### [<ins>Back to Table of Contents<ins>](#table-of-contents)

## Install Git

```bash
sudo apt update && sudo apt install -y git
```

### Validate Git Installation

```bash
git --version
```

### Example Output

```bash
$ git --version
git version 2.34.1
$ 
```

### [<ins>Back to Table of Contents<ins>](#table-of-contents)

## Configure Git Credentials

```bash
git config --global user.name "<username>"   
git config --global user.email "<email>"
```

### [<ins>Back to Table of Contents<ins>](#table-of-contents)

## Clone Repositories

```bash
git clone https://github.com/scotttyso/intersight-tools
git clone https://github.com/scotttyso/Cisco-AI-Pods
cd Cisco-AI-Pods
```

### [<ins>Back to Table of Contents<ins>](#table-of-contents)

## Install Visual Studio Code

- Download Here: [*Visual Studio Code*](https://code.visualstudio.com/Download)

## Install Visual Studio Code Extensions

- Recommended Extensions: 
  - GitHub Pull Requests and Issues - Author GitHub
  - HashiCorp HCL - Author HashiCorp
  - HashiCorp Terraform - Author HashiCorp
  - Pylance - Author Microsoft
  - Python - Author Microsoft
  - YAML - Author Red Hat (Required)

- Authorize Visual Studio Code to GitHub via the GitHub Extension

### [<ins>Back to Table of Contents<ins>](#table-of-contents)

## Install Python

```bash
sudo apt update && sudo apt install -y python3 python3-pip python3-venv
```

### Validate Python Install

```bash
python3 --version
```

### Example Output

```bash
$ python3 --version
Python 3.10.12
$
```

### Create and Activate a Virtual Environment (Recommended)

```bash
cd ~
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
```

> Note: Keep the virtual environment active for all Python and Ansible commands in this guide.

### [<ins>Back to Table of Contents<ins>](#table-of-contents)

### Create a Virtual Environment through Visual Studio Code

To create local environments in VS Code using virtual environments, you can follow these steps: open the Command Palette (Ctrl+Shift+P), search for the Python: Create Environment command, and select it.

> Choose one approach for virtual environment creation: terminal-based (`python3 -m venv`) or VS Code wizard. Do not create multiple virtual environments for the same workspace unless you have a specific need.

![Venv](images/venv1.png)

### Select an Interpreter

![Venv Interpreter](images/venv_interpreter.png)

### Visual Studio will create the environment

![Venv Creation](images/venv_creating.png)

### Select the Requirements File and press OK

![Venv Creation](images/venv_requirements.png)

### [<ins>Back to Table of Contents<ins>](#table-of-contents)

## YAML Schema for auto-completion, Help, and Error Validation

Add the Following to `YAML: Schemas` in Visual Studio Code: Settings > Search for `YAML: Schema`: Click edit in `settings.json`.  In the `yaml.schemas` section:

```json
"https://raw.githubusercontent.com/scotttyso/intersight-tools/master/variables/fsai-schema.json": "*.fsai.yaml",
"https://raw.githubusercontent.com/terraform-cisco-modules/easy-imm/main/yaml_schema/easy-imm.json": "*.ezi.yaml"
```

### Example

```json
    "yaml.schemas": {
        "https://raw.githubusercontent.com/terraform-cisco-modules/easy-imm/main/yaml_schema/easy-imm.json": "*.ezi.yaml",
        "https://raw.githubusercontent.com/scotttyso/intersight-tools/master/variables/fsai-schema.json": "*.fsai.yaml"
    },
```

### [<ins>Back to Table of Contents<ins>](#table-of-contents)

## Install Ansible on Ubuntu

[Others](https://docs.ansible.com/ansible/latest/installation_guide/installation_distros.html)

Install Ansible inside the active virtual environment:

```bash
python -m pip install "ansible>=9,<11"
```

Install Python module dependencies used by automation:

```bash
cd Cisco-AI-Pods
python -m pip install -r requirements.txt
```

Verify Python dependencies:

```bash
python -m pip show purestorage py-pure-client kubernetes openshift
```

Install Ansible collections used by automation:

```bash
cd Cisco-AI-Pods
ansible-galaxy collection install -r requirements.yaml
```

Verify installed collections:

```bash
ansible-galaxy collection list | grep -E "kubernetes.core|purestorage.flasharray|purestorage.flashblade|ansible.posix"
```

### Validate Ansible Installation

```bash
ansible --version
```

### Example Output

```bash
$ ansible --version
ansible [core 2.x]
  config file = None
  executable location = /home/<user>/.venv/bin/ansible
  python version = 3.x.x
$ 
```

### [<ins>Back to Table of Contents<ins>](#table-of-contents)

## Install Terraform on Ubuntu

[Others](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli)

Ensure that your system is up to date and you have installed the gnupg, software-properties-common, and curl packages installed. You will use these packages to verify HashiCorp's GPG signature and install HashiCorp's Debian package repository.

```bash
sudo apt-get update && sudo apt-get install -y gnupg software-properties-common
```

#### Install the HashiCorp GPG key.

```bash
wget -O- https://apt.releases.hashicorp.com/gpg | \
gpg --dearmor | \
sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg > /dev/null
```

#### Verify the key's fingerprint.

```bash
gpg --no-default-keyring \
--keyring /usr/share/keyrings/hashicorp-archive-keyring.gpg \
--fingerprint
```

#### The gpg command will report the key fingerprint:

```bash
/usr/share/keyrings/hashicorp-archive-keyring.gpg
-------------------------------------------------
pub   rsa4096 XXXX-XX-XX [SC]
AAAA AAAA AAAA AAAA
uid           [ unknown] HashiCorp Security (HashiCorp Package Signing) <security+packaging@hashicorp.com>
sub   rsa4096 XXXX-XX-XX [E]
```

Add the official HashiCorp repository to your system. The lsb_release -cs command finds the distribution release codename for your current system, such as buster, groovy, or sid.

```bash
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(grep -oP '(?<=UBUNTU_CODENAME=).*' /etc/os-release || lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
```

### Download the package information from HashiCorp and Install Terraform

```bash
sudo apt update && sudo apt install terraform
```

### Verify the Terraform installation

Verify that the installation worked by opening a new terminal session and listing Terraform's available subcommands.

```bash
terraform --version
```

### Example Output

```bash
$ terraform --version
Terraform v1.11.4
on linux_amd64

Your version of Terraform is out of date! The latest version
is 1.12.2. You can update by downloading from https://developer.hashicorp.com/terraform/install
$ 
```

### [<ins>Back to Table of Contents<ins>](#table-of-contents)

If needed, reactivate the virtual environment:

```bash
source ~/.venv/bin/activate
```

