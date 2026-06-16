# -*- coding: utf‑8 -*-
from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "output" / "51job_sample_10000_enhanced.csv"
ALERT_FILE = BASE_DIR / "output" / "51job_job_alerts.csv"
COEF_FILE = BASE_DIR / "output" / "salary_factor_coefficients.csv"

@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    df = pd.read_csv(DATA_FILE, encoding="utf‑8‑sig")
    alerts = pd.read_csv(ALERT_FILE, encoding="utf‑8‑sig")
    coef = pd.read_csv(COEF_FILE, encoding="utf‑8‑sig")

    df["发布时间"] = pd.to_datetime(df["发布时间"], errors="coerce")
    df["年月"] = df["发布时间"].dt.strftime("%Y‑%m")
    df["平均薪资"] = pd.to_numeric(df["平均薪资"], errors="coerce")
    df["技能数量"] = df["技能关键词"].fillna("").astype(str).apply(
        lambda s: 0 if not s.strip() else len([x for x in s.split("、") if x.strip()])
    )
    df["福利数量"] = df["福利关键词"].fillna("").astype(str).apply(
        lambda s: 0 if not s.strip() else len([x for x in s.split("、") if x.strip()])
    )
    return df, alerts, coef

def filter_nonempty(series: pd.Series) -> list[str]:
    vals = sorted(v for v in series.fillna("").astype(str).unique().tolist() if v.strip())
    return vals

def make_heatmap(data:pd.DataFrame, row_col: str, col_col: str, title: str) -> go.Figure:
    ct = pd.crosstab(data[row_col], data[col_col])
    ct = ct.loc[ct.sum(axis=1).sort_values(ascending=False).head(8).index]
    fig = px.imshow(
        ct,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="Blues",
        labels=dict(x=col_col, y=row_col, color="数量"),
        title=title,
    )
    fig.update_layout(margin=dict(l=20, r=20, t=50, b=20))
    return fig

st.set_page_config(
    page_title="就业形势分析看板",
    page_icon="📊",
    layout="wide",
)

df, alerts, coef = load_data()

st.title("基于网络招聘信息的就业形势分析看板")
st.caption("数据源：51job 1万条增强样本，含岗位类别、行业类别、工作地点、技能关键词、福利关键词、预警结果和薪资影响因素分析。")

with st.sidebar:
    st.header("筛选条件")
    year_options = sorted(df["发布年份"].dropna().astype(int).unique().tolist())
    role_options = filter_nonempty(df["岗位类别"])
    industry_options = filter_nonempty(df["行业类别"])
    location_options = filter_nonempty(df["工作地点"])

    selected_years = st.multiselect("发布年份", year_options, default=year_options)
    selected_roles = st.multiselect("岗位类别", role_options, default=role_options[: min(6, len(role_options))])
    selected_industries = st.multiselect("行业类别", industry_options, default=industry_options[: min(8, len(industry_options))])
    salary_range = st.slider(
        "平均薪资区间",
        min_value=0,
        max_value=int(df["平均薪资"].fillna(0).quantile(0.99)),
        value=(0, int(df["平均薪资"].fillna(0).quantile(0.90))),
        step=500,
    )
    selected_locations = st.multiselect("工作地点", location_options, default=[])

    filtered = df.copy()
    filtered = filtered[filtered["发布年份"].fillna(-1).astype(int).isin(selected_years)]
    if selected_roles:
        filtered = filtered[filtered["岗位类别"].isin(selected_roles)]
    if selected_industries:
        filtered = filtered[filtered["行业类别"].isin(selected_industries)]
    filtered = filtered[
        filtered["平均薪资"].fillna(0).between(salary_range[0], salary_range[1], inclusive="both")
    ]
    if selected_locations:
        filtered = filtered[filtered["工作地点"].isin(selected_locations)]

    valid_salary = filtered["平均薪资"].dropna()

col1, col2, col3, col4 = st.columns(4)
col1.metric("当前样本数", f"{len(filtered):,}")
col2.metric("平均薪资均值", f"{valid_salary.mean():,.0f}" if not valid_salary.empty else "0")
col3.metric("平均薪资中位数", f"{valid_salary.median():,.0f}" if not valid_salary.empty else "0")
col4.metric("预警条数", f"{len(alerts):,}")

