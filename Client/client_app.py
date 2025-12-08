import customtkinter as ctk
import socket
import threading
import struct
import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime
from tkinter import filedialog # <-- Thêm dòng này
import os # <-- Thêm dòng này để lấy tên file
import subprocess # Để mở file trên Windows an toàn
import sys

# --- CẤU HÌNH ---
SERVER_IP = '127.0.0.1'
SERVER_PORT = 8888
PACK_FORMAT = f'i 32s 32s 32s 32s 1024s'
PACK_SIZE = 1156

# Message Types
MSG_LOGIN_REQ = 0
MSG_LOGIN_SUCCESS = 1
MSG_LOGIN_FAIL = 2
MSG_PRIVATE_CHAT = 3
MSG_GROUP_CHAT = 4
MSG_FRIEND_REQ = 5
MSG_FRIEND_ACCEPT = 6
MSG_ADD_FRIEND_SUCC = 7
MSG_CREATE_GROUP_REQ = 8
MSG_JOIN_GROUP_REQ = 9
MSG_ADD_GROUP_SUCC = 10
MSG_HISTORY = 11
MSG_CREATE_GROUP_FAIL = 12
MSG_REQ_MEMBER_LIST   = 13
MSG_RESP_MEMBER_LIST  = 14

MSG_LEAVE_GROUP       = 15
MSG_UNFRIEND          = 16
MSG_REMOVE_CONTACT    = 17  # Server báo Client xóa nút khỏi Sidebar

MSG_FILE_START        = 18  # Bắt đầu gửi file
MSG_FILE_DATA         = 19  # Dữ liệu file
MSG_FILE_END          = 20  # Kết thúc gửi file
MSG_FILE_NOTIFY       = 21  # Thông báo đã gửi file
MSG_FILE_DOWNLOAD_REQ = 22  # Yêu cầu tải file

class ContactButton(ctk.CTkButton):
    # Thêm tham số on_right_click vào cuối
    def __init__(self, master, real_name, display_text, type, callback, on_right_click):
        super().__init__(master, text=display_text, anchor="w", command=lambda: callback(real_name, type))
        self.type = type
        self.real_name = real_name
        self.pack(fill="x", pady=2, padx=5)
        self.configure(fg_color="transparent", text_color="white", height=40)
        
        # Gắn sự kiện chuột phải
        self.bind("<Button-3>", lambda event: on_right_click(event, real_name, type))

    def set_unread(self, active):
        if active: self.configure(fg_color="#C0392B") 
        else: self.configure(fg_color="transparent")

    def set_active_bg(self, active):
        if active: self.configure(fg_color="#2980B9") 
        else: self.configure(fg_color="transparent")

