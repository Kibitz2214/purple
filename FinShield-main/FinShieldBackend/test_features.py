"""
통합 테스트: 참여형 블랙리스트 자동 검증 + 개인 행동 베이스라인
"""
import sys, time
sys.path.insert(0, ".")

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from main import app
from database.tidb import SessionLocal
from database.mongodb import SyncCollections

client = TestClient(app, raise_server_exceptions=False)
TS = str(int(time.time()))[-6:]

RESULTS = []

# ── 헬퍼 ─────────────────────────────────────────────────────────────

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
    return r.json()

def report(token, account_number, bank_name="사기은행", content="사기 신고"):
    return client.post("/api/v1/reports/", json={
        "account_number": account_number,
        "bank_name": bank_name,
        "content": content,
    }, headers=auth(token))

def transfer(token, sender_id, recv_num, amount):
    return client.post("/api/v1/transactions/", json={
        "sender_account_id": sender_id,
        "receiver_account_number": recv_num,
        "receiver_bank_name": "테스트은행",
        "amount": amount,
        "memo": "베이스라인 테스트",
    }, headers=auth(token))

def check_blacklist(account_number):
    r = client.get(f"/api/v1/blacklist/check/{account_number}")
    return r.json()

def get_notifications(token):
    r = client.get("/api/v1/notifications/", headers=auth(token))
    return r.json() if r.status_code == 200 else []

def promote_to_admin(email: str):
    """TiDB에서 직접 admin 권한 부여"""
    db: Session = SessionLocal()
    try:
        from models.user import User, UserRole
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.role = UserRole.ADMIN
            db.commit()
            return True
        return False
    finally:
        db.close()

def get_mongo_baseline(user_id: int):
    return SyncCollections.user_behavior_baselines.find_one(
        {"user_id": user_id}, {"_id": 0}
    )

def get_user_id(token):
    r = client.get("/api/v1/users/me", headers=auth(token))
    return r.json().get("id")

def ok(cond): return "[OK]" if cond else "[X]"
def result(name, passed): RESULTS.append((name, passed))

# ═══════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("TEST 1-1: 5회 신고 시 자동 블랙리스트 등록")
print("="*60)

TARGET_ACCOUNT = f"BL{TS}0001"
admin_email = f"admin_{TS}@test.com"
admin_token = reg_login(admin_email, "관리자", f"010-{TS[:4]}-9001")
promote_to_admin(admin_email)
# 재로그인으로 admin 토큰 갱신
admin_token = (client.post("/api/v1/auth/login",
    data={"username": admin_email, "password": "test1234"}).json()["access_token"])

notifs_before = len([n for n in get_notifications(admin_token)
                     if n["notification_type"] == "system"])

# 5명이 동일 계좌 신고
for i in range(5):
    t = reg_login(f"reporter{i}_{TS}@test.com", f"신고자{i}", f"010-{TS[:3]}{i}-{1000+i}")
    resp = report(t, TARGET_ACCOUNT)

# 블랙리스트 등록 확인
bl = check_blacklist(TARGET_ACCOUNT)
is_blacklisted = bl.get("is_blacklisted", False)
reason_ok = "자동등록" in bl.get("reason", "") if is_blacklisted else False

print(f"  블랙리스트 등록됨  : {ok(is_blacklisted)} ({bl.get('is_blacklisted')})")
print(f"  reason 포함 '자동등록': {ok(reason_ok)} ({bl.get('reason', 'N/A')})")

notifs_after = len([n for n in get_notifications(admin_token)
                    if n["notification_type"] == "system"])
admin_notif_ok = notifs_after > notifs_before
print(f"  관리자 system 알림  : {ok(admin_notif_ok)} ({notifs_before} → {notifs_after}개)")

p = is_blacklisted and reason_ok and admin_notif_ok
result("5회 신고 → 자동 블랙리스트 등록", p)
print(f"  → {'PASS' if p else 'FAIL'}")

# ═══════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("TEST 1-2: 6번째 신고 시 중복 등록 방지")
print("="*60)

extra_reporter = reg_login(f"reporter6_{TS}@test.com", "6번째신고자", f"010-{TS[:4]}-0099")
report(extra_reporter, TARGET_ACCOUNT)

# 블랙리스트 count가 1개인지 확인 (중복 등록 없어야 함)
bl_count_resp = client.get("/api/v1/blacklist/", headers=auth(admin_token))
bl_list = bl_count_resp.json() if bl_count_resp.status_code == 200 else []
normalized = TARGET_ACCOUNT.replace("-", "")
target_entries = [b for b in bl_list if b.get("account_number", "").replace("-", "") == normalized]

