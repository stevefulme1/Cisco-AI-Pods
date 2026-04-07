# NVIDIA DCGM Metrics Collection for Splunk Observability

## Table of Contents
* [Overview](#overview)
* [Prerequisites](#prerequisites)
* [Configuration](#configuration)
* [Deployment](#deployment)
* [Verification](#verification)
* [Troubleshooting](#troubleshooting)

## Overview

This directory contains configuration for deploying NVIDIA DCGM (Data Center GPU Manager) metrics collection with Splunk Observability. DCGM exporter collects GPU performance metrics and exposes them in Prometheus format for collection by the OpenTelemetry collector.

**Note:** This configuration has already been integrated into the main [openshift-gitops deployment](../../openshift/openshift-gitops/README.md). This directory is provided for reference and standalone deployments.

**Reference:** [NVIDIA GPU Operator Documentation](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/1.9.1/getting-started.html)

### [<ins>Back to Table of Contents<ins>](#table-of-contents)

## Prerequisites

Before deploying DCGM metrics collection, ensure you have:

1. NVIDIA GPU Operator installed on your OpenShift cluster
2. Kubectl or OpenShift CLI (oc) configured and authenticated
3. Access to the nvidia-gpu-operator namespace
4. The DCGM metrics configuration file (dcgm-metrics.csv)

### [<ins>Back to Table of Contents<ins>](#table-of-contents)

## Configuration

### DCGM Metrics File

The `dcgm-metrics.csv` file defines which GPU metrics are collected. Standard metrics include:

* GPU utilization
* Memory usage
* Temperature
* Power consumption
* Clock speeds
* Error counters

### [<ins>Back to Table of Contents<ins>](#table-of-contents)

## Deployment

### Step 1: Create ConfigMap for Metrics Configuration

Create a ConfigMap in the nvidia-gpu-operator namespace with the DCGM metrics configuration:

```bash
oc create configmap metrics-config -n nvidia-gpu-operator --from-file=dcgm-metrics.csv
```

### Step 2: Update GPU Cluster Policy

Update the GPU Cluster Policy to enable DCGM exporter with the metrics configuration. Add or modify the following in your `cluster-policy.yaml`:

```yaml
spec:
  dcgmExporter:
    config:
      name: 'metrics-config'
    enabled: true
    env:
      - name: DCGM_EXPORTER_COLLECTORS
        value: "/etc/dcgm-exporter/dcgm-metrics.csv"
    serviceMonitor:
      enabled: true
```

**Key Components:**
- `config.name` - References the ConfigMap containing dcgm-metrics.csv
- `enabled` - Enables the DCGM exporter
- `DCGM_EXPORTER_COLLECTORS` - Path to the metrics configuration file
- `serviceMonitor.enabled` - Enables Prometheus ServiceMonitor for metric scraping

### Step 3: Apply Changes

Apply the updated cluster policy:

```bash
oc apply -f cluster-policy.yaml
```

### [<ins>Back to Table of Contents<ins>](#table-of-contents)

## Verification

Verify the DCGM exporter is running:

```bash
# Check DCGM exporter pods
oc get pods -n nvidia-gpu-operator -l app=nvidia-dcgm-exporter

# View DCGM exporter logs
oc logs -n nvidia-gpu-operator -l app=nvidia-dcgm-exporter -f

# Check ServiceMonitor is created
oc get servicemonitor -n nvidia-gpu-operator
```

Verify metrics are being collected:

```bash
# Port-forward to DCGM exporter service
oc port-forward -n nvidia-gpu-operator svc/nvidia-dcgm-exporter 9400:9400

# In another terminal, curl the metrics endpoint
curl http://localhost:9400/metrics | grep dcgm
```

### [<ins>Back to Table of Contents<ins>](#table-of-contents)

## Troubleshooting

### DCGM Exporter Pod Not Starting

1. Check pod status and events:
```bash
oc describe pod -n nvidia-gpu-operator -l app=nvidia-dcgm-exporter
```

2. Check for GPU driver issues:
```bash
oc logs -n nvidia-gpu-operator -l app=nvidia-driver-daemon -f
```

### ConfigMap Not Found

Ensure the ConfigMap exists:
```bash
oc get configmap -n nvidia-gpu-operator metrics-config
```

If missing, recreate it:
```bash
oc create configmap metrics-config -n nvidia-gpu-operator --from-file=dcgm-metrics.csv
```

### Metrics Not Appearing

1. Verify ServiceMonitor is correctly configured:
```bash
oc get servicemonitor -n nvidia-gpu-operator -o yaml
```

2. Check OpenTelemetry collector is scraping the endpoint:
```bash
oc logs -n otel -l app=splunk-otel-collector | grep dcgm
```

3. Verify network policies allow communication between namespaces