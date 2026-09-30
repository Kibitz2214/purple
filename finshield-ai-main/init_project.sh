#!/bin/bash
# FinShieldAI 초기 프로젝트 구조 생성
# finshield-ai/ 루트에서 실행하세요

mkdir -p FinShieldAI/{core,models,routers,schemas,services,training/data}

touch FinShieldAI/main.py
touch FinShieldAI/core/config.py
touch FinShieldAI/routers/fraud.py
touch FinShieldAI/routers/risk.py
touch FinShieldAI/routers/health.py
touch FinShieldAI/schemas/fraud.py
touch FinShieldAI/schemas/risk.py
touch FinShieldAI/services/fraud_service.py
touch FinShieldAI/services/risk_service.py
touch FinShieldAI/training/train_fraud.py
touch FinShieldAI/training/train_risk.py
touch FinShieldAI/training/data/.gitkeep
touch FinShieldAI/models/.gitkeep

echo "✅ FinShieldAI 폴더 구조 생성 완료"
