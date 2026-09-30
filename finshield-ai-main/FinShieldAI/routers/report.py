from fastapi import APIRouter, HTTPException
from schemas.report import ReportReviewRequest, ReportReviewResponse
from services.report_service import predict_report_review

router = APIRouter()


@router.post('/report-review', response_model=ReportReviewResponse)
async def report_review(request: ReportReviewRequest):
    try:
        result = predict_report_review(request)
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'심사 중 오류: {str(e)}')
