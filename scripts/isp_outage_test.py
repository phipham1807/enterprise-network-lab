"""
KỊCH BẢN 3: ISP OUTAGE / BGP DOWN (PHIÊN BẢN CHI TIẾT VÀ NÂNG CAO)
Mô phỏng sự cố mất kết nối mạng diện rộng (đứt cáp nối với nhà mạng).
Phân tích chi tiết đường đi của gói tin, trạng thái BGP và định tuyến.
"""

import subprocess
import time
import re

# ============================================================
# CẤU HÌNH THIẾT BỊ VÀ THÔNG SỐ
# ============================================================
CONTAINERS = {
    "R1": "clab-enterprise-r1",
    "R5": "clab-enterprise-r5",
    "PC-A": "clab-enterprise-pc-a"
}

ISP_INTERFACE = "eth3"       # Cổng vật lý trên R1 kết nối với R5
ISP_PEER_IP = "172.16.15.2"  # IP của ISP (R5)
EXTERNAL_IP = "203.0.113.1"  # IP đích mạng ngoài cần ping
EXTERNAL_NET = "203.0.113.0/24"
PING_COUNT = 4
PING_TIMEOUT = 2

# ============================================================
# CÁC HÀM GIAO TIẾP VỚI HỆ THỐNG
# ============================================================
def docker_cmd(node, *args):
    """Thực thi lệnh bên trong container qua Docker."""
    command = ["sudo", "-n", "docker", "exec", CONTAINERS[node], *args]
    result = subprocess.run(command, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def frr_cmd(node, command):
    """Chạy lệnh VTYSH để lấy cấu hình định tuyến từ FRRouting."""
    stdout, _, _ = docker_cmd(node, "vtysh", "-c", command)
    return stdout

def set_isp_link(enabled):
    """Bật/tắt liên kết vật lý (đứt/cắm cáp)."""
    action = "up" if enabled else "down"
    stdout, stderr, code = docker_cmd("R1", "ip", "link", "set", ISP_INTERFACE, action)
    if code != 0:
        raise RuntimeError(f"Lỗi cổng {ISP_INTERFACE}: {stderr}")

def get_bgp_state():
    """Kiểm tra trạng thái láng giềng BGP trên R1."""
    output = frr_cmd("R1", f"show bgp neighbor {ISP_PEER_IP}")
    match = re.search(r"BGP state = (\w+)", output)
    return match.group(1) if match else "Unknown"

def get_route_info(prefix):
    """Kiểm tra bảng định tuyến OSPF/BGP trên R1."""
    output = frr_cmd("R1", f"show ip route {prefix}")
    if "Network not in table" in output or not output:
        return None
    # Trích xuất giao thức và Next-hop
    protocol = "BGP" if 'Known via "bgp"' in output else "Khác"
    nh_match = re.search(r"\*\s+([\d\.]+),\s+via\s+(\w+)", output)
    if nh_match:
        return {"protocol": protocol, "next_hop": nh_match.group(1), "interface": nh_match.group(2)}
    return {"protocol": protocol, "next_hop": "Unknown", "interface": "Unknown"}

def ping_advanced(source, target):
    """Thực hiện ping và tính toán thông số RTT, Packet Loss."""
    stdout, _, code = docker_cmd(source, "ping", "-n", "-c", str(PING_COUNT), "-W", str(PING_TIMEOUT), target)
    
    packet_match = re.search(r"(\d+)\s+packets transmitted,\s+(\d+)\s+(?:packets )?received", stdout)
    sent = int(packet_match.group(1)) if packet_match else PING_COUNT
    received = int(packet_match.group(2)) if packet_match else 0
    loss = round((sent - received) / sent * 100, 2) if sent > 0 else 100.0
    
    rtt_match = re.search(r"=\s*([\d.]+)/([\d.]+)/([\d.]+)", stdout)
    avg_rtt = rtt_match.group(2) if rtt_match else "N/A"
    
    return {"status": "PASS" if received > 0 else "FAIL", "loss": loss, "rtt": avg_rtt}

# ============================================================
# KỊCH BẢN CHÍNH
# ============================================================
def main():
    print("\n" + "=" * 70)
    print("BẮT ĐẦU KỊCH BẢN: ISP OUTAGE VÀ BGP CONVERGENCE")
    print("=" * 70)
    
    print("""
    [THÔNG TIN KIẾN TRÚC MẠNG DOANH NGHIỆP]
    - R1 (AS 65001): Router biên của doanh nghiệp.
    - R5 (AS 65005): Router của Nhà cung cấp dịch vụ (ISP).
    - Liên kết R1-R5: Qua cáp vật lý (cổng eth3).
    - Đường đi gói tin: PC-A -> R2 -> R1 -> eth3 -> R5 -> Mạng ngoài (203.0.113.1)
    """)

    try:
        # ---------------------------------------------------------
        # BƯỚC 1: BASELINE
        # ---------------------------------------------------------
        print("\n[1] TRẠNG THÁI BÌNH THƯỜNG (TRƯỚC SỰ CỐ)")
        
        bgp_state = get_bgp_state()
        print(f"[*] Trạng thái eBGP R1-R5: {bgp_state}")
        
        route = get_route_info(EXTERNAL_NET)
        if route:
            print(f"[*] Tuyến đường ra {EXTERNAL_NET}: Học qua {route['protocol']} | Cổng xuất: {route['interface']} | Trỏ về: {route['next_hop']}")
        else:
            print(f"[*] CẢNH BÁO: R1 chưa học được tuyến đường tới {EXTERNAL_NET}. Hãy kiểm tra lại cấu hình BGP!")
            return

        print(f"[*] Đang thực hiện Ping đo đạc từ PC-A -> External ({EXTERNAL_IP})...")
        res = ping_advanced("PC-A", EXTERNAL_IP)
        print(f"    -> Kết quả: {res['status']} | Tỉ lệ rớt gói: {res['loss']}% | RTT trung bình: {res['rtt']} ms")

        if res['status'] == "FAIL":
            print("\n[!] LỖI: Mạng không thông suốt. Hủy bài test để tránh sai lệch kết quả.")
            return

        # ---------------------------------------------------------
        # BƯỚC 2: GIẢ LẬP SỰ CỐ ĐỨT CÁP QUANG
        # ---------------------------------------------------------
        print("\n[2] KÍCH HOẠT SỰ CỐ ĐỨT CÁP QUANG TỚI ISP (ETH3: DOWN)")
        set_isp_link(False)
        time.sleep(3) # Chờ vài giây để hạt nhân Linux xóa định tuyến
        
        print("[*] Kiểm tra lại não bộ (Bảng định tuyến) của R1:")
        bgp_state_fail = get_bgp_state()
        route_fail = get_route_info(EXTERNAL_NET)
        
        print(f"    - Trạng thái eBGP hiện tại: {bgp_state_fail}")
        if not route_fail:
            print(f"    - Bảng định tuyến: ĐÃ XÓA TỰ ĐỘNG tuyến đường tới {EXTERNAL_NET}.")
            print("    - Hành vi hệ thống: R1 đã phân phối lại (redistribute) lệnh xóa này vào OSPF để báo cho R2, R3, R4 biết mạng ngoài đã sập.")
        
        print(f"[*] Ping thử từ PC-A trong lúc đứt cáp...")
        res_fail = ping_advanced("PC-A", EXTERNAL_IP)
        print(f"    -> Kết quả (Mong đợi rớt mạng): {res_fail['status']} | Tỉ lệ rớt gói: {res_fail['loss']}%")

        # ---------------------------------------------------------
        # BƯỚC 3: KHÔI PHỤC VÀ ĐO THỜI GIAN HỘI TỤ BGP
        # ---------------------------------------------------------
        print("\n[3] CẮM LẠI CÁP VÀ ĐO ĐẠC QUÁ TRÌNH HỘI TỤ (ETH3: UP)")
        start_recovery_time = time.time()
        set_isp_link(True)
        
        print("[*] Liên kết vật lý đã khôi phục. Đang chờ phiên TCP của BGP thiết lập lại...")
        
        # Vòng lặp chờ BGP Established
        converged = False
        for i in range(1, 15):
            time.sleep(2)
            current_state = get_bgp_state()
            if current_state == "Established":
                end_recovery_time = time.time()
                converged = True
                total_time = round(end_recovery_time - start_recovery_time, 2)
                print(f"    [+] BGP đã thiết lập trạng thái ESTABLISHED sau {total_time} giây!")
                break
            else:
                print(f"    - Giây thứ {i*2}: BGP đang ở trạng thái {current_state}...")
        
        if not converged:
            print("[-] LỖI: BGP hội tụ thất bại hoặc quá 30 giây!")
            return
            
        print("[*] Kiểm tra lại Bảng định tuyến trên R1:")
        route_recv = get_route_info(EXTERNAL_NET)
        if route_recv:
            print(f"    - Tuyến đường đã quay lại: Học qua {route_recv['protocol']} | Trỏ về ISP {route_recv['next_hop']}")
            
        print(f"[*] Ping kiểm tra độ ổn định cuối cùng từ PC-A...")
        res_recv = ping_advanced("PC-A", EXTERNAL_IP)
        print(f"    -> Kết quả: {res_recv['status']} | Tỉ lệ rớt gói: {res_recv['loss']}% | RTT trung bình: {res_recv['rtt']} ms")

    except Exception as e:
        print(f"\n[LỖI NGHIÊM TRỌNG]: {e}")
    finally:
        print("\n[*] Dọn dẹp: Đảm bảo cổng kết nối ISP luôn mở...")
        set_isp_link(True)
        print("=" * 70)
        print("HOÀN TẤT QUÁ TRÌNH!!!")
        print("=" * 70)

if __name__ == "__main__":
    main()