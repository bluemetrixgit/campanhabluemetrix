# Streamlit App — Campanha NET (deploy) — v9 (ranking compacto & transparente)
# Autor: ChatGPT ("Chico")
# Como rodar:
#   pip install streamlit pandas numpy openpyxl xlsxwriter pytz plotly pillow
#   streamlit run app_campanha_net_v9.py
#
# Estrutura de arquivos esperada no repositório:
#   ./logo.branca(.png|.jpg|.jpeg|.webp)
#   ./dados/Campanha Captação.xlsx            (aba Planilha1)
#   ./dados/FX Dolar.xlsx                     (colunas: Date, USDBRL)

from __future__ import annotations

import io
from typing import List, Tuple, Optional
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import pytz
import plotly.express as px
from PIL import Image

# ===================== CONFIG =====================
APP_TITLE = "Campanha de Captação — NET (R$)"
BASELINE_COL_STR = "30/06/2025"  # baseline fixo
PERIODO_INICIO = "30/06/2025"
PERIODO_FIM = "10/12/2025"
GOAL_META = 65_000_000.0

# Caminhos relativos
LOGO_CANDIDATES = ["logo.branca", "logo.branca.png", "logo.branca.jpg", "logo.branca.jpeg", "logo.branca.webp"]
FILE_CAMPANHA = Path("dados") / "Campanha Captação.xlsx"
FILE_FX = Path("dados") / "FX Dolar.xlsx"   # colunas: Date, USDBRL

# Corretoras em USD (converter para BRL)
USD_BROKERS = {"XP Internacional", "Pershing", "Interactive Brokers", "Avenue"}

SP_TZ = pytz.timezone("America/Sao_Paulo")

# ===================== UTILS =====================
def format_brl(x: float) -> str:
    try:
        return "R$ {:,.2f}".format(float(x)).replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(x)

def load_logo() -> Optional[Image.Image]:
    for name in LOGO_CANDIDATES:
        p = Path(name)
        if p.suffix == "":
            for ext in [".png",".jpg",".jpeg",".webp"]:
                q = p.with_suffix(ext)
                if q.exists():
                    return Image.open(q)
        else:
            if p.exists():
                return Image.open(p)
    return None

def detect_current_col(cols: List[str]) -> Tuple[str, List[str]]:
    cols = [str(c).strip() for c in cols]
    d1 = [c for c in cols if "d-1" in c.lower()]
    if d1:
        return d1[-1], d1
    dates = []
    for c in cols:
        if c.count("/") == 2:
            try:
                pd.to_datetime(c, dayfirst=True, errors="raise")
                dates.append(c)
            except Exception:
                pass
    if dates:
        dates = sorted(dates, key=lambda x: pd.to_datetime(x, dayfirst=True))
        return dates[-1], []
    return BASELINE_COL_STR, []

def read_fx_table(path: Path) -> Optional[pd.DataFrame]:
    if not path.exists():
        return None
    try:
        if path.suffix.lower() in [".csv",".txt"]:
            fx = pd.read_csv(path)
        else:
            fx = pd.read_excel(path)
        fx.columns = [str(c).strip() for c in fx.columns]
        date_col = next((c for c in fx.columns if c.lower() in ["date","data"]), None)
        rate_col = next((c for c in fx.columns if c.lower() in ["usdxbrl","usdbrl","cambio","rate"]), None)
        if date_col is None or rate_col is None:
            if "Date" in fx.columns and "USDBRL" in fx.columns:
                date_col, rate_col = "Date", "USDBRL"
            else:
                return None
        fx = fx[[date_col, rate_col]].rename(columns={date_col:"Date", rate_col:"USDBRL"})
        fx["Date"] = pd.to_datetime(fx["Date"], errors="coerce").dt.date
        fx = fx.dropna(subset=["Date","USDBRL"]).copy()
        return fx
    except Exception:
        return None

def fx_for_label(label: str, fx_table: Optional[pd.DataFrame], manual_rate: float) -> float:
    dt = None
    try:
        dt = pd.to_datetime(label, dayfirst=True, errors="raise").date()
    except Exception:
        pass
    if dt is None and "d-1" in label.lower():
        dt = (datetime.now(SP_TZ).date() - timedelta(days=1))
    if dt is None or fx_table is None:
        return manual_rate
    row = fx_table.loc[fx_table["Date"] == dt]
    if row.empty:
        prior = fx_table.loc[fx_table["Date"] <= dt].sort_values("Date").tail(1)
        if prior.empty:
            return manual_rate
        return float(prior["USDBRL"].iloc[0])
    return float(row["USDBRL"].iloc[0])

