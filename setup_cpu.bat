@echo off
python -m venv .venv_cpu
call .venv_cpu\Scripts\activate
pip install -r requirements.txt
pip install torch --index-url https://download.pytorch.org/whl/cpu
