from fastapi import APIRouter
from services.fraud_service import is_loaded as fraud_loaded
from services.risk_service import is_loaded as risk_loaded

router = APIRouter()


@router.get('/health')
def health_check():
    # 파일 존재가 아닌 실제 메모리 로드 상태 반영
    fraud_ok = fraud_loaded()
    risk_ok = risk_loaded()

    return {
        'status': 'ok',
        'fraud_model': 'loaded' if fraud_ok else 'not_loaded',
        'risk_model': 'loaded' if risk_ok else 'not_loaded',
    }
