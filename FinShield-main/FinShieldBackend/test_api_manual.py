import httpx
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_flow():
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        print("\n1. 회원가입 테스트 (User A & User B)")
        
        # User A
        user_a_data = {
            "name": "User A",
            "email": "usera@test.com",
            "password": "password123",
            "age": 30,
            "phone": "010-1111-1111",
            "is_vulnerable": False
        }
        res_reg_a = client.post("/auth/register", json=user_a_data)
        print(f"User A Reg: {res_reg_a.status_code}")

        # User B
        user_b_data = {
            "name": "User B",
            "email": "userb@test.com",
            "password": "password123",
            "age": 70,
            "phone": "010-2222-2222",
            "is_vulnerable": True
        }
        res_reg_b = client.post("/auth/register", json=user_b_data)
        print(f"User B Reg: {res_reg_b.status_code}")

        print("\n2. 로그인 및 토큰 획득")
        # User A Login
        res_login_a = client.post("/auth/login", data={"username": "usera@test.com", "password": "password123"})
        token_a = res_login_a.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # User B Login
        res_login_b = client.post("/auth/login", data={"username": "userb@test.com", "password": "password123"})
        token_b = res_login_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}
        print("Tokens acquired.")

        print("\n3. 계좌 생성")
        # User A Account (100,000 KRW)
        acc_a_data = {
            "account_number": "111222333444",
            "bank_name": "TestBank",
            "account_name": "User A Main",
            "initial_balance": 100000
        }
        res_acc_a = client.post("/accounts/", json=acc_a_data, headers=headers_a)
        acc_a_id = res_acc_a.json()["id"]
        print(f"User A Account created: ID {acc_a_id}, Balance: {res_acc_a.json()['balance']}")

        # User B Account (0 KRW)
        acc_b_data = {
            "account_number": "555666777888",
            "bank_name": "TestBank",
            "account_name": "User B Main",
            "initial_balance": 0
        }
        res_acc_b = client.post("/accounts/", json=acc_b_data, headers=headers_b)
        acc_b_id = res_acc_b.json()["id"]
        print(f"User B Account created: ID {acc_b_id}, Balance: {res_acc_b.json()['balance']}")

        print("\n4. 이체 테스트 (User A -> User B: 30,000 KRW)")
        transfer_data = {
            "sender_account_id": acc_a_id,
            "receiver_account_id": acc_b_id,
            "amount": 30000,
            "memo": "Test Transfer"
        }
        res_transfer = client.post("/transactions/", json=transfer_data, headers=headers_a)
        print(f"Transfer status: {res_transfer.status_code}")
        print(f"Transfer result: {json.dumps(res_transfer.json(), indent=2, ensure_ascii=False)}")

        print("\n5. 잔액 확인")
        res_verify_a = client.get(f"/accounts/{acc_a_id}", headers=headers_a)
        res_verify_b = client.get(f"/accounts/{acc_b_id}", headers=headers_b)
        print(f"User A Balance: {res_verify_a.json()['balance']} (Expected: 70000)")
        print(f"User B Balance: {res_verify_b.json()['balance']} (Expected: 30000)")

        print("\n6. 거래 내역 조회")
        res_history = client.get("/transactions/me", headers=headers_a)
        print(f"User A Transaction History: {len(res_history.json())} items")
        for tx in res_history.json():
            print(f"- TX ID: {tx['id']}, Amount: {tx['amount']}, Status: {tx['status']}")

if __name__ == "__main__":
    try:
        test_flow()
    except Exception as e:
        print(f"Test failed: {e}")
        print("Make sure the FastAPI server is running (uvicorn main:app --reload)")
