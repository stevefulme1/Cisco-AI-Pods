# Cisco AI Pods Pure Storage Deployment Guide

## Runbook Components

## Prerequisites

**Ansible Collections**: Ensure you have the `kubernetes.core`, `purestorage.flasharray`, and `purestorage.flashblade` collection installed.

```bash
ansible-galaxy collection install -r requirements.yaml
```

**Python Requirements**: These libraries are necessary for the Ansible modules to communicate with the Pure Storage APIs.

```bash
pip install -r requirements.txt
```

### Summary of Requirements per Module

**FlashBlade (`purefb`)**: Python >= 3.9, `py-pure-client`, `netaddr`, `datetime`, `pytz`, `distro`, `pycountry`, `urllib3` [per documentation](https://docs.ansible.com/projects/ansible/latest/collections/purestorage/flashblade/purefb_tz_module.html).
**FlashArray (`purefa`)**: Python >= 3.3, `purestorage`, `py-pure-client`, `netaddr`, `requests`, `pycountry`, `urllib3` [per documentation](https://docs.ansible.com/projects/ansible/latest/collections/purestorage/flasharray/purefa_alert_module.html).

### 🌐 [Array Deployment](README_pure_storage_arrays.md)
**Pure Storage Array's deployment guide**

### 🚀 [Portworx Deployment](README_portworx.md)
**Portworx deployment guide**
