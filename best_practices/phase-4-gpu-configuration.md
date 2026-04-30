# Phase 4B: GPU Runtime Configuration and Performance Validation

[Back to Best Practices README](README.md) | [Back to README](../README.md)

## Executive Summary

Phase 4B applies runtime-level GPU controls and validation for Cisco AI Pods. Training profiles target B300 and H200 nodes for sustained throughput. Inference profiles target RTX6000 and RTX4500 nodes for low-latency, stable serving.

## 1. Hardware Roles and Runtime Targets

| Node Class | GPU Type | Primary Objective | Runtime Priority |
|---|---|---|---|
| Training | B300 | Maximum distributed training throughput | Stable clocks, fabric health, RDMA path |
| Training | H200 | High-memory training and fine-tuning | NVLink integrity, RDMA consistency |
| Inference | RTX6000 | High-throughput model serving | Latency stability, thermal consistency |
| Inference | RTX4500 | Cost-efficient serving tiers | Predictable p95 latency |

## 2. Persistence and Fabric Services

On training-capable systems, keep GPU runtime services persistent and verify fabric bring-up before benchmarks.

### Enable Services

```bash
systemctl enable --now nvidia-persistenced
systemctl enable --now nvidia-fabricmanager
```

### Verify

```bash
nvidia-smi -q | grep -i "Persistence Mode"
systemctl status nvidia-fabricmanager --no-pager
```

Expected outcome:
- Persistence mode enabled.
- Fabric Manager active on systems requiring NVSwitch/NVLink fabric control.

## 3. Clock and Power Policy Guidance

### Training (B300/H200)

- Lock clocks only after thermal baseline is established.
- Use validated clock ranges from platform qualification.
- Favor consistency over absolute peak values.

Example flow:

```bash
nvidia-smi -q -d SUPPORTED_CLOCKS | head -n 20
# Apply validated values from your qualification sheet
nvidia-smi --lock-gpu-clocks=<min>,<max>
```

### Inference (RTX6000/RTX4500)

- Tune for latency stability, not max sustained power.
- Keep power policy and fan behavior consistent across inference pools.
- Validate p95/p99 latency under realistic concurrency.

## 4. Topology and Fabric Validation

Validate that intended high-speed paths are active and no traffic falls back to slower paths.

### Commands

```bash
nvidia-smi topo -m
nvidia-smi nvlink -s
```

### Acceptance Guidance

- Training nodes (B300/H200): expected NVLink connectivity visible and consistent.
- Any unexpected SYS/PXB path in critical pairs should be investigated before production.

## 5. GPUDirect RDMA Validation

For multi-node training, verify direct GPU-memory data movement with RDMA enabled.

### Module Check

```bash
modprobe nvidia_peermem
lsmod | grep nvidia_peermem
```

### NCCL Baseline Example

```bash
./all_reduce_perf -b 8 -e 8G -f 2 -g 8
```

Validation goals:
- Throughput aligns with known-good baseline for cluster size.
- Transport logs indicate direct path usage (GDR where applicable).

## 6. Thermal and Power Monitoring

Continuous monitoring is mandatory to avoid hidden throttling.

### Telemetry Command

```bash
nvidia-smi --query-gpu=temperature.gpu,power.draw,clocks.current.graphics,clocks_throttle_reasons.active --format=csv -l 1
```

### Best Practices

- Track sustained temperature and throttle flags during representative workloads.
- Keep role-specific thermal thresholds documented:
  - Training pools (B300/H200)
  - Inference pools (RTX6000/RTX4500)
- Align Intersight thermal policies with rack power and cooling design.

## 7. Troubleshooting Guide

### 7.1 Fabric Manager Not Active

- Symptoms:
  - Incomplete topology visibility.
  - Unexpected low inter-GPU bandwidth.
- Actions:
  1. Verify service state and startup logs.
  2. Validate driver and fabric-manager package compatibility.
  3. Re-test topology and NCCL baseline.

### 7.2 RDMA Underperforming

- Symptoms:
  - All-reduce throughput lower than baseline.
  - High host CPU usage during collectives.
- Actions:
  1. Confirm nvidia_peermem is loaded.
  2. Validate NIC and GPU firmware/driver parity.
  3. Check RoCE policy, MTU consistency, and queue settings.

### 7.3 Thermal Throttling Under Load

- Symptoms:
  - Clock drops during sustained runs.
  - Throughput degrades over time.
- Actions:
  1. Inspect throttle reasons and fan policy.
  2. Validate chassis airflow and blanking panel placement.
  3. Reduce clock lock targets until stability is restored.

### 7.4 Inference Tail Latency Spikes (RTX6000/RTX4500)

- Symptoms:
  - p95/p99 latency outliers at steady RPS.
- Actions:
  1. Correlate GPU clocks and power draw with latency timeline.
  2. Validate CPU pinning and NIC IRQ placement for serving process.
  3. Check model cache and storage burst contention.

## 8. Phase Completion Checklist

- [ ] GPU services active and persistent across reboot.
- [ ] Topology and fabric checks pass for each node class.
- [ ] RDMA baseline validated on training pools.
- [ ] Thermal and power baselines captured.
- [ ] Inference latency SLOs validated for RTX6000 and RTX4500 pools.
- [ ] Runbooks published for top failure modes.

## Summary

Phase 4B is complete when GPU runtime behavior is stable, measurable, and role-appropriate. B300/H200 training nodes and RTX6000/RTX4500 inference nodes should each have dedicated baselines and incident playbooks before production workload onboarding.
