#!/usr/bin/env python3
"""
generate_page.py — HTML 웹페이지 생성 (data embed fix)
"""
import json, re
from pathlib import Path
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
SKILL_DIR = Path(__file__).parent.parent
TEMPLATE   = SKILL_DIR / "assets" / "template.html"
ARTICLES   = SKILL_DIR / "data" / "raw_articles.json"
INSIGHTS   = SKILL_DIR / "data" / "insights_report.json"
OUTPUT     = SKILL_DIR / "public" / "index.html"

def js_string(s):
    """Python string → safe JS string literal (handles any encoding)"""
    # Escape for JS string — use JSON-safe encoding
    s = json.dumps(s, ensure_ascii=False)
    return s  # json.dumps already produces valid JS string

def main():
    articles = json.load(open(ARTICLES))["articles"]
    insights = json.load(open(INSIGHTS))

    html = TEMPLATE.read_text(encoding="utf-8")

    # articles → JS array literal
    article_js_parts = []
    for a in articles:
        article_js_parts.append(
            f'{{source:{js_string(a.get("source",""))},'
            f'title:{js_string(a.get("title",""))},'
            f'description:{js_string(a.get("description","")[:300])},'
            f'link:{js_string(a.get("link",""))}}}'
        )
    articles_js = "[" + ",".join(article_js_parts) + "]"

    # insights → JS object literal
    insights_js = json.dumps(insights, ensure_ascii=False)

    # Embedded data script
    data_script = f'<script>\nwindow.ARTICLES={articles_js};\nwindow.INSIGHTS={insights_js};\n</script>'

    # Replace template data loader
    html = re.sub(
        r'<script>\s*// ===== 데이터 로드.*?</script>',
        data_script,
        html,
        flags=re.DOTALL
    )

    # Replace load() call
    html = html.replace(
        'document.addEventListener("DOMContentLoaded", load);',
        'document.addEventListener("DOMContentLoaded", function(){ render({ articles:window.ARTICLES, insights:window.INSIGHTS }); });'
    )

    now_kst = datetime.now(KST)
    html = html.replace("{{date}}", now_kst.strftime("%Y-%m-%d"))
    html = html.replace("{{generated_at}}", now_kst.strftime("%Y-%m-%d %H:%M KST"))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(html, encoding="utf-8")

    print(f"✅ HTML 생성 완료 ({OUTPUT.stat().st_size} bytes)")
    print(f"   기사: {len(articles)}건, 트렌드: {len(insights.get('trends',[]))}건")

if __name__ == "__main__":
    main()