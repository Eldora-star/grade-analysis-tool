import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from matplotlib.lines import Line2D

# 1. 页面基本设置
st.set_page_config(page_title="成绩分布交互分析工具", layout="wide")

# --- 替换后的代码 ---
import matplotlib.font_manager as fm

# 1. 尝试寻找系统中可用的中文字体（解决 Linux 服务器无黑体问题）
# Streamlit Cloud 通常支持内置的无衬线字体渲染中文
plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei', 'Droid Sans Fallback', 'Source Han Sans CN', 'Arial Unicode MS', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# 2. 额外强制设置，确保在高版本 matplotlib 中生效
import matplotlib
matplotlib.rc('font', family='sans-serif')
# ------------------

st.title("📊 成绩分布交互式分析网页")
st.markdown("---")

# --- 2. 侧边栏交互设置 ---
st.sidebar.header("⚙️ 绘图参数配置")
uploaded_file = st.sidebar.file_uploader("1. 上传成绩文件 (Excel 或 CSV)", type=["xlsx", "csv"])

if uploaded_file is not None:
    try:
        # 数据加载
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        # 获取第一列有效分数
        scores = df.iloc[:, 0].dropna().values
        
        # 基础统计量
        n_total = len(scores)
        mean_val = np.mean(scores)
        median_val = np.median(scores)
        std_val = np.std(scores)

        # 2. 动态区间设置
        st.sidebar.subheader("2. 范围与步长设置")
        # 默认取数据的整十位最小值和最大值
        default_min = int(np.floor(min(scores) / 10) * 10)
        default_max = int(np.ceil(max(scores) / 10) * 10)
        
        start_score = st.sidebar.number_input("起始分数 (横轴左起点)", value=default_min)
        end_score = st.sidebar.number_input("终止分数 (横轴右终点)", value=default_max)
        bin_width = st.sidebar.slider("调整步长 (Bin Width)", min_value=1, max_value=50, value=10)
        
        st.sidebar.subheader("3. 标注高度调节")
        mu_offset = st.sidebar.slider("μ 标注抬高高度", min_value=0.0, max_value=20.0, value=5.0)

        # --- 3. 核心统计逻辑 ---
        bins = np.arange(start_score, end_score + bin_width, bin_width)
        actual_counts, _ = np.histogram(scores, bins=bins)

        # 计算理论频数 (正态分布)
        theoretical_freqs = []
        for i in range(len(bins)-1):
            p = stats.norm.cdf(bins[i+1], median_val, std_val) - stats.norm.cdf(bins[i], median_val, std_val)
            theoretical_freqs.append(p * n_total)

        # --- 4. 绘图部分 ---
        fig, ax = plt.subplots(figsize=(12, 8), dpi=100)
        
        # 渐变蓝色条形图
        colors = plt.cm.Blues(np.linspace(0.4, 0.8, len(actual_counts)))
        bars = ax.bar(bins[:-1], actual_counts, width=bin_width, align='edge',
                      color=colors, edgecolor='midnightblue', alpha=0.8)

        # 标注数值 (实际频数与理论频数)
        for i in range(len(actual_counts)):
            x_center = bins[i] + bin_width / 2
            if actual_counts[i] > 0:
                # 实际人数 (红色)
                ax.text(x_center, actual_counts[i] + 0.3, str(int(actual_counts[i])), 
                        ha='center', va='bottom', fontsize=10, color='red', fontweight='bold')
            if theoretical_freqs[i] > 0.1:
                # 理论人数 (蓝色括号)
                ax.text(x_center, actual_counts[i] + (max(actual_counts)*0.08), f'({theoretical_freqs[i]:.1f})', 
                        ha='center', va='bottom', fontsize=9, color='blue')

        # 绘制正态拟合曲线
        x_axis = np.linspace(start_score, end_score, 500)
        y_pdf = stats.norm.pdf(x_axis, median_val, std_val) * n_total * bin_width
        ax.plot(x_axis, y_pdf, color='darkviolet', linewidth=2.5, alpha=0.8)

        # 标注 Mu (μ)
        y_max_curve = np.max(y_pdf)
        ax.text(median_val, y_max_curve + mu_offset, f'$\mu$ = {median_val:.2f}', 
                ha='center', va='bottom', fontsize=11, color='darkviolet', fontweight='bold')

        # 参考线
        ax.axvline(mean_val, color='red', linestyle='-', linewidth=1.5)
        ax.axvline(median_val, color='green', linestyle='--', linewidth=1.5)

        # --- 5. 坐标轴与样式定制 ---
        ax.set_xticks(bins)
        ax.set_xlim(start_score, end_score)
        # 动态留白 Y 轴
        ax.set_ylim(0, max(max(actual_counts), y_max_curve) * 1.3)
        
        ax.set_title(f"{uploaded_file.name.split('.')[0]} 成绩分布图", fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('分数区间', fontsize=12)
        ax.set_ylabel('频数 (人数)', fontsize=12)

        # --- 6. 图例设置 (参考图一风格) ---
        legend_elements = [
            Line2D([0], [0], color='red', lw=1.5, label=f'平均分: {mean_val:.2f}'),
            Line2D([0], [0], color='green', lw=1.5, ls='--', label=f'中位数: {median_val:.2f}'),
            Line2D([0], [0], color='darkviolet', lw=2.5, label='正态拟合曲线'),
            plt.Rectangle((0, 0), 1, 1, fc="none", ec="none", label='( )内为理论频数'),
        ]
        ax.legend(handles=legend_elements, loc='upper left', frameon=True, fontsize=10)

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(axis='y', linestyle=':', alpha=0.3)

        # 在网页显示图表
        st.pyplot(fig)

        # 底部统计报表
        st.subheader("📋 统计概览")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("实考人数", f"{int(n_total)} 人")
        c2.metric("平均分", f"{mean_val:.2f}")
        c3.metric("中位数", f"{median_val:.2f}")
        c4.metric("标准差", f"{std_val:.2f}")

    except Exception as e:
        st.error(f"⚠️ 处理出错：请检查文件格式。错误详情: {e}")
else:
    st.info("👋 请在左侧侧边栏上传您的成绩 Excel 或 CSV 文件开始分析。")