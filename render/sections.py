"""종목별 탭 패널 렌더 — v2.11 디자인 충실 재현"""

from __future__ import annotations

import html
from typing import Any, Dict, List


def esc(v) -> str:
    return html.escape(str(v if v is not None else ""))


def _num(v, suffix=""):
    return f"{v}{suffix}" if v is not None else "—"


def _i(v, default=0):
    try:
        return int(round(float(v)))
    except (TypeError, ValueError):
        return default


def _score_color(s) -> str:
    try:
        s = float(s)
    except (TypeError, ValueError):
        return "var(--text-muted)"
    return "var(--color-bull)" if s >= 70 else "var(--color-warning)" if s >= 50 else "var(--color-bear)"


_DIR = {"bull": "var(--color-bull)", "warn": "var(--color-warning)", "bear": "var(--color-bear)"}
_DIRRGBA = {"bull": "rgba(74,222,128,0.2)", "warn": "rgba(107,114,128,0.2)", "bear": "rgba(248,113,113,0.2)"}
_DIRTEXT = {"bull": "var(--color-bull)", "warn": "var(--text-quaternary)", "bear": "var(--color-bear)"}


def _dir_color(d) -> str:
    return _DIR.get(d, "var(--text-muted)")


def _sparkline(series: List[float], w=80, h=44) -> str:
    s = [x for x in (series or []) if x is not None]
    if len(s) < 2:
        return ""
    lo, hi = min(s), max(s)
    rng = (hi - lo) or 1
    pts = " ".join(f"{i/(len(s)-1)*w:.1f},{h-(v-lo)/rng*(h-4)-2:.1f}" for i, v in enumerate(s))
    col = "#4ADE80" if s[-1] >= s[0] else "#F87171"
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">'
            f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="1.5" '
            f'stroke-linejoin="round" stroke-linecap="round"/></svg>')


def _section_title(num, name, sub="") -> str:
    sub_html = f'<span class="section-sub">{esc(sub)}</span>' if sub else ""
    style = ' style="background:linear-gradient(135deg,#B45309,#F59E0B);"' if str(num) == "11" else ""
    return (f'<div class="section-title"><div class="section-num"{style}>{esc(num)}</div>'
            f'<div class="section-name">{esc(name)}</div>{sub_html}</div>')


def _row(label, value_html) -> str:
    return f'<div class="row"><span class="row-label">{esc(label)}</span>{value_html}</div>'


def _val(text, cls="") -> str:
    return f'<span class="row-val {cls}" style="font-size:12px;">{esc(text)}</span>'


def _tag(text, kind="warn") -> str:
    return f'<span class="tag tag-{kind}">{esc(text)}</span>'


def _tagval(field, fallback="warn") -> str:
    """문자열이면 평문 row-val, {text,dir}면 컬러 태그로 렌더 (v2.11식)."""
    if isinstance(field, dict):
        t = field.get("text") or field.get("val") or ""
        return _tag(t, field.get("dir") or fallback) if t else _val("")
    return _val(field)


# ── 120분봉 RSI 시그널 + 차트 (ef-*) ─────────────────────────────────────
def _rsi_signal(series):
    """120분봉 RSI 시계열에서 '30/70 터치 + 방향 전환'을 핵심 시그널로 판정.

    반환: (라벨, 색상, 강조여부)
    """
    s = [x for x in (series or []) if x is not None]
    if len(s) < 3:
        return ("데이터 부족", "var(--text-muted)", False)
    cur, prv = s[-1], s[-2]
    win = s[-6:]                      # 최근 6봉(≈12시간)
    mn, mx = min(win), max(win)
    rising = cur > prv
    GREEN, RED, YEL, GRAY = "var(--color-bull)", "var(--color-bear)", "var(--color-warning)", "var(--text-muted)"
    # 70 터치 후 하락 전환 → 매도 시그널
    if mx >= 70 and cur < 70 and not rising:
        return ("과열 후 하락 — 매도 시그널", RED, True)
    # 30 터치 후 반등 → 매수 시그널
    if mn <= 30 and cur > 30 and rising:
        return ("과매도 후 반등 — 매수 시그널", GREEN, True)
    if cur >= 70:
        return ("과매수권 — 조정 임박", RED, False)
    if cur <= 30:
        return ("과매도권 — 반등 대기", GREEN, False)
    if cur >= 60 and rising:
        return ("과매수 접근 중", YEL, False)
    if cur <= 40 and not rising:
        return ("과매도 접근 중", YEL, False)
    return ("상승 진행" if rising else "하락 진행", GREEN if rising else GRAY, False)


