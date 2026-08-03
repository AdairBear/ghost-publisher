#!/bin/bash
# Remove the weekly ghost-publisher launchd agent.
#
#   ./scripts/uninstall-launchd.sh
#
# Stops future runs. Does not touch the queue, published/, or state.

set -euo pipefail

LABEL="com.thomasadair.ghost-publisher"
TARGET="$HOME/Library/LaunchAgents/$LABEL.plist"

launchctl bootout "gui/$UID/$LABEL" 2>/dev/null || true

if [[ -f "$TARGET" ]]; then
    rm "$TARGET"
    echo "removed $TARGET"
else
    echo "nothing installed at $TARGET"
fi

echo "weekly ghost-publisher trigger is off."
