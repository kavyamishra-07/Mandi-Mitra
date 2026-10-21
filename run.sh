#!/bin/bash
cd "$(dirname "$0")"
[ -d venv ] || python3 -m venv venv
source venv/bin/activate
pip install -q -r requirements.txt
echo "Starting Mandi Mitra. Open http://localhost:8000 in Chrome."
python -m mandi_mitra.server
