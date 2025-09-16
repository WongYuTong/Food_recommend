from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from content_analyzer.analyze_restaurant_indicators import analyze_restaurant_indicators
from content_analyzer.analyze_user_preferences import analyze_user_preferences

app = FastAPI()

class PostData(BaseModel):
    post_id: int
    content: str
    user_id: int
    place_id: str

@app.post("/analyze/restaurant/")
def analyze_restaurant(data: PostData):
    result = analyze_restaurant_indicators(data.content, data.place_id)
    return {"status": "success", "data": result}

@app.post("/analyze/user/")
def analyze_user(data: PostData):
    result = analyze_user_preferences(data.content, data.user_id)
    return {"status": "success", "data": result}