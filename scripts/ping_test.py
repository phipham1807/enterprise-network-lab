"""
BÀI KIỂM TRA ĐỘ BỀN MẠNG DOANH NGHIỆP

Dự án:
    Lab Độ bền Mạng Doanh nghiệp:
    Định tuyến OSPF, Dự phòng & Mở rộng BGP

Chức năng:
1. Kiểm tra định tuyến OSPF chính và dự phòng.
2. Ping PC-A, PC-B đến server và mạng bên ngoài.
3. Mô phỏng sự cố liên kết R1-R3.
4. Đo thời gian OSPF chuyển sang đường dự phòng.
5. Kiểm tra kết nối sau failover.
6. Khôi phục liên kết và đo thời gian failback.
7. Kiểm tra eBGP R1-AS65001 với R5-AS65005.
8. Kiểm tra route BGP được phân phối vào OSPF.
9. Lưu kết quả vào CSV.
"""

import csv
import re
import subprocess
import time

from datetime import datetime
from pathlib import Path


# ============================================================
# 1. CẤU HÌNH TOPOLOGY
# ============================================================

CONTAINERS = {
    "R1": "clab-enterprise-r1",
    "R2": "clab-enterprise-r2",
    "R3": "clab-enterprise-r3",
    "R4": "clab-enterprise-r4",
    "R5": "clab-enterprise-r5",
    "PC-A": "clab-enterprise-pc-a",
    "PC-B": "clab-enterprise-pc-b",
    "SERVER": "clab-enterprise-server",
}

# Mạng PC-B được dùng để theo dõi route OSPF failover
ROUTE_PREFIX = "10.10.30.0/24"

DIRECT_NEXT_HOP = "172.16.13.2"
BACKUP_NEXT_HOP = "172.16.12.2"

# Liên kết trực tiếp R1-R3
R1_INTERFACE = "eth2"

# BGP
BGP_NEIGHBOR = "172.16.15.2"
BGP_REMOTE_AS = 65005
EXTERNAL_PREFIX = "203.0.113.0/24"
EXTERNAL_TEST_IP = "203.0.113.1"

# Tham số kiểm thử
MAX_WAIT_SECONDS = 45
POLL_INTERVAL = 0.2
PING_COUNT = 4
PING_TIMEOUT = 2

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"
CSV_FILE = DATA_DIR / "network_test_results.csv"


# ============================================================
# 2. THỰC THI LỆNH
# ============================================================

def run_command(command, timeout=15):
    """Thực thi lệnh và thu thập stdout/stderr."""
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def docker_command(node, *args, timeout=15):
    """Thực thi lệnh trong container Containerlab."""
    command = [
        "sudo", "-n", "docker", "exec",
        CONTAINERS[node],
        *args,
    ]

    return run_command(command, timeout=timeout)


def router_command(router, *commands):
    """Chạy lệnh FRR vtysh trên router."""
    args = ["vtysh"]

    for command in commands:
        args.extend(["-c", command])

    result = docker_command(router, *args)

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip()
            or f"Không thể thực thi lệnh trên {router}."
        )

    return result.stdout


# ============================================================
# 3. ĐỌC ROUTE VÀ KIỂM TRA NEXT-HOP
# ============================================================

def get_route(router, prefix):
    """Đọc route của một prefix trên router."""
    return router_command(
        router,
        f"show ip route {prefix}",
    )


def route_uses_next_hop(route, next_hop):
    """Kiểm tra route có next-hop mong muốn hay không."""
    return (
        'Known via "ospf"' in route
        and re.search(
            rf"^\s*\*\s+{re.escape(next_hop)}(?:,|\s)",
            route,
            re.MULTILINE,
        ) is not None
    )


def wait_for_route(router, prefix, next_hop):
    """Chờ đến khi router cài đặt route qua next-hop mong muốn."""
    deadline = time.monotonic() + MAX_WAIT_SECONDS
    last_route = ""

    while time.monotonic() < deadline:
        try:
            last_route = get_route(router, prefix)

            if route_uses_next_hop(last_route, next_hop):
                return time.monotonic(), last_route

        except (RuntimeError, subprocess.TimeoutExpired):
            pass

        time.sleep(POLL_INTERVAL)

    return None, last_route


# ============================================================
# 4. KIỂM TRA INTERFACE R1 ETH2
# ============================================================

def interface_is_up():
    """Kiểm tra trạng thái interface eth2 trên R1."""
    result = docker_command(
        "R1",
        "ip", "-br", "link", "show", R1_INTERFACE,
    )

    if result.returncode != 0:
        return False

    # Ví dụ: eth2 UP ...
    fields = result.stdout.split()

    return len(fields) >= 2 and fields[1] == "UP"


