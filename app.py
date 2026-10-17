from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict

from implementation.answer import answer_question

app = FastAPI(title="GYMLLM API")

class HRRequest(BaseModel):
    hr_question: str
    history: List[Dict[str, str]] = []

@app.post("/GYMLLM")
async def gymllm_answer(request: HRRequest):
    async def generate():
        try:
            async for token in answer_question(
                question=request.hr_question,
                history=request.history
            ):
                yield token
                
        except Exception as e:
            yield f"Error: {str(e)}"

    return StreamingResponse(generate(), media_type="text/event-stream")