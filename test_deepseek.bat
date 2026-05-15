@echo off
chcp 65001 >nul 2>&1
title ATLAS - DeepSeek Test
cd /d "%~dp0"
venv\Scripts\python.exe test_deepseek.py
