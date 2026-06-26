#!/bin/bash
# Auto-sync script for MRS-workSpace
# Checks for changes and auto-commits + pushes to GitHub

REPO_DIR="d:/translation"
cd "$REPO_DIR" || exit 1

# Check if there are any changes
if [ -z "$(git status --porcelain)" ]; then
    # No changes, nothing to do
    exit 0
fi

# Stage all changes
git add -A

# Commit with timestamp
TIMESTAMP=$(date "+%Y-%m-%d %H:%M")
git commit -m "🔄 auto: $TIMESTAMP"

# Push to GitHub
git push
