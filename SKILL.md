---
name: daily-curation
description: |
  데일리 큐레이션 퍼블리셔 스킬. 매일 아침 RSS/Atom 피드(AI타임스, GeekNews 등)를
  자동 수집 → 24시간 이내 기사 필터링 → 인사이트/트렌드/액션아이템 생성 →
  다크테마+카드형+Hermes Orange 웹페이지 생성 → GitHub + Vercel 자동 배포 →
  Telegram으로 배포 URL 보고. 트리거: 매크론(cron) 또는 "데일리 큐레이션 실행"
  요청 시. 절대 수동으로 articles나 insights를 직접 수정하지 않는다.
---

# ⚡ Daily Curation Publisher

매일 아침 7시, 기술 뉴스 RSS를 수집 → 분석 → 웹페이지로 퍼블리싱하는 자동화 스킬.

## 🏗️ 구조

```
daily-curation/
├── SKILL.md           ← 이 파일
├── config/
│   └── sources.json   ← RSS/Atom 소스 목록
├── data/
│   ├── raw_articles.json      ← RSS 수집 결과
│   └── insights_report.json  ← 인사이트/트렌드/액션아이템
├── scripts/
│   ├── fetch_rss.py          ← RSS 수집 + 24시간 필터
│   ├── generate_insights.py  ← 서브에이전트 인사이트 생성
│   ├── generate_page.py      ← HTML 웹페이지 생성
│   └── deploy.sh             ← 전체 자동화 파이프라인
├── public/
│   └── index.html            ← Vercel 배포용 정적 페이지
└── assets/
    └── template.html         ← 다크/카드/Hermes HTML 템플릿
```

## ⚙️ RSS 소스 설정

`config/sources.json`에 소스 추가/수정:

```json
{
  "sources": [
    {
      "name": "AI타임스",
      "url": "https://www.aitimes.com/rss/allArticle.xml",
      "scrape_type": "rss",
      "lang": "ko",
      "translate": false,
      "category": "tech",
      "max_articles": 10
    },
    {
      "name": "GeekNews",
      "url": "http://feeds.feedburner.com/geeknews-feed",
      "scrape_type": "atom",
      "lang": "ko",
      "translate": false,
      "category": "tech",
      "max_articles": 15
    }
  ],
  "settings": {
    "filter_hours": 24
  }
}
```

## 📋 실행 흐름

```
cron (매일 07:00)
  → deploy.sh 실행
    → fetch_rss.py     → raw_articles.json (25건 수집)
    → 3호 에이전트     → insights_report.json (인사이트/트렌드/액션)
    → generate_page.py → public/index.html
    → GitHub push      → main branch
    → Vercel 배포      → https://daily-curation-kappa.vercel.app
    → Telegram 보고    → URL 전달
```

## 🎨 웹페이지 디자인

- **테마**: 다크 (#0D0D0F 배경)
- **카드형**: border-radius 12px, 카드 간격 1rem
- **accent**: Hermes Orange (#FF6B00)
- **레이아웃**: Header → 요약 → 트렌드 → 인사이트 → 액션아이템 → 원문기사
- **렌더링**: 모든 섹션 HTML 내에 직접 렌더링 (JS fetch 없음)
- **파일명**: `{yyyymmdd}.html` 형태 (예: `20260425.html`)
- **기사 링크**: 모든 원문 카드에 실제 URL 직접 링크 (target=_blank)

## 🔧 수동 실행

```bash
cd ~/.openclaw/skills/daily-curation
bash scripts/deploy.sh
```

## ⚠️ 주의사항

- `data/` 폴더의 JSON 파일은 **절대 수동 편집 금지** (cron 재실행 시 덮어씌워짐)
- Vercel/GitHub 인증 상태는 주기적으로 확인
- 인사이트 생성 실패 시 `insights_report.json`이 비어있을 수 있음 → 3호 재요청