def _rsi_chart_svg(series) -> str:
    """최근 20봉(120분) RSI 라인차트 — 30/50/70 기준선 + 터치 지점 마커."""
    s = [x for x in (series or []) if x is not None][-20:]
    if len(s) < 2:
        return '<div style="font-size:11px;color:var(--text-muted);padding:8px 0;">RSI 데이터 부족</div>'
    W, H, L, R, T, B = 600, 200, 34, 594, 14, 172
    n = len(s)
    X = lambda i: L + (R - L) * i / (n - 1)
    Y = lambda v: B - (B - T) * max(0, min(100, v)) / 100
    # 과열/과매도 영역
    zones = (f'<rect x="{L}" y="{Y(100):.1f}" width="{R-L}" height="{Y(70)-Y(100):.1f}" fill="#F87171" opacity="0.07"/>'
             f'<rect x="{L}" y="{Y(30):.1f}" width="{R-L}" height="{Y(0)-Y(30):.1f}" fill="#4ADE80" opacity="0.07"/>')
    grid = ""
    for lvl, col in [(70, "#F87171"), (50, "#6B7280"), (30, "#4ADE80")]:
        y = Y(lvl)
        grid += (f'<line x1="{L}" y1="{y:.1f}" x2="{R}" y2="{y:.1f}" stroke="{col}" stroke-width="1" stroke-dasharray="3 3" opacity="0.5"/>'
                 f'<text x="{L-4}" y="{y+3:.1f}" fill="{col}" font-size="9" text-anchor="end">{lvl}</text>')
    poly = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(s))
    marks = ""
    for i, v in enumerate(s):
        if v <= 30 or v >= 70:   # 터치 지점 강조
            c = "#4ADE80" if v <= 30 else "#F87171"
            marks += f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="2.6" fill="{c}"/>'
    cv = s[-1]
    cc = "#F87171" if cv >= 70 else "#4ADE80" if cv <= 30 else "#A78BFA"
    cur = (f'<circle cx="{X(n-1):.1f}" cy="{Y(cv):.1f}" r="4" fill="{cc}" stroke="#000" stroke-width="1"/>'
           f'<text x="{X(n-1):.1f}" y="{Y(cv)-7:.1f}" fill="{cc}" font-size="11" font-weight="700" text-anchor="end">{cv}</text>')
    # height:auto SVG가 모바일/인앱 브라우저에서 높이 0으로 접히는 문제 방지 →
    # padding-bottom 비율 래퍼로 높이를 항상 확보 (모든 브라우저 호환)
    svg = (f'<svg viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet" '
           f'style="position:absolute;top:0;left:0;width:100%;height:100%;display:block;" xmlns="http://www.w3.org/2000/svg">'
           f'{zones}{grid}<polyline points="{poly}" fill="none" stroke="#A78BFA" stroke-width="1.8" stroke-linejoin="round"/>{marks}{cur}</svg>')
    return (f'<div style="position:relative;width:100%;padding-bottom:{H/W*100:.1f}%;height:0;margin:6px 0 2px;">{svg}</div>')


def _entry_forecast(tk, intra, et) -> str:
    series = intra.get("rsi_series") or []
    cur = intra.get("rsi")
    label, color, hot = _rsi_signal(series)
    win = et.get("window", {}) or {}

    window_html = ""
    if win.get("date") or win.get("price"):
        window_html = f'''
      <div class="ef-window">
        <div><div class="ef-window-label">대응 시나리오</div><div class="ef-window-date">{esc(win.get("date",""))}</div></div>
        <div class="ef-window-divider"></div>
        <div><div class="ef-window-label">관심 가격대</div><div class="ef-window-price" style="color:var(--accent-blue);">{esc(win.get("price",""))}</div></div>
        <div class="ef-window-divider"></div>
        <div class="ef-window-note">{esc(win.get("note",""))}</div>
      </div>'''

    return f'''
    <div class="entry-forecast">
      <div class="ef-header">
        <span class="ef-icon">📈</span>
        <span class="ef-title" style="color:var(--color-warning);">120분봉 RSI 시그널 — {esc(tk)}</span>
        <span class="ef-phase" style="background:{color}22;color:{color};border:1px solid {color}55;">{esc(label)}</span>
      </div>
      {_rsi_chart_svg(series)}
      <div style="font-size:10px;color:var(--text-muted);text-align:right;margin-bottom:8px;">
        최근 20봉 · 프리장·정규장·애프터장 포함 · 현재 RSI {_num(cur)}
        &nbsp;|&nbsp; 🟢30 터치·반등=매수 / 🔴70 터치·하락=매도
      </div>{window_html}
    </div>'''


