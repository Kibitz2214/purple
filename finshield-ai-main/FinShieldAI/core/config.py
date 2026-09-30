import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# 기본 경로
BASE_DIR = Path(__file__).resolve().parent.parent

# 모델 파일 경로
FRAUD_MODEL_PATH = BASE_DIR / 'models' / 'fraud_model.pkl'
RISK_MODEL_PATH  = BASE_DIR / 'models' / 'risk_model.pkl'

# 서버 설정
AI_SERVER_PORT = int(os.getenv('AI_SERVER_PORT', 8001))

# 피처 컬럼 (학습/추론 동일하게 유지 필수)
FEATURE_COLUMNS = [
    'amount_log',
    'hour_of_day',
    'day_of_week',
    'is_blacklisted',
    'is_new_receiver',
    'sender_tx_count_7d',
    'sender_avg_amount_30d_log',
    'sender_balance_before_log',
    'amount_to_balance_ratio_log',
]
