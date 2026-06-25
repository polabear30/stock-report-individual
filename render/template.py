"""전체 페이지 조립 (헤더 탭 + 패널 + switchTab JS + 푸터)"""

from __future__ import annotations

import os
from typing import Any, Dict, List

from render.sections import esc, render_panel

_CSS_PATH = os.path.join(os.path.dirname(__file__), "report.css")

# 탭 점 색상
_DOT = {"IONQ": "#38BDF8", "EOSE": "#34D399", "OKLO": "#FB923C",
        "SOXL": "#A78BFA", "KORU": "#F472B6"}


def _load_css() -> str:
    with open(_CSS_PATH, encoding="utf-8") as f:
        return f.read()


def render_report(panels: List[Dict[str, Any]], gen_time: str, status: Dict[str, bool]) -> str:
    """panels: [{"meta":..., "market":..., "analysis":...}, ...]"""
    css = _load_css()
    date_short = gen_time[5:10].replace("-", "/")

    tabs = ""
    body_panels = ""
    for i, p in enumerate(panels):
        tk = p["meta"]["ticker"]
        dot = _DOT.get(tk, "#9CA3AF")
        active = i == 0
        tabs += (f'<div class="tab-item{" active" if active else ""}" data-tab="{tk.lower()}" '
                 f'onclick="switchTab(\'{tk.lower()}\', this)">'
                 f'<span class="tab-dot" style="background:{dot};"></span>{esc(tk)}'
                 f'<span class="tab-date">{esc(date_short)}</span></div>')
        body_panels += render_panel(p["meta"], p["market"], p["analysis"], active)

    status_html = " · ".join(
        f'<span style="color:{"#4ADE80" if ok else "#F87171"};">{"●" if ok else "○"} {esc(k)}</span>'
        for k, ok in status.items())

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="format-detection" content="telephone=no">
<title>미국주식 개별 종목 AI 분석 · {esc(gen_time)}</title>
<link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard-dynamic-subset.min.css" rel="stylesheet">
<style>{css}</style>
</head>
<body>
<header class="top-header">
<div class="header-inner">
  <div style="font-size:11px;color:var(--text-quaternary);letter-spacing:0.3px;margin-bottom:4px;">
    © 전세영 &nbsp;·&nbsp; <a href="mailto:coolboy30a@naver.com" style="color:var(--text-quaternary);text-decoration:none;">coolboy30a@naver.com</a>
  </div>
  <div style="font-size:10px;color:var(--text-muted);letter-spacing:0.3px;margin-bottom:6px;">
    AI 분석 리포트 · 매일 자동 생성 · 참고용(투자권유 아님)
  </div>
  <div class="header-title-row">
    <span class="header-main-title">미국주식 개별 종목</span>
    <span class="header-main-sub">Individual Equity AI Analysis</span>
  </div>
  <div class="tab-row" id="tabRow">{tabs}</div>
</div>
</header>

<div class="page">
{body_panels}
  <div class="footer" style="text-align:center;padding:24px 0;font-size:11px;color:var(--text-muted);">
    생성 {esc(gen_time)} · 데이터 스냅샷<br>
    데이터 상태: {status_html}<br>
    카탈리스트·시나리오는 제공 뉴스/데이터 근거의 AI 추정이며 투자 권유가 아닙니다.
  </div>
</div>

<script>
function switchTab(tab, el){{
  document.querySelectorAll('.tab-panel').forEach(function(p){{ p.classList.remove('active'); }});
  var panel = document.getElementById('panel-' + tab);
  if (panel) panel.classList.add('active');
  document.querySelectorAll('.tab-item').forEach(function(t){{ t.classList.remove('active'); }});
  el.classList.add('active');
  window.scrollTo(0, 0);
}}
</script>
</body>
</html>"""
