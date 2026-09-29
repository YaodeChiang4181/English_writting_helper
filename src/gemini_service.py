from google import genai
from .config import GEMINI_API_KEY
import asyncio

client = genai.Client(api_key=GEMINI_API_KEY)

BATCH_PROMPT_TEMPLATE = """You are a distinguished professor and academic evaluator at a top-tier research university in Taiwan, specializing in graduate admissions. Your mission is to evaluate, grade, and refine students' academic essays written for graduate entrance examinations.

When guiding, generating, or evaluating essays based on provided academic reading materials, strictly adhere to the following evaluation criteria and structural constraints:

---

### 1. Core Evaluation Dimensions (Grading Rubric)

1. **Literature Synthesis & Source Attribution (30%)**
   - **No Isolated Opinions:** The author must synthesize arguments using evidence from ALL provided texts (e.g., empirical findings, theoretical mechanisms) rather than relying on unsubstantiated personal assertions.
   - **Academic Citation Style:** Ensure seamless in-text attributions (e.g., "As Brynjolfsson et al. (2025) demonstrate...", "Extending attribution theory (Reif et al., 2025)...").

2. **Argumentative Rigor & Nuance (30%)**
   - **Definitive Thesis Statement:** The introduction must establish an unambiguous stance answering the core prompt.
   - **Mandatory Counter-Argument & Refutation:** The essay must include at least one robust, non-trivial opposing viewpoint grounded in the literature, followed by a persuasive refutation (e.g., distinguishing short-term friction from long-term equilibrium, or demonstrating conditional boundary conditions).
   - **Theoretical Depth:** Prioritize structural mechanisms (e.g., human capital accumulation, signaling, complementary friction, attribution bias) over surface-level descriptions.

3. **Academic Lexicon & Register (20%)**
   - **Tone:** Maintain a formal, objective, scholarly register. Strictly ban colloquialisms (e.g., "kids", "stuff", "a lot of"), contractions ("don't", "can't"), and overly emotive rhetoric.
   - **Precision & Hedging:** Reward precise disciplinary terminology and calibrated hedging language (e.g., "tends to indicate", "under specific institutional constraints", "serves as a catalyst").

4. **Coherence & Structural Progression (20%)**
   - **Standard Scaffolding:** 4 to 5 paragraphs (Introduction with Thesis -> Body Paragraph 1 [Core Mechanism] -> Body Paragraph 2 [Complementary Evidence] -> Body Paragraph 3 [Counterargument & Refutation] -> Conclusion [Restatement & Synthesis]).
   - **Word Count Discipline:** Enforce strict adherence to examination word limits (typically 350–500 words for exam essays, or within the specified prompt range).

---

### 2. Output Formatting & Action Guidelines

When reviewing a student's submission:
1. **Diagnostic Score Breakdown:** Provide scores (0–100 or letter grade) across the four dimensions above.
2. **Structural & Logical Audit:** Pinpoint logical gaps, weak topic sentences, or superficial synthesis.
3. **Lexical & Syntactic Upgrades:** Highlight informal phrasing and offer 3–5 high-impact academic sentence upgrades using advanced syntactic structures (e.g., participial phrases, inversion, nominalization).
4. **Exemplary Revision:** Provide a revised model paragraph illustrating how to elevate the student's raw draft into publication/admission-ready academic prose.

IMPORTANT: You will receive a batch of {batch_size} submissions. You MUST evaluate EACH submission individually.
Separate each evaluation strictly with the exact string "===REVIEW_SEPARATOR===".
Do not add any text before the first evaluation or after the last evaluation. The output should be just the evaluations separated by "===REVIEW_SEPARATOR===".

Here are the submissions:

{submissions_text}
"""

async def review_peel_writing_batch(submissions: list[dict]) -> list[str]:
    if not submissions:
        return []
        
    submissions_text = ""
    for i, sub in enumerate(submissions, 1):
        submissions_text += f"[Submission {i}]\n"
        submissions_text += f"- Point (主張): {sub.get('point', '')}\n"
        submissions_text += f"- Explanation (解釋): {sub.get('explanation', '')}\n"
        submissions_text += f"- Example (舉例): {sub.get('example', '')}\n"
        submissions_text += f"- Link (結論與連結): {sub.get('link', '')}\n\n"
        
    prompt = BATCH_PROMPT_TEMPLATE.format(
        batch_size=len(submissions),
        submissions_text=submissions_text
    )
    
    max_retries = 5
    base_delay = 5  # seconds
    
    models_to_try = [
        "gemini-3.7-flash",
        "gemini-3.8-flash",
        "gemini-3.5-flash",
        "gemini-2.5-flash",
        "gemini-flash-latest",
        "gemini-3.6-flash"
    ]
    
    for attempt in range(max_retries):
        last_exception = None
        for model_name in models_to_try:
            try:
                response = await asyncio.wait_for(
                    client.aio.models.generate_content(
                        model=model_name,
                        contents=prompt
                    ),
                    timeout=120.0
                )
                
                reports = response.text.split("===REVIEW_SEPARATOR===")
                reports = [r.strip() for r in reports if r.strip()]
                
                while len(reports) < len(submissions):
                    reports.append("⚠️ AI 審核過程中遺漏了這筆回應，請稍後再試。")
                    
                return reports[:len(submissions)]
                
            except asyncio.TimeoutError as e:
                last_exception = e
                continue
            except Exception as e:
                last_exception = e
                continue
        
        if attempt == max_retries - 1:
            if isinstance(last_exception, asyncio.TimeoutError):
                return ["⚠️ AI 教練思考時間過長 (超過 120 秒)，請稍後再試。"] * len(submissions)
            else:
                return [f"⚠️ 審核過程中發生錯誤，請稍後再試。\n詳細錯誤：{str(last_exception)}"] * len(submissions)
        
        # Exponential backoff before retrying all models again
        await asyncio.sleep(base_delay * (2 ** attempt))

async def review_peel_writing(point: str, explanation: str, example: str, link: str) -> str:
    res = await review_peel_writing_batch([
        {'point': point, 'explanation': explanation, 'example': example, 'link': link}
    ])
    return res[0]
