"""종목별 탭 패널 렌더 — 첨부 디자인의 클래스에 정확히 매핑"""

from __future__ import annotations

import html
from typing import Any, Dict, List


def esc(v) -> str:
    return html.escape(str(v if v is not None else ""))


def _num(v, suffix=""):
    return f"{v}{suffix}" if v is not None else "—"


def _score_color(s) -> str:
    try:
        s = float(s)
    except (TypeError, ValueError):
        return "var(--text-muted)"
    return "var(--color-bull)" if s >= 70 else "var(--color-warning)" if s >= 50 else "var(--color-bear)"


_DIR = {"bull": "var(--color-bull)", "warn": "var(--color-warning)", "bear": "var(--color-bear)"}


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
    """v2.11식 풋/콜 비율 섹션 (전체 PCR + 심리 게이지 + 플로우 + 만기별 Wall 카드)."""
    pcr = opt.get("pcr")
    gauge = opt.get("gauge_pct", 50)
    cd, pd = opt.get("call_dollar") or 0, opt.get("put_dollar") or 0
    col = _pcr_color(pcr)

    def _usd(v):
        if v >= 1e6:
            return f"${v/1e6:.1f}M"
        if v >= 1e3:
            return f"${v/1e3:.0f}K"
        return f"${v:.0f}"

    flow_txt = ""
    if cd or pd:
        if cd >= pd and pd > 0:
            flow_txt = f"→ 기관 콜 우세 (콜 {cd/pd:.1f}배)"
        elif pd > cd and cd > 0:
            flow_txt = f"→ 기관 풋 우세 (풋 {pd/cd:.1f}배)"
    c_pct = round(cd / (cd + pd) * 100) if (cd + pd) else 50
    p_pct = 100 - c_pct

    overall = f'''
    <div class="card" style="border-top:3px solid #F59E0B;margin-bottom:12px;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;flex-wrap:wrap;gap:12px;">
        <div>
          <div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">전체 OI 기준 PCR</div>
          <div style="font-size:32px;font-weight:900;color:{col};">{_num(pcr)}</div>
          <div style="font-size:11px;color:var(--text-muted);">{esc(_pcr_interp(pcr))}</div>
        </div>
        <div style="text-align:right;">
          <div style="font-size:10px;color:var(--text-muted);margin-bottom:6px;">기관 옵션 플로우 (추산)</div>
          <div style="display:flex;flex-direction:column;gap:4px;align-items:flex-end;">
            <div style="display:flex;align-items:center;gap:8px;"><span style="font-size:11px;color:var(--color-bear);">Put</span>
              <div style="width:80px;height:10px;background:var(--bg-elevated);border-radius:3px;overflow:hidden;"><div style="width:{p_pct}%;height:100%;background:var(--color-bear);opacity:0.8;"></div></div>
              <span style="font-size:11px;font-weight:700;color:var(--color-bear);">{_usd(pd)}</span></div>
            <div style="display:flex;align-items:center;gap:8px;"><span style="font-size:11px;color:var(--color-bull);">Call</span>
              <div style="width:80px;height:10px;background:var(--bg-elevated);border-radius:3px;overflow:hidden;"><div style="width:{c_pct}%;height:100%;background:var(--color-bull);opacity:0.8;"></div></div>
              <span style="font-size:11px;font-weight:700;color:var(--color-bull);">{_usd(cd)}</span></div>
            <div style="font-size:10px;color:var(--color-bull);font-weight:700;margin-top:2px;">{esc(flow_txt)}</div>
          </div>
        </div>
      </div>
      <div style="font-size:10px;color:var(--text-muted);margin-bottom:6px;text-transform:uppercase;letter-spacing:0.5px;">PCR 심리 게이지</div>
      <div style="position:relative;height:20px;background:linear-gradient(90deg,#4ADE80,#FBBF24,#F87171);border-radius:10px;margin-bottom:4px;">
        <div style="position:absolute;left:{gauge}%;top:-4px;width:4px;height:28px;background:white;border-radius:2px;box-shadow:0 0 6px rgba(0,0,0,0.5);"></div>
      </div>
      <div style="display:flex;justify-content:space-between;margin-top:8px;">
        <span style="font-size:10px;color:var(--color-bull);">극단 강세 (0.5↓)</span>
        <span style="font-size:10px;color:var(--color-warning);">중립 (1.0)</span>
        <span style="font-size:10px;color:var(--color-bear);">극단 약세 (2.0↑)</span>
      </div>
    </div>'''

    # 만기별 카드
    cards = ""
    labels = ["1차 만기", "2차 만기", "3차 만기"]
    for i, ex in enumerate(opt.get("per_exp", [])[:3]):
        epcr = ex.get("pcr")
        ecol = _pcr_color(epcr)
        pp, cp = ex.get("put_pct") or 50, ex.get("call_pct") or 50
        cards += f'''
      <div class="card" style="border-top:3px solid {ecol};">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
          <div><div style="font-size:9px;color:var(--text-muted);text-transform:uppercase;">{esc(labels[i] if i < len(labels) else "만기")}</div>
            <div style="font-size:13px;font-weight:800;">{esc(ex.get("exp",""))}</div></div>
          <div style="text-align:right;"><div style="font-size:9px;color:var(--text-muted);">PCR</div>
            <div style="font-size:20px;font-weight:900;color:{ecol};">{_num(epcr)}</div></div>
        </div>
        <div style="margin-bottom:8px;">
          <div style="display:flex;align-items:center;gap:5px;margin-bottom:3px;"><span style="font-size:10px;color:var(--text-muted);width:40px;">Put</span>
            <div style="flex:1;height:8px;background:var(--bg-elevated);border-radius:3px;overflow:hidden;"><div style="width:{pp}%;height:100%;background:var(--color-bear);opacity:0.7;"></div></div></div>
          <div style="display:flex;align-items:center;gap:5px;"><span style="font-size:10px;color:var(--text-muted);width:40px;">Call</span>
            <div style="flex:1;height:8px;background:var(--bg-elevated);border-radius:3px;overflow:hidden;"><div style="width:{cp}%;height:100%;background:var(--color-bull);opacity:0.7;"></div></div></div>
        </div>
        {_row("Put Wall", f'<span class="tag tag-bear">${_num(ex.get("put_wall"))}</span>')}
        {_row("Call Wall", f'<span class="tag tag-bull">${_num(ex.get("call_wall"))}</span>')}
        <div class="row" style="border:none;"><span class="row-label">해석</span><span style="font-size:11px;color:var(--text-muted);">{esc(_pcr_interp(epcr))}</span></div>
      </div>'''

    comment = a.get("pcr_comment", "")
    comment_html = (f'<div class="card" style="background:rgba(251,191,36,0.04);border-color:rgba(251,191,36,0.3);">'
                    f'<div style="font-size:10px;color:var(--color-warning);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px;">PCR 종합 해석</div>'
                    f'<div style="font-size:12px;color:var(--text-tertiary);">{esc(comment)}</div></div>') if comment else ""

    grid = f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px;">{cards}</div>' if cards else ""
    return (_section_title(11, "풋/콜 비율 (Put/Call Ratio)", "옵션 OI 기준")
            + overall + grid + comment_html)


