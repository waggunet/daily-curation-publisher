#!/usr/bin/env python3
"""
generate_page.py — HTML 웹페이지 생성
raw_articles.json + insights_report.json → public/index.html
"""
import json, sys, copy
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

    # articles → JSON 삽입 (스크립트 태그로 렌더링)
    articles_json = json.dumps(articles, ensure_ascii=False)
    insights_json = json.dumps(insights, ensure_ascii=False)

    # 데이터 인라인 임베딩 (data.js로 분리)
    data_js = f"const ARTICLES = {articles_json};\nconst INSIGHTS = {insights_json};"
    
    # 데이터 태그 삽입
    data_script = f'<script>\nconst ARTICLES = {articles_json};\nconst INSIGHTS = {insights_json};\n'
    # template의 load() 함수에서 DATA_PATH 대신 ARTICLES 사용하도록 교체
    data_script += '''
async function load() {
  const data = { articles: ARTICLES, insights: INSIGHTS };
  render(data);
}
document.addEventListener('DOMContentLoaded', load);
    </script>'''

    # 기존 load 스크립트 제거 후 데이터 스크립트로 교체
    import re
    # 기존 데이터 로드 스크립트 블록 제거
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