@echo off
cd /d "%~dp0"
echo Starting a new AI Playbook Policy Document Finder run...
python ai_playbook_policy_document_finder.py --quick --max-results 3
pause
