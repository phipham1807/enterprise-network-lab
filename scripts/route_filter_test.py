"""
KỊCH BẢN BẢO MẬT: BGP ROUTE FILTERING (ZERO TRUST)
Tự động cấu hình và kiểm tra bộ lọc Prefix-List & Route-Map
ngăn chặn rò rỉ dải mạng nội bộ ra ngoài biên ISP.
"""

import subprocess
import time
import re

EXTERNAL_IP = "203.0.113.1"
PCA_NET = "10.10.20.0/24"
PCB_NET = "10.10.30.0/24"
BGP_PEER = "172.16.15.2"

def run_cmd(node, *args):
    res = subprocess.run(["sudo", "-n", "docker", "exec", f"clab-enterprise-{node}"] + list(args), capture_output=True, text=True)
    return res.stdout.strip()

def frr_cmd(node, *commands):
    args = ["vtysh"]
    for cmd in commands: args.extend(["-c", cmd])
    return run_cmd(node, *args)

def main():
    print("=" * 70)
    print("BẮT ĐẦU KIỂM THỬ BẢO MẬT: BGP ROUTE FILTERING (ZERO TRUST)")
    print("=" * 70)

    try:
        print("\n[1] Đẩy cấu hình bảo mật Prefix-List xuống biên R1...")
        frr_cmd("r1", 
            "conf t",
            f"ip prefix-list BLOCK_PCA deny {PCA_NET}",
            "ip prefix-list BLOCK_PCA permit any",
            "route-map RM_BGP_OUT permit 10",
            "match ip address prefix-list BLOCK_PCA",
            "router bgp 65001",
            "address-family ipv4 unicast",
            f"neighbor {BGP_PEER} route-map RM_BGP_OUT out",
            "do write"
        )
        frr_cmd("r1", f"clear ip bgp {BGP_PEER} soft out")
        time.sleep(3)

        print("\n[2] Kiểm tra bảng định tuyến trên ISP (R5)...")
        r5_route_pca = frr_cmd("r5", f"show ip route {PCA_NET}")
        r5_route_pcb = frr_cmd("r5", f"show ip route {PCB_NET}")
        
        pca_blocked = "Network not in table" in r5_route_pca or not r5_route_pca
        print(f" - Mạng PC-A ({PCA_NET}): {'ĐÃ BỊ CHẶN HOÀN TOÀN (Bảo mật tốt)' if pca_blocked else 'VẪN BỊ LỘ ROUTE!'}")
        print(f" - Mạng PC-B ({PCB_NET}): {'VẪN HOẠT ĐỘNG BÌNH THƯỜNG' if 'Known via \"bgp\"' in r5_route_pcb else 'Lỗi cấu hình'}")

        print("\n[3] Kiểm chứng Data Plane (Thực tế truyền thông)...")
        ping_pca = run_cmd("pc-a", "ping", "-c", "2", "-W", "2", EXTERNAL_IP)
        print(f" - PC-A ping ra ngoài: {'RỚT MẠNG (Đúng kỳ vọng Zero Trust)' if '100%' in ping_pca or '0 received' in ping_pca else 'Vẫn thông'}")

    finally:
        print("\n[4] Khôi phục trạng thái ban đầu (Rollback)...")
        frr_cmd("r1", 
            "conf t",
            "router bgp 65001",
            "address-family ipv4 unicast",
            f"neighbor {BGP_PEER} route-map PERMIT_ALL out",
            "exit-address-family",
            "exit",
            "no route-map RM_BGP_OUT",
            "no ip prefix-list BLOCK_PCA",
            "do write"
        )
        frr_cmd("r1", f"clear ip bgp {BGP_PEER} soft out")
        print("[+] Hoàn tất dọn dẹp hệ thống mạng.")
        print("=" * 70)

if __name__ == "__main__":
    main()
