import customtkinter as ctk
from tkinter import filedialog, messagebox
from openai import OpenAI
from google import genai
import base64
import threading
import re
import os
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

# --- CẤU HÌNH ---
BASE_URL_FPT = os.getenv("BASE_URL")
API_KEY_FPT = os.getenv("API_KEY")
OCR_MODEL = "DeepSeek-OCR"

# Việt nhớ kiểm tra tên biến môi trường này cho khớp với file .env nhé
GEMINI_API_KEY = os.getenv("YOUR_GEMINI_API_KEY") 
gemini_client = genai.Client(api_key=GEMINI_API_KEY)
GEMINI_MODEL_ID = "gemini-3-flash-preview" # Đổi sang model mạnh nhất trong list của Việt

client_fpt = OpenAI(api_key=API_KEY_FPT, base_url=BASE_URL_FPT)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class OCRApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AI OCR & Gemini Translator - Việt Võ")
        
        # --- TỐI ƯU CỬA SỔ ---
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # Kích thước tối thiểu (40% màn hình)
        min_w = int(screen_width * 0.4)
        min_h = int(screen_height * 0.4)
        self.minsize(min_w, min_h)

        # Kích thước khởi tạo (nên để to hơn min một chút cho đẹp)
        start_w = 900
        start_h = 950
        
        # Tính toán để cửa sổ luôn ở giữa
        x = (screen_width // 2) - (start_w // 2)
        y = (screen_height // 2) - (start_h // 2)
        self.geometry(f"{start_w}x{start_h}+{x}+{y}")
        
        # Cho phép phóng to tối đa
        self.after(0, lambda: self.state('zoomed')) 

        self.setup_ui()

    def setup_ui(self):
        # Header
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(self.header_frame, text="FPT OCR + Gemini Translate", 
                     font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")
        
        self.theme_switch = ctk.CTkSwitch(self.header_frame, text="Dark Mode", command=self.toggle_theme)
        self.theme_switch.select()
        self.theme_switch.pack(side="right")

        # File Selection
        self.file_frame = ctk.CTkFrame(self)
        self.file_frame.pack(fill="x", padx=20, pady=10)
        self.entry_path = ctk.CTkEntry(self.file_frame, placeholder_text="Đường dẫn file ảnh...", height=35)
        self.entry_path.pack(side="left", padx=10, expand=True, fill="x")
        ctk.CTkButton(self.file_frame, text="Chọn ảnh", command=self.select_file, width=100).pack(side="left", padx=10)

        # Options
        self.option_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.option_frame.pack(fill="x", padx=20, pady=5)
        self.translate_var = ctk.BooleanVar(value=False)
        self.check_translate = ctk.CTkCheckBox(self.option_frame, text="Dịch sang Tiếng Việt bằng Gemini", variable=self.translate_var)
        self.check_translate.pack(side="left", padx=10)

        # Preview (Tăng cường khả năng co giãn)
        self.image_container = ctk.CTkScrollableFrame(self, label_text="Ảnh đã chọn")
        self.image_container.pack(fill="both", padx=20, pady=5, expand=True)
        self.img_label = ctk.CTkLabel(self.image_container, text="(Trống)")
        self.img_label.pack(expand=True, pady=10)

        # Action Button
        self.btn_scan = ctk.CTkButton(self, text="BẮT ĐẦU XỬ LÝ", command=self.run_ocr, height=50, 
                                      font=ctk.CTkFont(size=16, weight="bold"), fg_color="#1f538d")
        self.btn_scan.pack(fill="x", padx=20, pady=15)

        # Result Toolbar (Nơi đặt nút Copy)
        self.toolbar_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.toolbar_frame.pack(fill="x", padx=20, pady=(0, 5))

        ctk.CTkLabel(self.toolbar_frame, text="Kết quả xử lý:", 
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")

        self.btn_copy = ctk.CTkButton(
            self.toolbar_frame, text="Copy", command=self.copy_to_clipboard,
            width=60, height=25, fg_color="#2b2b2b", border_width=1
        )
        self.btn_copy.pack(side="right")

        # Result Textbox (Đã tối ưu wrap="word")
        self.text_result = ctk.CTkTextbox(
            self, font=("Segoe UI", 13), height=300, wrap="word", padx=10, pady=10, border_width=1
        )
        self.text_result.pack(fill="both", padx=20, pady=(0, 20), expand=True)

    def copy_to_clipboard(self):
        content = self.text_result.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(content)
        messagebox.showinfo("Thông báo", "Đã chép bản dịch rồi nhé Việt!")

    def toggle_theme(self):
        ctk.set_appearance_mode("dark" if self.theme_switch.get() == 1 else "light")

    def select_file(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.jpeg *.png")])
        if path:
            self.entry_path.delete(0, "end")
            self.entry_path.insert(0, path)
            img = Image.open(path)
            # Tối ưu kích thước xem trước dựa trên chiều rộng cửa sổ hiện tại
            display_w = 600
            w, h = img.size
            display_h = int(h * (display_w / w))
            my_image = ctk.CTkImage(light_image=img, dark_image=img, size=(display_w, display_h))
            self.img_label.configure(image=my_image, text="")

    def translate_with_gemini(self, text):
        try:
            # Prompt tối ưu để loại bỏ phần "giải thích" thừa thãi
            prompt = (
                "Bạn là chuyên gia dịch thuật game chuyên nghiệp. Nhiệm vụ của bạn:\n"
                "1. Ghép các từ bị tách rời (ví dụ 'Di spels' thành 'Dispels').\n"
                "2. Dịch sang tiếng Việt văn chương, mượt mà.\n"
                "CHỈ TRẢ VỀ KẾT QUẢ DỊCH. Tuyệt đối không chào hỏi, không phân tích, không giải thích gì thêm.\n\n"
                f"Văn bản: {text}"
            )
            response = gemini_client.models.generate_content(model=GEMINI_MODEL_ID, contents=prompt)
            return response.text.strip()
        except Exception as e:
            return f"\n[Lỗi Gemini: {str(e)}]"

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

    def run_ocr(self):
        image_path = self.entry_path.get()
        if not image_path:
            messagebox.showwarning("Chú ý", "Việt chưa chọn ảnh kìa!")
            return

        def process():
            try:
                self.btn_scan.configure(state="disabled", text="Đang xử lý...")
                self.text_result.delete("1.0", "end")
                
                with open(image_path, "rb") as f:
                    base64_image = base64.b64encode(f.read()).decode("utf-8")

                ocr_resp = client_fpt.chat.completions.create(
                    model=OCR_MODEL,
                    messages=[{"role": "user", "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                        {"type": "text", "text": "Free OCR."}
                    ]}]
                )
                
                raw_text = self.clean_ocr_text(ocr_resp.choices[0].message.content)
                
                if self.translate_var.get():
                    final_output = self.translate_with_gemini(raw_text)
                else:
                    final_output = raw_text

                self.text_result.insert("end", final_output)
            except Exception as e:
                messagebox.showerror("Lỗi", f"Hệ thống báo lỗi: {str(e)}")
            finally:
                self.btn_scan.configure(state="normal", text="BẮT ĐẦU XỬ LÝ")

        threading.Thread(target=process).start()

if __name__ == "__main__":
    app = OCRApp()
    app.mainloop()