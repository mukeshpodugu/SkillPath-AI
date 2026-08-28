@echo off
echo Starting SkillPath AI Backend...
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
pause
