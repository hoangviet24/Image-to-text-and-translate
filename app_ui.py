import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
import threading

class OCRApp(ctk.CTk):
    def __init__(self, ai_service):
        super().__init__()
        self.bind("<Control-v>", lambda e: self.paste_image())
        self.ai = ai_service
        self.title("AI OCR & Gemini Translator - Việt Võ")
        
        # Thiết lập cửa sổ trước
        self._setup_window()
        
        # Khởi tạo UI sau
        self.setup_ui()
    def paste_image(self):
        """Xử lý dán ảnh từ Clipboard"""
        try:
            from PIL import ImageGrab, Image
            import os
            
            # Lấy ảnh từ Clipboard
            img = ImageGrab.grabclipboard()
            
            if isinstance(img, Image.Image):
                # Tạo thư mục temp nếu chưa có
                os.makedirs("temp", exist_ok=True)
                temp_path = os.path.join("temp", "pasted_image.png")
                
                # Lưu ảnh tạm để tí nữa truyền vào OCR
                img.save(temp_path)
                
                # Cập nhật đường dẫn vào Entry và hiện Preview
                self.entry_path.delete(0, "end")
                self.entry_path.insert(0, temp_path)
                
                # Hiển thị Preview (tái sử dụng logic cũ của Việt)
                w, h = img.size
                display_w = 600
                display_h = int(h * (display_w / w))
                my_image = ctk.CTkImage(light_image=img, dark_image=img, size=(display_w, display_h))
                self.img_label.configure(image=my_image, text="")
                
                self.log("Đã dán ảnh thành công từ Clipboard!")
            else:
                self.log("Clipboard không chứa dữ liệu ảnh.")
                messagebox.showwarning("Chú ý", "Việt ơi, trong bộ nhớ tạm không có ảnh kìa!")
        except Exception as e:
            self.log(f"Lỗi khi dán ảnh: {e}")
    def _setup_window(self):
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.minsize(int(sw*0.4), int(sh*0.4))
        w, h = 900, 950
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        # self.state('zoomed') # Mở comment nếu muốn mặc định toàn màn hình

    # --- ĐỊNH NGHĨA CÁC HÀM XỬ LÝ TRƯỚC KHI SETUP UI ---
    
    def toggle_theme(self):
        """Đổi giao diện Sáng/Tối"""
        mode = "dark" if self.theme_switch.get() == 1 else "light"
        ctk.set_appearance_mode(mode)

    def copy_to_clipboard(self):
        """Sao chép kết quả"""
        content = self.text_result.get("1.0", "end-1c")
        if content.strip():
            self.clipboard_clear()
            self.clipboard_append(content)
            messagebox.showinfo("Thông báo", "Đã chép vào bộ nhớ đệm rồi nhé Việt!")
        else:
            messagebox.showwarning("Chú ý", "Chưa có gì để chép hết Việt ơi!")

    def select_file(self):
        """Chọn ảnh"""
        path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.jpeg *.png")])
        if path:
            self.entry_path.delete(0, "end")
            self.entry_path.insert(0, path)
            img = Image.open(path)
            w, h = img.size
            display_w = 600
            display_h = int(h * (display_w / w))
            my_image = ctk.CTkImage(light_image=img, dark_image=img, size=(display_w, display_h))
            self.img_label.configure(image=my_image, text="")

    # --- HÀM SETUP UI CHÍNH ---

    def setup_ui(self):
        # Header
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(self.header_frame, text="FPT OCR + Gemini Translate", 
                     font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")
        
        # Switch đổi theme - Gọi đến self.toggle_theme đã định nghĩa ở trên
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
        self.check_translate = ctk.CTkCheckBox(self.option_frame, text="Dịch sang Tiếng Việt bằng Gemini", 
                                              variable=self.translate_var)
        self.check_translate.pack(side="left", padx=10)

        # Preview
        self.image_container = ctk.CTkScrollableFrame(self, label_text="Ảnh đã chọn")
        self.image_container.pack(fill="both", padx=20, pady=5, expand=True)
        self.img_label = ctk.CTkLabel(self.image_container, text="(Trống)")
        self.img_label.pack(expand=True, pady=10)

        # Action Button
        self.btn_scan = ctk.CTkButton(self, text="BẮT ĐẦU XỬ LÝ", command=self.run_ocr, height=50, 
                                      font=ctk.CTkFont(size=16, weight="bold"), fg_color="#1f538d")
        self.btn_scan.pack(fill="x", padx=20, pady=(15, 5))
        # THÊM: Progress Bar (Mặc định ẩn)
        self.progress_bar = ctk.CTkProgressBar(self, orientation="horizontal", mode="indeterminate")
        self.progress_bar.pack(fill="x", padx=25, pady=(0, 10))
        self.progress_bar.set(0) # Ban đầu để 0
        # Result Toolbar
        self.toolbar_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.toolbar_frame.pack(fill="x", padx=20, pady=(0, 5))
        ctk.CTkLabel(self.toolbar_frame, text="Kết quả xử lý:", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        
        self.btn_copy = ctk.CTkButton(self.toolbar_frame, text="Copy", command=self.copy_to_clipboard, 
                                      width=60, height=25, fg_color="#2b2b2b", border_width=1)
        self.btn_copy.pack(side="right")

        # Textbox
        self.text_result = ctk.CTkTextbox(self, font=("Segoe UI", 13), height=300, wrap="word", 
                                          padx=10, pady=10, border_width=1)
        self.text_result.pack(fill="both", padx=20, pady=(0, 20), expand=True)
    def log(self, message):
        """Hàm in log ra console có kèm timestamp cho chuyên nghiệp"""
        from datetime import datetime
        time_str = datetime.now().strftime("%H:%M:%S")
        print(f"[{time_str}] {message}")
    def run_ocr(self):
        image_path = self.entry_path.get()
        if not image_path:
            return messagebox.showwarning("Chú ý", "Việt chưa chọn ảnh kìa!")

        def process():
            try:
                self.log("Bắt đầu xử lý Stream...")
                self.btn_scan.configure(state="disabled", text="Đang xử lý...")
                self.progress_bar.start()
                
                # Bước 1: OCR
                self.log("Đang gửi ảnh lên FPT OCR...")
                raw_text = self.ai.process_ocr(image_path)
                self.log(f"Đã nhận văn bản từ OCR (độ dài: {len(raw_text)} ký tự).")
                # Bước 2: Dịch với Streaming
                self.text_result.delete("1.0", "end")
                # Bước 3: Dịch
                if self.translate_var.get():
                    self.log("Đang nhận bản dịch (Streaming)...")
                    stream = self.ai.translate_stream(raw_text)
                    
                    if stream:
                        for chunk in stream:
                            # Lấy text từ chunk và chèn ngay vào Textbox
                            if chunk.text:
                                # Dùng after để đảm bảo UI update mượt mà trên Windows
                                self.after(0, lambda c=chunk.text: self.text_result.insert("end", c))
                                # Tự động cuộn xuống cuối khi chữ dài
                                self.after(0, lambda: self.text_result.see("end"))
                    else:
                        self.text_result.insert("end", "[Lỗi khởi tạo Stream]")
                else:
                    self.text_result.delete("1.0", "end")
                    self.text_result.insert("end", raw_text)
                    self.log("Đã hiển thị kết quả lên màn hình.")

            except Exception as e:
                self.log(f"LỖI HỆ THỐNG: {str(e)}")
                messagebox.showerror("Lỗi", f"Hệ thống báo lỗi: {str(e)}")
            finally:
                self.progress_bar.stop() # Dừng thanh tiến trình
                self.btn_scan.configure(state="normal", text="BẮT ĐẦU XỬ LÝ")
                self.log("Kết thúc phiên làm việc.")

        threading.Thread(target=process).start()