from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os 
from typing import List, Dict

from implementation.answer import answer_question


app = FastAPI(title="GYMLLM API")

class HRRequest(BaseModel):
    hr_question: str
    history: List[Dict[str, str]] = []

class GYMLLMResponse(BaseModel):
    GYM_LLM_Response: str


@app.post("/GYMLLM", response_model=GYMLLMResponse)
async def gymllm_answer(request: HRRequest):

    try:
        response, _ = await answer_question(
            question=request.hr_question,
            history=request.history
        )
        return GYMLLMResponse(GYM_LLM_Response=response)

    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM/Retrieval pipeline error: {str(e)}")
    