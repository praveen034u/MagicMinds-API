#!/bin/bash

# GitHub Push Helper Script
# This script helps push your code to GitHub

echo "🚀 Pushing to GitHub: https://github.com/praveen034u/MagicMinds-API"
echo ""
echo "You'll need your GitHub Personal Access Token"
echo "Get it from: https://github.com/settings/tokens/new"
echo ""
echo "When prompted:"
echo "  Username: praveen034u"
echo "  Password: <paste your token>"
echo ""

cd /app/api
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully pushed to GitHub!"
    echo "View your code at: https://github.com/praveen034u/MagicMinds-API"
else
    echo ""
    echo "❌ Push failed. Check your token and try again."
    echo ""
    echo "Alternative: Push manually with token in URL:"
    echo "git push https://praveen034u:YOUR_TOKEN@github.com/praveen034u/MagicMinds-API.git main"
fi
