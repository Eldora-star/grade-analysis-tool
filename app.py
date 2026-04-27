import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from matplotlib.lines import Line2D

# --- 修改后的代码开头 ---
import matplotlib.font_manager as font_manager
import os

# 1. 页面基本设置
st.set_page_config(page_title="成绩分布交互分析工具", layout="wide")

# 2. 强制加载同目录下的字体文件
font_path = 'font.ttf'
if os.path.exists(font_path):
    # 注册字体文件
    font_manager.fontManager.addfont(font_path)
    prop = font_manager.FontProperties(fname=font_path)
    # 设置全局字体
    plt.rcParams['font.sans-serif'] = [prop.get_name()]
else:
    # 如果文件不存在，备用方案
    plt.rcParams['font.sans-serif'] = ['sans-serif']

plt.rcParams['axes.unicode_minus'] = False
# -----------------------
# 2. 额外强制设置，确保在高版本 matplotlib 中生效
import matplotlib
matplotlib.rc('font', family='sans-serif')
# ------------------

st.title("📊 成绩分布交互式分析网页")

# --- 新增使用说明部分 ---
with st.expander("📖 点击展开使用说明"):
    st.markdown("""
    ### 快速上手指南：
    1. **准备数据**：
        * 确保您的 Excel 表格**第一列**是学生的分数（程序会自动读取第一列）。
        * 建议将 Excel 文件重命名为 **“年级+练习名称+学科”**（如：*六年级期中考试数学.xlsx*），这样生成的图表标题会自动匹配。
    2. **上传文件**：点击左侧边栏的 **Browse files**，选中您的成绩表。
    3. **调整参数**：
        * **起始/终止分数**：根据科目总分调整（如：数学 0-100）。
        * **组间距**：根据学科总分设置组间距，建议设置为 5 或 10，观察不同跨度下的分布情况。
    4. **保存图片**：右键点击生成的图表，选择“图片另存为”即可。
    
    *💡 提示：如果图表显示异常，请检查 Excel 中是否有非数字单元格（如“缺考”或空行）。*
    """)
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
        st.sidebar.subheader("2. 范围与组间距设置")
        # 默认取数据的整十位最小值和最大值
        default_min = int(np.floor(min(scores) / 10) * 10)
        default_max = int(np.ceil(max(scores) / 10) * 10)
        
        start_score = st.sidebar.number_input("起始分数 (横轴左起点)", value=default_min)
        end_score = st.sidebar.number_input("终止分数 (横轴右终点)", value=default_max)
        bin_width = st.sidebar.slider("调整组间距 (Bin Width)", min_value=1, max_value=50, value=10)
        
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
                ha='center', va='bottom', fontproperties=prop, fontsize=11, color='darkviolet', fontweight='bold')

        # 参考线
        ax.axvline(mean_val, color='red', linestyle='-', linewidth=1.5)
        ax.axvline(median_val, color='green', linestyle='--', linewidth=1.5)

        # --- 5. 坐标轴与样式定制 ---
        ax.set_xticks(bins)
        ax.set_xlim(start_score, end_score)
        # 动态留白 Y 轴
        ax.set_ylim(0, max(max(actual_counts), y_max_curve) * 1.3)
        
        # 修改为（加上 fontproperties=prop）
        ax.set_title(f"{uploaded_file.name.split('.')[0]} 成绩分布图", fontproperties=prop, fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('分数区间', fontproperties=prop, fontsize=12)
        ax.set_ylabel('频数 (人数)', fontproperties=prop, fontsize=12)

        # --- 6. 图例设置 (参考图一风格) ---
        legend_elements = [
            Line2D([0], [0], color='red', lw=1.5, label=f'平均分: {mean_val:.2f}'),
            Line2D([0], [0], color='green', lw=1.5, ls='--', label=f'中位数: {median_val:.2f}'),
            Line2D([0], [0], color='darkviolet', lw=2.5, label='正态拟合曲线'),
            plt.Rectangle((0, 0), 1, 1, fc="none", ec="none", label='( )内为理论频数'),
        ]
        ax.legend(handles=legend_elements, loc='upper left', frameon=True, prop=prop)

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(axis='y', linestyle=':', alpha=0.3)

        # 在网页显示图表
    
        

        # --- 找到 st.pyplot(fig) 后，从此开始替换 ---

        st.pyplot(fig)

        st.divider()  # 添加一条分割线
        st.subheader("💡 数据自动诊断报告")
        # --- 补上这两行定义，解决报错 ---
        min_score = float(df.iloc[:, 0].min())
        max_score = float(df.iloc[:, 0].max())


        # 1. 计算低分段界限 (总分前 40% 范围)
        analysis_data = []
        low_score_limit = (max_score - min_score) * 0.4 + min_score 

        for i in range(len(actual_counts)):
            diff = actual_counts[i] - theoretical_freqs[i] 
            bin_center = (bins[i] + bins[i+1]) / 2
            bin_label = f"{bins[i]} - {bins[i+1]}"
            
            analysis_data.append({
                "区间": bin_label,
                "实际": actual_counts[i],
                "偏离_原始": diff,
                "is_low_zone": bin_center < low_score_limit
            })
        
        # ... 后面的逻辑保持不变 ...
        # 1. 核心计算：计算原始差值
        analysis_data = []
        # 计算总分的 40% 作为低分段界限
        low_score_limit = (max_score - min_score) * 0.4 + min_score 

        for i in range(len(actual_counts)):
            diff = actual_counts[i] - theoretical_freqs[i] 
            bin_center = (bins[i] + bins[i+1]) / 2  # 取区间中值判断是否属于低分段
            bin_label = f"{bins[i]} - {bins[i+1]}"
            
            analysis_data.append({
                "区间": bin_label,
                "实际": actual_counts[i],
                "偏离_原始": diff,
                "is_low_zone": bin_center < low_score_limit
            })

        # 2. 识别显著特征
        threshold = n_total * 0.05

        # 人数偏多逻辑：原标准 (5%) OR (处于低分段且实际>理论)
        over_bins = [
            d for d in analysis_data 
            if d["偏离_原始"] > threshold or (d["is_low_zone"] and d["偏离_原始"] > 0)
        ]
        # 人数偏少逻辑：保持原标准 (5%)
        under_bins = [d for d in analysis_data if d["偏离_原始"] < -threshold]

        # 3. 渲染结果：【位置已调换】
        col1, col2 = st.columns(2)

        with col1:
            st.write("📉 **人数偏少区间**")
            if under_bins:
                for d in under_bins:
                    val = abs(round(d["偏离_原始"], 1))
                    st.warning(f"**{d['区间']}分**：实际比理论少了 **{val}** 人。该层次学生可能出现断层。")
            else:
                st.write("✅ 该成绩段分布平稳，无显著断层。")

        with col2:
            st.write("📈 **人数偏多区间**")
            if over_bins:
                for d in over_bins:
                    val = abs(round(d["偏离_原始"], 1))
                    # 针对低分段偏多给出一个特殊的警告样式
                    if d["is_low_zone"] and d["偏离_原始"] > 0:
                        st.error(f"**{d['区间']}分(低分预警)**：实际比理论多出 **{val}** 人。需关注基础薄弱群体。")
                    else:
                        st.success(f"**{d['区间']}分**：实际比理论多出 **{val}** 人。该分数段学生非常集中。")
            else:
                st.write("✅ 该成绩段分布平稳，无显著聚集。")

        # 4. 底部综合分析
        st.divider()
        st.info("**教师教学建议：**")
        if median_val > mean_val:
            st.markdown("👉 **当前成绩分布呈现“负偏态”**：高分人数较多，中位数高于平均分，说明大部分学生掌握情况良好。")
        else:
            st.markdown("👉 **当前成绩分布呈现“正偏态”**：低分人数偏多，说明题目具有挑战性，或需要加强基础知识的补缺补差。")

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