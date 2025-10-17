from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI(title='CulinAIry Agentic API')

class MealRequest(BaseModel):
    meals_per_day: int
    days: int
    preferences: List[str] = []

@app.post("/plan-meals")
def plan_meals(request: MealRequest):
    # Retrieve NIN LLM
    return{
        "message" : "This is a placeholder plan",
        "meals_per_day": request.meals_per_day,
        "days" : request.days,
        "preferences" : request.preferences
    }

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)