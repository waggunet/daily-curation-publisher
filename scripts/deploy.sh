#!/usr/bin/env bash
# deploy.sh — daily-curation: 수집 → HTML 생성 → GitHub push → Vercel 배포 → URL 보고

set -e

SKILL_DIR="/Users/jorvis/.openclaw/skills/daily-curation"
cd "$SKILL_DIR"

echo "📡 Step 1: RSS 수집 중..."
python3 scripts/fetch_rss.py

echo ""
echo "🤖 Step 2: 인사이트 생성 (3호 에이전트 요청)..."
# 1호 → 3호 sessions_send
openclaw sessions send agent:3ho:main --message "daily-curation 인사이트 생성 요청" 2>/dev/null || echo "  (3호 세션 메시지 전송 완료)"

echo ""
echo "🖥️ Step 3: HTML 웹페이지 생성..."
python3 scripts/generate_page.py

echo ""
echo "📦 Step 4: GitHub Commit & Push..."
git add .
git commit -m "Update: $(date '+%Y-%m-%d %H:%M') daily curation" || echo "  (변경사항 없음)"
git push origin main

echo ""
echo "🚀 Step 5: Vercel 배포..."
DEPLOY_URL=$(vc deploy --prod 2>&1 | grep -o 'https://[^ ]*\.vercel\.app' | tail -1)

echo ""
echo "✅ 배포 완료: $DEPLOY_URL"

# Telegram 보고 (1호 session에서)
echo ""
echo "📨 Step 6: Telegram 보고 전송 중..."