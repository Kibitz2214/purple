import httpx
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_report_flow():
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        print("\n1. 테스트 유저 로그인")
        # 테스트를 위해 매번 새로운 유저를 생성하거나 기존 유저 사용
        user_data = {
            "name": "Reporter User",
            "email": "reporter@test.com",
            "password": "password123",
            "age": 35,
            "phone": "010-9999-8888",
            "is_vulnerable": False
        }
        client.post("/auth/register", json=user_data)
        
        login_res = client.post("/auth/login", data={"username": "reporter@test.com", "password": "password123"})
        if login_res.status_code != 200:
            print("Login failed. Make sure the server is running.")
            return

        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Login successful.")

        print("\n2. 사기 거래 신고 생성")
        report_data = {
            "reported_account": "123-456-7890",
            "content": "이 계좌는 중고거래 사기에 이용된 계좌입니다. 조치 부탁드립니다."
        }
        res_create = client.post("/reports/", json=report_data, headers=headers)
        print(f"Create Report: {res_create.status_code}")
        report_id = res_create.json()["id"]
        print(f"Report ID: {report_id}")

        print("\n3. 신고 내역 목록 조회")
        res_list = client.get("/reports/", headers=headers)
        print(f"List Reports: {res_list.status_code}, Count: {len(res_list.json())}")
        
        print("\n4. 신고 상세 정보 및 처리 결과 조회")
        res_detail = client.get(f"/reports/{report_id}", headers=headers)
        print(f"Report Detail: {res_detail.status_code}")
        detail = res_detail.json()
        print(f" - Status: {detail['status']}")
        print(f" - Content: {detail['content']}")
        print(f" - Admin Note: {detail.get('admin_note') or 'No note yet'}")

        print("\n5. 신고 철회 테스트")
        res_withdraw = client.delete(f"/reports/{report_id}", headers=headers)
        print(f"Withdraw Report: {res_withdraw.status_code}")
        print(f"Response: {res_withdraw.json().get('detail')}")

        print("\n6. 철회 후 조회 (404 예상)")
        res_after = client.get(f"/reports/{report_id}", headers=headers)
        print(f"Get after withdraw: {res_after.status_code} (Expected 404)")

if __name__ == "__main__":
    try:
        test_report_flow()
    except Exception as e:
        print(f"Test failed: {e}")