# ===================== THEME =====================
st.set_page_config(page_title=APP_TITLE, page_icon="🎯", layout="wide")
st.markdown("""
    <style>
    .stApp {background: radial-gradient(1200px 600px at 10% -20%, #0f1c3a 0%, #0b1220 60%, #0b1220 100%);}
    .metric-card {padding: 16px 18px; border-radius: 14px; background: #101a33; border: 1px solid rgba(255,255,255,0.06); box-shadow: 0 10px 25px rgba(0,0,0,0.25);}
    .metric-title {color: #9fb3ff; font-size: 12px; text-transform: uppercase; letter-spacing: .12em; margin-bottom: 6px;}
    .metric-value {color: #e8eeff; font-size: 22px; font-weight: 700;}
    .badge {display: inline-block; padding: 6px 10px; border-radius: 999px; font-size: 12px; margin-right: 8px; border: 1px solid rgba(255,255,255,0.14);}
    .badge-green {background: rgba(0,180,120,0.15); color:#bfffe9;}
    .badge-yellow {background: rgba(247,208,96,0.15); color:#ffe8a6;}
    .badge-blue {background: rgba(99,150,255,0.15); color:#cfe0ff;}
    .panel {padding: 18px; border-radius: 16px; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06);}
    .title-hero {font-size: 28px; font-weight: 800; color:#e9efff; letter-spacing:.02em;}
    .subtitle {color:#b8c3ff;}
    .stDataFrame th {background: #0f1c3a !important; color:#cfe0ff !important; white-space: normal !important;}
    .stDataFrame td {color:#e8eeff !important; white-space: normal !important;}
    </style>
""", unsafe_allow_html=True)

# ===================== HEADER =====================
left, right = st.columns([6,2])
with left:
    st.markdown(f'<div class="title-hero">{APP_TITLE}</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Acompanhamento consolidado com conversão USD→BRL e D‑1 inteligente</div>', unsafe_allow_html=True)
    st.markdown(f'<span class="badge badge-blue"><b>Período</b>: {PERIODO_INICIO} → {PERIODO_FIM}</span>', unsafe_allow_html=True)
    st.markdown('<span class="badge badge-yellow"><b>Retrato</b>: toda <b>quarta‑feira</b></span>', unsafe_allow_html=True)
    st.markdown(f'<span class="badge badge-green"><b>Meta NET</b>: {format_brl(GOAL_META)}</span>', unsafe_allow_html=True)
    st.markdown('<div class="panel" style="margin-top:8px;">'
                '<b>Premiação</b>: 1º R$ 50.000 • 2º R$ 30.000 • 3º R$ 20.000'
                '</div>', unsafe_allow_html=True)
with right:
    logo_img = None
    for name in LOGO_CANDIDATES:
        p = Path(name)
        if p.suffix == "":
            for ext in [".png",".jpg",".jpeg",".webp"]:
                q = p.with_suffix(ext)
                if q.exists():
                    logo_img = Image.open(q)
                    break
        elif p.exists():
            logo_img = Image.open(p)
            break
    if logo_img is not None:
        st.image(logo_img, width=250)

# ===================== LOAD DATA =====================
if not FILE_CAMPANHA.exists():
    st.error(f"Arquivo de campanha não encontrado: {FILE_CAMPANHA}")
    st.stop()
df = pd.read_excel(FILE_CAMPANHA, sheet_name="Planilha1")
df.columns = [str(c).strip() for c in df.columns]

fx_table = None
if FILE_FX.exists():
    fx_table = pd.read_excel(FILE_FX)
    fx_table.columns = [str(c).strip() for c in fx_table.columns]
    date_col = next((c for c in fx_table.columns if c.lower() in ["date","data"]), None)
    rate_col = next((c for c in fx_table.columns if c.lower() in ["usdxbrl","usdbrl","cambio","rate"]), None)
    if date_col and rate_col:
        fx_table = fx_table[[date_col, rate_col]].rename(columns={date_col:"Date", rate_col:"USDBRL"})
        fx_table["Date"] = pd.to_datetime(fx_table["Date"], errors="coerce").dt.date
        fx_table = fx_table.dropna(subset=["Date","USDBRL"]).copy()
    else:
        fx_table = None

