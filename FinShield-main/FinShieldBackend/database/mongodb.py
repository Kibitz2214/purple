from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo import MongoClient
from pymongo.collection import Collection as SyncCollection
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

# ── 비동기 클라이언트 (async 라우터용) ──────────────────────────────
client = AsyncIOMotorClient(MONGO_URI)
db: AsyncIOMotorDatabase = client["finshield"]


def get_collection(name: str) -> AsyncIOMotorCollection:
    return db[name]


class Collections:
    user_behavior_logs: AsyncIOMotorCollection = db["user_behavior_logs"]
    transaction_logs: AsyncIOMotorCollection = db["transaction_logs"]
    fraud_patterns: AsyncIOMotorCollection = db["fraud_patterns"]
    conversation_logs: AsyncIOMotorCollection = db["conversation_logs"]
    notification_logs: AsyncIOMotorCollection = db["notification_logs"]
    blacklist_reports: AsyncIOMotorCollection = db["blacklist_reports"]


# ── 동기 클라이언트 (sync 엔드포인트용 — pymongo) ────────────────────
_sync_client = MongoClient(MONGO_URI)
_sync_db = _sync_client["finshield"]


class SyncCollections:
    user_behavior_baselines: SyncCollection = _sync_db["user_behavior_baselines"]


async def create_indexes():
    """컬렉션 인덱스 생성 (앱 시작 시 호출)"""
    # 동기 컬렉션 인덱스 (user_behavior_baselines)
    SyncCollections.user_behavior_baselines.create_index("user_id", unique=True, background=True)
    # 비동기 컬렉션 인덱스
    await Collections.user_behavior_logs.create_index([("user_id", 1), ("timestamp", -1)])
    await Collections.transaction_logs.create_index([("transaction_id", 1)], unique=True)
    await Collections.transaction_logs.create_index([("sender_id", 1), ("timestamp", -1)])
    await Collections.fraud_patterns.create_index([("pattern_type", 1)])
    await Collections.conversation_logs.create_index([("transaction_id", 1)])
    await Collections.conversation_logs.create_index([("user_id", 1), ("timestamp", -1)])
    await Collections.notification_logs.create_index([("user_id", 1), ("sent_at", -1)])
    await Collections.blacklist_reports.create_index([("reported_account", 1)])
    await Collections.blacklist_reports.create_index([("report_id", 1)], unique=True)
    print("MongoDB 인덱스 생성 완료!")


async def test_connection():
    try:
        await client.admin.command("ping")
        print("MongoDB 연결 성공!")
    except Exception as e:
        print(f"MongoDB 연결 실패: {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_connection())