def set_interface(enabled):
    """Bật/tắt liên kết R1-R3 bằng Linux ip link."""
    action = "up" if enabled else "down"

    result = docker_command(
        "R1",
        "ip", "link", "set", R1_INTERFACE, action,
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip()
            or f"Không thể đặt {R1_INTERFACE} {action}."
        )


# ============================================================
# 5. PING VÀ THU THẬP METRICS
# ============================================================

def ping_test(source, destination):
    """Ping từ container nguồn đến địa chỉ đích."""
    result = docker_command(
        source,
        "ping",
        "-n",
        "-c", str(PING_COUNT),
        "-W", str(PING_TIMEOUT),
        destination,
        timeout=PING_COUNT * PING_TIMEOUT + 10,
    )

    output = result.stdout + "\n" + result.stderr

    packet_match = re.search(
        r"(\d+)\s+packets transmitted,\s+"
        r"(\d+)\s+(?:packets )?received",
        output,
    )

    sent = int(packet_match.group(1)) if packet_match else PING_COUNT
    received = int(packet_match.group(2)) if packet_match else 0

    loss_percent = (
        round((sent - received) / sent * 100, 2)
        if sent > 0 else 100.0
    )

    # Hỗ trợ output Linux ping và Alpine ping
    rtt_match = re.search(
        r"(?:rtt|round-trip)\s+"
        r"(?:min/avg/max(?:/[\w]+)?)\s*=\s*"
        r"([\d.]+)/([\d.]+)/([\d.]+)",
        output,
        re.IGNORECASE,
    )

    avg_rtt = (
        float(rtt_match.group(2))
        if rtt_match else None
    )

    success = (
        result.returncode == 0
        and sent > 0
        and received == sent
    )

    return {
        "status": "PASS" if success else "FAIL",
        "sent": sent,
        "received": received,
        "loss_percent": loss_percent,
        "min_rtt_ms": (
            float(rtt_match.group(1)) if rtt_match else None
        ),
        "avg_rtt_ms": avg_rtt,
        "max_rtt_ms": (
            float(rtt_match.group(3)) if rtt_match else None
        ),
        "details": output.strip(),
    }


# ============================================================
# 6. KIỂM TRA BGP
# ============================================================

def check_bgp():
    """Kiểm tra neighbor BGP và các prefix đang được quảng bá."""
    neighbor_output = router_command(
        "R1",
        f"show bgp neighbor {BGP_NEIGHBOR}",
    )

    established = bool(
        re.search(
            r"BGP state\s*=\s*Established",
            neighbor_output,
            re.IGNORECASE,
        )
    )

    bgp_table = router_command(
        "R1",
        "show bgp ipv4 unicast",
    )

    external_route_received = (
        EXTERNAL_PREFIX in bgp_table
    )

    r5_table = router_command(
        "R5",
        "show bgp ipv4 unicast",
    )

    lan20_advertised = "10.10.20.0/24" in r5_table
    lan30_advertised = "10.10.30.0/24" in r5_table

    return {
        "neighbor_established": established,
        "external_route_received": external_route_received,
        "lan20_received_by_r5": lan20_advertised,
        "lan30_received_by_r5": lan30_advertised,
    }


def check_ospf_redistribution():
    """Kiểm tra route mạng ngoài trên R2, R3 và R4."""
    results = {}

    for router in ("R2", "R3", "R4"):
        try:
            route = get_route(router, EXTERNAL_PREFIX)

            results[router] = (
                'Known via "ospf"' in route
                and "Installed" in route
            )

        except (RuntimeError, subprocess.TimeoutExpired):
            results[router] = False

    return results


# ============================================================
# 7. LƯU KẾT QUẢ CSV
# ============================================================

