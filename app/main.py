from fastapi import FastAPI
from app.routes import predict, recommend, simulation, insight_loan, insight_spending

app = FastAPI(title="AI Risk API", version="1.0")

# 라우터 등록
app.include_router(predict.router, prefix="/api/ai", tags=["Risk Prediction"])
app.include_router(recommend.router, prefix="/api/ai", tags=["Spending Recommendation"])
app.include_router(simulation.router, prefix="/api/ai", tags=["Simulation Risk"])
app.include_router(insight_loan.router, prefix="/api/ai", tags=["Loan Insight"])
app.include_router(insight_spending.router, prefix="/api/ai", tags=["Spending Insight"])

@app.get("/")
def root():
    return {"message": "AI API Server Running"}
