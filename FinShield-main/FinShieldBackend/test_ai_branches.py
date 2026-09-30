"""
AI 분기 테스트: warn / guardian_approval / block
call_ai_server를 mock으로 교체해 각 구간의 fraud_probability를 강제 설정
"""
import sys, time
sys.path.insert(0, ".")

from unittest.mock import patch
from fastapi.testclient import TestClient
from core.ai_client import FraudResponse
from main import app

TS = str(int(time.time()))[-6:]  # 충돌 방지용 고유 접미사

client = TestClient(app, raise_server_exceptions=False)

# ─────────── 헬퍼 ───────────

def reg_login(email, name, phone):
    client.post("/api/v1/auth/register", json={
        "name": name, "email": email, "password": "test1234",
        "age": 30, "phone": phone, "is_vulnerable": False,
    })
    r = client.post("/api/v1/auth/login",
                    data={"username": email, "password": "test1234"})
    return r.json()["access_token"]

def auth(token):
    return {"Authorization": f"Bearer {token}"}

def mkaccount(token, number, balance=500000):
    r = client.post("/api/v1/accounts/", json={
        "account_number": number, "bank_name": "테스트은행",
        "account_name": "테스트통장", "initial_balance": balance,
    }, headers=auth(token))
    return r.json()["id"]

def transfer(token, sender_id, recv_num, amount=50000):
    return client.post("/api/v1/transactions/", json={
        "sender_account_id": sender_id,
        "receiver_account_number": recv_num,
        "receiver_bank_name": "테스트은행",
        "amount": amount,
        "memo": "AI 분기 테스트",
    }, headers=auth(token))

def notifs(token):
    r = client.get("/api/v1/notifications/", headers=auth(token))
    return r.json()

def notif_types(token):
    return [n["notification_type"] for n in notifs(token)]

def mock_ai(rec, prob):
    return FraudResponse(
        transaction_id=0,
        fraud_probability=prob,
        is_fraud=prob >= 0.5,
        risk_level="low" if prob < 0.3 else "medium" if prob < 0.5 else "high" if prob < 0.8 else "critical",
        top_reasons=["테스트 사유"],
        recommendation=rec,
    )

# ─────────── 공통 수신자 세팅 ───────────
RECV_EMAIL  = f"branch_recv_{TS}@test.com"
RECV_PHONE  = f"010-{TS[:4]}-0001"
RECV_ACCNUM = f"9{TS}-0001"

recv_token = reg_login(RECV_EMAIL, "수신자", RECV_PHONE)
mkaccount(recv_token, RECV_ACCNUM, 100000)

results = []

# ═══════════════════════════════════════════
# CASE 1: warn (0.3 ≤ prob < 0.5)
# 기대: status=completed, risk_alert 알림 생성
# ═══════════════════════════════════════════
print("\n" + "="*55)
print("CASE 1: warn (fraud_probability=0.40)")
print("="*55)

warn_token = reg_login(f"warn_{TS}@test.com", "경고테스트", f"010-{TS[:4]}-0002")
warn_acc   = mkaccount(warn_token, f"9{TS}-0002")
notifs_before = notif_types(warn_token)

with patch("routers.transactions.call_ai_server", return_value=mock_ai("warn", 0.40)):
    resp = transfer(warn_token, warn_acc, RECV_ACCNUM)

tx = resp.json()
notifs_after = notif_types(warn_token)
new_notifs   = [n for n in notifs_after if n not in notifs_before]

status_ok = tx.get("status") == "completed"
alert_ok  = "risk_alert" in new_notifs

print(f"  거래 status  : {tx.get('status')} → {'completed [OK]' if status_ok else 'FAIL [X]'}")
print(f"  risk_alert  : {'있음 [OK]' if alert_ok else '없음 [X]'}")
print(f"  새 알림 목록 : {new_notifs}")

case1_pass = status_ok and alert_ok
results.append(("warn", case1_pass))
print(f"  → {'PASS PASS' if case1_pass else 'FAIL FAIL'}")

# ═══════════════════════════════════════════
# CASE 2: guardian_approval (0.5 ≤ prob < 0.8)
# 기대: status=flagged, 보호자에게 guardian_request 알림
# ═══════════════════════════════════════════
print("\n" + "="*55)
print("CASE 2: guardian_approval (fraud_probability=0.65)")
print("="*55)

