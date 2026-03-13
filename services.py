import re
import base64
from google import genai
from openai import OpenAI
from google.genai import types as GTypes

class AIService:
    def __init__(self, fpt_key, fpt_url, gemini_key, gemini_model):
        self.client_fpt = OpenAI(api_key=fpt_key, base_url=fpt_url)
        self.gemini_client = genai.Client(api_key=gemini_key)
        self.gemini_model = gemini_model

    def clean_ocr_text(self, text):
        if not text: return ""
        lines = [line.strip() for line in text.split('\n')]
        cleaned_text = ""
        for i in range(len(lines)):
            line = lines[i]
            if not line:
                cleaned_text += "\n\n"
                continue
            cleaned_text += line
            if i < len(lines) - 1 and lines[i+1]:
                if not line.endswith(('.', '!', '?', ':', ';', ']', ')')):
                    cleaned_text += " "
                else:
                    cleaned_text += "\n" 
        return re.sub(r' +', ' ', cleaned_text).strip()

    def process_ocr(self, image_path):
        with open(image_path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode("utf-8")
        
        resp = self.client_fpt.chat.completions.create(
            model="DeepSeek-OCR",
            messages=[{"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                {"type": "text", "text": "Free OCR."}
            ]}]
        )
        return self.clean_ocr_text(resp.choices[0].message.content)

    # def translate(self, text):
    #     try:
    #         # Prompt tối ưu để loại bỏ phần "giải thích" thừa thãi
    #         prompt = (
    #             "Bạn là chuyên gia dịch thuật game chuyên nghiệp. Nhiệm vụ của bạn:\n"
    #             "1. Ghép các từ bị tách rời (ví dụ 'Di spels' thành 'Dispels').\n"
    #             "2. Dịch sang tiếng Việt văn chương, mượt mà.\n"
    #             "CHỈ TRẢ VỀ KẾT QUẢ DỊCH. Tuyệt đối không chào hỏi, không phân tích, không giải thích gì thêm.\n\n"
    #             f"Văn bản: {text}"
    #         )
    #         response = self.gemini_client.models.generate_content(model=self.gemini_model, contents=prompt)
    #         return response.text.strip()
    #     except Exception as e:
    #         return f"\n[Lỗi Gemini: {str(e)}]"
    def get_config(self): 
        return GTypes.GenerateContentConfig(
            temperature=0.3,
            top_p=0.8,
            max_output_tokens=1024,
        )
    def translate_stream(self, text):
        """Hàm này trả về một generator để app ui có thể lặp qua từng từ"""
        try:
            prompt = (
                f"dịch đoạn văn bản sau {text} sang tiếng Việt, chỉ trả về kết quả dịch, không giải thích gì thêm."
            )
            
            # Sử dụng stream để nhận kết quả từng phần
            response_stream = self.gemini_client.models.generate_content_stream(
                model=self.gemini_model,
                contents=prompt,
                config=self.get_config() # Tách config ra hàm riêng hoặc truyền vào
            )
            return response_stream
        except Exception as e:
            print(f"Lỗi Stream: {e}")
            return None