# ── 메인 ──────────────────────────────────────────────────────────────────
def render_panel(meta: Dict[str, Any], market: Dict[str, Any],
                 a: Dict[str, Any], active: bool) -> str:
    tk = meta["ticker"]
    is_etf = meta.get("type") == "etf_leveraged"
    d = market.get("daily", {}) or {}
    intra = market.get("intraday_120m", {}) or {}
    price = market.get("price", {}) or {}
    info = market.get("info", {}) or {}
    an = market.get("analyst", {}) or {}
    opt = market.get("options", {}) or {}
    hm = a.get("headline_metrics", {})
    last = price.get("last") or d.get("last")
    chg = price.get("chg_pct")
    chg_cls = "price-bar-change-pos" if (chg or 0) >= 0 else "price-bar-change-neg"
    arrow = "▲" if (chg or 0) >= 0 else "▼"
    sign = "+" if (chg or 0) >= 0 else ""

    P: List[str] = [f'<div class="tab-panel{" active" if active else ""}" id="panel-{tk.lower()}">']

    # 가격 바
    P.append(f'''
    <div class="price-bar">
      <div class="price-bar-candles">{_sparkline(market.get("series_daily"))}</div>
      <div class="price-bar-info">
        <div class="price-bar-ticker">{esc(tk)} · {esc(meta.get("name",""))} · {esc(meta.get("sector") or meta.get("underlying",""))}</div>
        <div class="price-bar-main">
          <span class="price-bar-close">${_num(last)}</span>
          <span class="{chg_cls}">{arrow} {sign}{_num(chg)}%</span>
        </div>
        <div class="price-bar-sub">52주 ${_num(info.get("low_52w"))} ~ ${_num(info.get("high_52w"))} · 시총 {_fmt_cap(info.get("market_cap"))}</div>
      </div>
    </div>''')

    # 진입 예상 타임라인
    P.append(_entry_forecast(tk, intra, a.get("entry_timeline", {})))

    # 최종 결론
    cc = a.get("conclusion", {})
    P.append(f'''
    <div class="conclusion-box" style="margin-bottom:16px;">
      <div class="conclusion-eyebrow">최종 결론</div>
      <div class="conclusion-text">{esc(cc.get("text",""))}<br><span class="hl">{esc(cc.get("highlight",""))}</span></div>
      <div class="conclusion-note">본 분석은 참고용이며 투자 권유가 아닙니다. 투자 판단과 책임은 본인에게 있습니다.</div>
    </div>''')

    # 메트릭 그리드 (8칸)
    P.append(_metric_grid(d, intra, an, opt, hm, a, market, is_etf, meta))

    # ① 일봉
    dd = a.get("daily", {})
    P.append(_section_title(1, "기술적 분석 · 일봉"))
    P.append(f'''<div class="card">
      {_row("단기 이평 (5·20일)", _tagval(dd.get("ma_short")))}
      {_row("중기 이평 (100일)", _tagval(dd.get("ma_mid")))}
      {_row("장기 이평 (200일)", _tagval(dd.get("ma_long")))}
      {_row("RSI (일봉)", f'<span style="display:flex;gap:8px;align-items:center;"><span class="row-val">{_num(d.get("rsi"))}</span>{_tagval(dd.get("rsi"))}</span>')}
      {_row("MACD (일봉)", f'<span style="display:flex;gap:8px;align-items:center;"><span class="row-val">{_num(d.get("macd"))}</span>{_tagval(dd.get("macd"))}</span>')}
      {_row("볼린저밴드", _tagval(dd.get("bollinger")))}
      {_row("핵심 저항/지지", _tagval(dd.get("resistance")))}
      {_row("20일선 대비", _val(f'{_num(d.get("vs_sma20_pct"))}%'))}
    </div>''')

    # ② 120분봉
    ia = a.get("intraday", {})
    ir = ia.get("rows", {})
    cr = ia.get("criteria", {})
    cb = ia.get("combined", {})
    P.append(_section_title(2, "기술적 분석 · 120분봉", "단기 트레이딩 핵심 타임프레임"))
    if ia.get("info"):
        P.append(f'<div class="info-box">{esc(ia["info"])}</div>')
    ind_html = ""
    for label, key in [("이동평균선", "ma"), ("RSI", "rsi"), ("스토캐스틱", "stoch"),
                       ("볼린저밴드", "bollinger"), ("거래량", "volume"), ("MACD", "macd")]:
        cell = ir.get(key, {})
        if isinstance(cell, dict):
            val, dirc, sig = cell.get("val", ""), cell.get("dir", "warn"), cell.get("sig", "")
        else:
            val, dirc, sig = cell, "warn", ""
        ind_html += (f'<div class="ind-card"><div class="ind-name">{esc(label)}</div>'
                     f'<div class="ind-val" style="color:{_dir_color(dirc)};">{esc(val)}</div>'
                     f'<div class="ind-sig">{esc(sig)}</div></div>')
    P.append(f'<div class="ind-grid">{ind_html}</div>')
    P.append(f'''<div class="card"><div class="card-title">120분봉 진입 타이밍 기준</div>
      {_row("RSI 진입", _val(cr.get("rsi","")))}
      {_row("스토캐스틱", _val(cr.get("stoch","")))}
      {_row("볼린저밴드", _val(cr.get("bollinger","")))}
      {_row("MACD", _val(cr.get("macd","")))}
      {_row("예상 진입 타이밍", _tag(cr.get("entry","") or "—", "orange"))}
    </div>''')
    P.append(f'''<div class="summary-box"><div class="summary-label">일봉 + 120분봉 통합 판단</div>
      <div class="grid2" style="gap:8px;">
        <div style="background:var(--bg-card);border:1px solid var(--border-primary);border-radius:var(--radius-md);padding:12px;">
          <div style="font-size:10px;color:var(--text-muted);margin-bottom:4px;">일봉</div>
          <div style="font-size:13px;color:var(--color-bull);">{esc(cb.get("daily",""))}</div></div>
        <div style="background:var(--bg-card);border:1px solid var(--border-primary);border-radius:var(--radius-md);padding:12px;">
          <div style="font-size:10px;color:var(--text-muted);margin-bottom:4px;">120분봉</div>
          <div style="font-size:13px;color:var(--color-bear);">{esc(cb.get("intraday",""))}</div></div>
      </div>
      <div class="summary-result">→ {esc(ia.get("summary",""))}</div></div>''')

    # ③ 호재/리스크
    P.append(_section_title(3, "기초지수 동인 / 구조 위험" if is_etf else "상승 이유 / 리스크"))
    def _cr(items, kind):
        rows = "".join(
            f'<div class="row"><span class="row-label">{esc(it.get("title",""))}'
            + (f'<br><span style="font-size:10px;color:var(--text-muted);">{esc(it.get("source",""))}</span>' if it.get("source") else "")
            + f'</span>{_tag(it.get("tag",""), kind)}</div>' for it in (items or []))
        return rows or '<div class="row"><span class="row-label" style="color:var(--text-muted);">근거 뉴스 없음</span></div>'
    P.append(f'''<div class="grid2">
      <div class="card"><div class="card-title" style="color:var(--color-bull);">{"상방 동인" if is_etf else "호재 카탈리스트"}</div>{_cr(a.get("catalysts"),"bull")}</div>
      <div class="card"><div class="card-title" style="color:var(--color-bear);">리스크 요인</div>{_cr(a.get("risks"),"bear")}</div>
    </div>''')
    if is_etf:
        etf = a.get("etf", {})
        P.append(f'''<div class="card" style="border-top:3px solid var(--color-warning);margin-top:10px;">
          <div class="card-title" style="color:var(--color-warning);">⚠ 레버리지 ETF 주의</div>
          {_row("기초지수 방향", _val(etf.get("underlying_view","")))}
          {_row("레버리지 소실(decay)", _val(etf.get("decay_warning","")))}
          {_row("변동성", _val(etf.get("volatility","")))}
          {_row("권장 보유기간", _val(etf.get("hold_period","")))}</div>''')

    # ④ 파동/시나리오
    P.append(_section_title(4, "엘리어트 파동 / 시나리오"))
    waves = (a.get("waves", []) or [])[:5]
    if waves:
        ws = "".join(f'<div class="wave-seg{" current" if w.get("current") else ""}">'
                     f'<div class="wave-num"{" style=color:var(--accent-purple);" if w.get("current") else ""}>{esc(w.get("num",""))}</div>'
                     f'<div class="wave-range">{esc(w.get("range",""))}</div>'
                     f'<div class="wave-desc">{esc(w.get("desc",""))}</div></div>' for w in waves)
        P.append(f'<div class="wave-row" style="grid-template-columns:repeat({len(waves)},1fr);">{ws}</div>')
    sc = "".join(f'<div class="scenario-row"><span class="scenario-label">{esc(s.get("label",""))}</span>'
                 f'<span class="scenario-pct {s.get("dir","")}">{_i(s.get("pct"))}%</span>'
                 f'<div class="scenario-bar"><div class="scenario-fill" style="width:{_i(s.get("pct"))}%;background:{_dir_color(s.get("dir"))};"></div></div></div>'
                 for s in a.get("scenarios", []))
    if sc:
        P.append(f'<div class="card"><div class="card-title">향후 시나리오</div>{sc}</div>')

    # ⑤ 전략
    P.append(_section_title(5, "트레이딩 전략"))
    st = a.get("strategy", {})
    def _tr(items):
        return "".join(f'<div class="trade-row"><span class="trade-label">{esc(i.get("label",""))}</span>'
                       f'<span class="trade-val">{esc(i.get("price",""))}</span></div>' for i in (items or []))
    P.append(f'''<div class="trade-grid">
      <div class="trade-card"><div class="trade-card-title bull">▲ 매수 트리거</div>{_tr(st.get("buy"))}</div>
      <div class="trade-card"><div class="trade-card-title bear">▼ 매도 / 손절</div>{_tr(st.get("sell"))}</div></div>''')

    # ⑥ 점수
    P.append(_section_title(6, "AI 종합 점수"))
    scr = a.get("scores", {})
    items = [("기술적 분석 (일봉)", scr.get("technical_daily")), ("기술적 분석 (120분봉)", scr.get("technical_intraday")),
             ("수급", scr.get("supply")), ("기초지수 추세" if is_etf else "실적 / 펀더멘털", scr.get("fundamental")),
             ("성장성", scr.get("growth"))]
    sr = "".join(f'<div class="score-row"><span class="score-label">{esc(n)}</span>'
                 f'<div class="score-bg"><div class="score-fill" style="width:{_i(v)}%;background:{_score_color(v)};"></div></div>'
                 f'<span class="score-num">{_i(v)}</span></div>' for n, v in items)
    P.append(f'<div class="card">{sr}<div class="score-total"><span class="score-total-label">종합 점수</span>'
             f'<span class="score-total-val" style="color:{_score_color(scr.get("total"))};">{_i(scr.get("total"))}점</span></div></div>')

    # ⑦ 손익
    sim = a.get("simulation", {})
    P.append(_section_title(7, "손익 시뮬레이션"))
    cells = [("목표가", sim.get("target"), sim.get("target_pct"), "bull"), ("손절가", sim.get("stop"), sim.get("stop_pct"), "bear"),
             ("손익비", sim.get("rr"), "", "warn"), ("권장 비중", sim.get("weight"), "", "")]
    P.append('<div class="sim-grid">' + "".join(
        f'<div class="sim-card"><div class="sim-label">{esc(l)}</div><div class="sim-val {c}">{esc(v or "—")}</div>'
        f'<div class="sim-sub {c}">{esc(s)}</div></div>' for l, v, s, c in cells) + '</div>')

    # ⑧ 확률
    prob = a.get("probability", [])
    if prob:
        P.append(_section_title(8, "확률 분포"))
        segs = "".join(f'<div class="prob-seg" style="width:{_i(p.get("pct"))}%;background:{_DIRRGBA.get(p.get("dir"),"rgba(107,114,128,0.2)")};color:{_DIRTEXT.get(p.get("dir"),"var(--text-quaternary)")};">{esc(p.get("label",""))} {_i(p.get("pct"))}%</div>' for p in prob)
        leg = "".join(f'<div class="prob-legend-item"><div class="prob-dot" style="background:{_dir_color(p.get("dir"))};"></div>{esc(p.get("label",""))} {_i(p.get("pct"))}%</div>' for p in prob)
        P.append(f'<div class="card"><div class="prob-bar">{segs}</div><div class="prob-legend">{leg}</div></div>')

    # ⑨ 투자자별
    P.append(_section_title(9, "투자자별 전략"))
    inv = a.get("investor", [])
    if isinstance(inv, dict):  # 구버전 호환
        inv = [{"type": "공격형", "verdict": "", "verdict_dir": "bull", "detail": inv.get("aggressive", "")},
               {"type": "중립형", "verdict": "", "verdict_dir": "warn", "detail": inv.get("neutral", "")},
               {"type": "보수형", "verdict": "", "verdict_dir": "bear", "detail": inv.get("conservative", "")}]
    ic = "".join(f'<div class="inv-card"><div class="inv-type">{esc(i.get("type",""))}</div>'
                 f'<div class="inv-verdict {i.get("verdict_dir","warn")}">{esc(i.get("verdict",""))}</div>'
                 f'<div class="inv-detail">{esc(i.get("detail",""))}</div></div>' for i in (inv or [])[:3])
    P.append(f'<div class="inv-grid">{ic}</div>')

    # ⑩ 심리/애널리스트
    P.append(_section_title(10, "시장 심리 / 애널리스트"))
    P.append(_sentiment_section(a, an, market, last, is_etf))

    # 신뢰도
    rel = a.get("reliability", {})
    stars = _i(rel.get("stars", 3), 3)
    star_html = "".join(
        '<div class="rel-star" style="background:var(--color-bull);"></div>' if i < stars
        else '<div class="rel-star" style="background:var(--bg-elevated);border:1px solid var(--border-primary);"></div>'
        for i in range(5))
    P.append(f'''<div class="card" style="display:flex;align-items:center;justify-content:space-between;gap:16px;margin-top:8px;">
      <div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">데이터 신뢰도</div>
      <div style="font-size:13px;color:var(--text-quaternary);">{esc(rel.get("note",""))}</div></div>
      <div class="rel-stars">{star_html}</div></div>''')

    # ⑪ PCR
    P.append(_pcr_section(opt, a))

    P.append('</div>')
    return "".join(P)