class ChatClient(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Messenger Pro Max")
        self.geometry("1100x700")
        ctk.set_appearance_mode("Dark")
        
        self.client = None
        self.my_name = ""
        self.contacts = {} 
        self.messages = {} 
        self.current_target = None
        
        self.init_ui()

    def init_ui(self):
        # LOGIN SCREEN
        self.login_frame = ctk.CTkFrame(self)
        self.login_frame.pack(fill="both", expand=True)
        ctk.CTkLabel(self.login_frame, text="ĐĂNG NHẬP", font=("Arial", 30, "bold")).pack(pady=40)
        self.entry_user = ctk.CTkEntry(self.login_frame, placeholder_text="Username", width=300)
        self.entry_user.pack(pady=10)
        self.entry_pass = ctk.CTkEntry(self.login_frame, placeholder_text="Password", show="*", width=300)
        self.entry_pass.pack(pady=10)
        ctk.CTkButton(self.login_frame, text="Login", command=self.login, width=300).pack(pady=20)

        # MAIN SCREEN
        self.main_ui = ctk.CTkFrame(self)
        
        # Sidebar
        self.sidebar = ctk.CTkFrame(self.main_ui, width=260, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        
        self.lbl_name = ctk.CTkLabel(self.sidebar, text="...", font=("Arial", 20, "bold"))
        self.lbl_name.pack(pady=15)
        
        self.entry_add = ctk.CTkEntry(self.sidebar, placeholder_text="Nhập tên người/nhóm...")
        self.entry_add.pack(fill="x", padx=10, pady=5)
        
        btn_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        btn_frame.pack(fill="x", padx=5)
        ctk.CTkButton(btn_frame, text="+ Bạn", width=70, fg_color="green", command=self.req_friend).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="+ Nhóm", width=70, fg_color="#D35400", command=self.create_group).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="Vào Nhóm", width=70, fg_color="#2980B9", command=self.join_group).pack(side="left", padx=2)

        ctk.CTkLabel(self.sidebar, text="─── DANH SÁCH ───").pack(pady=10)
        self.scroll_contacts = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent")
        self.scroll_contacts.pack(fill="both", expand=True)

        # Chat Area
        self.right_frame = ctk.CTkFrame(self.main_ui)
        self.right_frame.pack(side="right", fill="both", expand=True)

        # Header Frame (Để chứa tên nhóm và nút xem thành viên)
        self.header_frame = ctk.CTkFrame(self.right_frame, height=40, fg_color="#222")
        self.header_frame.pack(fill="x")

        self.header_chat = ctk.CTkLabel(self.header_frame, text="Chào mừng!", font=("Arial", 16, "bold"), text_color="white")
        self.header_chat.pack(side="left", padx=20, pady=5)

        # Nút xem thành viên (Mặc định ẩn, chỉ hiện khi chat nhóm)
        self.btn_members = ctk.CTkButton(self.header_frame, text="Thành viên", width=80, height=25, 
                                         fg_color="#555", command=self.req_members)
        
        self.header_chat = ctk.CTkLabel(self.right_frame, text="Chào mừng!", font=("Arial", 16, "bold"), height=40, fg_color="#222")
        self.header_chat.pack(fill="x")

        self.scroll_chat = ctk.CTkScrollableFrame(self.right_frame, fg_color="#1a1a1a")
        self.scroll_chat.pack(fill="both", expand=True, padx=5, pady=5)

        self.input_frame = ctk.CTkFrame(self.right_frame, height=50)
        self.input_frame.pack(fill="x", padx=5, pady=5)

        # --- NÚT GỬI FILE (BÊN TRÁI) ---
        self.btn_file = ctk.CTkButton(self.input_frame, text="+", width=35, fg_color="#444", command=self.choose_file)
        self.btn_file.pack(side="left", padx=5)

        self.entry_msg = ctk.CTkEntry(self.input_frame, placeholder_text="Nhập tin nhắn...")
        self.entry_msg.pack(side="left", fill="x", expand=True, padx=5)
        self.entry_msg.bind("<Return>", self.send_msg)
        
        # Biến hỗ trợ tải file
        self.downloading_file = None # Biến giữ file đang tải về
        self.downloading_path = ""   # Đường dẫn lưu file

        ctk.CTkButton(self.input_frame, text="Gửi", width=60, command=self.send_msg).pack(side="right", padx=5)

    def pack(self, type, name="", pwd="", target="", gpwd="", data=""):
        return struct.pack(PACK_FORMAT, type, name.encode(), pwd.encode(), target.encode(), gpwd.encode(), data.encode())

    def login(self):
        u = self.entry_user.get()
        p = self.entry_pass.get()
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((SERVER_IP, SERVER_PORT))
            self.client.send(self.pack(MSG_LOGIN_REQ, u, p))
            
            raw = self.client.recv(PACK_SIZE)
            data = struct.unpack(PACK_FORMAT, raw)
            if data[0] == MSG_LOGIN_SUCCESS:
                self.my_name = u
                self.lbl_name.configure(text=f"Hi, {u}")
                self.login_frame.pack_forget()
                self.main_ui.pack(fill="both", expand=True)
                threading.Thread(target=self.loop, daemon=True).start()
            else:
                messagebox.showerror("Lỗi", "Sai thông tin đăng nhập")
        except Exception as e: messagebox.showerror("Lỗi", f"Lỗi kết nối: {e}")

    def loop(self):
        buffer = b""
        while True:
            try:
                chunk = self.client.recv(4096)
                if not chunk: break
                buffer += chunk
                while len(buffer) >= PACK_SIZE:
                    packet = buffer[:PACK_SIZE]
                    buffer = buffer[PACK_SIZE:]
                    data = struct.unpack(PACK_FORMAT, packet)
                    self.after(0, self.handle_packet, data)
            except: break

    # --- HÀM GỬI FILE MỚI ---  
    def choose_file(self):
        if not self.current_target:
            messagebox.showwarning("Chú ý", "Hãy chọn người nhận trước!")
            return

        # Mở hộp thoại chọn file
        filepath = filedialog.askopenfilename()
        if filepath:
            # Chạy thread gửi file để không lag giao diện
            threading.Thread(target=self.sending_file_thread, args=(filepath,)).start()

    # Hàm gửi file trong thread riêng
    def sending_file_thread(self, filepath):
        try:
            filename = os.path.basename(filepath)
            filesize = os.path.getsize(filepath)
            
            # Hiển thị tin nhắn giả (Bubble) phía mình trước
            self.after(0, self.render_bubble, self.my_name, f"[FILE] Đang gửi: {filename}...", True, False)

            # 1. Gửi gói START: name=sender, target=receiver, data=filename
            # Dùng trường password để gửi kích thước file (hack trick)
            self.client.send(self.pack(MSG_FILE_START, self.my_name, str(filesize), self.current_target, "", filename))
            
            # 2. Đọc file và gửi từng chunk (Binary)
            with open(filepath, "rb") as f:
                while True:
                    chunk = f.read(1024) # Đọc 1024 bytes (khớp BUFF_SIZE bên C++)
                    if not chunk: break
                    
                    # Gói tin DATA: Cần pack cẩn thận vì chunk là bytes, không phải string
                    # data=chunk
                    # password=độ dài chunk (Vì chunk cuối có thể < 1024 bytes)
                    
                    # Lưu ý: struct.pack cần đúng độ dài 1024s. Ta phải đệm (padding) nếu thiếu.
                    chunk_len = len(chunk)
                    padded_chunk = chunk.ljust(1024, b'\0') 
                    
                    # Tự pack tay gói tin MSG_FILE_DATA để đảm bảo binary không bị lỗi decode
                    # Format: i 32s 32s 32s 32s 1024s
                    pkt = struct.pack(PACK_FORMAT, 
                                      MSG_FILE_DATA, 
                                      self.my_name.encode(), 
                                      str(chunk_len).encode(), # Gửi độ dài thật qua password
                                      self.current_target.encode(), 
                                      b"", 
                                      padded_chunk)
                    self.client.send(pkt)
                    
                    # Nghỉ cực ngắn để Server kịp xử lý (tránh dính gói tin)
                    import time
                    time.sleep(0.005) 

            # 3. Gửi gói END
            self.client.send(self.pack(MSG_FILE_END, self.my_name, "", self.current_target))
            
            self.after(0, self.render_bubble, self.my_name, f"[FILE] Đã gửi: {filename}", True, False)
            self.after(0, self.scroll_to_bottom)
            
        except Exception as e:
            print(f"Lỗi gửi file: {e}")
            messagebox.showerror("Lỗi", "Không thể gửi file!")

    def handle_packet(self, data):
        """Xử lý logic khi nhận được gói tin"""
        
        # --- HÀM GIẢI MÃ AN TOÀN ---
        def decode_safe(bytes_data):
            try:
                return bytes_data.partition(b'\0')[0].decode('utf-8', errors='replace')
            except:
                return ""

        m_type = data[0]
        sender = decode_safe(data[1])
        # pass (data[2]) bỏ qua ở đây, xử lý trong process_chat_msg nếu cần
        target = decode_safe(data[3])
        # group_pass (data[4])
        content = decode_safe(data[5])
        
        print(f"[DEBUG] Type={m_type} | Sender={sender} | Target={target}") 

        # ---------------------------------------------------------
        # SỬA LẠI: Gọi thẳng hàm process_chat_msg để xử lý tin nhắn
        # Thay vì viết logic lặp lại gây lỗi
        # ---------------------------------------------------------
        if m_type in [MSG_PRIVATE_CHAT, MSG_GROUP_CHAT, MSG_HISTORY]:
            self.process_chat_msg(m_type, sender, target, content, data)

        # 2. Xử lý thông báo thêm bạn/nhóm thành công
        elif m_type == MSG_ADD_FRIEND_SUCC:
            self.add_contact_btn(target, "PRIVATE")
            self.add_system_message(target, "Hai bạn đã trở thành bạn bè.")
            
        elif m_type == MSG_ADD_GROUP_SUCC:
            self.add_contact_btn(target, "GROUP")
            self.add_system_message(target, f"Bạn đã tham gia nhóm {target}")
            
        # 3. Xử lý lời mời kết bạn
        elif m_type == MSG_FRIEND_REQ:
            ans = messagebox.askyesno("Kết bạn", f"{sender} muốn kết bạn. Đồng ý?")
            if ans:
                self.client.send(self.pack(MSG_FRIEND_ACCEPT, self.my_name, "", sender))

        # Xử lý lỗi tạo nhóm trùng tên
        elif m_type == MSG_CREATE_GROUP_FAIL:
            messagebox.showerror("Thất bại", content)

        # Xử lý hiển thị danh sách thành viên
        elif m_type == MSG_RESP_MEMBER_LIST:
            # content chứa danh sách thành viên
            # target chứa tên nhóm
            messagebox.showinfo(f"Thành viên nhóm {target}", f"Danh sách:\n{content}")

        # --- XÓA NÚT KHI RỜI NHÓM/HỦY KẾT BẠN THÀNH CÔNG ---
        elif m_type == MSG_REMOVE_CONTACT:
            target_name = target # Tên cần xóa
            
            # 1. Xóa nút khỏi giao diện
            if target_name in self.contacts:
                self.contacts[target_name].destroy() # Xóa widget
                del self.contacts[target_name]       # Xóa khỏi dict
            
            # 2. Xóa dữ liệu chat cũ (tùy chọn)
            if target_name in self.messages:
                del self.messages[target_name]

            # 3. Nếu đang mở đoạn chat đó thì clear màn hình
            if self.current_target == target_name:
                self.current_target = None
                self.header_chat.configure(text="...")
                self.btn_members.pack_forget() # Ẩn nút thành viên
                for w in self.scroll_chat.winfo_children(): w.destroy()
                messagebox.showinfo("Thông báo", f"Đã xóa liên hệ {target_name}")

        elif m_type == MSG_FILE_NOTIFY:
            # content chính là tên file (VD: baitap.docx)
            display_text = f"FILE: {content}"
            
            # 1. Xác định đoạn chat (Private hay Group)
            chat_key = ""
            if target == self.my_name: # Chat riêng (Người khác gửi cho mình)
                chat_key = sender
                mode = "PRIVATE"
            else: # Chat nhóm (Người khác gửi vào nhóm)
                chat_key = target
                mode = "GROUP"
                
            # 2. Lưu tin nhắn vào RAM 
            # QUAN TRỌNG: Lưu thêm cờ 'is_file' và 'filename' để phục vụ việc tải sau này
            if chat_key not in self.messages: self.messages[chat_key] = []
            
            self.messages[chat_key].append({
                'sender': sender, 
                'content': display_text, 
                'is_sys': False,
                'is_file': True,      # Đánh dấu đây là tin nhắn chứa file
                'filename': content   # Lưu tên file gốc (quan trọng để gửi yêu cầu tải)
            })
            
            # 3. Tạo nút trên Sidebar nếu chưa có (Trường hợp người lạ gửi file)
            if chat_key not in self.contacts:
                self.add_contact_btn(chat_key, mode)
                
            # 4. Cập nhật giao diện
            if self.current_target == chat_key:
                # Gọi hàm render_bubble với tham số is_file=True để vẽ nút Download màu xanh
                # Lưu ý: sender == self.my_name là False (vì đây là file người khác gửi đến)
                self.render_bubble(sender, display_text, False, False, is_file=True, filename=content)
                
                # Cuộn xuống dưới cùng để thấy file mới
                self.after(50, self.scroll_to_bottom)
            else:
                # Nếu đang không mở cuộc trò chuyện này thì báo đỏ (unread)
                if chat_key in self.contacts: self.contacts[chat_key].set_unread(True)
        
        # 1. SERVER BẮT ĐẦU GỬI FILE VỀ
        elif m_type == MSG_FILE_START:
            # Server xác nhận bắt đầu gửi. 
            # (Thực ra mình đã mở file ở hàm request_download rồi, nên ở đây ko cần làm gì nhiều)
            print(f"[DOWNLOAD] Bat dau nhan file size={sender} bytes") # sender chứa filesize do server gửi

        # 2. NHẬN DỮ LIỆU FILE
        elif m_type == MSG_FILE_DATA:
            if self.downloading_file:
                try:
                    # Lấy độ dài chunk từ password (data[2])
                    # Lưu ý: partition(b'\0')[0] để cắt bỏ ký tự null thừa
                    chunk_len_str = data[2].partition(b'\0')[0].decode('utf-8', errors='replace')
                    
                    if chunk_len_str.isdigit():
                        chunk_len = int(chunk_len_str)
                        
                        # data[5] là dữ liệu binary (bytes)
                        # Cắt đúng độ dài thực tế để loại bỏ padding
                        chunk_data = data[5][:chunk_len]
                        
                        self.downloading_file.write(chunk_data)
                except Exception as e:
                    print(f"Lỗi ghi file: {e}")

        # 3. KẾT THÚC TẢI
        elif m_type == MSG_FILE_END:
            if self.downloading_file:
                self.downloading_file.close()
                self.downloading_file = None
                
                ans = messagebox.askyesno("Tải xong", "Đã tải xong file. Bạn có muốn mở ngay không?")
                if ans:
                    try:
                        # Mở file trên Windows
                        os.startfile(self.downloading_path)
                    except:
                        # Fallback cho các OS khác (nếu cần)
                        subprocess.call(['open', self.downloading_path])

    def process_chat_msg(self, type, sender, target, content, raw_data):
        chat_key = ""
        is_history = (type == MSG_HISTORY)
        
        if is_history:
            real_type = int(raw_data[2].decode().strip('\x00'))
            if real_type == MSG_PRIVATE_CHAT:
                chat_key = sender if sender != self.my_name else target
                mode = "PRIVATE"
            else:
                chat_key = target
                mode = "GROUP"
        else:
            if type == MSG_PRIVATE_CHAT:
                chat_key = sender if sender != self.my_name else target
                mode = "PRIVATE"
            else:
                chat_key = target
                mode = "GROUP"

        if chat_key not in self.messages: self.messages[chat_key] = []
        self.messages[chat_key].append({'sender': sender, 'content': content, 'is_sys': False})
        
        if chat_key not in self.contacts:
            self.add_contact_btn(chat_key, mode)

        if self.current_target == chat_key:
            # SỬA: Thêm tham số thứ 4 là False (vì đây là tin nhắn thường, không phải system)
            self.render_bubble(sender, content, sender == self.my_name, False) 
            
            # Auto scroll xuống dưới cùng khi có tin mới
            self.after(50, self.scroll_to_bottom)
            
        elif not is_history:
            # Nếu đang không mở chat với người này thì hiện màu đỏ thông báo
            if chat_key in self.contacts:
                self.contacts[chat_key].set_unread(True)

    def add_system_message(self, target, text):
        """Thêm tin nhắn hệ thống vào đoạn chat (Thay vì Popup)"""
        if target not in self.messages: self.messages[target] = []
        self.messages[target].append({'sender': 'SYSTEM', 'content': text, 'is_sys': True})
        
        # Nếu đang mở đoạn chat đó thì hiện luôn
        if self.current_target == target:
            self.render_bubble("SYSTEM", text, False, True)
        else:
            # Nếu không thì báo đỏ để người dùng bấm vào xem
            if target in self.contacts: self.contacts[target].set_unread(True)

    def add_contact_btn(self, name, mode):
        # name ở đây là tên gốc (VD: "AI")
        if name in self.contacts: return
        
        # Tạo tên hiển thị (Thêm [N] nếu là nhóm)
        display_text = f"[N] {name}" if mode == "GROUP" else name
        
        # TRUYỀN CẢ 2 TÊN VÀO: name (gốc) và display_text (hiển thị)
        btn = ContactButton(self.scroll_contacts, name, display_text, mode, self.select_contact, self.show_context_menu)
        
        # Lưu vào dict bằng tên gốc
        self.contacts[name] = btn 
        
        if name not in self.messages: self.messages[name] = []

    def show_context_menu(self, event, name, type):
        # Tạo menu kiểu cổ điển của Tkinter (Vì CustomTkinter chưa hỗ trợ Menu tốt)
        menu = tk.Menu(self, tearoff=0)
        
        if type == "GROUP":
            menu.add_command(label="Rời nhóm", command=lambda: self.req_leave_group(name))
        else:
            menu.add_command(label="Hủy kết bạn", command=lambda: self.req_unfriend(name))
            
        # Hiển thị menu ngay tại vị trí con trỏ chuột
        menu.post(event.x_root, event.y_root)

    def req_leave_group(self, name):
        if messagebox.askyesno("Xác nhận", f"Rời nhóm {name}?"):
            self.client.send(self.pack(MSG_LEAVE_GROUP, self.my_name, "", name))

    def req_unfriend(self, name):
        if messagebox.askyesno("Xác nhận", f"Hủy kết bạn với {name}?"):
            self.client.send(self.pack(MSG_UNFRIEND, self.my_name, "", name))

    def req_members(self):
        if self.current_target:
            # Gửi yêu cầu Type 13 lên Server
            self.client.send(self.pack(MSG_REQ_MEMBER_LIST, self.my_name, "", self.current_target))

    def select_contact(self, name, mode):
        if self.current_target and self.current_target in self.contacts:
            self.contacts[self.current_target].set_active_bg(False)
        self.current_target = name
        self.contacts[name].set_active_bg(True)
        self.contacts[name].set_unread(False)
        self.header_chat.configure(text=f"Đang chat với: {name}")

        # LOGIC MỚI: Hiện nút thành viên nếu là nhóm
        if mode == "GROUP":
            self.btn_members.pack(side="right", padx=10, pady=5)
        else:
            self.btn_members.pack_forget() # Ẩn đi nếu chat riêng
        
        # Load tin nhắn
        for w in self.scroll_chat.winfo_children(): w.destroy()
        if name in self.messages:
            for msg in self.messages[name]:
                self.render_bubble(msg['sender'], msg['content'], msg['sender'] == self.my_name, msg.get('is_sys', False))
        
        # --- THÊM DÒNG NÀY ---
        # Đợi 50ms để giao diện vẽ xong tin nhắn rồi mới cuộn
        self.after(50, self.scroll_to_bottom)

    def render_bubble(self, sender, content, is_me, is_sys, is_file=False, filename=""):
        frame = ctk.CTkFrame(self.scroll_chat, fg_color="transparent")
        
        if is_sys:
            frame.pack(fill="x", pady=5)
            ctk.CTkLabel(frame, text=content, font=("Arial", 11, "italic"), text_color="gray").pack()
        elif is_me:
            frame.pack(fill="x", pady=5, anchor="e")
            ctk.CTkLabel(frame, text=content, fg_color="#0084ff", text_color="white", corner_radius=15, padx=10, pady=5).pack(side="right")
        else:
            frame.pack(fill="x", pady=5, anchor="w")
            ctk.CTkLabel(frame, text=sender, font=("Arial", 9), text_color="gray").pack(anchor="w", padx=5)
            
            # Bây giờ biến is_file đã được định nghĩa, code này sẽ chạy đúng
            if is_file:
                # NẾU LÀ FILE: Vẽ nút Tải về
                btn = ctk.CTkButton(frame, text=f"⬇ {content}", 
                                    fg_color="#2ecc71", hover_color="#27ae60",
                                    width=150,
                                    command=lambda: self.request_download(filename))
                btn.pack(side="left")
            else:
                # Tin nhắn thường
                ctk.CTkLabel(frame, text=content, fg_color="#333", text_color="white", corner_radius=15, padx=10, pady=5).pack(side="left")

    def req_friend(self):
        t = self.entry_add.get().strip()
        if t: 
            self.client.send(self.pack(MSG_FRIEND_REQ, self.my_name, "", t))
            messagebox.showinfo("Thông báo", f"Đã gửi lời mời tới {t}")
            self.entry_add.delete(0, "end")

    def create_group(self):
        t = self.entry_add.get().strip()
        if t:
            p = simpledialog.askstring("Mật khẩu", f"Đặt pass cho nhóm {t}:")
            if p: self.client.send(self.pack(MSG_CREATE_GROUP_REQ, self.my_name, "", t, p))
            self.entry_add.delete(0, "end")

    def join_group(self):
        t = self.entry_add.get().strip()
        if t:
            p = simpledialog.askstring("Mật khẩu", f"Nhập pass nhóm {t}:")
            if p: self.client.send(self.pack(MSG_JOIN_GROUP_REQ, self.my_name, "", t, p))
            self.entry_add.delete(0, "end")

    def send_msg(self, event=None):
        txt = self.entry_msg.get()
        if txt and self.current_target:
            mode = self.contacts[self.current_target].type
            type = MSG_PRIVATE_CHAT if mode == "PRIVATE" else MSG_GROUP_CHAT
            self.client.send(self.pack(type, self.my_name, "", self.current_target, "", txt))
            
            if self.current_target not in self.messages: self.messages[self.current_target] = []
            self.messages[self.current_target].append({'sender': self.my_name, 'content': txt, 'is_sys': False})
            self.render_bubble(self.my_name, txt, True, False)
            self.entry_msg.delete(0, "end")
            self.after(50, self.scroll_to_bottom)

    def scroll_to_bottom(self):
        """Hàm cuộn xuống dưới cùng khung chat"""
        # _parent_canvas là thành phần nội bộ của CTkScrollableFrame
        # yview_moveto(1.0) nghĩa là cuộn đến vị trí 100% (đáy)
        self.scroll_chat._parent_canvas.yview_moveto(1.0)

    # --- HÀM YÊU CẦU TẢI FILE MỚI ---
    def request_download(self, filename):
        # 1. Hỏi người dùng muốn lưu vào đâu
        save_path = filedialog.asksaveasfilename(initialfile=filename, title="Lưu file")
        
        if save_path:
            self.downloading_path = save_path
            
            # Mở file sẵn để chờ ghi dữ liệu
            try:
                self.downloading_file = open(save_path, "wb")
                
                # 2. Gửi yêu cầu lên Server (Type 22)
                self.client.send(self.pack(MSG_FILE_DOWNLOAD_REQ, self.my_name, "", "", "", filename))
                
                messagebox.showinfo("Bắt đầu tải", f"Đang tải {filename}...")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể tạo file: {e}")

if __name__ == "__main__":
    app = ChatClient()
    app.mainloop()