def save_result(record):
    """Lưu kết quả và giữ nguyên các lần chạy trước."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    file_exists = (
        CSV_FILE.exists()
        and CSV_FILE.stat().st_size > 0
    )

    with CSV_FILE.open(
        "a",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(record.keys()),
        )

        if not file_exists:
            writer.writeheader()

        writer.writerow(record)


# ============================================================
# 8. HIỂN THỊ KẾT QUẢ
# ============================================================

def print_ping(label, result):
    print(f"\n{label}: {result['status']}")
    print(
        f"  Đã nhận (Received): {result['received']}/{result['sent']}"
    )
    print(f"  Tỷ lệ mất gói (Packet loss): {result['loss_percent']}%")
    print(f"  RTT trung bình (Average RTT): {result['avg_rtt_ms']} ms")


# ============================================================
# 9. CHƯƠNG TRÌNH CHÍNH
# ============================================================

def main():
    started_at = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )

    failover_seconds = None
    failback_seconds = None

    initial_ping = None
    failover_ping = None
    failback_ping = None

    failover_ok = False
    failback_ok = False
    failure_triggered = False
    restoration_ok = False

    bgp = {}
    redistribution = {}
    connectivity = {}

    errors = []

    print("=" * 72)
    print("BÀI KIỂM TRA ĐỘ BỀN MẠNG DOANH NGHIỆP")
    print("=" * 72)

    # --------------------------------------------------------
    # A. BASELINE
    # --------------------------------------------------------

    try:
        print("\n[A] ĐƯỜNG CƠ SỞ OSPF (BASELINE)")

        if not interface_is_up():
            raise RuntimeError(
                "R1 eth2 không UP. Không bắt đầu failover test."
            )

        initial_route = get_route("R1", ROUTE_PREFIX)
        print(initial_route)

        if not route_uses_next_hop(
            initial_route, DIRECT_NEXT_HOP
        ):
            raise RuntimeError(
                "Route ban đầu không đi qua R3 trực tiếp."
            )

        initial_ping = ping_test("PC-A", "10.10.30.10")
        print_ping("PC-A -> PC-B trước sự cố", initial_ping)

        if initial_ping["status"] != "PASS":
            raise RuntimeError(
                "Ping baseline thất bại; không tiếp tục failover."
            )

    except Exception as exc:
        errors.append(f"Baseline: {exc}")
        print(f"LỖI BASELINE: {exc}")

    # --------------------------------------------------------
    # B. CONNECTIVITY VÀ BGP
    # --------------------------------------------------------

    if not errors:
        print("\n[B] KIỂM TRA KẾT NỐI (CONNECTIVITY TESTS)")

        tests = [
            ("PC-A", "10.10.10.10", "PC-A -> Server"),
            ("PC-A", "203.0.113.1", "PC-A -> Mạng ngoài (External)"),
            ("PC-B", "10.10.10.10", "PC-B -> Server"),
            ("PC-B", "203.0.113.1", "PC-B -> Mạng ngoài (External)"),
        ]

        for source, destination, label in tests:
            try:
                result = ping_test(source, destination)
                connectivity[label] = result
                print_ping(label, result)
            except Exception as exc:
                errors.append(f"{label}: {exc}")
                connectivity[label] = {
                    "status": "ERROR",
                    "loss_percent": None,
                    "avg_rtt_ms": None,
                }

        print("\n[C] TRẠNG THÁI BGP")

        try:
            bgp = check_bgp()
            for name, value in bgp.items():
                print(f"{name}: {'PASS' if value else 'FAIL'}")
        except Exception as exc:
            errors.append(f"BGP: {exc}")
            print(f"LỖI BGP: {exc}")

        print("\n[D] PHÂN PHỐI LẠI BGP-VÀO-OSPF (REDISTRIBUTION)")

        try:
            redistribution = check_ospf_redistribution()
            for router, value in redistribution.items():
                print(
                    f"{router}: "
                    f"{'PASS' if value else 'FAIL'}"
                )
        except Exception as exc:
            errors.append(f"Redistribution: {exc}")
            print(f"LỖI REDISTRIBUTION: {exc}")

    # --------------------------------------------------------
    # E. OSPF FAILOVER
    # --------------------------------------------------------

    if not errors:
        print("\n[E] KIỂM TRA OSPF FAILOVER (CHUYỂN DỰ PHÒNG)")

        try:
            failure_start = time.monotonic()

            set_interface(False)
            failure_triggered = True

            detected_at, backup_route = wait_for_route(
                "R1",
                ROUTE_PREFIX,
                BACKUP_NEXT_HOP,
            )

            if detected_at is not None:
                failover_ok = True
                failover_seconds = round(
                    detected_at - failure_start, 3
                )

            print(
                f"Chuyển dự phòng (Failover): {'PASS' if failover_ok else 'FAIL'}"
            )
            print(f"Thời gian phát hiện: {failover_seconds} giây")
            print(backup_route)

            if failover_ok:
                failover_ping = ping_test(
                    "PC-A", "10.10.30.10"
                )
                print_ping(
                    "PC-A -> PC-B sau failover",
                    failover_ping,
                )

        except Exception as exc:
            errors.append(f"Failover: {exc}")
            print(f"LỖI FAILOVER: {exc}")

        finally:
            # Luôn thử khôi phục link sau khi đã bắt đầu sự cố
            if failure_triggered:
                print("\n[F] KHÔI PHỤC LIÊN KẾT R1-R3")

                try:
                    restore_start = time.monotonic()
                    set_interface(True)

                    restored_at, restored_route = wait_for_route(
                        "R1",
                        ROUTE_PREFIX,
                        DIRECT_NEXT_HOP,
                    )

                    if restored_at is not None and interface_is_up():
                        failback_ok = True
                        failback_seconds = round(
                            restored_at - restore_start, 3
                        )

                    print(
                        f"Khôi phục (Failback): "
                        f"{'PASS' if failback_ok else 'FAIL'}"
                    )
                    print(
                        f"Thời gian khôi phục: {failback_seconds} giây"
                    )
                    print(restored_route)

                    failback_ping = ping_test(
                        "PC-A", "10.10.30.10"
                    )
                    print_ping(
                        "PC-A -> PC-B sau failback",
                        failback_ping,
                    )

                    restoration_ok = (
                        interface_is_up()
                        and failback_ok
                    )

                except Exception as exc:
                    errors.append(f"Restore: {exc}")
                    print(f"LỖI RESTORE: {exc}")

                    # Thử bật lại link nếu quá trình phục hồi gặp lỗi
                    try:
                        set_interface(True)
                    except Exception as retry_exc:
                        errors.append(
                            f"Restore retry: {retry_exc}"
                        )

    # --------------------------------------------------------
    # G. LƯU KẾT QUẢ
    # --------------------------------------------------------

    record = {
        "started_at": started_at,
        "finished_at": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "route_prefix": ROUTE_PREFIX,
        "direct_next_hop": DIRECT_NEXT_HOP,
        "backup_next_hop": BACKUP_NEXT_HOP,

        "initial_ping_status": (
            initial_ping["status"] if initial_ping else "CHƯA CHẠY"
        ),
        "initial_ping_loss_percent": (
            initial_ping["loss_percent"] if initial_ping else None
        ),
        "initial_avg_rtt_ms": (
            initial_ping["avg_rtt_ms"] if initial_ping else None
        ),

        "failover_success": failover_ok,
        "failover_detection_seconds": failover_seconds,
        "failover_ping_status": (
            failover_ping["status"] if failover_ping else "CHƯA CHẠY"
        ),
        "failover_ping_loss_percent": (
            failover_ping["loss_percent"] if failover_ping else None
        ),

        "failback_success": failback_ok,
        "failback_detection_seconds": failback_seconds,
        "failback_ping_status": (
            failback_ping["status"] if failback_ping else "CHƯA CHẠY"
        ),
        "failback_ping_loss_percent": (
            failback_ping["loss_percent"] if failback_ping else None
        ),

        "bgp_established": bgp.get(
            "neighbor_established", False
        ),
        "bgp_external_route_received": bgp.get(
            "external_route_received", False
        ),
        "r2_external_route_installed": redistribution.get(
            "R2", False
        ),
        "r3_external_route_installed": redistribution.get(
            "R3", False
        ),
        "r4_external_route_installed": redistribution.get(
            "R4", False
        ),

        "restoration_ok": restoration_ok,
        "errors": " | ".join(errors),
    }

    try:
        save_result(record)
        print(f"\nĐã lưu CSV: {CSV_FILE}")
    except Exception as exc:
        print(f"\nLỖI LƯU CSV: {exc}")

    print("\n" + "=" * 72)
    print("TỔNG KẾT BÀI KIỂM TRA")
    print("=" * 72)

    print(f"Failover: {'PASS' if failover_ok else 'THẤT BẠI/CHƯA CHẠY'}")
    print(f"Failback: {'PASS' if failback_ok else 'THẤT BẠI/CHƯA CHẠY'}")
    print(
        "BGP: "
        + (
            "PASS"
            if bgp.get("neighbor_established", False)
            else "THẤT BẠI/CHƯA CHẠY"
        )
    )
    print(
        "BGP-to-OSPF: "
        + (
            "PASS"
            if redistribution
            and all(redistribution.values())
            else "THẤT BẠI/CHƯA CHẠY"
        )
    )
    print(
        "Khôi phục (Restoration): "
        + ("PASS" if restoration_ok else "CẦN KIỂM TRA")
    )

    if errors:
        print("\nCác lỗi (Errors):")
        for error in errors:
            print(f"- {error}")

    print("=" * 72)


if __name__ == "__main__":
    main()