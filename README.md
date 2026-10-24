# Enterprise Network Resilience & Automation Lab

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Containerlab](https://img.shields.io/badge/Containerlab-Latest-orange.svg)](https://containerlab.dev/)
[![FRRouting](https://img.shields.io/badge/FRRouting-FRR-green.svg)](https://frrouting.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An academic-grade, automated enterprise network simulation and validation framework. This project demonstrates high availability, dynamic routing convergence (**OSPF & eBGP**), and security enforcement via **Zero Trust Network Architecture (ZTNA)** using **Containerlab**, **FRRouting**, and **Python automation scripts**.

---

## Project Overview

Modern enterprise networks require absolute resilience against physical link failures and strict security controls to prevent data leakage at network perimeters. This lab environment simulates a multi-tier enterprise network connected to an external Internet Service Provider (ISP), managed entirely through code-driven testing and professional data visualization.

### Key Highlights:
- **Closed-Loop Automation:** Automated execution flow: Test setup $\rightarrow$ Inject failure $\rightarrow$ Verify recovery $\rightarrow$ Rollback state.
- **Sub-Second OSPF Failover:** Rapid detection and dynamic rerouting during core link disruptions.
- **BGP Multi-Hop & Redistribution:** Seamless integration of internal OSPF with external eBGP routing domains.
- **Zero Trust Route Filtering:** Perimeter security enforcement using Prefix-Lists and Route-Maps to isolate sensitive subnets from the public internet.
- **Academic Data Visualization:** Automated generation of high-resolution analytics charts (`Matplotlib` & `Seaborn`) for thesis documentation.

---

## Network Topology Architecture

The simulation environment consists of 8 containerized nodes running FRRouting:
- **Enterprise AS 65001:**
  - **`R1`**: Enterprise Edge Router (managing eBGP peer with ISP and internal OSPF routing).
  - **`R2`, `R3`, `R4`**: Internal Core/Distribution Routers running OSPF Area 0.
  - **`PC-A`, `PC-B`, `SERVER`**: End-user nodes and internal application servers.
- **ISP AS 65005:**
  - **`R5`**: Upstream Provider Router connected via physical link (`eth3` on R1).

---

## Tech Stack

- **Virtualization & Orchestration:** Containerlab, Docker, Linux Network Namespaces.
- **Routing Engine:** FRRouting (FRR) via `vtysh` CLI interface.
- **Automation & Scripting:** Python 3 (Subprocess, Regex, CSV logging).
- **Data Analysis & Plotting:** Pandas, Matplotlib, Seaborn.

---

## Repository Structure

```text
enterprise-network-lab/
│
├── data/
│   └── network_test_results.csv        # Log data generated from test runs
│
├── output_charts/
│   ├── ospf_convergence_comparison.png # OSPF Failover/Failback convergence charts
│   ├── rtt_performance_trend.png       # RTT latency variation trend
│   ├── zero_trust_comprehensive_analysis.png # Control & Data plane security evaluation
│   └── isp_outage_bgp_convergence_timeline.png # ISP outage recovery timeline
│
├── scripts/
│   ├── ping_test.py                    # Scenario 1: OSPF Resilience & RTT testing
│   ├── route_filter_test.py            # Scenario 2: Zero Trust BGP Route Filtering
│   ├── isp_outage_test.py              # Scenario 3: ISP Outage & BGP Convergence
│   ├── plot_network_metrics.py         # Plotting script for Scenario 1
│   ├── plot_zero_trust_metrics.py      # Plotting script for Scenario 2
│   └── plot_isp_outage_metrics.py      # Plotting script for Scenario 3
│
├── topology.yml                        # Containerlab topology definition
└── README.md                           # Project Documentation
```

---

## Installation & Setup

### 1. Prerequisites
Ensure your Linux environment (or WSL2) has Docker and Containerlab installed:
```bash
sudo apt update && sudo apt install -y python3-pip python3-venv
```

### 2. Clone Repository & Setup Virtual Environment
```bash
git clone https://github.com/phipham1807/enterprise-network-lab
cd enterprise-network-lab
python3 -m venv .venv
source .venv/bin/activate
pip install pandas matplotlib seaborn
```

### 3. Deploy Lab Topology
```bash
sudo containerlab deploy -t topology.yml --reconfigure
```

---

## Execution Guide & Test Scenarios

Activate your virtual environment before running any script:
```bash
source .venv/bin/activate
```

### Scenario 1: OSPF Resilience & Latency Test
Validates primary vs. backup OSPF routing, measures sub-second failover times, and logs RTT metrics.
```bash
sudo python3 scripts/ping_test.py
python3 scripts/plot_network_metrics.py
```

### Scenario 2: Zero Trust Route Filtering Test
Automatically applies `Prefix-List` and `Route-Map` policies on edge router `R1` to isolate sensitive subnet `PC-A` (`10.10.20.0/24`) from leaking to the ISP (`R5`), then performs control/data plane validation.
```bash
sudo python3 scripts/route_filter_test.py
python3 scripts/plot_zero_trust_metrics.py
```

### Scenario 3: ISP Outage & BGP Convergence Timeline
Simulates physical fiber cuts (`Link Down`) on the WAN interface, tracks BGP state transitions (`Established` $\rightarrow$ `Active`), and records recovery convergence duration.
```bash
sudo python3 scripts/isp_outage_test.py
python3 scripts/plot_isp_outage_metrics.py
```

---

## Experimental Results & Key Findings

| Scenario | Metric Evaluated | Observed Performance | Status |
| :--- | :--- | :--- | :---: |
| **OSPF Failover** | Link Down Detection | $\approx 0.100\text{s} - 0.160\text{s}$ | **PASS** |
| **OSPF Failback** | Route Recovery Time | $\approx 5.28\text{s} - 10.36\text{s}$ | **PASS** |
| **Data Plane RTT** | Internal Latency | $0.14\text{ ms} - 0.47\text{ ms}$ (0% packet loss) | **PASS** |
| **Zero Trust ZTNA** | Perimeter Leakage Prevention | 100% blocked on ISP routing table ($0\%$ visibility) | **PASS** |
| **BGP Convergence** | WAN Session Re-establishment | $\approx 2.14\text{s}$ after physical link up | **PASS** |

---

## License

This project is open-source and available under the [MIT License](LICENSE).
