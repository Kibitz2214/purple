from fastapi import APIRouter, HTTPException
from schemas.risk import RiskRequest, RiskResponse
from services.risk_service import predict_risk

router = APIRouter()


@router.post('/risk-score', response_model=RiskResponse)
async def risk_predict(request: RiskRequest):
    try:
        result = predict_risk(request)
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'추론 중 오류: {str(e)}')