if BASELINE_COL_STR not in df.columns:
    st.error(f"Coluna de baseline '{BASELINE_COL_STR}' não encontrada no arquivo.")
    st.stop()

def detect_current_col(cols: List[str]) -> Tuple[str, List[str]]:
    cols = [str(c).strip() for c in cols]
    d1 = [c for c in cols if "d-1" in c.lower()]
    if d1:
        return d1[-1], d1
    dates = []
    for c in cols:
        if c.count("/") == 2:
            try:
                pd.to_datetime(c, dayfirst=True, errors="raise")
                dates.append(c)
            except Exception:
                pass
    if dates:
        dates = sorted(dates, key=lambda x: pd.to_datetime(x, dayfirst=True))
        return dates[-1], []
    return BASELINE_COL_STR, []

current_col, d1_list = detect_current_col(df.columns)

# FX
USD_BASE_MANUAL = 5.00
USD_CURR_MANUAL = 5.00
usd_rate_base = fx_for_label(BASELINE_COL_STR, fx_table, USD_BASE_MANUAL)
usd_rate_curr = fx_for_label(current_col, fx_table, USD_CURR_MANUAL)

# Painel base
for c in [BASELINE_COL_STR, current_col]:
    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)

keep = ["Corretora","Cliente","Conta","Escritório","UF","Assessor","Carteira"]
keep = [c for c in keep if c in df.columns]
panel = df[keep + [BASELINE_COL_STR, current_col]].copy()
panel = panel.rename(columns={BASELINE_COL_STR:"PL_30_06_2025", current_col:"PL_Atual"})

# Conversão para BRL
is_usd = panel["Corretora"].isin(USD_BROKERS) if "Corretora" in panel.columns else False
panel["PL_30_06_2025_BRL"] = np.where(is_usd, panel["PL_30_06_2025"] * usd_rate_base, panel["PL_30_06_2025"])
panel["PL_Atual_BRL"] = np.where(is_usd, panel["PL_Atual"] * usd_rate_curr, panel["PL_Atual"])
panel["Delta_BRL"] = panel["PL_Atual_BRL"] - panel["PL_30_06_2025_BRL"]

# ===================== FILTERS =====================
st.markdown("#### Filtros")
c1, c2, c3 = st.columns(3)
with c1:
    escrit = ["(Todos)"] + sorted([x for x in panel.get("Escritório", pd.Series()).dropna().unique().tolist()])
    f_escr = st.selectbox("Escritório", escrit, index=0)
with c2:
    corrs = ["(Todos)"] + sorted([x for x in panel.get("Corretora", pd.Series()).dropna().unique().tolist()])
    f_corr = st.selectbox("Corretora", corrs, index=0)
with c3:
    ufs = ["(Todas)"] + sorted([x for x in panel.get("UF", pd.Series()).dropna().unique().tolist()])
    f_uf = st.selectbox("UF", ufs, index=0)

flt = panel.copy()
if f_escr != "(Todos)":
    flt = flt[flt["Escritório"] == f_escr]
if f_corr != "(Todos)":
    flt = flt[flt["Corretora"] == f_corr]
if f_uf != "(Todas)":
    flt = flt[flt["UF"] == f_uf]

# ===================== KPIs =====================
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown('<div class="metric-card"><div class="metric-title">PL Base (30/06/2025)</div>'
                f'<div class="metric-value">{format_brl(flt["PL_30_06_2025_BRL"].sum())}</div></div>', unsafe_allow_html=True)
with k2:
    st.markdown('<div class="metric-card"><div class="metric-title">PL Atual</div>'
                f'<div class="metric-value">{format_brl(flt["PL_Atual_BRL"].sum())}</div></div>', unsafe_allow_html=True)
with k3:
    cap_liq = flt["Delta_BRL"].sum()
    st.markdown('<div class="metric-card"><div class="metric-title">Captação Líquida NET</div>'
                f'<div class="metric-value">{format_brl(cap_liq)}</div></div>', unsafe_allow_html=True)
with k4:
    st.markdown('<div class="metric-card"><div class="metric-title">Data Atual Usada</div>'
                f'<div class="metric-value">{current_col}</div></div>', unsafe_allow_html=True)

