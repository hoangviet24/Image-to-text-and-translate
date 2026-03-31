# Hướng dẫn cấu hình dự án Image to text and translate
## lưu ý: Chỉ dịch từ anh sang việt, nếu muốn đổi sang ngôn ngữ khác cần phải thay đổi prompt ở file services.py

```python
ai_service = AIService(
    fpt_key=os.getenv("API_KEY"), #API lấy từ FPT AI Factory, lấy ở tab FPT AI Inference
    fpt_url=os.getenv("BASE_URL"), #Lấy ở phần Deepseek OCR
    gemini_key=os.getenv("YOUR_GEMINI_API_KEY"), #Lấy ở google studio 
    gemini_model="models/gemini-flash-latest" --> phần này sẽ hướng dẫn ở dưới
)
```

## cách để biết những model có thể hoạt động
### chạy câu lệnh này, nó sẽ hiện ra những model có thể dùng được, 
### nên dùng gemini-2.5-flash hoặc pro
```python
import google.generativeai as genai
import os
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("YOUR_GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)
```
