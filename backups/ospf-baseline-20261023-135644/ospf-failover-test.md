# OSPF Failover Test Report

## Environment
- Containerlab: 0.82.0
- FRRouting: 10.7.1
- Routing protocol: OSPF
- OSPF area: 0.0.0.0

## Baseline Connectivity
- PC-A (10.10.20.10) -> PC-B (10.10.30.10): PASS
- PC-A (10.10.20.10) -> Server (10.10.10.10): PASS
- PC-B (10.10.30.10) -> Server (10.10.10.10): PASS
- Packet loss in recorded baseline tests: 0%

## Failover Test
- Primary path: R1 -> R3
- Primary next-hop: 172.16.13.2
- Primary OSPF metric: 20
- Failure simulation: R1 eth2 set down
- Backup path: R1 -> R2 -> R4 -> R3
- Backup next-hop: 172.16.12.2
- Backup OSPF metric: 40
- PC-A -> PC-B after convergence: PASS
- Packet loss in the recorded post-convergence test: 0%

## Recovery Test
- Recovery action: R1 eth2 set up
- Restored next-hop: 172.16.13.2
- Restored OSPF metric: 20
- PC-A -> PC-B after recovery: PASS
- Packet loss in the recorded recovery test: 0%

## Conclusion
OSPF selected the backup route when the primary R1-R3 link was disabled.
After the primary link was restored, OSPF returned to the lower-metric route.
Connectivity was successful in the recorded tests before failure, after convergence,
and after recovery. The exact convergence interruption duration was not measured.
