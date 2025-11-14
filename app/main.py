import logging
from fastapi import FastAPI
from app.routes import predict, recommend, simulation, insight_loan
from dotenv import load_dotenv

# .env 불러오기
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("app")
logger.info("AI API Server 로딩 중")

app = FastAPI(title="AI Risk API", version="1.0")

# 라우터 등록
app.include_router(predict.router, prefix="/api/ai", tags=["Risk Prediction"])
app.include_router(recommend.router, prefix="/api/ai", tags=["Spending Recommendation"])
app.include_router(simulation.router, prefix="/api/ai", tags=["Simulation Risk"])
app.include_router(insight_loan.router, prefix="/api/ai", tags=["Loan Insight"])

@app.get("/")
def root():
    return {"message": "AI API Server Running"}