def _fmt_cap(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return "—"
    if v >= 1e12:
        return f"${v/1e12:.1f}T"
    if v >= 1e9:
        return f"${v/1e9:.1f}B"
    if v >= 1e6:
        return f"${v/1e6:.0f}M"
    return f"${v:.0f}"


def _rec_dir(rec) -> str:
    r = (rec or "").lower()
    if "strong_buy" in r or "buy" in r:
        return "bull"
    if "sell" in r or "underperform" in r:
        return "bear"
    return "warn"


def _metric_grid(d, intra, an, opt, hm, a, market, is_etf, meta) -> str:
    scr = a.get("scores", {})
    total = _i(scr.get("total"))
    score_dir = hm.get("score_dir") or ("bull" if total >= 70 else "warn" if total >= 50 else "bear")
    # (label, val, sub, val_dir, sub_dir)
    cards = [
        ("RSI · 일봉", _num(d.get("rsi")), hm.get("rsi_daily_label", ""), hm.get("rsi_daily_dir", "warn"), hm.get("rsi_daily_dir", "warn")),
        ("RSI · 120분봉", _num(intra.get("rsi")), hm.get("rsi_intraday_label", ""), hm.get("rsi_intraday_dir", "warn"), hm.get("rsi_intraday_dir", "warn")),
        ("AI 종합 점수", f'{total}점', hm.get("score_note", "AI 산출"), score_dir, score_dir),
        ("MACD · 일봉", _num(d.get("macd")), hm.get("macd_daily_label", ""), hm.get("macd_daily_dir", "warn"), hm.get("macd_daily_dir", "warn")),
        ("예상 진입", hm.get("entry_zone", "—"), "AI 추정", "blue", "muted"),
        ("예상 매도", hm.get("exit_zone", "—"), "AI 추정", "purple", "muted"),
    ]
    if is_etf:
        cards += [("레버리지", f'{meta.get("leverage","3")}X', "일일 리밸런싱", "warn", "warn"),
                  ("베타", _num((market.get("info") or {}).get("beta")), "변동성", "", "muted")]
    else:
        cards += [("다음 어닝", market.get("earnings_date", "—"), "최대 변수", "orange", "warn"),
                  ("애널 목표가", f'${_num(an.get("target_mean"))}', esc(an.get("recommendation") or ""),
                   _rec_dir(an.get("recommendation")), _rec_dir(an.get("recommendation")))]

    _C = {"bull": "var(--color-bull)", "bear": "var(--color-bear)", "warn": "var(--color-warning)",
          "orange": "var(--color-orange)", "blue": "var(--accent-blue)", "purple": "var(--accent-purple)",
          "muted": "var(--text-muted)", "": "var(--text-primary)"}
    out = ""
    for l, v, s, vd, sd in cards:
        vc = _C.get(vd, "var(--text-primary)")
        sc = _C.get(sd, "var(--text-muted)")
        out += (f'<div class="metric-card"><div class="lbl">{esc(l)}</div>'
                f'<div class="val" style="color:{vc};">{esc(v)}</div>'
                f'<div class="sub" style="color:{sc};">{esc(s)}</div></div>')
    return f'<div class="metric-grid" style="margin-top:4px;">{out}</div>'


def _sentiment_section(a, an, market, last, is_etf) -> str:
    sd = a.get("sentiment_detail", {})
    rows = []
    # ① 소매 심리
    rows.append(f'<div class="row"><span class="row-label">① 소매 심리</span>{_tag(sd.get("retail","—"), sd.get("retail_dir","warn"))}</div>')
    n = 2
    if not is_etf:
        b, h, s = an.get("buy"), an.get("hold"), an.get("sell")
        if b is not None or h is not None or s is not None:
            b, h, s = b or 0, h or 0, s or 0
            tot = (b + h + s) or 1
            rows.append(f'''<div class="row"><span class="row-label">② 애널리스트 ({an.get("num_analysts") or tot}명)</span>
              <span style="display:flex;gap:6px;align-items:center;">{_tag(f"Buy {b}","bull")}{_tag(f"Hold {h}","warn")}{_tag(f"Sell {s}","bear")}</span></div>
              <div style="padding:2px 0 6px;"><div class="analyst-bar">
                <div style="width:{b/tot*100:.0f}%;background:var(--color-bull);height:100%;border-radius:3px 0 0 3px;"></div>
                <div style="width:{h/tot*100:.0f}%;background:var(--color-warning);height:100%;"></div>
                <div style="width:{s/tot*100:.0f}%;background:var(--color-bear);height:100%;border-radius:0 3px 3px 0;"></div></div></div>''')
            n = 3
        tgt = an.get("target_mean")
        vs = ""
        if tgt and last:
            pct = (tgt / last - 1) * 100
            vs = f'<span style="font-size:11px;color:var(--text-muted);font-weight:400;">현재가 대비 {"+" if pct>=0 else ""}{pct:.1f}%</span>'
        rows.append(f'<div class="row"><span class="row-label">{_circ(n)} 컨센서스 목표가</span><span class="row-val">${_num(tgt)} {vs}</span></div>')
        n += 1
    # 내부자
    rows.append(f'<div class="row"><span class="row-label">{_circ(n)} 내부자 동향</span><span style="font-size:12px;color:var(--text-quaternary);">{esc(sd.get("insider","—"))}</span></div>')
    n += 1
    if not is_etf and market.get("earnings_date"):
        rows.append(f'<div class="row"><span class="row-label">{_circ(n)} 다음 어닝</span>{_tag(market.get("earnings_date")+" ★","orange")}</div>')
        n += 1
    rows.append(f'<div class="row"><span class="row-label">{_circ(n)} 심리 요약</span><span style="font-size:12px;color:var(--text-quaternary);">{esc(sd.get("summary","—"))}</span></div>')
    n += 1
    rows.append(f'<div class="row"><span class="row-label">{_circ(n)} 주요 이슈 데드라인</span><span style="font-size:12px;color:var(--text-quaternary);">{esc(sd.get("deadline","—"))}</span></div>')
    return f'<div class="card">{"".join(rows)}</div>'


def _circ(n) -> str:
    return "①②③④⑤⑥⑦⑧⑨"[n - 1] if 1 <= n <= 9 else str(n)


# ── PCR 섹션 11 ────────────────────────────────────────────────────────────
def _pcr_color(pcr) -> str:
    try:
        pcr = float(pcr)
    except (TypeError, ValueError):
        return "var(--text-muted)"
    return "var(--color-bull)" if pcr < 0.8 else "var(--color-warning)" if pcr <= 1.2 else "var(--color-bear)"


def _pcr_interp(pcr) -> str:
    try:
        pcr = float(pcr)
    except (TypeError, ValueError):
        return "데이터 부족"
    if pcr >= 1.3:
        return "풋 우세 — 하방 헤지 집중"
    if pcr >= 1.0:
        return "풋 소폭 우세 — 중립~약세"
    if pcr >= 0.7:
        return "균형 — 중립 심리"
    return "콜 우세 — 상방 베팅"


def _pcr_section(opt: Dict[str, Any], a: Dict[str, Any]) -> str:
    pcr = opt.get("pcr")
    gauge = opt.get("gauge_pct", 50)
    cd, pd = opt.get("call_dollar") or 0, opt.get("put_dollar") or 0
    col = _pcr_color(pcr)

    def _usd(v):
        return f"${v/1e6:.1f}M" if v >= 1e6 else f"${v/1e3:.0f}K" if v >= 1e3 else f"${v:.0f}"

    flow = ""
    if cd >= pd and pd > 0:
        flow = f"→ 기관 콜 우세 (콜 {cd/pd:.1f}배)"
    elif pd > cd and cd > 0:
        flow = f"→ 기관 풋 우세 (풋 {pd/cd:.1f}배)"
    c_pct = round(cd / (cd + pd) * 100) if (cd + pd) else 50

    overall = f'''
    <div class="card" style="border-top:3px solid #F59E0B;margin-bottom:12px;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;flex-wrap:wrap;gap:12px;">
        <div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">전체 OI 기준 PCR</div>
          <div style="font-size:32px;font-weight:900;color:{col};">{_num(pcr)}</div>
          <div style="font-size:11px;color:var(--text-muted);">{esc(_pcr_interp(pcr))}</div></div>
        <div style="text-align:right;"><div style="font-size:10px;color:var(--text-muted);margin-bottom:6px;">기관 옵션 플로우 (추산)</div>
          <div style="display:flex;flex-direction:column;gap:4px;align-items:flex-end;">
            <div style="display:flex;align-items:center;gap:8px;"><span style="font-size:11px;color:var(--color-bear);">Put</span>
              <div style="width:80px;height:10px;background:var(--bg-elevated);border-radius:3px;overflow:hidden;"><div style="width:{100-c_pct}%;height:100%;background:var(--color-bear);opacity:0.8;"></div></div>
              <span style="font-size:11px;font-weight:700;color:var(--color-bear);">{_usd(pd)}</span></div>
            <div style="display:flex;align-items:center;gap:8px;"><span style="font-size:11px;color:var(--color-bull);">Call</span>
              <div style="width:80px;height:10px;background:var(--bg-elevated);border-radius:3px;overflow:hidden;"><div style="width:{c_pct}%;height:100%;background:var(--color-bull);opacity:0.8;"></div></div>
              <span style="font-size:11px;font-weight:700;color:var(--color-bull);">{_usd(cd)}</span></div>
            <div style="font-size:10px;color:var(--color-bull);font-weight:700;margin-top:2px;">{esc(flow)}</div></div></div>
      </div>
      <div style="font-size:10px;color:var(--text-muted);margin-bottom:6px;text-transform:uppercase;letter-spacing:0.5px;">PCR 심리 게이지</div>
      <div style="position:relative;height:20px;background:linear-gradient(90deg,#4ADE80,#FBBF24,#F87171);border-radius:10px;margin-bottom:4px;">
        <div style="position:absolute;left:{gauge}%;top:-4px;width:4px;height:28px;background:white;border-radius:2px;box-shadow:0 0 6px rgba(0,0,0,0.5);"></div></div>
      <div style="display:flex;justify-content:space-between;margin-top:8px;">
        <span style="font-size:10px;color:var(--color-bull);">극단 강세 (0.5↓)</span>
        <span style="font-size:10px;color:var(--color-warning);">중립 (1.0)</span>
        <span style="font-size:10px;color:var(--color-bear);">극단 약세 (2.0↑)</span></div>
    </div>'''

    cards = ""
    labels = ["1차 만기", "2차 만기", "3차 만기", "4차 만기"]
    for i, ex in enumerate(opt.get("per_exp", [])[:4]):
        ec = _pcr_color(ex.get("pcr"))
        pp, cp = ex.get("put_pct") or 50, ex.get("call_pct") or 50
        cards += f'''
      <div class="card" style="border-top:3px solid {ec};">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
          <div><div style="font-size:9px;color:var(--text-muted);text-transform:uppercase;">{esc(labels[i] if i<len(labels) else "만기")}</div>
            <div style="font-size:13px;font-weight:800;">{esc(ex.get("exp",""))}</div></div>
          <div style="text-align:right;"><div style="font-size:9px;color:var(--text-muted);">PCR</div>
            <div style="font-size:20px;font-weight:900;color:{ec};">{_num(ex.get("pcr"))}</div></div></div>
        <div style="margin-bottom:8px;">
          <div style="display:flex;align-items:center;gap:5px;margin-bottom:3px;"><span style="font-size:10px;color:var(--text-muted);width:40px;">Put</span>
            <div style="flex:1;height:8px;background:var(--bg-elevated);border-radius:3px;overflow:hidden;"><div style="width:{pp}%;height:100%;background:var(--color-bear);opacity:0.7;"></div></div></div>
          <div style="display:flex;align-items:center;gap:5px;"><span style="font-size:10px;color:var(--text-muted);width:40px;">Call</span>
            <div style="flex:1;height:8px;background:var(--bg-elevated);border-radius:3px;overflow:hidden;"><div style="width:{cp}%;height:100%;background:var(--color-bull);opacity:0.7;"></div></div></div></div>
        {_row("Put Wall", _tag(f'${_num(ex.get("put_wall"))}', "bear"))}
        {_row("Call Wall", _tag(f'${_num(ex.get("call_wall"))}', "bull"))}
        <div class="row" style="border:none;"><span class="row-label">해석</span><span style="font-size:11px;color:var(--text-muted);">{esc(_pcr_interp(ex.get("pcr")))}</span></div>
      </div>'''
    grid = f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px;">{cards}</div>' if cards else ""

    cm = a.get("pcr_comment", "")
    cm_html = (f'<div class="card" style="background:rgba(251,191,36,0.04);border-color:rgba(251,191,36,0.3);">'
               f'<div style="font-size:10px;color:var(--color-warning);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px;">PCR 종합 해석</div>'
               f'<div style="font-size:12px;color:var(--text-tertiary);">{esc(cm)}</div></div>') if cm else ""
    return _section_title(11, "풋/콜 비율 (Put/Call Ratio)", "옵션 OI 기준") + overall + grid + cm_html
