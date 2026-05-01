import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ────────────────────────────────────────────
# ページ設定
# ────────────────────────────────────────────
st.set_page_config(
    page_title="NPB 2026 選手成績予測",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ────────────────────────────────────────────
# カスタムCSS
# ────────────────────────────────────────────
st.markdown("""
<style>
    /* 全体背景 */
    .stApp { background-color: #0f1117; }

    /* サイドバー */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1d2e 0%, #16192a 100%);
        border-right: 1px solid #2e3250;
    }

    /* メトリクスカード */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #1e2139 0%, #252845 100%);
        border: 1px solid #3a3f6e;
        border-radius: 12px;
        padding: 16px;
    }

    /* ヘッダー */
    h1 { color: #f0f4ff !important; }
    h2, h3 { color: #c8d4ff !important; }

    /* テーブル */
    [data-testid="stDataFrame"] {
        border-radius: 10px;
        overflow: hidden;
    }

    /* タブ */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1a1d2e;
        border-radius: 10px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #8899cc;
        border-radius: 8px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3a4a9f !important;
        color: #ffffff !important;
    }

    /* ピル型バッジ */
    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        margin: 2px;
    }
    .badge-high { background:#1a4a2e; color:#4ade80; border:1px solid #166534; }
    .badge-mid  { background:#1e3a5f; color:#60a5fa; border:1px solid #1e40af; }
    .badge-low  { background:#3d1f1f; color:#f87171; border:1px solid #7f1d1d; }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────
# データ読み込み & 前処理
# ────────────────────────────────────────────
@st.cache_data(ttl=0)
def load_data():
    df = pd.read_csv("final_predict_2026.csv", index_col=0)
    df.columns = ["選手名", "チーム", "打率予測", "HR予測", "OPS予測"]

    # ソート用数値列を追加
    def ba_to_num(s):
        try:
            # ".270-.279" -> 0.270
            return float(s.split("-")[0])
        except:
            return 0.0

    def hr_to_num(s):
        try:
            # "5-9本" -> 5, "30-34本" -> 30
            return int(s.replace("本", "").split("-")[0])
        except:
            return 0

    def ops_to_num(s):
        try:
            # ".750-.799" -> 0.750
            return float(s.split("-")[0])
        except:
            return 0.0

    df["打率_num"] = df["打率予測"].apply(ba_to_num)
    df["HR_num"]  = df["HR予測"].apply(hr_to_num)
    df["OPS_num"] = df["OPS予測"].apply(ops_to_num)

    # 全角表示用ラベル "30-34本" -> "３０本〜３４本"
    def hr_to_label(s):
        try:
            s2 = s.replace("本", "")
            lo, hi = s2.split("-")
            def to_zen(n):
                return str(n).translate(str.maketrans("0123456789", "０１２３４５６７８９"))
            return f"{to_zen(lo)}本〜{to_zen(hi)}本"
        except:
            return s
    df["HR_label"] = df["HR予測"].apply(hr_to_label)

    # リーグ区分
    セ = {"ヤクルト","巨人","阪神","広島","中日","ＤｅＮＡ"}
    df["リーグ"] = df["チーム"].apply(lambda t: "セ・リーグ" if t in セ else "パ・リーグ")
    return df

df = load_data()

# チームカラー
TEAM_COLORS = {
    "ヤクルト": "#00A0E9", "巨人": "#F7971E", "阪神": "#FFE200",
    "広島": "#E60012",     "中日": "#003087", "ＤｅＮＡ": "#004B87",
    "ソフトバンク": "#FFD700", "楽天": "#9B111E", "日本ハム": "#00529B",
    "ロッテ": "#000000",   "西武": "#003E7E", "オリックス": "#00318F",
}

# ────────────────────────────────────────────
# サイドバー：フィルター
# ────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚾ フィルター設定")
    st.markdown("---")

    # リーグ
    leagues = ["全リーグ"] + sorted(df["リーグ"].unique().tolist())
    sel_league = st.selectbox("🏟️ リーグ", leagues)

    # チーム
    if sel_league == "全リーグ":
        teams_avail = sorted(df["チーム"].unique().tolist())
    else:
        teams_avail = sorted(df[df["リーグ"]==sel_league]["チーム"].unique().tolist())
    sel_teams = st.multiselect("🎽 チーム（複数選択可）", teams_avail, default=teams_avail)

    st.markdown("---")

    # HR フィルター
    hr_options = ["全て", "0-4本", "5-9本", "10-14本", "15-19本", "20-24本", "25-29本", "30-34本"]
    sel_hr = st.multiselect("💪 本塁打予測", hr_options[1:], default=hr_options[1:])
    if not sel_hr:
        sel_hr = hr_options[1:]

    st.markdown("---")

    # ソート
    sort_col = st.selectbox("📊 並び順", ["打率_num", "HR_num", "OPS_num"], format_func=lambda x: {"打率_num":"打率（高い順）","HR_num":"本塁打（多い順）","OPS_num":"OPS（高い順）"}[x])

    st.markdown("---")
    st.markdown("### 📌 選手名検索")
    search = st.text_input("選手名を入力", placeholder="例：大谷")

# ────────────────────────────────────────────
# データ絞り込み
# ────────────────────────────────────────────
filtered = df.copy()
if sel_teams:
    filtered = filtered[filtered["チーム"].isin(sel_teams)]
filtered = filtered[filtered["HR予測"].isin(sel_hr)]
if search:
    filtered = filtered[filtered["選手名"].str.contains(search, na=False)]
filtered = filtered.sort_values(sort_col, ascending=False).reset_index(drop=True)

# ────────────────────────────────────────────
# ヘッダー
# ────────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(135deg,#1a2a6c,#b21f1f,#1a2a6c);
            padding:24px 32px;border-radius:16px;margin-bottom:24px;">
  <h1 style="margin:0;color:#fff;font-size:2rem;">⚾ NPB 2026 選手成績予測ダッシュボード</h1>
  <p style="margin:6px 0 0;color:#ccd;">機械学習による2026年シーズン打撃成績予測</p>
</div>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────
# サマリーメトリクス
# ────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📋 表示選手数", f"{len(filtered)} 名", f"全{len(df)}名中")
with col2:
    top_ba = filtered.nlargest(1,"打率_num")
    name_ba = top_ba["選手名"].values[0] if len(top_ba) else "-"
    val_ba  = top_ba["打率予測"].values[0] if len(top_ba) else "-"
    st.metric("🏆 打率トップ", name_ba, val_ba)
with col3:
    top_hr = filtered.nlargest(1,"HR_num")
    name_hr = top_hr["選手名"].values[0] if len(top_hr) else "-"
    val_hr  = top_hr["HR予測"].values[0] if len(top_hr) else "-"
    st.metric("💣 HR予測トップ", name_hr, val_hr)
with col4:
    top_ops = filtered.nlargest(1,"OPS_num")
    name_ops = top_ops["選手名"].values[0] if len(top_ops) else "-"
    val_ops  = top_ops["OPS予測"].values[0] if len(top_ops) else "-"
    st.metric("⚡ OPSトップ", name_ops, val_ops)

st.markdown("<br>", unsafe_allow_html=True)

# ────────────────────────────────────────────
# タブ
# ────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📋 一覧テーブル", "📊 チーム別分析", "🔥 ランキング", "🗺️ 分布マップ"])

# ──────── TAB 1: テーブル ────────
with tab1:
    st.markdown("### 選手成績予測一覧")

    # 表示用DataFrameを rename 後の列名で一本化
    display_df = filtered[["選手名","チーム","リーグ","打率_num","打率予測","HR_num","HR_label","OPS_num","OPS予測"]].copy()
    display_df = display_df.rename(columns={
        "打率_num":  "打率(数値)",
        "HR_num":   "HR(数値)",
        "HR_label": "本塁打予測",
        "OPS_num":  "OPS(数値)",
    })
    display_df.index = range(1, len(display_df)+1)

    # ── グラデーション: 列全体を受け取り各セルのスタイルを返す ──
    def grad_col(series, low_rgb, high_rgb):
        mn, mx = series.min(), series.max()
        def cell(val):
            t = (val - mn) / (mx - mn) if mx != mn else 0.5
            r = int(low_rgb[0] + t * (high_rgb[0] - low_rgb[0]))
            g = int(low_rgb[1] + t * (high_rgb[1] - low_rgb[1]))
            b = int(low_rgb[2] + t * (high_rgb[2] - low_rgb[2]))
            lum = 0.299*r + 0.587*g + 0.114*b
            fg = "#ffffff" if lum < 140 else "#111111"
            return f"background-color:rgb({r},{g},{b});color:{fg};font-weight:600;"
        return series.apply(cell)

    styled = (
        display_df
        .style
        # rename後の列名で直接 applymap
        .apply(lambda s: grad_col(s, (20,50,90),  (0,200,160)),  subset=["打率(数値)"])
        .apply(lambda s: grad_col(s, (60,35,15),  (220,55,15)),  subset=["HR(数値)"])
        .apply(lambda s: grad_col(s, (35,25,65),  (155,75,235)), subset=["OPS(数値)"])
        .format({
            "打率(数値)": "{:.3f}",
            "HR(数値)":  "{:d}",
            "OPS(数値)": "{:.3f}",
        })
    )

    st.dataframe(
        styled,
        use_container_width=True,
        height=540,
        column_config={
            "選手名":   st.column_config.TextColumn(width=130),
            "チーム":   st.column_config.TextColumn(width=100),
            "リーグ":   st.column_config.TextColumn(width=100),
            "打率(数値)": st.column_config.NumberColumn(width=95),
            "打率予測":  st.column_config.TextColumn("打率予測帯", width=105),
            "HR(数値)":  st.column_config.NumberColumn(width=80),
            "本塁打予測": st.column_config.TextColumn(width=125),
            "OPS(数値)": st.column_config.NumberColumn(width=95),
            "OPS予測":  st.column_config.TextColumn("OPS予測帯", width=105),
        }
    )

    # CSV ダウンロード
    csv_dl = display_df[["選手名","チーム","リーグ","打率予測","本塁打予測","OPS予測"]]
    csv = csv_dl.to_csv(encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button("📥 CSVダウンロード", csv, "npb2026_filtered.csv", "text/csv")

# ──────── TAB 2: チーム別分析 ────────
with tab2:
    st.markdown("### チーム別 平均予測値")

    team_agg = (
        filtered.groupby("チーム")[["打率_num","HR_num","OPS_num"]]
        .mean()
        .reset_index()
        .sort_values("OPS_num", ascending=False)
    )

    c1, c2 = st.columns(2)

    with c1:
        fig_ba = px.bar(
            team_agg, x="チーム", y="打率_num",
            title="チーム別 平均打率予測",
            color="チーム",
            color_discrete_map=TEAM_COLORS,
            text=team_agg["打率_num"].apply(lambda v: f".{int(v*1000):03d}"),
        )
        fig_ba.update_layout(
            plot_bgcolor="#0f1117", paper_bgcolor="#0f1117",
            font_color="#c8d4ff", showlegend=False,
            xaxis_tickangle=-40,
        )
        fig_ba.update_traces(textposition="outside")
        st.plotly_chart(fig_ba, use_container_width=True)

    with c2:
        fig_hr = px.bar(
            team_agg, x="チーム", y="HR_num",
            title="チーム別 平均HR予測",
            color="チーム",
            color_discrete_map=TEAM_COLORS,
            text=team_agg["HR_num"].apply(lambda v: f"{v:.1f}本"),
        )
        fig_hr.update_layout(
            plot_bgcolor="#0f1117", paper_bgcolor="#0f1117",
            font_color="#c8d4ff", showlegend=False,
            xaxis_tickangle=-40,
        )
        fig_hr.update_traces(textposition="outside")
        st.plotly_chart(fig_hr, use_container_width=True)

    # OPS バブルチャート
    fig_ops = px.scatter(
        team_agg, x="打率_num", y="OPS_num",
        size="HR_num", color="チーム",
        color_discrete_map=TEAM_COLORS,
        text="チーム",
        title="チーム別 打率 vs OPS（バブル=HR）",
        labels={"打率_num":"平均打率","OPS_num":"平均OPS"},
        size_max=50,
    )
    fig_ops.update_layout(
        plot_bgcolor="#0f1117", paper_bgcolor="#0f1117",
        font_color="#c8d4ff", showlegend=False, height=420,
    )
    fig_ops.update_traces(textposition="top center")
    st.plotly_chart(fig_ops, use_container_width=True)

    # リーグ別円グラフ
    league_cnt = filtered.groupby("リーグ").size().reset_index(name="人数")
    fig_pie = px.pie(
        league_cnt, names="リーグ", values="人数",
        title="リーグ別 選手構成",
        color_discrete_sequence=["#4f7bef","#e05a5a"],
        hole=0.45,
    )
    fig_pie.update_layout(
        plot_bgcolor="#0f1117", paper_bgcolor="#0f1117",
        font_color="#c8d4ff",
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# ──────── TAB 3: ランキング ────────
with tab3:
    st.markdown("### 🏆 各部門トップ10")

    r1, r2, r3 = st.columns(3)

    def rank_card(col, metric_col, label, fmt):
        top10 = filtered.nlargest(10, metric_col)[["選手名","チーム", metric_col]]
        top10 = top10.reset_index(drop=True)
        top10.index += 1

        bars = []
        max_v = top10[metric_col].max() if len(top10) else 1
        for i, row in top10.iterrows():
            pct = row[metric_col] / max_v * 100 if max_v else 0
            medal = {1:"🥇",2:"🥈",3:"🥉"}.get(i,"")
            tc = TEAM_COLORS.get(row["チーム"], "#555577")
            bars.append(f"""
            <div style="margin-bottom:8px;">
              <div style="display:flex;justify-content:space-between;
                          color:#e0e8ff;font-size:13px;margin-bottom:3px;">
                <span>{medal} <b>{row['選手名']}</b>
                      <span style="color:#9aadcc;font-size:11px;"> {row['チーム']}</span></span>
                <span style="color:#93c5fd;font-weight:600;">{fmt(row[metric_col])}</span>
              </div>
              <div style="background:#1e2139;border-radius:4px;height:6px;">
                <div style="background:{tc};width:{pct:.0f}%;height:6px;
                            border-radius:4px;"></div>
              </div>
            </div>""")

        col.markdown(f"#### {label}", unsafe_allow_html=False)
        col.markdown("".join(bars), unsafe_allow_html=True)

    with r1:
        rank_card(r1, "打率_num", "打率ランキング", lambda v: f".{int(v*1000):03d}")
    with r2:
        rank_card(r2, "HR_num",  "本塁打ランキング", lambda v: f"{int(v)}本")
    with r3:
        rank_card(r3, "OPS_num", "OPSランキング",   lambda v: f".{int(v*1000):03d}")

# ──────── TAB 4: 分布マップ ────────
with tab4:
    st.markdown("### 📊 予測値の分布")

    d1, d2 = st.columns(2)

    with d1:
        hr_cnt = filtered["HR予測"].value_counts().reset_index()
        hr_cnt.columns = ["HR予測","人数"]
        hr_order = ["0-4本","5-9本","10-14本","15-19本","20-24本","25-29本","30-34本"]
        hr_cnt["sort_key"] = hr_cnt["HR予測"].apply(lambda x: hr_order.index(x) if x in hr_order else 99)
        hr_cnt = hr_cnt.sort_values("sort_key")

        fig_hr_dist = px.bar(
            hr_cnt, x="HR予測", y="人数",
            title="本塁打予測分布",
            color="人数",
            color_continuous_scale="Blues",
            text="人数",
        )
        fig_hr_dist.update_layout(
            plot_bgcolor="#0f1117", paper_bgcolor="#0f1117",
            font_color="#c8d4ff", showlegend=False,
            coloraxis_showscale=False,
        )
        fig_hr_dist.update_traces(textposition="outside")
        st.plotly_chart(fig_hr_dist, use_container_width=True)

    with d2:
        ops_cnt = filtered["OPS予測"].value_counts().reset_index()
        ops_cnt.columns = ["OPS予測","人数"]
        fig_ops_dist = px.bar(
            ops_cnt, x="OPS予測", y="人数",
            title="OPS予測分布",
            color="人数",
            color_continuous_scale="Purples",
            text="人数",
        )
        fig_ops_dist.update_layout(
            plot_bgcolor="#0f1117", paper_bgcolor="#0f1117",
            font_color="#c8d4ff", showlegend=False,
            coloraxis_showscale=False,
        )
        fig_ops_dist.update_traces(textposition="outside")
        st.plotly_chart(fig_ops_dist, use_container_width=True)

    # 打率分布（ヒートマップ風）
    ba_cnt = filtered["打率予測"].value_counts().reset_index()
    ba_cnt.columns = ["打率予測","人数"]
    ba_cnt = ba_cnt.sort_values("打率予測")

    fig_ba_dist = px.bar(
        ba_cnt, x="打率予測", y="人数",
        title="打率予測分布（全選手）",
        color="人数",
        color_continuous_scale="Teal",
        text="人数",
    )
    fig_ba_dist.update_layout(
        plot_bgcolor="#0f1117", paper_bgcolor="#0f1117",
        font_color="#c8d4ff", showlegend=False,
        coloraxis_showscale=False,
        xaxis_tickangle=-40,
    )
    fig_ba_dist.update_traces(textposition="outside")
    st.plotly_chart(fig_ba_dist, use_container_width=True)

    # チーム×HR ヒートマップ
    st.markdown("#### チーム × HR予測 ヒートマップ")
    pivot = pd.crosstab(filtered["チーム"], filtered["HR予測"])
    hr_order2 = [c for c in hr_order if c in pivot.columns]
    pivot = pivot.reindex(columns=hr_order2, fill_value=0)

    fig_heat = px.imshow(
        pivot,
        title="チーム × 本塁打予測（人数）",
        color_continuous_scale="Blues",
        text_auto=True,
        aspect="auto",
    )
    fig_heat.update_layout(
        plot_bgcolor="#0f1117", paper_bgcolor="#0f1117",
        font_color="#c8d4ff", height=420,
    )
    st.plotly_chart(fig_heat, use_container_width=True)

# ────────────────────────────────────────────
# フッター
# ────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#4a5280;font-size:12px;'>"
    "NPB 2026 予測ダッシュボード | データ: final_predict_2026.csv"
    "</p>",
    unsafe_allow_html=True
)
