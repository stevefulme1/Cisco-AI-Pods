# GPU Configuration Best Practices for Cisco AI Pods

This unified technical guide provides the consolidated optimization and validation steps for Cisco AI Pods utilizing the latest NVIDIA architectures: H200 (Hopper) and Blackwell (B200/B300) on Cisco UCS C885A M8 and C880A M8 platforms.

## 1. Hardware Platform Comparison

| Feature | Cisco UCS C885A M8 | Cisco UCS C880A M8 |
|---|---|---|
| Primary GPU | NVIDIA H200 (Hopper) | NVIDIA B300 (Blackwell Ultra) |
| GPU Interconnect | NVLink 4.0 (900 GB/s) | NVLink 5.0 (1.8 TB/s) |
| Networking | 8x ConnectX-7 (400G) | 8x ConnectX-8 (800G) |
| Power Delivery | 12V / 54V Hybrid | 54V Native (12x PSUs, 6+6) |
| Cooling | 12x Front Fan Modules | 20x High-Pressure Fans (10RU) |


## 2. NVIDIA Persistence Mode & Fabric Manager

For H200 and Blackwell GPUs, the NVIDIA Persistence Daemon is the modern standard, replacing the legacy -pm 1 command to ensure the driver remains resident and the NVLink fabric is stable.


**Enable Services:**

```bash
# Mandatory for HGX systems to initialize the NVLink fabric
systemctl enable --now nvidia-persistenced
systemctl enable --now nvidia-fabricmanager
```

**Verification:**

```bash
nvidia-smi -q | grep -i "Persistence Mode"
# Status should be "Enabled"
```

## 3. GPU Clock Frequency Optimization

Training workloads require consistent performance. Locking clocks prevents the GPU from entering lower power states during small idle periods (e.g., data loading between batches).


**H200 (Hopper):** Lock graphics clocks to ~1755MHz.

```bash
nvidia-smi --lock-gpu-clocks=1755,1755
```

**B300 (Blackwell Ultra):** Lock to higher targets (e.g., 1800MHz+ depending on SKU).

```bash
# Query max supported for your specific B300 SKU first
nvidia-smi -q -d SUPPORTED_CLOCKS | head -n 10
nvidia-smi --lock-gpu-clocks=1800,1800
```

## 4. NVLink Topology Validation

In Cisco AI Pods, ensuring GPUs are communicating over the high-speed NVLink fabric rather than the PCIe bus is the single most important validation step.


**Command:**

```bash
nvidia-smi topo -m
```

**Expected Results:**

- **H200:** Look for `NV12` (NVLink 4.0) status.
- **B300:** Look for `NV18` (NVLink 5.0) status.

> **Note:** If you see `SYS` or `PXB`, the Fabric Manager is likely not running or the NVLink training failed.

## 5. GPU Direct RDMA Verification

For multi-node training across the Cisco AI Pod fabric, data must move directly from one GPU's memory to another via the ConnectX-7 (400G) or ConnectX-8 (800G) NICs.


**Load Kernel Module:**

```bash
modprobe nvidia_peermem
lsmod | grep nvidia_peermem
```

**Performance Validation (NCCL):** Use the NCCL `all_reduce_perf` test to verify line-rate throughput.

```bash
# Example for 8-GPU B300 node
./all_reduce_perf -b 8 -e 8G -f 2 -g 8
```

Check for `GDR` (GPU Direct RDMA) in the transport logs to confirm the CPU is being bypassed.

## 6. Thermal & Power Monitoring (Cisco Intersight)

The C880A M8 with Blackwell GPUs can draw over 10kW per chassis. Establishing thermal baselines is critical to prevent "Power Braking" or thermal throttling.


**Intersight Policy Tuning:**

- **Thermal Policy:** Set to `High Power` or `Maximum`. This forces the 20-fan array in the C880A to maintain the required static pressure for Blackwell's 1000W TDP.
- **Power Policy:** Ensure `Grid Redundancy` is active to utilize the full 54V power rail capacity.

**Real-time Monitoring Baseline:**

```bash
nvidia-smi --query-gpu=temperature.gpu,power.draw,clocks.current.graphics --format=csv -l 1
```

- **H200 Target:** < 75°C under sustained load.
- **B300 Target:** Monitor for `Thermal Slowdown` flags in `nvidia-smi -q -d PERFORMANCE`.


## Summary Checklist for Cisco AI Pod Deployment

| # | Task | Details |
|---|---|---|
| 1 | Firmware | Ensure Cisco UCS Release 5.2+ (or latest for M8) is applied |
| 2 | Persistence | `nvidia-persistenced` active |
| 3 | Fabric | `nvidia-fabricmanager` active and `topo -m` shows NVLink status |
| 4 | Clocks | Clocks locked to max supported for the specific SKU |
| 5 | RDMA | `nvidia_peermem` loaded; NCCL tests passing at line-rate |
| 6 | Cooling | Intersight Thermal Policy set to `Maximum` for Blackwell/H200 |

## Summary Checklist for Cisco AI Pod Deployment

| Task | Tool/Command | Expected Result |
|---|---|---|
| Persistence | `nvidia-smi -pm 1` | Enabled |
| Clock Speed | `nvidia-smi --lock-gpu-clocks` | Consistent Max Frequency |
| Fabric | `nvidia-smi topo -m` | NVLink status confirmed |
| RDMA | `lsmod \| grep peermem` | Module loaded |
| Thermal | Intersight / `nvidia-smi` | Temps within 70°C–80°C range |