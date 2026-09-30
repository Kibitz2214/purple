from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from routers import fraud, risk, health, report
from services.fraud_service import load_fraud_model
from services.risk_service import load_risk_model

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 시작 시 모델 1회 로드
    try:
        load_fraud_model()
        logger.info('fraud_model 로드 완료')
    except RuntimeError as e:
        logger.warning(f'fraud_model 로드 실패: {e}')

    try:
        load_risk_model()
        logger.info('risk_model 로드 완료')
    except RuntimeError as e:
        logger.warning(f'risk_model 로드 실패: {e}')

    yield


app = FastAPI(
    title='FinShield AI Server',
    description='이상거래 탐지 및 리스크 스코어링 추론 서버',
    version='1.0.0',
    lifespan=lifespan,
)

# FinShieldBackend 내부 통신만 허용 (운영 시 백엔드 IP로 제한)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(health.router, tags=['health'])
app.include_router(fraud.router, prefix='/predict', tags=['fraud'])
app.include_router(risk.router, prefix='/predict', tags=['risk'])
app.include_router(report.router, prefix='/predict', tags=['report'])


@app.get('/')
def root():
    return {'service': 'FinShield AI Server', 'status': 'running'}
