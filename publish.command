#!/bin/bash
# ============================================================
#  Publish the UiPath PSE Support Assistant to GitHub Pages
#  Double-click this file in Finder to push your latest changes.
#
#  It (1) refreshes the embedded guides from your NEWEST exported
#  .skill package, then (2) commits and pushes. Live in ~1 min.
# ============================================================
set -e
cd "$(dirname "$0")"
export PATH="$HOME/.local/bin:$PATH"

echo "==============================================="
echo " Publishing UiPath PSE Support Assistant"
echo "==============================================="

echo "-> Syncing embedded guides from your latest skill export..."
python3 sync_from_skill.py

git add -A
git commit -m "Update $(date '+%Y-%m-%d %H:%M')" || echo "(nothing new to commit)"
echo "-> Pushing to GitHub..."
git push

# ---- Verify the live site actually updates; auto-fix a stuck Pages build ----
URL="https://dinesh12nov.github.io/uipath-orchestrator-assistant-test/index.html"
REPO_SLUG="Dinesh12nov/uipath-orchestrator-assistant-test"
WANT=$(wc -c < index.html | tr -d ' ')

live_size() { curl -sI "$URL" | awk 'tolower($1)=="content-length:"{gsub(/\r/,"");print $2}'; }

echo "-> Waiting for GitHub Pages to publish (expecting $WANT bytes)..."
ok=0
for i in $(seq 1 6); do
  sleep 20
  [ "$(live_size)" = "$WANT" ] && { ok=1; break; }
  echo "   still building... (~$((i*20))s)"
done

if [ "$ok" != "1" ]; then
  echo "-> Build looks stuck — forcing a fresh Pages build..."
  gh api -X POST "repos/$REPO_SLUG/pages/builds" >/dev/null 2>&1 || true
  for i in $(seq 1 9); do
    sleep 20
    [ "$(live_size)" = "$WANT" ] && { ok=1; break; }
    echo "   rebuilding... (~$((i*20))s)"
  done
fi

echo ""
if [ "$ok" = "1" ]; then
  echo "✅ LIVE and updated:"
else
  echo "⚠️ Not confirmed live yet. Check again in a few minutes, or tell Claude. URL:"
fi
echo "   https://dinesh12nov.github.io/uipath-orchestrator-assistant-test/"

echo ""
echo "Press any key to close this window..."
read -n 1 -s
