import google.generativeai as genai
from .config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

PROMPT_TEMPLATE = """You are an expert academic English writing coach. Evaluate the following user-submitted PEEL paragraph.

[User Submission]
- Point (主張): {point}
- Explanation (解釋): {explanation}
- Example (舉例): {example}
- Link (結論與連結): {link}

[Evaluation Rules]
Please generate a structured report in Traditional Chinese (繁體中文) containing:
1. 🏆 **架構完整度評分 (1-10分)**：
   - 評估各要素是否合格（Point 是否明確、Explanation 是否充分、Example 是否具體且相關、Link 是否扣回主張）。
2. ✍️ **文法與用詞修正 (Grammar & Polish)**：
   - 列出原句中的文法錯誤與更道地、學術化的用詞建議。
3. 🚀 **最佳化重寫版本 (Polished Paragraph)**：
   - 將四部分無縫融合為一篇自然流暢、高水準的英文短文。
"""

async def review_peel_writing(point: str, explanation: str, example: str, link: str) -> str:
    try:
        prompt = PROMPT_TEMPLATE.format(
            point=point,
            explanation=explanation,
            example=example,
            link=link
        )
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ 審核過程中發生錯誤，請稍後再試。\n詳細錯誤：{str(e)}"
