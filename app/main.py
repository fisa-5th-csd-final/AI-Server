import logging
import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from app.routes import predict, recommend, simulation, insight_loan
from app.services.kafka.kafka_consumer import start_kafka_consumer
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from app.services.feature.update_feature import update_features_daily

# .env 불러오기
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("app")
logger.info("AI API Server 로딩 중")

# Lifespan 이벤트 핸들러
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 시작
    logger.info("Kafka Consumer 백그라운드 태스크 실행")
    consumer_task = asyncio.create_task(start_kafka_consumer())

    # FastAPI가 실행되도록 yield
    yield

    # 서버 종료
    logger.info("서버 종료: Kafka Consumer 종료 요청")
    consumer_task.cancel()

app = FastAPI(title="AI Risk API", version="1.0", lifespan=lifespan)

# 라우터 등록
app.include_router(predict.router, prefix="/api/ai", tags=["Risk Prediction"])
app.include_router(recommend.router, prefix="/api/ai", tags=["Spending Recommendation"])
app.include_router(simulation.router, prefix="/api/ai", tags=["Simulation Risk"])
app.include_router(insight_loan.router, prefix="/api/ai", tags=["Loan Insight"])

@app.get("/")
def root():
    return {"message": "AI API Server Running"}
