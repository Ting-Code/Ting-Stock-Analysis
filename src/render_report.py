"""Render single-stock review HTML with Plotly charts."""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.offline import plot as plot_offline
from .market import resample_ohlcv
from .valuation import percentile

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>__NAME__(__CODE__) 复盘页</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
:root{--bg:#f6f3ee;--ink:#1c1917;--muted:#78716c;--card:#fffdf9;--line:#e7e0d5;--accent:#0f766e}
*{box-sizing:border-box}
body{margin:0;font-family:Segoe UI,PingFang SC,Microsoft YaHei,sans-serif;background:linear-gradient(180deg,#efe8dc 0%,var(--bg) 240px);color:var(--ink);line-height:1.55}
.wrap{max-width:1100px;margin:0 auto;padding:28px 18px 60px}
h1{font-size:1.8rem;margin:0 0 6px}
.sub{color:var(--muted);margin-bottom:18px}
.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:18px 0 28px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px}
.card .label{color:var(--muted);font-size:.82rem}
.card .value{font-size:1.35rem;font-weight:650;margin-top:4px}
.card .hint{color:var(--muted);font-size:.78rem;margin-top:4px}
section{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:14px 14px 8px;margin-bottom:18px}
h2{font-size:1.05rem;margin:4px 8px 8px;color:var(--accent)}
.note{color:var(--muted);font-size:.86rem;padding:0 8px 8px}
.disclaimer{margin-top:24px;padding:14px 16px;border-left:3px solid var(--accent);background:#fff;color:var(--muted);font-size:.85rem}
@media(max-width:800px){.cards{grid-template-columns:1fr 1fr}}
</style></head><body><div class="wrap">
<h1>__NAME__ <span style="font-weight:500;color:var(--muted)">(__CODE__)</span></h1>
<div class="sub">单票复盘页 · 数据截至 __ASOF__ · 前复权 · 估值锚定：季报发布日次月月末收盘</div>
<div class="cards">
<div class="card"><div class="label">现价</div><div class="value">__PRICE__</div><div class="hint">最新交易日收盘</div></div>
<div class="card"><div class="label">动态PE (TTM扣非)</div><div class="value">__PE__</div><div class="hint">历史分位 __PE_PCT__</div></div>
<div class="card"><div class="label">市净率 PB</div><div class="value">__PB__</div><div class="hint">历史分位 __PB_PCT__</div></div>
<div class="card"><div class="label">股息率</div><div class="value">__DIV__</div><div class="hint">近12个月已实施现金分红/现价 · 分位 __DIV_PCT__</div></div>
</div>
<section><h2>A. 行情 K 线</h2><div class="note">可切换日/周/月/季；滚轮缩放、拖动平移。</div>__K__</section>
<section><h2>B. 季度营收与利润</h2><div class="note">东财报表为累计值，已拆成单季；扣非=归母扣非净利润。</div>__F__</section>
<section><h2>C. 估值序列 vs 现价</h2><div class="note">观察点：NOTICE次月月末收盘价 / TTM扣非每股；同日标 PB、股息率。红虚线=当前PE。</div>__V__</section>
<div class="disclaimer">本页仅供学习与复盘展示，不构成投资建议。数据来自 BaoStock / 东财(AkShare)，请以官方披露为准。</div>
</div></body></html>
"""

def _kline_figure(daily: pd.DataFrame, title: str) -> go.Figure:
    periods = [('日线', 'D'), ('周线', 'W'), ('月线', 'M'), ('季线', 'Q')]
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.72, 0.28], vertical_spacing=0.03)
    buttons = []
    for i, (label, p) in enumerate(periods):
        df = resample_ohlcv(daily, p)
        visible = [False] * (len(periods) * 2)
        visible[i * 2] = True
        visible[i * 2 + 1] = True
        colors = ['#ef5350' if c >= o else '#26a69a' for o, c in zip(df['open'], df['close'])]
        fig.add_trace(go.Candlestick(x=df['date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name='K-' + label, increasing_line_color='#ef5350', decreasing_line_color='#26a69a', visible=(i == 0)), row=1, col=1)
        fig.add_trace(go.Bar(x=df['date'], y=df['volume'], name='V-' + label, marker_color=colors, opacity=0.8, visible=(i == 0), showlegend=False), row=2, col=1)
        buttons.append(dict(label=label, method='update', args=[{'visible': visible}]))
    fig.update_layout(title=title, template='plotly_white', height=560, margin=dict(l=40, r=20, t=60, b=30), xaxis_rangeslider_visible=False, hovermode='x unified', dragmode='pan', updatemenus=[dict(type='buttons', direction='right', x=0, y=1.12, xanchor='left', buttons=buttons)])
    fig.update_yaxes(title_text='价格', row=1, col=1)
    fig.update_yaxes(title_text='成交量', row=2, col=1)
    return fig


def _fundamental_figure(fundamentals: pd.DataFrame) -> go.Figure:
    df = fundamentals.dropna(subset=['REPORT_DATE']).copy()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['REPORT_DATE'], y=df['revenue_q'] / 1e8, name='单季营收(亿)', marker_color='#42a5f5', opacity=0.85))
    fig.add_trace(go.Scatter(x=df['REPORT_DATE'], y=df['deduct_np_q'] / 1e8, name='单季扣非(亿)', mode='lines+markers', yaxis='y2', line=dict(color='#ef6c00', width=2)))
    fig.add_trace(go.Scatter(x=df['REPORT_DATE'], y=df['parent_np_q'] / 1e8, name='单季归母净利(亿)', mode='lines+markers', yaxis='y2', line=dict(color='#7e57c2', width=1.5, dash='dot')))
    fig.update_layout(title='上市以来季度盈利（累计报表已拆单季）', template='plotly_white', height=420, margin=dict(l=40, r=50, t=50, b=30), yaxis=dict(title='营收(亿元)'), yaxis2=dict(title='利润(亿元)', overlaying='y', side='right'), legend=dict(orientation='h', y=1.08), hovermode='x unified')
    return fig


def _valuation_figure(val: pd.DataFrame, snap: dict) -> go.Figure:
    fig = make_subplots(specs=[[{'secondary_y': True}]])
    fig.add_trace(go.Scatter(x=val['anchor_date'], y=val['pe_ttm_deduct'], mode='lines+markers', name='动态PE(TTM扣非)', line=dict(color='#ef5350', width=2)), secondary_y=False)
    fig.add_trace(go.Scatter(x=val['anchor_date'], y=val['pb'], mode='lines+markers', name='PB', line=dict(color='#42a5f5', width=1.5)), secondary_y=True)
    fig.add_trace(go.Scatter(x=val['anchor_date'], y=val['div_yield_pct'], mode='lines+markers', name='股息率%', line=dict(color='#26a69a', width=1.5, dash='dot')), secondary_y=True)
    if snap.get('pe_ttm_deduct') is not None:
        fig.add_hline(y=snap['pe_ttm_deduct'], line_dash='dash', line_color='#c62828', annotation_text='当前PE %.1f' % snap['pe_ttm_deduct'], secondary_y=False)
    fig.update_layout(title='估值序列：季报发布日后次月月末收盘锚定', template='plotly_white', height=420, margin=dict(l=40, r=50, t=50, b=30), legend=dict(orientation='h', y=1.08), hovermode='x unified')
    fig.update_yaxes(title_text='PE', secondary_y=False)
    fig.update_yaxes(title_text='PB / 股息率%', secondary_y=True)
    return fig


def _fmt(v, nd=2, suffix=''):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return '-'
    return (('%.' + str(nd) + 'f') % v) + suffix


def render_html(*, name, code, daily, fundamentals, valuation, snap, out_path):
    pe_pct = percentile(valuation['pe_ttm_deduct'], snap.get('pe_ttm_deduct'))
    pb_pct = percentile(valuation['pb'], snap.get('pb'))
    div_pct = percentile(valuation['div_yield_pct'], snap.get('div_yield_pct'))
    k_html = plot_offline(_kline_figure(daily, '%s(%s) 行情K线' % (name, code)), output_type='div', include_plotlyjs=False)
    f_html = plot_offline(_fundamental_figure(fundamentals), output_type='div', include_plotlyjs=False)
    v_html = plot_offline(_valuation_figure(valuation, snap), output_type='div', include_plotlyjs=False)
    asof = pd.Timestamp(snap['asof']).strftime('%Y-%m-%d')
    html = TEMPLATE
    reps = {
        '__NAME__': name, '__CODE__': code, '__ASOF__': asof,
        '__PRICE__': _fmt(snap['price']),
        '__PE__': _fmt(snap.get('pe_ttm_deduct'), 1),
        '__PE_PCT__': _fmt(pe_pct, 1, '%'),
        '__PB__': _fmt(snap.get('pb'), 2),
        '__PB_PCT__': _fmt(pb_pct, 1, '%'),
        '__DIV__': _fmt(snap.get('div_yield_pct'), 2, '%'),
        '__DIV_PCT__': _fmt(div_pct, 1, '%'),
        '__K__': k_html, '__F__': f_html, '__V__': v_html,
    }
    for k, v in reps.items():
        html = html.replace(k, v)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding='utf-8')
    return out_path

