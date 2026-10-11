#!/usr/bin/env bash
set -eu
cd /workspace/CloudLifeOS
python3 --version
node --version
git --version
test -x /usr/bin/chromium
python3 scripts/bootstrap.py
npm --cache /workspace/CloudLifeOS/.local/npm-cache ci --ignore-scripts --no-audit --no-fund
python3 -m unittest discover -s tests -p 'test_*.py'
