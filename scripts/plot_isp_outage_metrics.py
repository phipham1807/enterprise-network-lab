"""
SCRIPT VẼ ĐỒ THỊ CHUYÊN BIỆT CHO KỊCH BẢN ISP OUTAGE & BGP CONVERGENCE
Trực quan hóa các mốc thời gian hội tụ của phiên eBGP qua các giai đoạn:
Trạng thái ổn định -> Sự cố đứt cáp -> Kiểm soát định tuyến -> Khôi phục kết nối.
"""

import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Cấu hình phong cách biểu đồ đạt chuẩn học thuật
sns.set_theme(style="whitegrid")
plt.rcParams.update({'font.sans-serif': 'DejaVu Sans', 'font.family': 'sans-serif'})

CHARTS_DIR = Path("output_charts")

def main():
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 60)
    print("BẮT ĐẦU VẼ ĐỒ THỊ MỐC THỜI GIAN HỘI TỤ BGP (ISP OUTAGE)")
    print("=" * 60)

    # Các mốc giai đoạn sự cố và thời gian tích lũy tương ứng (giây)
    stages = [
        'Trạng thái ổn định\n(Established)', 
        'Sự cố đứt cáp\n(Link Down)', 
        'Xóa tuyến đường\n(Control Plane)', 
        'Cắm lại cáp\n(Link Up)', 
        'Tái thiết lập BGP\n(Established lại)'
    ]
    timeline_seconds = [0.0, 3.0, 3.5, 6.0, 8.13]

    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Vẽ đường timeline hội tụ
    ax.plot(stages, timeline_seconds, marker='o', color='#8e44ad', linewidth=3.5, markersize=11, label='Tiến trình hội tụ eBGP (Giây)')

    ax.set_ylabel('Thời gian tích lũy (Giây)', fontsize=12, fontweight='bold')
    ax.set_title('Biểu đồ dòng thời gian hội tụ và khôi phục phiên eBGP khi xảy ra sự cố ISP', fontsize=14, fontweight='bold', pad=15)
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Ghi chú mốc thời gian trực tiếp trên từng điểm nút
    for i, txt in enumerate(timeline_seconds):
        ax.annotate(f"{txt}s", (stages[i], timeline_seconds[i]), textcoords="offset points", xytext=(0, 12), ha='center', fontsize=11, fontweight='bold', color='#2c3e50')

    ax.set_ylim(-1, 12)
    ax.legend(loc='upper left', frameon=True, fontsize=11)

    plt.tight_layout()
    chart_path = CHARTS_DIR / "isp_outage_bgp_convergence_timeline.png"
    plt.savefig(chart_path, dpi=300)
    print(f"[+] Đã xuất biểu đồ ISP Outage thành công: {chart_path}")
    plt.close()

    print("=" * 60)
    print("HOÀN TẤT XUẤT ĐỒ THỊ! TỆP ĐÃ LƯU TRONG THƯ MỤC output_charts/")
    print("=" * 60)

if __name__ == "__main__":
    main()
