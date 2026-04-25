#!/usr/bin/env python3
"""
generate_page.py — Static HTML 웹페이지 생성 (모든 섹션 미리 렌더링)
"""
import json, re
from pathlib import Path
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
SKILL_DIR = Path(__file__).parent.parent
TEMPLATE   = SKILL_DIR / "assets" / "template.html"
ARTICLES   = SKILL_DIR / "data" / "raw_articles.json"
INSIGHTS   = SKILL_DIR / "data" / "insights_report.json"

def escHtml(s):
    if not s: return ''
    return str(s).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;')

def main():
    articles = json.load(open(ARTICLES))["articles"]
    insights = json.load(open(INSIGHTS))
    html = TEMPLATE.read_text(encoding="utf-8")
    now = datetime.now(KST)
    date_str = now.strftime("%Y%m%d")

    # ===== Render articles =====
    articles_html = ""
    for a in articles:
        link = escHtml(a.get("link",""))
        source = escHtml(a.get("source",""))
        title = escHtml(a.get("title",""))
        desc = escHtml((a.get("description") or "")[:200])
        articles_html += f'<a href="{link}" class="article-card" target="_blank" rel="noopener"><div class="source-tag">{source}</div><div class="article-title">{title}</div><div class="article-desc">{desc}</div></a>'

    # ===== Render summary =====
    summary_html = escHtml(insights.get("summary",""))

    # ===== Render trends =====
    trends_html = ""
    for t in insights.get("trends", []):
        impact = t.get("impact","medium")
        sources = "".join(f'<span class="trend-source">• {escHtml(s)}</span>' for s in (t.get("sources") or []))
        trends_html += f'<div class="trend-card {impact}"><div class="trend-title">{escHtml(t["title"])}</div><div class="trend-desc">{escHtml(t["description"])}</div><div class="trend-meta"><span class="impact-badge impact-{impact}">{impact}</span>{sources}</div></div>'

    # ===== Render insights =====
    insights_html = ""
    for i in insights.get("insights", []):
        trend_ref = f'<span class="trend-ref"># {escHtml(i["trend_ref"])}</span>' if i.get("trend_ref") else ''
        insights_html += f'<div class="insight-card"><div class="insight-title">💡 {escHtml(i["title"])}</div><div class="insight-content">{escHtml(i["content"])}</div>{trend_ref}</div>'

    # ===== Render actions =====
    actions_html = ""
    for a in insights.get("action_items", []):
        p = a.get("priority","medium")
        effort = escHtml(a.get("effort","?"))
        trend_ref = f'<span class="trend-ref"># {escHtml(a["trend_ref"])}</span>' if a.get("trend_ref") else ''
        actions_html += f'<div class="action-item {p}"><div class="priority-dot"></div><div class="action-body"><div class="action-title">{escHtml(a["title"])}</div><div class="action-desc">{escHtml(a["description"])}</div><div class="action-meta"><span class="priority-label {p}">{p}</span><span class="effort-badge">⏱ {effort}</span>{trend_ref}</div></div></div>'

    # ===== Render business impact =====
    biz_html = ""
    bi = insights.get("business_impact", {})
    if bi.get("opportunities"):
        items = "".join(f'<li>{escHtml(o)}</li>' for o in bi["opportunities"])
        biz_html += f'<div class="biz-card opportunities"><h3>🟢 기회</h3><ul class="biz-list">{items}</ul></div>'
    if bi.get("threats"):
        items = "".join(f'<li>{escHtml(o)}</li>' for o in bi["threats"])
        biz_html += f'<div class="biz-card threats"><h3>🔴 위협</h3><ul class="biz-list">{items}</ul></div>'
    if bi.get("recommendations"):
        items = "".join(f'<li>{escHtml(o)}</li>' for o in bi["recommendations"])
        biz_html += f'<div class="biz-card recommendations" style="grid-column:1/-1"><h3>🟠 권고사항</h3><ul class="biz-list">{items}</ul></div>'

    # ===== Replace placeholders =====
    html = html.replace('<div class="summary-banner" id="summary"></div>',
                        f'<div class="summary-banner" id="summary">{summary_html}</div>')
    html = html.replace('<div class="trend-grid" id="trends"></div>',
                        f'<div class="trend-grid" id="trends">{trends_html}</div>')
    html = html.replace('<div id="insights"></div>',
                        f'<div id="insights">{insights_html}</div>')
    html = html.replace('<div class="action-list" id="actions"></div>',
                        f'<div class="action-list" id="actions">{actions_html}</div>')
    html = html.replace('<div class="biz-grid" id="biz-grid"></div>',
                        f'<div class="biz-grid" id="biz-grid">{biz_html}</div>')
    html = html.replace('<div class="article-grid" id="articles"></div>',
                        f'<div class="article-grid" id="articles">{articles_html}</div>')
    html = html.replace('<div class="date" id="page-date"></div>',
                        f'<div class="date" id="page-date">{now.strftime("%Y년 %m월 %d일")}</div>')
    html = html.replace('<title>Daily Curation — {{date}}</title>',
                        f'<title>Daily News Curation — {now.strftime("%Y년 %m월 %d일")}</title>')
    html = html.replace("{{date}}", now.strftime("%Y-%m-%d"))
    html = html.replace("{{generated_at}}", now.strftime("%Y-%m-%d %H:%M KST"))

    # Remove old async fetch script block
    html = re.sub(
        r'<script>\s*// ===== 데이터 로드.*?</script>',
        '<script>/* static render — all content embedded at build time */</script>',
        html,
        flags=re.DOTALL
    )

    OUTPUT = SKILL_DIR / "public" / f"{date_str}.html"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"✅ HTML 생성 완료 ({OUTPUT.stat().st_size} bytes)")
    print(f"   기사:{len(articles)} 트렌드:{len(insights.get('trends',[]))} 인사이트:{len(insights.get('insights',[]))} 액션:{len(insights.get('action_items',[]))}")

if __name__ == "__main__":
    main()
