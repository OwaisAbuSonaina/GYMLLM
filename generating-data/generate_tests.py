import asyncio
import json
import math
from pathlib import Path
from typing import Literal
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from dotenv import load_dotenv
load_dotenv(override=True)

# ==========================================
# 1. Schema Definition
# ==========================================

class TestQuestion(BaseModel):
    """A test question with expected keywords and reference answer."""
    question: str = Field(
        description="A realistic, standalone inquiry an HQ HR team member would ask."
    )
    keywords: list[str] = Field(
        description="3 to 6 unique, highly specific entity names, policy terms, dates, or technical tokens that MUST appear in the retrieved context to verify hit accuracy."
    )
    reference_answer: str = Field(
        description="A concise, factual, and complete answer derived strictly from the provided text chunk(s)."
    )
    category: Literal["direct_fact", "spanning", "temporal", "policy_procedural", "compliance_conflict"] = Field(
        description="Evaluation difficulty tier and reasoning category."
    )

class QuestionBatch(BaseModel):
    items: list[TestQuestion]

# ==========================================
# 2. Master System & User Prompts
# ==========================================

SYSTEM_PROMPT = """You are an expert MLOps Evaluation Engineer specializing in RAG benchmark synthesis for enterprise HR systems.

Your objective is to generate high-fidelity, leakage-free benchmark evaluation questions based STRICTLY on provided text chunks from an enterprise gym HR knowledge base.

Guidelines:
1. QUESTION REALISM: Frame inquiries as an HQ HR Specialist, Legal Auditor, or Payroll Manager would ask (e.g., specific to branch licenses, trainer certification renewal rules, equity vesting, commission caps, or disciplinary steps).
2. STANDALONE NATURE: Questions must NEVER refer to "the text", "the document", "the chunk", or "the provided markdown". They must read as real-world operational questions.
3. GROUNDED REFERENCE ANSWERS: Answers must be 100% faithful to the text chunk provided. Do NOT hallucinate external legal codes or fitness standards.
4. PRECISE KEYWORDS: Keywords are retrieval signals. Pick distinctive entity names, section headers, statutory numbers, or specialized roles directly present in the snippet that a retriever must score high on.
5. CATEGORIES:
   - direct_fact: Explicit single-hop lookups.
   - spanning: Synthesis requiring multiple facts within the context.
   - temporal: Inquiries involving duration, tenure, notice periods, shift timings, or effective dates.
   - policy_procedural: Step-by-step resolution, onboarding, or escalation processes.
   - compliance_conflict: Disciplinary, regulatory, contract conflict, or safety protocol enforcement.

CRITICAL DISTRIBUTION RULE:
Do NOT default to simple `direct_fact` questions just because a chunk contains structured data. You must actively extract complex scenarios to generate `spanning`, `policy_procedural`, and `compliance_conflict` questions."""

# ==========================================
# 3. Pipeline Core
# ==========================================

class RAGBenchmarkGenerator:
    def __init__(
        self,
        docs_dir: str = "knowledge_base",
        output_file: str = "tests/tests.jsonl",
        total_questions: int = 150,
        model: str = "gpt-4.1-mini",
        concurrency: int = 8,
    ):
        self.docs_dir = Path(docs_dir)
        self.output_file = Path(output_file)
        self.total_questions = total_questions
        self.model = model
        self.semaphore = asyncio.Semaphore(concurrency)
        self.client = AsyncOpenAI()

    def load_chunks(self) -> dict[str, list[dict]]:
        """Scans the directory structure and loads markdown files by category."""
        data_by_domain = {}
        for md_file in self.docs_dir.rglob("*.md"):
            domain = md_file.parent.name
            if domain not in data_by_domain:
                data_by_domain[domain] = []
            
            content = md_file.read_text(encoding="utf-8").strip()
            if len(content) > 100:
                data_by_domain[domain].append({
                    "file_name": md_file.name,
                    "content": content
                })
        return data_by_domain

    async def _generate_for_chunk(
        self,
        domain: str,
        chunk_text: str,
        num_questions: int
    ) -> list[TestQuestion]:
        """Prompts gpt-4.1-mini using structured parsing to produce validated questions."""
        user_prompt = f"""Target Domain: {domain}
Number of Questions to Generate: {num_questions}

Knowledge Base Context:
---
{chunk_text}
---

Generate {num_questions} varied, non-overlapping evaluation questions following the specified format. 

DISTRIBUTION REQUIREMENT FOR THIS BATCH:
- You MUST force a balanced mix of categories.
- Maximize the use of 'spanning', 'compliance_conflict', 'policy_procedural', and 'temporal'.
- Limit 'direct_fact' questions to an absolute maximum of 1 out of every 3 questions generated. If you are generating 1 or 2 questions, try to make 0 of them 'direct_fact' if the text allows for a more complex question."""

        async with self.semaphore:
            try:
                response = await self.client.beta.chat.completions.parse(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format=QuestionBatch,
                    temperature=0.4, # Slightly increased to encourage varied reasoning
                )
                return response.choices[0].message.parsed.items
            except Exception as e:
                print(f"[Error] Failed batch for domain '{domain}': {e}")
                return []

    async def run(self):
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        chunks_by_domain = self.load_chunks()

        if not chunks_by_domain:
            raise FileNotFoundError(f"No markdown documents found in '{self.docs_dir}'.")

        domains = list(chunks_by_domain.keys())
        base_per_domain = self.total_questions // len(domains)
        remainder = self.total_questions % len(domains)

        tasks = []
        for idx, (domain, items) in enumerate(chunks_by_domain.items()):
            domain_target = base_per_domain + (1 if idx < remainder else 0)
            if not items:
                continue

            # Generate 1 to 2 questions per selected document snippet
            questions_per_item = max(1, math.ceil(domain_target / len(items)))
            allocated = 0

            for doc in items:
                if allocated >= domain_target:
                    break
                k = min(questions_per_item, domain_target - allocated)
                tasks.append(self._generate_for_chunk(domain, doc["content"], k))
                allocated += k

        print(f"Scheduled {len(tasks)} generation tasks across {len(domains)} domains.")
        results = await asyncio.gather(*tasks)

        # Flatten, trim to exact total, and write to JSONL
        all_questions = [q for batch in results for q in batch][:self.total_questions]

        with open(self.output_file, "w", encoding="utf-8") as f:
            for q in all_questions:
                f.write(q.model_dump_json() + "\n")

        print(f"Done. Successfully generated {len(all_questions)} test cases in '{self.output_file}'.")

# ==========================================
# 4. Entrypoint
# ==========================================

if __name__ == "__main__":
    generator = RAGBenchmarkGenerator(
        docs_dir="../knowledge-base",  
        output_file="tests/tests.jsonl",
        total_questions=150,
        model="gpt-4.1-mini",
        concurrency=6
    )
    asyncio.run(generator.run())