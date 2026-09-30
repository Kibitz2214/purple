"""
사용자 행동 베이스라인 CRUD (MongoDB — pymongo 동기 클라이언트)

user_behavior_baselines 컬렉션 구조:
{
    user_id            : int          # unique index
    avg_amount         : float        # 전체 평균 송금액 (이동 평균)
    max_amount         : float        # 역대 최대 송금액
    tx_count_total     : int          # 총 거래 횟수
    hour_distribution  : {str: int}   # 시간대별 거래 횟수 {"0"~"23": n}
    dow_distribution   : {str: int}   # 요일별 거래 횟수 {"0"~"6": n}  (0=월)
    tx_count_daily_avg : float        # 일평균 거래 빈도
    tx_count_weekly_avg: float        # 주평균 거래 빈도
    receiver_counts    : {str: int}   # 수신 계좌번호별 거래 횟수
    frequent_receivers : [str]        # 빈도순 상위 MAX_RECEIVERS 수신 계좌
    first_tx_date      : datetime
    last_updated       : datetime
}
"""
from datetime import datetime, timezone
from typing import Optional

from database.mongodb import SyncCollections

_COL = SyncCollections.user_behavior_baselines
MAX_RECEIVERS = 20  # frequent_receivers 최대 보관 수


def get_baseline(user_id: int) -> Optional[dict]:
    return _COL.find_one({"user_id": user_id}, {"_id": 0})


def get_baseline_avg_amount(user_id: int) -> float:
    """AI 서버 fallback용: 30일 데이터 없는 신규 유저에게 전체 평균 송금액 반환."""
    doc = _COL.find_one({"user_id": user_id}, {"avg_amount": 1, "_id": 0})
    return float(doc["avg_amount"]) if doc else 0.0


def update_baseline(
    user_id: int,
    amount: float,
    hour_of_day: int,
    day_of_week: int,
    receiver_account: str,
    tx_date: datetime,
) -> None:
    """송금 완료 후 베이스라인 업데이트 (upsert). MongoDB 오류는 호출부에서 처리."""
    doc = get_baseline(user_id)
    now = datetime.now(timezone.utc)
    h_key = str(hour_of_day)
    d_key = str(day_of_week)

    if doc is None:
        # 신규 유저 — 첫 베이스라인 생성
        _COL.insert_one({
            "user_id": user_id,
            "avg_amount": amount,
            "max_amount": amount,
            "tx_count_total": 1,
            "hour_distribution": {h_key: 1},
            "dow_distribution": {d_key: 1},
            "tx_count_daily_avg": 1.0,
            "tx_count_weekly_avg": 1.0,
            "receiver_counts": {receiver_account: 1},
            "frequent_receivers": [receiver_account],
            "first_tx_date": tx_date,
            "last_updated": now,
        })
        return

    total = doc.get("tx_count_total", 0)
    new_total = total + 1

    # 이동 평균으로 avg_amount 업데이트
    new_avg = (doc.get("avg_amount", 0.0) * total + amount) / new_total
    new_max = max(doc.get("max_amount", 0.0), amount)

    # 시간대 분포
    h_dist = doc.get("hour_distribution", {})
    h_dist[h_key] = h_dist.get(h_key, 0) + 1

    # 요일 분포
    d_dist = doc.get("dow_distribution", {})
    d_dist[d_key] = d_dist.get(d_key, 0) + 1

    # 수신 계좌 빈도 — 빈도순 상위 MAX_RECEIVERS 유지
    recv_counts = doc.get("receiver_counts", {})
    recv_counts[receiver_account] = recv_counts.get(receiver_account, 0) + 1
    top_receivers = sorted(recv_counts, key=lambda k: recv_counts[k], reverse=True)[:MAX_RECEIVERS]

    # 첫 거래일 기준 일평균/주평균
    first_date = doc.get("first_tx_date", now)
    if isinstance(first_date, datetime) and first_date.tzinfo is None:
        first_date = first_date.replace(tzinfo=timezone.utc)
    days_elapsed = max(1, (now - first_date).days + 1)

    _COL.update_one(
        {"user_id": user_id},
        {"$set": {
            "avg_amount": round(new_avg, 2),
            "max_amount": round(new_max, 2),
            "tx_count_total": new_total,
            "hour_distribution": h_dist,
            "dow_distribution": d_dist,
            "tx_count_daily_avg": round(new_total / days_elapsed, 4),
            "tx_count_weekly_avg": round(new_total / max(1, days_elapsed / 7), 4),
            "receiver_counts": recv_counts,
            "frequent_receivers": top_receivers,
            "last_updated": now,
        }},
    )
