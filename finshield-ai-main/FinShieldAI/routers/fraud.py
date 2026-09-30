from fastapi import APIRouter, HTTPException
from schemas.fraud import FraudRequest, FraudResponse
from services.fraud_service import predict_fraud

router = APIRouter()


@router.post('/fraud', response_model=FraudResponse)
async def fraud_detection(request: FraudRequest):
    try:
        result = predict_fraud(request)
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'추론 중 오류: {str(e)}')
