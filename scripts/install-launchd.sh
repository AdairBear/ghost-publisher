#!/bin/bash
# Install the weekly ghost-publisher trigger as a launchd user agent.
#
#   ./scripts/install-launchd.sh
#
# Installs to ~/Library/LaunchAgents/com.thomasadair.ghost-publisher.plist and
# loads it. Safe to re-run — it unloads any previous copy first.
#
# It does NOT publish anything now; it only registers the Monday 08:00 run.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LABEL="com.thomasadair.ghost-publisher"
TEMPLATE="$PROJECT_DIR/scripts/$LABEL.plist"
TARGET="$HOME/Library/LaunchAgents/$LABEL.plist"

if [[ ! -f "$TEMPLATE" ]]; then
    echo "install-launchd: missing template $TEMPLATE" >&2
    exit 1
fi

mkdir -p "$HOME/Library/LaunchAgents" "$PROJECT_DIR/logs"
chmod +x "$PROJECT_DIR/run.sh"

sed "s|__PROJECT_DIR__|$PROJECT_DIR|g" "$TEMPLATE" > "$TARGET"
echo "wrote $TARGET"

# bootout is the modern unload; ignore failure when nothing is loaded yet.
launchctl bootout "gui/$UID/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$UID" "$TARGET"
echo "loaded $LABEL"

echo
echo "Scheduled: every Monday 08:00 local."
echo "Verify with : launchctl print gui/$UID/$LABEL | head -20"
echo "Run it now  : launchctl kickstart -p gui/$UID/$LABEL"
echo "Remove with : ./scripts/uninstall-launchd.sh"
