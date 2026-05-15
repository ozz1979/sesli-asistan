@echo off
chcp 65001 >nul 2>&1
title ATLAS - Model Deneme
cd /d "%~dp0"
venv\Scripts\python.exe test_modeller.py