st.subheader("一、招聘趋势")
monthly = (
    filtered.groupby("年月", dropna=False)
    .agg({"jobid": "count", "平均薪资": "mean"})
    .rename(columns={"jobid": "招聘数量"})
    .reset_index()
    .sort_values("年月")
)
trend = go.Figure()
trend.add_scatter(x=monthly["年月"], y=monthly["招聘数量"], name="招聘数量", mode="lines+markers")
trend.add_scatter(
    x=monthly["年月"],
    y=monthly["平均薪资"],
    name="平均薪资",
    mode="lines+markers",
    yaxis="y2",
)
trend.update_layout(
    title="月度招聘数量与平均薪资趋势",
    xaxis_title="年月",
    yaxis=dict(title="招聘数量"),
    yaxis2=dict(title="平均薪资", overlaying="y", side="right"),
    legend=dict(orientation="h"),
    margin=dict(l=20, r=20, t=50, b=20),
)
st.plotly_chart(trend, width="stretch")

left, right = st.columns(2)
with left:
    role_top = (
        filtered["岗位类别"].value_counts().head(10).rename_axis("岗位类别").reset_index(name="数量")
    )
    fig_role = px.bar(role_top, x="数量", y="岗位类别", orientation="h", title="岗位类别分布 Top10")
    fig_role.update_layout(yaxis=dict(categoryorder="total ascending"))
    st.plotly_chart(fig_role, width="stretch")

with right:
    edu_top = (
        filtered["学历要求"].fillna("未知").value_counts().head(10).rename_axis("学历要求").reset_index(name="数量")
    )
    fig_edu = px.bar(edu_top, x="学历要求", y="数量", title="学历要求分布")
    st.plotly_chart(fig_edu, width="stretch")

st.subheader("二、结构分析")
heat_col1, heat_col2 = st.columns(2)
with heat_col1:
    st.plotly_chart(
        make_heatmap(filtered, "岗位类别", "学历要求", "岗位类别 × 学历要求"),
        width="stretch",
    )
with heat_col2:
    st.plotly_chart(
        make_heatmap(filtered, "岗位类别", "工作经验要求", "岗位类别 × 工作经验要求"),
        width="stretch",
    )

st.subheader("三、薪资分析")
sal_col1, sal_col2 = st.columns(2)
with sal_col1:
    hist = px.histogram(
        filtered[filtered["平均薪资"].notna() & (filtered["平均薪资"] <= filtered["平均薪资"].quantile(0.99))],
        x="平均薪资",
        nbins=30,
        title="平均薪资分布",
    )
    st.plotly_chart(hist, width="stretch")
with sal_col2:
    box_df = filtered[filtered["岗位类别"].isin(filtered["岗位类别"].value_counts().head(8).index)]
    box_df = box_df[box_df["平均薪资"].notna() & (box_df["平均薪资"] <= box_df["平均薪资"].quantile(0.99))]
    box = px.box(box_df, x="岗位类别", y="平均薪资", title="不同岗位类别薪资分布")
    box.update_layout(xaxis_tickangle=-25)
    st.plotly_chart(box, width="stretch")

scatter = px.scatter(
    filtered[filtered["平均薪资"].notna()],
    x="技能数量",
    y="平均薪资",
    color="岗位类别",
    title="技能数量与平均薪资关系",
    opacity=0.55,
)
st.plotly_chart(scatter, width="stretch")

st.subheader("四、预警结果")
alert_summary = alerts["预警类型"].value_counts().rename_axis("预警类型").reset_index(name="数量")
alert_bar = px.bar(alert_summary, x="预警类型", y="数量", title="预警类型分布")
st.plotly_chart(alert_bar, width="stretch")
st.dataframe(alerts, width="stretch", hide_index=True)

st.subheader("五、薪资影响因素")
coef_show = coef.sort_values("影响强度排序").head(15)
coef_bar = px.bar(
    coef_show,
    x="系数",
    y="变量",
    color="影响方向",
    orientation="h",
    title="薪资影响因素 Top15",
)
st.dataframe(coef_show, width="stretch", hide_index=True)
