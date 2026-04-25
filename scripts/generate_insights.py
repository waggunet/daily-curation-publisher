#!/usr/bin/env python3
"""
generate_insights.py — 서브에이전트를 통해 인사이트 + 액션아이템 생성
방향: 기술 트렌드 + 비즈니스/산업 영향 hybrid
"""
import json
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))

SKILL_DIR = Path(__file__).parent.parent
INPUT_FILE = SKILL_DIR / "data" / "raw_articles.json"
OUTPUT_FILE = SKILL_DIR / "data" / "insights_report.json"

def load_articles():
    with open(INPUT_FILE, encoding="utf-8") as f:
        return json.load(f)

def main():
    data = load_articles()
    articles = data.get("articles", [])
    fetched_at = data.get("fetched_at", datetime.now(KST).isoformat())
    print(f"📰 {len(articles)}건 기사 로드 완료")

    # 기사 목록을 프롬프트용 텍스트로 변환
    article_list = []
    for i, a in enumerate(articles, 1):
        desc = a.get("description", "")[:200]
        article_list.append(f"{i}. [{a['source']}] {a['title']}\n   {desc}...")
    articles_text = "\n".join(article_list)

    task = f"""[인사이트 생성 태스크]

오늘 수집된 뉴스 기사를 분석하여 insights_report.json 파일을 생성하라.

## 수집 기사 ({len(articles)}건, 수집시각: {fetched_at})
{articles_text}

## 출력 파일 경로
{SKILL_DIR}/data/insights_report.json

## 출력 JSON 구조 (반드시 이 구조로만 작성)
{{
  "summary": "오늘 뉴스 전체 요약 (3~5문장, 한국어)",
  "trends": [
    {{
      "title": "트렌드명",
      "description": "트렌드 설명 (2~3문장)",
      "sources": ["관련 기사 제목 1", "관련 기사 제목 2"],
      "impact": "high/medium/low"
    }}
  ],
  "insights": [
    {{
      "title": "인사이트 제목",
      "content": "인사이트 내용 (3~5문장)",
      "trend_ref": "관련 트렌드명"
    }}
  ],
  "action_items": [
    {{
      "title": "액션아이템",
      "description": "구체적으로 무엇을 해야 하는지 (2~3문장)",
      "priority": "high/medium/low",
      "trend_ref": "관련 트렌드명",
      "effort": "5min/30min/1hour/halfday"
    }}
  ],
  "business_impact": {{
    "opportunities": ["비즈니스 기회 1", "비즈니스 기회 2"],
    "threats": ["위협/리스크 1", "위협/리스크 2"],
    "recommendations": ["권고 사항 1", "권고 사항 2"]
  }}
}}

## 분석 관점
- 기술 트렌드: AI 에이전트, 멀티모달, 오픈소스, 클라우드, 보안 등 최신 기술 흐름
- 비즈니스/산업 영향: 해당 기술이 산업에 미치는 파급, 기존 비즈니스 모델 변화, 새로운 기회와 위협
- 실행 가능한 액션아이템: 구체적으로 무엇을試해볼 수 있는지 (5분~반나절圈内)

## 실행 방법
1. 위 기사를 분석한다
2. JSON 파일을 직접写入 {SKILL_DIR}/data/insights_report.json
3. 응답은 "완료" 또는 에러 메시지만 출력

반드시 유효한 JSON만 파일에写入할 것. 마크다운 코드블록이나 설명 추가 금지."""

    print("🤖 서브에이전트(3호 🦉) 호출하여 인사이트 생성 중...")
    
    # sessions_spawn으로 3호(리서치/분석) 에이전트 사용
    result = subprocess.run([
        sys.executable, "-c",
        f"""
import subprocess, json, sys
res = subprocess.run([
    'openclaw', 'sessions', 'spawn',
    '--runtime', 'subagent',
    '--label', 'daily-curation-insights',
    '--task', {json.dumps(task)}
], capture_output=True, text=True)
print(res.stdout)
print(res.stderr)
"""
    ], capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    # 서브에이전트 결과 확인
    if Path(OUTPUT_FILE).exists():
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            result_data = json.load(f)
        print(f"\\n✅ 인사이트 생성 완료")
        print(f"📊 트렌드 {len(result_data.get('trends', []))}건")
        print(f"💡 인사이트 {len(result_data.get('insights', []))}건")
        print(f"🎯 액션아이템 {len(result_data.get('action_items', []))}건")
    else:
        print(f"⚠️ 결과 파일 미생성 — 서브에이전트 응답 확인 필요")

if __name__ == "__main__":
    main()