def _section_title(num, name, sub="") -> str:
    sub_html = f'<span class="section-sub">{esc(sub)}</span>' if sub else ""
    return (f'<div class="section-title"><div class="section-num">{esc(num)}</div>'
            f'<div class="section-name">{esc(name)}</div>{sub_html}</div>')


def _row(label, value_html) -> str:
    return f'<div class="row"><span class="row-label">{esc(label)}</span>{value_html}</div>'


def _val(text, cls="") -> str:
    return f'<span class="row-val {cls}" style="font-size:12px;">{esc(text)}</span>'


# ──────────────────────────────────────────────────────────────────────────
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
    chg_cls = "bull" if (chg or 0) > 0 else "bear" if (chg or 0) < 0 else ""
    chg_sign = "+" if (chg or 0) > 0 else ""

    parts: List[str] = []
    parts.append(f'<div class="tab-panel{" active" if active else ""}" id="panel-{tk.lower()}">')

    # ── 가격 바 ──
    parts.append(f'''
    <div class="price-bar">
      <div class="price-bar-candles">{_sparkline(market.get("series_daily"))}</div>
      <div style="flex:1;">
        <div style="display:flex;align-items:baseline;gap:10px;">
          <span style="font-size:22px;font-weight:900;color:var(--text-primary);">{esc(tk)}</span>
          <span style="font-size:12px;color:var(--text-muted);">{esc(meta.get("name",""))} · {esc(meta.get("sector") or meta.get("underlying",""))}</span>
        </div>
        <div style="display:flex;align-items:baseline;gap:10px;margin-top:4px;">
          <span style="font-size:24px;font-weight:800;color:var(--text-primary);">${_num(last)}</span>
          <span class="{chg_cls}" style="font-size:14px;font-weight:700;">{chg_sign}{_num(chg)}%</span>
        </div>
      </div>
    </div>''')

    # ── 최종 결론 ──
    concl = a.get("conclusion", {})
    parts.append(f'''
    <div class="conclusion-box" style="margin:12px 0;">
      <div class="conclusion-eyebrow">최종 결론</div>
      <div class="conclusion-text">{esc(concl.get("text",""))}<br><span class="hl">{esc(concl.get("highlight",""))}</span></div>
      <div class="conclusion-note">본 분석은 참고용이며 투자 권유가 아닙니다. 투자 판단과 책임은 본인에게 있습니다.</div>
    </div>''')

    # ── 핵심 메트릭 ──
    metric_cards = [
        ("RSI · 일봉", _num(d.get("rsi")), hm.get("rsi_daily_label", "")),
        ("RSI · 120분봉", _num(intra.get("rsi")), hm.get("rsi_intraday_label", "")),
        ("AI 종합 점수", f'{a.get("scores",{}).get("total","—")}점', "AI 산출"),
        ("MACD · 일봉", _num(d.get("macd")), hm.get("macd_daily_label", "")),
        ("예상 진입", hm.get("entry_zone", "—"), "AI 추정"),
        ("예상 매도", hm.get("exit_zone", "—"), "AI 추정"),
    ]
    if not is_etf:
        metric_cards.append(("다음 어닝", market.get("earnings_date", "—"), "변수"))
        metric_cards.append(("애널 목표가", f'${_num(an.get("target_mean"))}', esc(an.get("recommendation") or "")))
    else:
        metric_cards.append(("레버리지", f'{meta.get("leverage","3")}X', "일일 리밸런싱"))
        metric_cards.append(("베타", _num(info.get("beta")), "변동성"))
    cards_html = "".join(
        f'<div class="metric-card"><div class="lbl">{esc(l)}</div>'
        f'<div class="val">{esc(v)}</div><div class="sub">{esc(s)}</div></div>'
        for l, v, s in metric_cards)
    parts.append(f'<div class="metric-grid">{cards_html}</div>')

    # ── ① 일봉 ──
    dd = a.get("daily", {})
    parts.append(_section_title(1, "기술적 분석 · 일봉"))
    parts.append(f'''<div class="card">
      {_row("단기 이평 (5·20일)", _val(dd.get("ma_short","")))}
      {_row("중기 이평 (100일)", _val(dd.get("ma_mid","")))}
      {_row("장기 이평 (200일)", _val(dd.get("ma_long","")))}
      {_row("RSI (일봉)", f'<span style="display:flex;gap:8px;align-items:center;"><span class="row-val">{_num(d.get("rsi"))}</span>{_val(dd.get("rsi",""))}</span>')}
      {_row("MACD (일봉)", _val(f'{_num(d.get("macd"))} · {dd.get("macd","")}'))}
      {_row("볼린저밴드", _val(dd.get("bollinger","")))}
      {_row("핵심 저항/지지", _val(dd.get("resistance","")))}
      {_row("20일선 대비", _val(f'{_num(d.get("vs_sma20_pct"))}%'))}
    </div>''')

    # ── ② 120분봉 ──
    ia = a.get("intraday", {})
    ir = ia.get("rows", {})
    parts.append(_section_title(2, "기술적 분석 · 120분봉", "단기 트레이딩 핵심"))
    if ia.get("info"):
        parts.append(f'<div class="info-box">{esc(ia["info"])}</div>')
    ind = [("이동평균선", ir.get("ma", "")), ("RSI", f'{_num(intra.get("rsi"))} · {ir.get("rsi","")}'),
           ("스토캐스틱", f'{_num(intra.get("stoch_k"))} · {ir.get("stoch","")}'),
           ("볼린저밴드", ir.get("bollinger", "")), ("거래량", ir.get("volume", "")),
           ("MACD", f'{_num(intra.get("macd"))} · {ir.get("macd","")}')]
    ind_html = "".join(f'<div class="ind-card"><div class="ind-name">{esc(n)}</div>'
                       f'<div class="ind-sig">{esc(v)}</div></div>' for n, v in ind)
    parts.append(f'<div class="ind-grid">{ind_html}</div>')
    if ia.get("summary"):
        parts.append(f'<div class="summary-box"><div class="summary-label">일봉+120분봉 통합</div>'
                     f'<div class="summary-result">→ {esc(ia["summary"])}</div></div>')

    # ── ③ 호재/리스크 (ETF는 동인/구조위험) ──
    parts.append(_section_title(3, "기초지수 동인 / 구조 위험" if is_etf else "호재 카탈리스트 / 리스크"))
    def _catrisk(items, color):
        rows = "".join(
            f'<div class="row"><span class="row-label">{esc(it.get("title",""))}'
            + (f'<br><span style="font-size:10px;color:var(--text-muted);">{esc(it.get("source",""))}</span>' if it.get("source") else "")
            + f'</span><span class="tag tag-{color}">{esc(it.get("tag",""))}</span></div>'
            for it in (items or []))
        return rows or '<div class="row"><span class="row-label" style="color:var(--text-muted);">해당 근거 뉴스 없음</span></div>'
    parts.append(f'''<div class="grid2">
      <div class="card"><div class="card-title" style="color:var(--color-bull);">{"상방 동인" if is_etf else "호재 카탈리스트"}</div>{_catrisk(a.get("catalysts"), "bull")}</div>
      <div class="card"><div class="card-title" style="color:var(--color-bear);">리스크 요인</div>{_catrisk(a.get("risks"), "bear")}</div>
    </div>''')

    # ETF: 레버리지 소실 경고 카드
    if is_etf:
        etf = a.get("etf", {})
        parts.append(f'''<div class="card" style="border-top:3px solid var(--color-warning);margin-top:10px;">
          <div class="card-title" style="color:var(--color-warning);">⚠ 레버리지 ETF 주의</div>
          {_row("기초지수 방향", _val(etf.get("underlying_view","")))}
          {_row("레버리지 소실(decay)", _val(etf.get("decay_warning","")))}
          {_row("변동성", _val(etf.get("volatility","")))}
          {_row("권장 보유기간", _val(etf.get("hold_period","")))}
        </div>''')

    # ── ④ 파동/시나리오 ──
    parts.append(_section_title(4, "엘리어트 파동 / 시나리오"))
    waves = a.get("waves", [])
    if waves:
        wseg = "".join(f'<div class="wave-seg{" current" if w.get("current") else ""}">'
                       f'<div class="wave-num">{esc(w.get("num",""))}</div>'
                       f'<div class="wave-range">{esc(w.get("range",""))}</div>'
                       f'<div class="wave-desc">{esc(w.get("desc",""))}</div></div>' for w in waves[:3])
        parts.append(f'<div class="wave-row">{wseg}</div>')
    scen = "".join(
        f'<div class="scenario-row"><span class="scenario-label">{esc(s.get("label",""))}</span>'
        f'<span class="scenario-pct {s.get("dir","")}">{s.get("pct","")}%</span>'
        f'<div class="scenario-bar"><div class="scenario-fill" style="width:{s.get("pct",0)}%;background:{_dir_color(s.get("dir"))};"></div></div></div>'
        for s in a.get("scenarios", []))
    if scen:
        parts.append(f'<div class="card"><div class="card-title">향후 시나리오</div>{scen}</div>')

    # ── ⑤ 트레이딩 전략 ──
    parts.append(_section_title(5, "트레이딩 전략"))
    strat = a.get("strategy", {})
    def _trows(items):
        return "".join(f'<div class="trade-row"><span class="trade-label">{esc(i.get("label",""))}</span>'
                       f'<span class="trade-val">{esc(i.get("price",""))}</span></div>' for i in (items or []))
    parts.append(f'''<div class="trade-grid">
      <div class="trade-card"><div class="trade-card-title bull">▲ 매수 트리거</div>{_trows(strat.get("buy"))}</div>
      <div class="trade-card"><div class="trade-card-title bear">▼ 매도 / 손절</div>{_trows(strat.get("sell"))}</div>
    </div>''')

    # ── ⑥ AI 종합점수 ──
    parts.append(_section_title(6, "AI 종합 점수"))
    sc = a.get("scores", {})
    score_items = [("기술 (일봉)", sc.get("technical_daily")), ("기술 (120분봉)", sc.get("technical_intraday")),
                   ("수급", sc.get("supply")),
                   ("기초지수 추세" if is_etf else "펀더멘털", sc.get("fundamental")), ("성장성", sc.get("growth"))]
    srows = "".join(f'<div class="score-row"><span class="score-label">{esc(n)}</span>'
                    f'<div class="score-bg"><div class="score-fill" style="width:{v or 0}%;background:{_score_color(v)};"></div></div>'
                    f'<span class="score-num">{v if v is not None else "—"}</span></div>' for n, v in score_items)
    parts.append(f'<div class="card">{srows}<div class="score-total"><span class="score-total-label">종합 점수</span>'
                 f'<span class="score-total-val">{sc.get("total","—")}점</span></div></div>')

    # ── ⑦ 손익 시뮬 ──
    sim = a.get("simulation", {})
    parts.append(_section_title(7, "손익 시뮬레이션"))
    sim_cells = [("목표가", sim.get("target"), sim.get("target_pct"), "bull"),
                 ("손절가", sim.get("stop"), sim.get("stop_pct"), "bear"),
                 ("손익비", sim.get("rr"), "", "warn"), ("권장 비중", sim.get("weight"), "눌림 후", "")]
    sim_html = "".join(f'<div class="sim-card"><div class="sim-label">{esc(l)}</div>'
                       f'<div class="sim-val {c}">{esc(v or "—")}</div><div class="sim-sub {c}">{esc(s)}</div></div>'
                       for l, v, s, c in sim_cells)
    parts.append(f'<div class="sim-grid">{sim_html}</div>')

    # ── ⑧ 확률 분포 ──
    prob = a.get("probability", [])
    if prob:
        parts.append(_section_title(8, "확률 분포"))
        segs = "".join(f'<div class="prob-seg" style="width:{p.get("pct",0)}%;background:{_dir_color(p.get("dir"))};color:#0B0D12;">{p.get("pct","")}%</div>' for p in prob)
        legend = "".join(f'<div class="prob-legend-item"><span style="width:10px;height:10px;border-radius:2px;background:{_dir_color(p.get("dir"))};display:inline-block;"></span>{esc(p.get("label",""))}</div>' for p in prob)
        parts.append(f'<div class="card"><div class="prob-bar">{segs}</div><div class="prob-legend">{legend}</div></div>')

    # ── ⑨ 투자자별 전략 ──
    inv = a.get("investor", {})
    parts.append(_section_title(9, "투자자별 전략"))
    parts.append(f'''<div class="grid3">
      <div class="card"><div class="card-title bull">공격형</div><div style="font-size:12px;color:var(--text-tertiary);">{esc(inv.get("aggressive",""))}</div></div>
      <div class="card"><div class="card-title warn">중립형</div><div style="font-size:12px;color:var(--text-tertiary);">{esc(inv.get("neutral",""))}</div></div>
      <div class="card"><div class="card-title" style="color:var(--accent-blue);">보수형</div><div style="font-size:12px;color:var(--text-tertiary);">{esc(inv.get("conservative",""))}</div></div>
    </div>''')

    # ── ⑩ 시장심리 / 애널리스트 ──
    parts.append(_section_title(10, "시장 심리 / 애널리스트"))
    analyst_rows = ""
    if not is_etf:
        analyst_rows = (
            _row("애널리스트 목표가", _val(f'평균 ${_num(an.get("target_mean"))} (최고 ${_num(an.get("target_high"))} / 최저 ${_num(an.get("target_low"))})'))
            + _row("투자의견", f'<span class="tag tag-bull">{esc(an.get("recommendation") or "—")}</span> <span class="row-val" style="font-size:12px;">{_num(an.get("num_analysts"))}명</span>'))
    parts.append(f'''<div class="card">{analyst_rows}
      <div style="font-size:12px;color:var(--text-tertiary);margin-top:8px;">{esc(a.get("sentiment",""))}</div>
    </div>''')

    # ── ⑪ 풋/콜 비율 (v2.11 반영) ──
    parts.append(_pcr_section(opt, a))

    parts.append('</div>')  # /tab-panel
    return "".join(parts)