no_duplicate = len(target_entries) == 1
print(f"  블랙리스트 등록 수  : {ok(no_duplicate)} ({len(target_entries)}개, 1개여야 함)")

# 관리자 알림도 중복 발송 안 됐는지 확인
notifs_after2 = len([n for n in get_notifications(admin_token)
                     if n["notification_type"] == "system"])
no_extra_notif = notifs_after2 == notifs_after
print(f"  관리자 알림 중복 없음: {ok(no_extra_notif)} ({notifs_after} → {notifs_after2}개)")

p = no_duplicate and no_extra_notif
result("6번째 신고 → 중복 등록 방지", p)
print(f"  → {'PASS' if p else 'FAIL'}")

# ═══════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("TEST 2-1: 신규 유저 첫 송금 → 베이스라인 생성")
print("="*60)

new_token  = reg_login(f"baseline_new_{TS}@test.com", "신규유저", f"010-{TS[:4]}-2001")
recv_token = reg_login(f"baseline_recv_{TS}@test.com", "수신자",   f"010-{TS[:4]}-2002")
new_uid    = get_user_id(new_token)

new_acc  = mkaccount(new_token,  f"BL{TS}NEW1", 1000000)
recv_acc = mkaccount(recv_token, f"BL{TS}RCV1", 100000)
sender_id   = new_acc.get("id")
recv_number = recv_acc.get("account_number")

# 베이스라인 없는 상태에서 송금 (신규 유저)
before_baseline = get_mongo_baseline(new_uid)
tx_resp = transfer(new_token, sender_id, recv_number, 50000)
tx_ok = tx_resp.json().get("status") in ("completed", "flagged", "blocked")

after_baseline = get_mongo_baseline(new_uid)
baseline_created = after_baseline is not None

print(f"  신규 유저 송금 성공  : {ok(tx_ok)} (status={tx_resp.json().get('status')})")
print(f"  베이스라인 생성됨    : {ok(baseline_created)}")
if after_baseline:
    print(f"    avg_amount   = {after_baseline.get('avg_amount')}")
    print(f"    max_amount   = {after_baseline.get('max_amount')}")
    print(f"    tx_count     = {after_baseline.get('tx_count_total')}")
    print(f"    frequent_recv= {after_baseline.get('frequent_receivers')}")

p = tx_ok and baseline_created
result("신규 유저 첫 송금 → 베이스라인 생성", p)
print(f"  → {'PASS' if p else 'FAIL'}")

# ═══════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("TEST 2-2: 여러 번 송금 → avg_amount 이동 평균 갱신")
print("="*60)

EXTRA_AMOUNTS = [30000, 20000]  # TEST 2-1에서 50000 이미 송금됨

for amt in EXTRA_AMOUNTS:
    transfer(new_token, sender_id, recv_number, amt)

# 실제 송금 내역: [50000, 30000, 20000] → 총 3건, 평균 33333.3
all_amounts  = [50000] + EXTRA_AMOUNTS
expected_avg   = sum(all_amounts) / len(all_amounts)
expected_count = len(all_amounts)

final_baseline = get_mongo_baseline(new_uid)
if final_baseline:
    actual_avg   = final_baseline.get("avg_amount", 0)
    actual_count = final_baseline.get("tx_count_total", 0)
    avg_ok   = abs(actual_avg - expected_avg) < 1
    count_ok = actual_count == expected_count

    h_dist = final_baseline.get("hour_distribution", {})
    d_dist = final_baseline.get("dow_distribution", {})

    print(f"  총 거래 수       : {ok(count_ok)} ({actual_count}건, {expected_count}건 기대)")
    print(f"  avg_amount       : {ok(avg_ok)} (실제={actual_avg:.1f}, 기대={expected_avg:.1f})")
    print(f"  hour_distribution: {ok(len(h_dist) > 0)} ({h_dist})")
    print(f"  dow_distribution : {ok(len(d_dist) > 0)} ({d_dist})")
    print(f"  frequent_receivers: {final_baseline.get('frequent_receivers')}")
    p = avg_ok and count_ok
else:
    print("  베이스라인 없음 [X]")
    p = False

result("여러 번 송금 → avg_amount 이동 평균 갱신", p)
print(f"  → {'PASS' if p else 'FAIL'}")

# ═══════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("최종 결과")
print("="*60)
print(f"  {'테스트':<35} {'결과'}")
print(f"  {'-'*50}")
for name, passed in RESULTS:
    print(f"  {name:<35} {'PASS' if passed else 'FAIL'}")
total = sum(1 for _, p in RESULTS if p)
print(f"\n  {total}/{len(RESULTS)} 통과")
