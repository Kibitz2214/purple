from pydantic import Field
from datetime import datetime, timezone
from typing import Dict, List, Optional
from schemas.mongo_base import MongoBase


class DeviceInfo(MongoBase):
    """접속 기기 정보"""
    os: Optional[str] = None
    device_type: Optional[str] = None      # mobile / pc / tablet
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class LocationInfo(MongoBase):
    """접속 위치 정보"""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    region: Optional[str] = None           # 지역명 (서울, 경기 등)


class UserBehaviorLog(MongoBase):
    """
    user_behavior_logs 컬렉션
    사용자의 앱 내 행동 패턴 로그 (로그인, 송금 시도 등)
    AI 이상 거래 탐지 학습 데이터로 활용
    """
    user_id: int                            # users.id FK
    action_type: str                        # login / transfer_attempt / report / guardian_request 등
    device_info: Optional[DeviceInfo] = None
    location: Optional[LocationInfo] = None
    extra: Optional[dict] = Field(default=None)   # 액션별 추가 데이터
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserBaseline(MongoBase):
    """
    user_behavior_baselines 컬렉션
    사용자별 거래 행동 베이스라인 — AI 이상 탐지 기준값으로 활용
    """
    user_id: int
    avg_amount: float = 0.0                         # 전체 평균 송금액 (이동 평균)
    max_amount: float = 0.0                         # 역대 최대 송금액
    tx_count_total: int = 0                         # 총 거래 횟수
    hour_distribution: Dict[str, int] = Field(default_factory=dict)   # {"0"~"23": count}
    dow_distribution: Dict[str, int] = Field(default_factory=dict)    # {"0"~"6": count} (0=월)
    tx_count_daily_avg: float = 0.0                 # 일평균 거래 빈도
    tx_count_weekly_avg: float = 0.0                # 주평균 거래 빈도
    receiver_counts: Dict[str, int] = Field(default_factory=dict)     # {계좌번호: 거래수}
    frequent_receivers: List[str] = Field(default_factory=list)       # 빈도순 상위 수신 계좌
    first_tx_date: Optional[datetime] = None
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserBehaviorLogCreate(MongoBase):
    """생성용 스키마 (id 제외)"""
    user_id: int
    action_type: str
    device_info: Optional[DeviceInfo] = None
    location: Optional[LocationInfo] = None
    extra: Optional[dict] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
