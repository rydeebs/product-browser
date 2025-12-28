#!/bin/bash
# Script to run analyze_posts.py with the correct virtual environment
cd "$(dirname "$0")"
source ../scrapers/venv/bin/activate
python analyze_posts.py
