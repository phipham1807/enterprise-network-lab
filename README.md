# Enterprise Network Resilience & Automation Lab

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Containerlab](https://img.shields.io/badge/Containerlab-Latest-orange.svg)](https://containerlab.dev/)
[![Routing Protocol](https://img.shields.io/badge/Protocols-OSPF%20%2F%20eBGP-green.svg)](https://frrouting.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An academic-grade, automated enterprise network simulation and validation framework. This project demonstrates high availability, dynamic routing convergence (**OSPF & eBGP**), and security enforcement via **Zero Trust Network Architecture (ZTNA)** using **Containerlab**, **FRRouting**, and automated **Python** testing scripts.

---

## 1. Project Overview

Modern enterprise networks require absolute resilience against physical link failures and strict security controls to prevent data leakage at network perimeters. This lab environment simulates a multi-tier enterprise network connected to an external Internet Service Provider (ISP), managed entirely through code-driven testing and professional data visualization.

### Key Technical Highlights:
- **Closed-Loop Automation:** Automated experimental execution flow: Topology Setup $\rightarrow$ Failure Injection $\rightarrow$ Convergence Verification $\rightarrow$ State Rollback.
- **Sub-Second OSPF Failover:** Rapid link-down detection and dynamic rerouting, achieving an average failover time of **$0.117$ seconds** across rigorous 8-run empirical sample sets.
- **eBGP Multi-Hop & Redistribution:** Seamless integration of internal OSPF domains with external eBGP routing domains.
- **Zero Trust Route Filtering:** Perimeter security enforcement using Prefix-Lists and Route-Maps to completely isolate sensitive subnets (`PC-A` - `10.10.20.0/24`) from public internet visibility ($100\%$ absolute block).
- **Academic Data Visualization:** Automated log parsing and high-resolution chart generation using `Matplotlib` and `Seaborn`.

---

## 2. Network Topology Architecture

The simulation environment consists of 8 containerized nodes running FRRouting and Alpine Linux:
- **Enterprise AS 65001:**
  - **`R1`**: Enterprise Edge Router (managing eBGP peering with the ISP and internal OSPF routing).
  - **`R2`, `R3`, `R4`**: Internal Core and Distribution Routers running OSPF Area 0.
  - **`PC-A`, `PC-B`, `SERVER`**: End-user workstations and internal application servers.
- **ISP AS 65005:**
  - **`R5`**: Upstream Provider Router connected via physical WAN link (`eth3` on R1).

---

## 3. Tech Stack

- **Virtualization & Orchestration:** Containerlab, Docker, Linux Network Namespaces.
- **Routing Engine:** FRRouting (FRR) via `vtysh` CLI interface.
- **Automation & Scripting:** Python 3 (Subprocess, Regex, CSV logging).
- **Data Analysis & Plotting:** Pandas, Matplotlib, Seaborn.

---

## 4. Repository Directory Structure

```text
enterprise-network-lab/
│
├── data/
│   ├── network_test_results.csv        # Experimental log data across 8 OSPF test runs
│   ├── ospf_average_metrics.csv        # Aggregated statistical summary of metrics
│   └── connectivity_results.csv        # Data Plane connectivity validation results
│
├── output_charts/
│   ├── ospf_failover_average_chart.png # OSPF Failover/Failback convergence charts
│   ├── rtt_average_trend.png           # RTT latency variation trend analysis
│   ├── zero_trust_comprehensive_analysis.png # ZTNA Control & Data Plane evaluation
│   └── isp_outage_bgp_convergence_timeline.png # ISP outage recovery timeline graph
│
├── scripts/
│   ├── ping_test.py                    # Scenario 1: OSPF Resilience & RTT testing (8 runs)
│   ├── route_filter_test.py            # Scenario 2: Zero Trust BGP Route Filtering validation
│   ├── isp_outage_test.py              # Scenario 3: ISP Outage & BGP Convergence tracking
│   ├── analyze_and_plot_metrics.py     # Analytics & plotting script for Scenario 1
│   ├── plot_zero_trust_metrics.py      # Plotting script for Scenario 2
│   └── plot_isp_outage_metrics.py      # Plotting script for Scenario 3
│
├── topology/
│   └── enterprise.clab.yml             # Containerlab topology definition file
└── README.md                           # Project technical documentation
```

---

## 5. Installation & Deployment Guide

### Step 1: Environment Preparation (Linux / WSL2)
Ensure your system has Docker and Containerlab installed. Set up the Python virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pandas matplotlib seaborn
```

### Step 2: Deploy Network Topology
```bash
sudo containerlab deploy -t topology/enterprise.clab.yml --reconfigure
```

---

## 6. Execution Guide & Test Scenarios

Always activate your Python virtual environment before running any test scripts:
```bash
source .venv/bin/activate
```

### Scenario 1: OSPF Resilience & RTT Testing (8-Run Sample Loop)
Executes an 8-iteration loop simulating physical link disruptions on `eth2` of `R1`, measuring failover/failback convergence durations and RTT:
```bash
for i in {1..8}; do
  echo "[+] Running iteration $i/8..."
  sudo python3 scripts/ping_test.py
  sleep 2
done

# Compute average statistics and generate analytical charts
python3 scripts/analyze_and_plot_metrics.py
```

### Scenario 2: Zero Trust Route Filtering Verification
Applies security filtering policies on edge router `R1` and verifies perimeter protection:
```bash
sudo python3 scripts/route_filter_test.py
python3 scripts/plot_zero_trust_metrics.py
```

### Scenario 3: ISP Outage & BGP Convergence Timeline
Simulates WAN fiber cuts (`eth3`), tracking eBGP session state transitions and recovery timelines:
```bash
sudo python3 scripts/isp_outage_test.py
python3 scripts/plot_isp_outage_metrics.py
```

---

## 7. Experimental Results & Performance Summary

Based on empirical data extracted from automated test logs and analytical plots stored in `output_charts/`, the network exhibits the following verified performance metrics:

| Test Scenario | Evaluated Metric | Real-World Experimental Result | Status |
| :--- | :--- | :--- | :---: |
| **OSPF Failover** | Average Link-Down Detection Time | $\approx \mathbf{0.117s}$ (ranging from $0.104s$ to $0.134s$) | **PASS** |
| **OSPF Failback** | Primary Route Restoration Time | $\approx \mathbf{45.234s}$ (stable across 8 empirical runs) | **PASS** |
| **Data Plane RTT** | Average Internal Round-Trip Latency | $\approx \mathbf{0.147\text{ ms}}$ ($0\%$ packet loss) | **PASS** |
| **Zero Trust ZTNA** | Control & Data Plane Visibility | $100\%$ absolute block of subnet `PC-A` (`10.10.20.0/24`) on ISP `R5` | **PASS** |
| **BGP Convergence** | WAN eBGP Session Re-establishment | Completed at $\mathbf{8.13\text{s}}$ post physical link recovery | **PASS** |

---
