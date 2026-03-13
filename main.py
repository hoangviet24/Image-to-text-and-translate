import os
from dotenv import load_dotenv
from services import AIService
from app_ui import OCRApp

def main():
    load_dotenv()
    
    # Khởi tạo Service
    ai_service = AIService(
        fpt_key=os.getenv("API_KEY"),
        fpt_url=os.getenv("BASE_URL"),
        gemini_key=os.getenv("YOUR_GEMINI_API_KEY"),
        gemini_model="models/gemini-flash-latest"
        
    )

    # Khởi chạy App
    app = OCRApp(ai_service)
    app.mainloop()

if __name__ == "__main__":
    main()