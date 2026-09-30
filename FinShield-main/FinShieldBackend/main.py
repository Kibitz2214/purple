from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse

from database.tidb import create_tables, run_migrations, test_connection as tidb_test
from database.mongodb import create_indexes, test_connection as mongo_test
from routers import auth, users, accounts, transactions, risk, reports, blacklist, guardians, notifications, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- 시작 ---
    print("=== FinShield 서버 시작 ===")

    # TiDB 연결 확인 및 테이블 생성
    tidb_test()
    create_tables()
    run_migrations()

    # MongoDB 연결 확인 및 인덱스 생성
    await mongo_test()
    await create_indexes()

    yield

    # --- 종료 ---
    print("=== FinShield 서버 종료 ===")


app = FastAPI(
    title="FinShield API",
    description="AI 기반 금융사기 예방 시스템 - 금융 취약계층을 위한 지능형 사전 예방 서비스",
    version="0.1.0",
    lifespan=lifespan,
    docs_url=None,  # 커스텀 /docs로 대체
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # 프론트 개발 서버
        "http://localhost:5173",   # Vite 개발 서버
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth.router,          prefix="/api/v1")
app.include_router(users.router,         prefix="/api/v1")
app.include_router(accounts.router,      prefix="/api/v1")
app.include_router(transactions.router,  prefix="/api/v1")
app.include_router(risk.router,          prefix="/api/v1")
app.include_router(reports.router,       prefix="/api/v1")
app.include_router(blacklist.router,     prefix="/api/v1")
app.include_router(guardians.router,     prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(admin.router,         prefix="/api/v1")


_OAUTH2_EMAIL_PATCH = """
<script>
  document.addEventListener("DOMContentLoaded", function () {
    new MutationObserver(function () {
      const label = document.querySelector('label[for="oauth_username"]');
      if (label) label.childNodes[0].textContent = "email (required)\\n";

      const input = document.querySelector("#oauth_username");
      if (input && !input.dataset.patched) {
        input.placeholder = "user@example.com";
        input.dataset.patched = "true";
      }
    }).observe(document.body, { childList: true, subtree: true });
  });
</script>
"""


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    html = get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title,
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
    )
    content = html.body.decode("utf-8").replace("</body>", _OAUTH2_EMAIL_PATCH + "</body>")
    return HTMLResponse(content=content)


@app.get("/", tags=["health"])
async def root():
    return {"service": "FinShield API", "status": "ok", "version": "0.1.0"}


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
