#!/usr/bin/env python3
"""
generate_page.py — HTML 웹페이지 생성
raw_articles.json + insights_report.json → public/index.html
"""
import json, sys, copy, base64
from pathlib import Path
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
SKILL_DIR = Path(__file__).parent.parent
TEMPLATE   = SKILL_DIR / "assets" / "template.html"
ARTICLES   = SKILL_DIR / "data" / "raw_articles.json"
INSIGHTS   = SKILL_DIR / "data" / "insights_report.json"
OUTPUT     = SKILL_DIR / "public" / "index.html"

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def main():
    articles = load_json(ARTICLES).get("articles", [])
    insights = load_json(INSIGHTS)

    # 템플릿 읽기
    html = TEMPLATE.read_text(encoding="utf-8")

    # 데이터를 base64로 인코딩해서 안전하게 embed
    articles_b64 = base64.b64encode(
        json.dumps(articles, ensure_ascii=False).encode("utf-8")
    ).decode("ascii")
    insights_b64 = base64.b64encode(
        json.dumps(insights, ensure_ascii=False).encode("utf-8")
    ).decode("ascii")

    # 데이터 로드 스크립트 (base64 디코딩 → JSON 파싱)
    data_script = f'''<script id="__data__" type="application/json">
{{"articles_b64":"{articles_b64}","insights_b64":"{insights_b64}"}}
</script>
<script>
(function(){{
  var d = JSON.parse(atob(document.getElementById("__data__").textContent));
  window.ARTICLES = JSON.parse(atob(d.articles_b64));
  window.INSIGHTS = JSON.parse(atob(d.insights_b64));
  render({{ articles: window.ARTICLES, insights: window.INSIGHTS }});
}})();
</script>'''

    # 기존 데이터 로드 스크립트 블록 제거 후 삽입
    import re
    html = re.sub(
        r'<script>\s*// ===== 데이터 로드.*?</script>',
        data_script,
        html,
        flags=re.DOTALL
    )

    # 날짜 치환
    now_kst = datetime.now(KST)
    html = html.replace("{{date}}", now_kst.strftime("%Y-%m-%d"))
    html = html.replace("{{generated_at}}", now_kst.strftime("%Y-%m-%d %H:%M KST"))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(html, encoding="utf-8")
    
    print(f"✅ HTML 생성 완료: {OUTPUT}")
    print(f"   - 기사 수: {len(articles)}건")
    trends_count = len(insights.get("trends", []))
    print(f"   - 트렌드: {trends_count}건")
    actions_count = len(insights.get("action_items", []))
    print(f"   - 액션아이템: {actions_count}건")

if __name__ == "__main__":
    main()