
import streamlit as st
import akshare as ak
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="A股短线选股器", layout="wide")
st.title("📈 A股短线选股器")
st.caption("筛选短线候选股，仅供研究，不构成买入建议")

st.sidebar.header("筛选条件")
min_change = st.sidebar.number_input("最低涨幅（%）", value=2.0)
max_change = st.sidebar.number_input("最高涨幅（%）", value=7.0)
min_turnover = st.sidebar.number_input("最低换手率（%）", value=3.0)
max_turnover = st.sidebar.number_input("最高换手率（%）", value=15.0)
min_amount = st.sidebar.number_input("最低成交额（万元）", value=5000)
top_n = st.sidebar.slider("显示候选数量", 10, 100, 30)

if st.button("🔄 获取行情并选股", type="primary"):
    try:
        with st.spinner("正在获取A股行情，请稍候……"):
            df = ak.stock_zh_a_spot_em()

        df["代码"] = df["代码"].astype(str).str.zfill(6)

        for col in ["最新价", "涨跌幅", "成交额", "换手率"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df[
            (~df["名称"].astype(str).str.contains("ST|退", case=False, na=False))
            & (df["最新价"] > 0)
            & (df["涨跌幅"].between(min_change, max_change))
            & (df["换手率"].between(min_turnover, max_turnover))
            & (df["成交额"] >= min_amount * 10000)
        ].copy()

        df["观察分"] = (
            df["涨跌幅"].between(2.5, 5.5).astype(int) * 2
            + df["成交额"].ge(3e8).astype(int) * 2
            + df["换手率"].between(4, 10).astype(int) * 2
        )

        df = df.sort_values(
            ["观察分", "成交额"], ascending=False
        ).head(top_n)

        st.success(
            f"获取时间：{datetime.now():%Y-%m-%d %H:%M:%S}｜"
            f"筛选出 {len(df)} 只候选股"
        )

        show = df[
            ["代码", "名称", "最新价", "涨跌幅", "成交额", "换手率", "观察分"]
        ].copy()
        show["成交额（万元）"] = (
            show.pop("成交额") / 10000
        ).round(0)

        st.dataframe(show, use_container_width=True, hide_index=True)

        st.download_button(
            "下载候选名单 CSV",
            data=show.to_csv(index=False).encode("utf-8-sig"),
            file_name="A股短线候选名单.csv",
            mime="text/csv",
        )

        st.warning(
            "观察分只是简单规则评分，不代表上涨概率。"
            "行情可能延迟，请以券商软件为准。A股短线存在亏损风险。"
        )

    except Exception as e:
        st.error(f"行情获取失败：{e}")
        st.info("请稍后重试；行情接口可能受网络或数据源变化影响。")