ward_token = reg_login(f"ward_{TS}@test.com",     "피보호자",  f"010-{TS[:4]}-0003")
grd_token  = reg_login(f"guardian_{TS}@test.com", "보호자",    f"010-{TS[:4]}-0004")
ward_acc   = mkaccount(ward_token, f"9{TS}-0003")

# 보호자 user_id 조회
grd_me = client.get("/api/v1/users/me", headers=auth(grd_token)).json()
grd_id = grd_me["id"]

# 보호자 등록 요청 → 보호자가 승인
req = client.post("/api/v1/guardians/request",
                  json={"guardian_id": grd_id}, headers=auth(ward_token))
link_id = req.json().get("id")

if link_id:
    client.patch(f"/api/v1/guardians/{link_id}/approve", headers=auth(grd_token))
    print(f"  보호자 설정 완료 (link_id={link_id}, guardian_id={grd_id})")
else:
    print(f"  보호자 설정 실패: {req.json()}")

notifs_before_grd = notif_types(grd_token)

with patch("routers.transactions.call_ai_server",
           return_value=mock_ai("guardian_approval", 0.65)):
    resp = transfer(ward_token, ward_acc, RECV_ACCNUM)

tx = resp.json()
notifs_ward = notif_types(ward_token)
notifs_grd_after = notif_types(grd_token)
new_grd_notifs = [n for n in notifs_grd_after if n not in notifs_before_grd]

status_ok = tx.get("status") == "flagged"
alert_ok  = "risk_alert" in notifs_ward
grd_ok    = "guardian_request" in new_grd_notifs

print(f"  거래 status        : {tx.get('status')} → {'flagged [OK]' if status_ok else 'FAIL [X]'}")
print(f"  ward risk_alert    : {'있음 [OK]' if alert_ok else '없음 [X]'}")
print(f"  보호자 guardian_req: {'있음 [OK]' if grd_ok else '없음 [X]'}")
print(f"  보호자 새 알림     : {new_grd_notifs}")

case2_pass = status_ok and alert_ok and grd_ok
results.append(("guardian_approval", case2_pass))
print(f"  → {'PASS PASS' if case2_pass else 'FAIL FAIL'}")

# ═══════════════════════════════════════════
# CASE 3: block (prob ≥ 0.8)
# 기대: status=blocked, risk_alert 알림 생성
# ═══════════════════════════════════════════
print("\n" + "="*55)
print("CASE 3: block (fraud_probability=0.90)")
print("="*55)

block_token = reg_login(f"block_{TS}@test.com", "차단테스트", f"010-{TS[:4]}-0005")
block_acc   = mkaccount(block_token, f"9{TS}-0005")
notifs_before = notif_types(block_token)

with patch("routers.transactions.call_ai_server", return_value=mock_ai("block", 0.90)):
    resp = transfer(block_token, block_acc, RECV_ACCNUM)

tx = resp.json()
notifs_after = notif_types(block_token)
new_notifs   = [n for n in notifs_after if n not in notifs_before]

status_ok = tx.get("status") == "blocked"
alert_ok  = "risk_alert" in new_notifs

print(f"  거래 status  : {tx.get('status')} → {'blocked [OK]' if status_ok else 'FAIL [X]'}")
print(f"  risk_alert  : {'있음 [OK]' if alert_ok else '없음 [X]'}")
print(f"  새 알림 목록 : {new_notifs}")

case3_pass = status_ok and alert_ok
results.append(("block", case3_pass))
print(f"  → {'PASS PASS' if case3_pass else 'FAIL FAIL'}")

# ═══════════════════════════════════════════
# 결과 요약
# ═══════════════════════════════════════════
print("\n" + "="*55)
print("최종 결과")
print("="*55)
print(f"  {'케이스':<22} {'결과'}")
print(f"  {'-'*40}")
for name, passed in results:
    mark = "PASS PASS" if passed else "FAIL FAIL"
    print(f"  {name:<22} {mark}")
total = sum(1 for _, p in results if p)
print(f"\n  {total}/{len(results)} 통과")

