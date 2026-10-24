
"""
SCRIPT VẼ ĐỒ THỊ NĂNG CAO: ĐÁNH GIÁ TOÀN DIỆN ZERO TRUST ROUTE FILTERING
Phân tích đa chiều trên cả Control Plane (Bảng định tuyến) và Data Plane (Giao tiếp thực tế).
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from pathlib import Path

# Cấu hình phong cách học thuật
sns.set_theme(style="whitegrid")
plt.rcParams.update({'font.sans-serif': 'DejaVu Sans', 'font.family': 'sans-serif'})

CHARTS_DIR = Path("output_charts")

def main():
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 60)
    print("ĐANG TẠO BIỂU ĐỒ CHO KỊCH BẢN ZERO TRUST...")
    print("=" * 60)

    # Dữ liệu mở rộng mô phỏng chi tiết các tầng mạng
    data = {
        "Segment": [
            "Mạng ngoài (External)", 
            "Mạng Core Server", 
            "Mạng PC-B", 
            "Mạng PC-A"
        ],
        "Control_Plane_Before": [100, 100, 100, 100], # % Route tồn tại trên ISP trước policy
        "Control_Plane_After": [100, 100, 100, 0],     # % Route tồn tại trên ISP sau policy
        "Data_Plane_Before": [100, 100, 100, 100],     # % Tỷ lệ ping thành công trước policy
        "Data_Plane_After": [100, 100, 100, 0]         # % Tỷ lệ ping thành công sau policy (bị chặn)
    }
    
    df = pd.DataFrame(data)

    # Thiết lập khung vẽ gồm 2 biểu đồ con (Subplots) song song
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    x = range(len(df))
    width = 0.35

    # Subplot 1: Tầng điều khiển (Control Plane)
    bars1 = ax1.bar([p - width/2 for p in x], df['Control_Plane_Before'], width, label='Trước cấu hình (Baseline mở)', color='#2980b9')
    bars2 = ax1.bar([p + width/2 for p in x], df['Control_Plane_After'], width, label='Sau cấu hình (Zero Trust Policy)', color='#e74c3c')
    
    ax1.set_title('Tầng điều khiển: Khả năng hiển thị Route (Control Plane)', fontsize=13, fontweight='bold', pad=12)
    ax1.set_ylabel('Tỷ lệ hiển thị trên ISP R5 (%)', fontsize=11, fontweight='bold')
    ax1.set_xticks(list(x))
    ax1.set_xticklabels(df['Segment'], rotation=15, ha='right', fontsize=10)
    ax1.set_ylim(0, 115)
    ax1.legend(frameon=True, fontsize=10)
    ax1.grid(axis='y', linestyle='--', alpha=0.7)

    for bar in bars1:
        h = bar.get_height()
        ax1.annotate(f'{h}%', xy=(bar.get_x() + bar.get_width()/2, h), xytext=(0,3), textcoords="offset points", ha='center', va='bottom', fontsize=9, fontweight='bold')
    for bar in bars2:
        h = bar.get_height()
        ax1.annotate(f'{h}%', xy=(bar.get_x() + bar.get_width()/2, h), xytext=(0,3), textcoords="offset points", ha='center', va='bottom', fontsize=9, fontweight='bold', color='#c0392b' if h==0 else '#27ae60')

    # Subplot 2: Tầng dữ liệu (Data Plane)
    bars3 = ax2.bar([p - width/2 for p in x], df['Data_Plane_Before'], width, label='Trước cấu hình (Baseline mở)', color='#3498db')
    bars4 = ax2.bar([p + width/2 for p in x], df['Data_Plane_After'], width, label='Sau cấu hình (Zero Trust Policy)', color='#e67e22')

    ax2.set_title('Tầng dữ liệu: Tỷ lệ truyền thông thành công (Data Plane)', fontsize=13, fontweight='bold', pad=12)
    ax2.set_ylabel('Tỷ lệ gói tin thành công - Ping (%)', fontsize=11, fontweight='bold')
    ax2.set_xticks(list(x))
    ax2.set_xticklabels(df['Segment'], rotation=15, ha='right', fontsize=10)
    ax2.set_ylim(0, 115)
    ax2.legend(frameon=True, fontsize=10)
    ax2.grid(axis='y', linestyle='--', alpha=0.7)

    for bar in bars3:
        h = bar.get_height()
        ax2.annotate(f'{h}%', xy=(bar.get_x() + bar.get_width()/2, h), xytext=(0,3), textcoords="offset points", ha='center', va='bottom', fontsize=9, fontweight='bold')
    for bar in bars4:
        h = bar.get_height()
        ax2.annotate(f'{h}%', xy=(bar.get_x() + bar.get_width()/2, h), xytext=(0,3), textcoords="offset points", ha='center', va='bottom', fontsize=9, fontweight='bold', color='#c0392b' if h==0 else '#27ae60')

    plt.suptitle('ĐÁNH GIÁ TOÀN DIỆN CHÍNH SÁCH BẢO MẬT ZERO TRUST ROUTE FILTERING', fontsize=15, fontweight='bold', y=1.03)
    plt.tight_layout()
    
    output_img = CHARTS_DIR / "zero_trust_comprehensive_analysis.png"
    plt.savefig(output_img, dpi=300, bbox_inches='tight')
    print(f"[+] Đã xuất biểu đồ nâng cao thành công: {output_img}")
    plt.close()

if __name__ == "__main__":
    main()
