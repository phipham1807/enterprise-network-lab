"""
SCRIPT PHÂN TÍCH VÀ VẼ ĐỒ THỊ THỐNG KÊ OSPF/BGP
Mục đích:
1. Đọc dữ liệu từ file log 8 lần chạy (network_test_results.csv).
2. Tính toán các giá trị trung bình (Failover, Failback, RTT).
3. Xuất kết quả thống kê trung bình ra file CSV riêng (ospf_average_metrics.csv).
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Cấu hình giao diện biểu đồ
sns.set_theme(style="whitegrid")
plt.rcParams.update({'font.sans-serif': 'DejaVu Sans', 'font.family': 'sans-serif'})

# Đường dẫn file
DATA_DIR = Path("data")
INPUT_CSV = DATA_DIR / "network_test_results.csv"
OUTPUT_STATS_CSV = DATA_DIR / "ospf_average_metrics.csv"
CHARTS_DIR = Path("output_charts")

def main():
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("BẮT ĐẦU PHÂN TÍCH SỐ LIỆU")
    print("=" * 70)

    if not INPUT_CSV.exists():
        print(f"[-] Không tìm thấy tệp {INPUT_CSV}. Hãy chạy ping_test.py trước để tạo dữ liệu.")
        return

    # Đọc dữ liệu từ CSV
    df = pd.read_csv(INPUT_CSV)
    df_valid = df.dropna(subset=['failover_detection_seconds'])

    if df_valid.empty:
        print("[-] Tệp dữ liệu không chứa bản ghi hợp lệ.")
        return
    
    so_lan_chay = len(df_valid)
    print(f"[+] Đã tải {so_lan_chay} bản ghi thực nghiệm từ {INPUT_CSV}")

    # ============================================================
    # 1. TÍNH TOÁN CÁC GIÁ TRỊ TRUNG BÌNH
    # ============================================================
    avg_failover = df_valid['failover_detection_seconds'].mean()
    avg_failback = df_valid['failback_detection_seconds'].mean() if 'failback_detection_seconds' in df_valid else 0
    avg_rtt = df_valid['initial_avg_rtt_ms'].mean() if 'initial_avg_rtt_ms' in df_valid else 0
    success_rate = (df_valid['failover_success'].sum() / so_lan_chay) * 100

    # ============================================================
    # 2. XUẤT KẾT QUẢ THỐNG KÊ RA FILE CSV RIÊNG
    # ============================================================
    stats_data = [{
        "total_runs": so_lan_chay,
        "average_failover_seconds": round(avg_failover, 3),
        "average_failback_seconds": round(avg_failback, 3),
        "average_rtt_ms": round(avg_rtt, 3),
        "failover_success_rate_percent": round(success_rate, 2)
    }]
    
    df_stats = pd.DataFrame(stats_data)
    df_stats.to_csv(OUTPUT_STATS_CSV, index=False, encoding="utf-8-sig")
    
    print(f"\n[+] Đã lưu kết quả tính toán trung bình vào: {OUTPUT_STATS_CSV}")
    print(f"    -> Thời gian Failover trung bình: {round(avg_failover, 3)} giây")
    print(f"    -> Thời gian Failback trung bình: {round(avg_failback, 3)} giây")
    print(f"    -> Tỉ lệ Failover thành công: {round(success_rate, 2)}%")

    # ============================================================
    # 3. VẼ ĐỒ THỊ 
    # ============================================================
    runs = [f"Lần {i+1}" for i in range(so_lan_chay)]
    x = range(len(runs))

    # ------------------------------------------------------------
    # ĐỒ THỊ 1: THỜI GIAN HỘI TỤ OSPF
    # ------------------------------------------------------------
    # Dùng 2 biểu đồ xếp chồng trên dưới (sharex=True để chung trục X)
    fig1, (ax_fo, ax_fb) = plt.subplots(2, 1, figsize=(10, 10), sharex=True)
    
    # --- Đồ thị con trên: Failover ---
    bars_fo = ax_fo.bar(x, df_valid['failover_detection_seconds'], width=0.45, label='Failover (Link Down)', color='#3498db')
    ax_fo.axhline(y=avg_failover, color='#e74c3c', linestyle='--', linewidth=2.5, label=f'Trung bình Failover: {avg_failover:.3f}s')
    
    ax_fo.set_ylabel('Thời gian (Giây)', fontsize=12, fontweight='bold')
    ax_fo.set_title(f'Thời gian hội tụ OSPF qua {so_lan_chay} lần chạy', fontsize=16, fontweight='bold', pad=15)
    ax_fo.legend(frameon=True, fontsize=10, loc='upper right')
    
    # Thêm khoảng trống phía trên (headroom) để chữ không bị cắt
    ax_fo.set_ylim(0, df_valid['failover_detection_seconds'].max() * 1.35)
    
    for bar in bars_fo:
        height = bar.get_height()
        ax_fo.annotate(f'{height:.3f}s', xy=(bar.get_x() + bar.get_width() / 2, height), 
                       xytext=(0, 5), textcoords="offset points", ha='center', va='bottom', 
                       fontsize=10, fontweight='bold', color='#2c3e50')

    # --- Đồ thị con dưới: Failback ---
    bars_fb = ax_fb.bar(x, df_valid['failback_detection_seconds'].fillna(0), width=0.45, label='Failback (Recovery)', color='#2ecc71')
    if avg_failback > 0:
        ax_fb.axhline(y=avg_failback, color='#27ae60', linestyle='--', linewidth=2.5, label=f'Trung bình Failback: {avg_failback:.3f}s')
    
    ax_fb.set_ylabel('Thời gian (Giây)', fontsize=12, fontweight='bold')
    ax_fb.set_xlabel('Các phiên kiểm thử', fontsize=12, fontweight='bold')
    ax_fb.legend(frameon=True, fontsize=10, loc='upper right')
    
    ax_fb.set_ylim(0, df_valid['failback_detection_seconds'].max() * 1.35)
    
    for bar in bars_fb:
        height = bar.get_height()
        if height > 0:
            ax_fb.annotate(f'{height:.3f}s', xy=(bar.get_x() + bar.get_width() / 2, height), 
                           xytext=(0, 5), textcoords="offset points", ha='center', va='bottom', 
                           fontsize=10, fontweight='bold', color='#2c3e50')
                           
    ax_fb.set_xticks(list(x))
    ax_fb.set_xticklabels(runs, fontsize=11)

    fig1.tight_layout()
    chart_path_1 = CHARTS_DIR / "ospf_failover_average_chart.png"
    fig1.savefig(chart_path_1, dpi=300)
    plt.close(fig1)
    print(f"[+] Đã xuất biểu đồ hội tụ OSPF: {chart_path_1}")

    # ------------------------------------------------------------
    # ĐỒ THỊ 2: RTT
    # ------------------------------------------------------------
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    
    sns.lineplot(ax=ax2, x=runs, y=df_valid['initial_avg_rtt_ms'], marker='o', color='#3498db', linewidth=3, markersize=10, label='RTT từng lần chạy')
    ax2.axhline(y=avg_rtt, color='#e74c3c', linestyle='--', linewidth=2.5, label=f'RTT Trung bình: {avg_rtt:.3f} ms')

    for i, val in enumerate(df_valid['initial_avg_rtt_ms']):
        ax2.annotate(f"{val:.3f}", (runs[i], val), textcoords="offset points", xytext=(0,10), 
                     ha='center', fontsize=10, fontweight='bold', color='#2c3e50')

    ax2.set_xlabel('Các phiên kiểm thử', fontsize=12, fontweight='bold')
    ax2.set_ylabel('RTT (ms)', fontsize=12, fontweight='bold')
    ax2.set_title('Độ trễ khứ hồi trung bình (RTT) trước sự cố', fontsize=14, fontweight='bold', pad=15)
    ax2.legend(frameon=True, fontsize=10, loc='upper left')

    y_max = df_valid['initial_avg_rtt_ms'].max()
    ax2.set_ylim(bottom=df_valid['initial_avg_rtt_ms'].min() - 0.01, top=y_max + (y_max * 0.15))

    fig2.tight_layout()
    chart_path_2 = CHARTS_DIR / "rtt_average_trend.png"
    fig2.savefig(chart_path_2, dpi=300)
    plt.close(fig2)
    print(f"[+] Đã xuất biểu đồ RTT: {chart_path_2}")
    print("=" * 70)

if __name__ == "__main__":
    main()