# ===================== RANKING (Tabela primeiro, Gráfico depois) =====================
st.markdown("### Ranking por Assessor — NET (R$)")

# Tabela compacta primeiro
page_len = st.slider("Linhas por página (ranking)", 10, 50, 20, 5)
rank_net = (flt.groupby("Assessor", dropna=False)["Delta_BRL"]
               .sum().sort_values(ascending=False).reset_index()
               .rename(columns={"Delta_BRL":"Captação NET (R$)"}))
rank_tbl = rank_net.copy()
rank_tbl["Captação NET (R$)"] = rank_tbl["Captação NET (R$)"].apply(format_brl)
st.dataframe(rank_tbl, use_container_width=True, height=48 + 32*min(page_len, len(rank_tbl)))

# Gráfico abaixo — compacto, fundo transparente, cor personalizada
BLUEMETRIX_ACCENT = "#d99c3a"  # dourado da marca
fig = px.bar(
    rank_net.sort_values("Captação NET (R$)", ascending=True),
    x="Captação NET (R$)", y="Assessor",
    orientation="h",
    title="Captação NET (R$) por Assessor (aplica filtros)",
    color_discrete_sequence=[BLUEMETRIX_ACCENT]
)
fig.update_layout(
    height=600,  # fixo e compacto
    template="plotly_dark",
    margin=dict(l=180, r=10, t=40, b=10),
    yaxis=dict(automargin=True),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    bargap=0.35  # barras mais finas
)
fig.update_traces(marker_line_color="rgba(255,255,255,0.15)", marker_line_width=0.5)
st.plotly_chart(fig, use_container_width=True)

# ===================== DIAGNÓSTICO POR ASSESSOR =====================
st.markdown("### Diagnóstico por Assessor (NET) — Detalhe cliente a cliente")
assessores = ["(Selecione)"] + sorted([x for x in flt["Assessor"].dropna().unique().tolist()])
sel = st.selectbox("Assessor", assessores, index=0)

if sel != "(Selecione)":
    base_ass = flt[flt["Assessor"] == sel].copy()

    total_base = base_ass["PL_30_06_2025_BRL"].sum()
    total_atual = base_ass["PL_Atual_BRL"].sum()
    total_delta = base_ass["Delta_BRL"].sum()

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-title">PL Base ({sel})</div>'
                    f'<div class="metric-value">{format_brl(total_base)}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div class="metric-title">PL Atual ({sel})</div>'
                    f'<div class="metric-value">{format_brl(total_atual)}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Captação NET ({sel})</div>'
                    f'<div class="metric-value">{format_brl(total_delta)}</div></div>', unsafe_allow_html=True)

    base_ass["Positivo"] = base_ass["Delta_BRL"] > 0
    qtd_pos = int(base_ass["Positivo"].sum())
    qtd_neg = int((~base_ass["Positivo"]).sum())
    st.markdown(f'<span class="badge badge-green">Clientes Positivos: {qtd_pos}</span> '
                f'<span class="badge badge-yellow">Clientes Negativos: {qtd_neg}</span>', unsafe_allow_html=True)

    st.markdown("#### Tabela — Clientes (R$)")
    show_cols = [c for c in ["Corretora","Cliente","Conta","Escritório","UF","Carteira",
                             "PL_30_06_2025_BRL","PL_Atual_BRL","Delta_BRL"] if c in base_ass.columns]
    base_ass_disp = base_ass[show_cols].copy()
    for c in ["PL_30_06_2025_BRL","PL_Atual_BRL","Delta_BRL"]:
        if c in base_ass_disp.columns:
            base_ass_disp[c] = base_ass_disp[c].apply(format_brl)
    rows = st.slider("Linhas por página (diagnóstico)", 10, 80, 25, 5)
    st.dataframe(base_ass_disp, use_container_width=True, height=48 + 32*min(rows, len(base_ass_disp)))

# ===================== DOWNLOAD =====================
st.markdown("---")
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
    panel.to_excel(writer, sheet_name="Painel_NET_R$", index=False)
    rank_net.to_excel(writer, sheet_name="Ranking_Assessores_NET", index=False)
buffer.seek(0)

st.download_button(
    label="📥 Baixar Excel (Painel NET R$ + Ranking)",
    data=buffer.read(),
    file_name="Diagnostico_Campanha_NET_R$_deploy.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
