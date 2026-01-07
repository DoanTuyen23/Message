# HỆ THỐNG CHAT CLIENT - SERVER (TCP/IP)

![Badge C++](https://img.shields.io/badge/Server-C++-00599C?logo=c%2B%2B&logoColor=white)
![Badge Python](https://img.shields.io/badge/Client-Python-3776AB?logo=python&logoColor=white)
![Badge Protocol](https://img.shields.io/badge/Protocol-TCP%2FIP-red)
![Badge Platform](https://img.shields.io/badge/Platform-Windows-blue)

## 1. TỔNG QUAN DỰ ÁN

Hệ thống là ứng dụng nhắn tin tức thời (Instant Messaging) hoạt động trên mô hình **Client-Server** thông qua giao thức **TCP/IP** 

[Image of client server network architecture diagram]
. Hệ thống hỗ trợ nhắn tin cá nhân, nhắn tin nhóm, gửi file đính kèm (cơ chế Store-and-Forward), và tích hợp trò chơi Caro (Gomoku) trực tuyến.

### Cấu trúc thư mục dự án
Dự án được chia thành 3 thư mục chính:

* **`Common/`**: Chứa các định nghĩa chung dùng cho cả hai phía (Protocol).
* **`Server/`**: Chứa mã nguồn máy chủ, xử lý logic trung tâm và cơ sở dữ liệu (File text).
* **`Client/`**: Chứa mã nguồn ứng dụng người dùng (Giao diện GUI).

---

## 2. GIAO THỨC TRUYỀN THÔNG (PROTOCOL)

Hệ thống sử dụng cơ chế đóng gói dữ liệu nhị phân (**Binary Serialization**) để đảm bảo tính nhất quán giữa C++ (Server) và Python (Client). 

### 2.1. Cấu trúc gói tin (Message Struct)
Được định nghĩa trong `Common/protocol.h`. Tổng kích thước gói tin là **1156 bytes**.

| Trường dữ liệu | Kiểu (C++) | Kiểu (Python) | Kích thước | Mô tả |
| :--- | :--- | :--- | :--- | :--- |
| **type** | `int` | `i` | 4 bytes | Loại hành động (Login, Chat, File...) |
| **name** | `char[32]` | `32s` | 32 bytes | Tên người gửi (Sender) |
| **password** | `char[32]` | `32s` | 32 bytes | Mật khẩu / Kích thước file / Cờ game |
| **target** | `char[32]` | `32s` | 32 bytes | Tên người nhận / Tên nhóm |
| **group_pass** | `char[32]` | `32s` | 32 bytes | Mật khẩu nhóm (hoặc dự phòng) |
| **data** | `char[1024]` | `1024s` | 1024 bytes | Nội dung tin nhắn / Dữ liệu File (Chunk) |

### 2.2. Các loại thông điệp (Message Types)
Hệ thống sử dụng các hằng số (Enum) để định danh hành động:

* **Hệ thống:** `LOGIN_REQ` (0), `LOGIN_SUCCESS` (1), `LOGIN_FAIL` (2).
* **Chat:** `PRIVATE_CHAT` (3), `GROUP_CHAT` (4), `HISTORY` (11).
* **Bạn bè/Nhóm:** `FRIEND_REQ` (5), `FRIEND_ACCEPT` (6), `ADD_FRIEND_SUCC` (7), `CREATE/JOIN_GROUP` (8,9,10), `REQ_MEMBER_LIST` (13), `LEAVE/UNFRIEND` (15,16).
* **File:** `FILE_START` (18), `FILE_DATA` (19), `FILE_END` (20), `FILE_NOTIFY` (21), `DOWNLOAD_REQ` (22).
* **Game:** `GAME_REQ` (23), `GAME_ACCEPT` (24), `GAME_MOVE` (25), `GAME_END` (26).

---

## 3. PHÂN TÍCH MODULE SERVER (`Server/`)

Server được viết bằng **C++ (Winsock)**, sử dụng đa luồng (**Multi-threading**) để xử lý nhiều Client đồng thời.

### 3.1. Quản lý dữ liệu (`storage.cpp` & `storage.h`)
Module này đóng vai trò là "Database Layer", thao tác trực tiếp với các file text trong thư mục `Server/Data/`.

**Giải thích các hàm:**

* **`ensure_data_dir()`**: Kiểm tra và tạo thư mục `Server` và `Server/Data` nếu chưa tồn tại (sử dụng `_mkdir`).
* **`check_login(user, pass)`**:
    * Mở file `accounts.txt`. Quét từng dòng, tách chuỗi bằng ký tự `|`.
    * Nếu tìm thấy user: So khớp password.
    * Nếu không tìm thấy: Tự động ghi dòng mới (Đăng ký) và trả về `true`.
* **`add_friend_db(u1, u2)`**: Ghi quan hệ bạn bè vào `friends.txt` theo định dạng `User1|User2`.
* **`get_friend_list(user)`**: Quét file `friends.txt`, tìm tất cả các dòng có chứa `user` và trả về danh sách đối phương.
* **`create_group_db` / `add_group_member_db`**: Ghi thông tin nhóm vào `groups.txt` và thành viên vào `group_members.txt`.
* **`get_user_groups(user)`**: Trả về danh sách các nhóm mà user đang tham gia.
* **`load_groups_to_memory`**: Đọc toàn bộ file `groups.txt` đưa vào `std::map` trên RAM khi Server khởi động để truy xuất nhanh mật khẩu nhóm.
* **`save_message(sender, target, content, type)`**: Ghi log tin nhắn vào `messages.txt` để phục vụ tính năng tải lại lịch sử.
* **`get_user_history(user)`**: Đọc toàn bộ file tin nhắn (Lưu ý: Hàm này hiện tại load hết và lọc lại ở tầng logic chính).
* **`get_group_members(group)`**: Lọc file `group_members.txt` để lấy danh sách thành viên của một nhóm cụ thể. Xử lý cắt bỏ ký tự xuống dòng thừa (`\r\n`).

### 3.2. Logic chính (`server_main.cpp`)
Đây là trái tim của Server, quản lý kết nối và điều hướng gói tin.

**Biến toàn cục quan trọng:**
* `online_users`: `map<string, SOCKET>` - Lưu trạng thái user đang online.
* `groups`: `map<string, GroupInfo>` - Lưu thông tin nhóm và danh sách socket thành viên đang online trong nhóm đó.
* `data_cs`: `CRITICAL_SECTION` - Khóa an toàn để đồng bộ hóa các luồng (Thread-safety).

**Giải thích các hàm:**

* **`init_server_data()`**: Gọi khi Server bật. Load danh sách nhóm từ file lên RAM (groups map).
* **`sync_client_data(client, username)`**: Được gọi ngay sau khi login thành công.
    * Gửi danh sách bạn bè (`MSG_ADD_FRIEND_SUCC`).
    * Gửi danh sách nhóm (`MSG_ADD_GROUP_SUCC`).
    * Gửi lịch sử chat (`MSG_HISTORY`). Có logic kiểm tra quyền riêng tư: chỉ gửi tin nhắn nếu user là người gửi hoặc người nhận (hoặc thành viên nhóm).
* **`remove_line_from_file(filename, text)`**: Hàm tiện ích để xóa một dòng trong file text (dùng cho Unfriend/Leave Group). Cơ chế: Đọc file cũ -> Ghi sang file `.tmp` (bỏ qua dòng cần xóa) -> Xóa file cũ -> Đổi tên file mới.
* **`handle_client(LPVOID param)`**: **Hàm quan trọng nhất**. Chạy trên một luồng riêng cho mỗi Client. Vòng lặp `while(true)` nhận gói tin (`recv`) và xử lý dựa trên `msg.type`:
    * *Login:* Kiểm tra DB, update `online_users`, gọi `sync_client_data`. Tự động add socket vào các nhóm cũ (`[RE-JOIN]`).
    * *Chat (Private/Group):* Lưu DB -> Tìm socket đích -> Forward gói tin.
    * *File:* Nhận gói tin Binary -> Ghi vào file trên Server -> Thông báo cho người nhận.
    * *Download:* Đọc file trên Server -> Gửi chunk binary cho Client.
    * *Game:* Chuyển tiếp gói tin (Relay) giữa 2 người chơi.
* **`main()`**: Khởi tạo Winsock, Bind port 8888, Listen. Khi có kết nối mới (`accept`) -> Tạo Thread mới chạy `handle_client`.

---

## 4. PHÂN TÍCH MODULE CLIENT (`Client/`)

Client viết bằng **Python**, sử dụng thư viện `socket` cho mạng và `customtkinter` cho giao diện.

### 4.1. Lớp giao diện (`client_app.py`)

**Các lớp chính:**
* **`ContactButton`**: Widget tùy chỉnh hiển thị nút bạn bè/nhóm trong Sidebar. Hỗ trợ sự kiện chuột phải (Right-click) để rời nhóm/hủy kết bạn.
* **`CaroBoard`**: Cửa sổ bàn cờ (Toplevel). Vẽ bàn cờ bằng Canvas. Xử lý logic click chuột -> tính tọa độ -> gửi lên Server. Kiểm tra điều kiện thắng (5 quân liên tiếp).
* **`ChatClient`**: Lớp ứng dụng chính.

**Giải thích các hàm trong `ChatClient`:**

* **`pack(...)`**: Hàm tiện ích đóng gói dữ liệu theo format struct của C++ (1156 bytes).
* **`login()`**: Kết nối socket, gửi `MSG_LOGIN_REQ`.
* **`loop()`**: Luồng nền (**Daemon Thread**). Liên tục `recv` dữ liệu từ Server. Xử lý vấn đề phân mảnh TCP (đảm bảo nhận đủ 1156 bytes). Gọi `handle_packet` để xử lý gói tin.
* **`handle_packet(data)`**: Bộ điều hướng (Router). Giải mã gói tin. Cập nhật giao diện (Thêm bạn, hiện tin nhắn, hiện popup mời game/kết bạn). Nếu là `FILE_DATA` thì ghi vào file đang tải.
* **`process_chat_msg(...)`**: Xử lý logic hiển thị tin nhắn chat. Phân biệt tin nhắn thường và tin nhắn File (có tiền tố `[FILE]`).
* **`sending_file_thread(filepath)`**: Chạy trong luồng riêng để không treo giao diện. Đọc file local -> Chia nhỏ 1024 bytes -> Gửi `MSG_FILE_DATA` liên tục lên Server. Sau khi gửi xong, tự tạo một "nút file giả" trên khung chat để báo thành công.
* **`request_download(filename)`**: Mở hộp thoại "Save As", gửi yêu cầu `DOWNLOAD_REQ` lên Server.
* **`render_bubble(...)`**: Vẽ bong bóng chat. Nếu là tin nhắn: Vẽ Label. Nếu là File: Vẽ Button (màu xanh lá để tải, màu xanh dương để xem).
* **`start_game(...)`**: Khởi tạo cửa sổ `CaroBoard` khi nhận lời mời hoặc được chấp nhận.

---

## 5. LUỒNG HOẠT ĐỘNG (ALGORITHMS & FLOWS)

### 5.1. Luồng Gửi và Nhận File (Store-and-Forward)
Đây là thuật toán phức tạp nhất trong dự án.

1.  **Gửi (Client A -> Server):**
    * A chọn file. A gửi gói `FILE_START` (kèm kích thước file).
    * Server mở file `Server/Data/Files/Timestamp_TenFile`.
    * A gửi hàng loạt gói `FILE_DATA` (mỗi gói tối đa 1024 bytes payload).
    * Server nhận và ghi nối tiếp vào file.
    * A gửi `FILE_END`. Server đóng file.
2.  **Thông báo (Server -> Client B):**
    * Server gửi `FILE_NOTIFY` chứa tên file mới (đã có timestamp) cho B.
    * Server lưu log tin nhắn dạng `[FILE] TenFile` vào `messages.txt`.
    * B nhận thông báo -> Hiện nút "Download" trên khung chat.
3.  **Tải về (Client B -> Server -> Client B):**
    * B bấm nút Download -> Gửi `MSG_FILE_DOWNLOAD_REQ`.
    * Server đọc file từ ổ cứng -> Gửi `FILE_START` (kèm kích thước).
    * Server đọc từng chunk 1024 bytes -> Gửi `FILE_DATA` về B.
    * B nhận và ghi vào ổ cứng local.

### 5.2. Luồng Game Caro (Relay Mode)
Server đóng vai trò trung chuyển, không lưu trạng thái bàn cờ.

1.  **Thách đấu:** A gửi `GAME_REQ` cho B. Server chuyển tiếp cho B.
2.  **Chấp nhận:** B đồng ý (`GAME_ACCEPT`). Server báo cho A.
    * A (người mời) đi trước (Quân X).
    * B (người nhận) đi sau (Quân O).
3.  **Đánh cờ:**
    * A click ô (5,5). Client A gửi `GAME_MOVE` (data="5,5") lên Server.
    * Server chuyển tiếp gói đó cho B.
    * Client B nhận gói, tự động vẽ quân X vào ô (5,5) của mình.

### 5.3. Luồng Đồng bộ dữ liệu (Synchronization)
Đảm bảo khi đăng nhập sang máy khác vẫn thấy dữ liệu cũ.

1.  Client gửi `LOGIN_REQ`.
2.  Server xác thực thành công.
3.  Server gọi `sync_client_data`:
    * Đọc `friends.txt` -> Gửi danh sách bạn (để hiển thị Sidebar).
    * Đọc `groups.txt` -> Gửi danh sách nhóm.
    * Đọc `messages.txt` -> Gửi toàn bộ lịch sử chat liên quan đến user này.
4.  Client nhận và vẽ dần lên giao diện.

---

## 6. HƯỚNG DẪN CÀI ĐẶT VÀ CHẠY

### Yêu cầu hệ thống
* **Server:** Windows (do sử dụng thư viện `winsock2.h`, `windows.h`, `direct.h`). Compiler hỗ trợ C++ (như MinGW hoặc MSVC).
* **Client:** Python 3.x. Thư viện: `customtkinter` (`pip install customtkinter`).

### Các bước chạy

#### 1. Biên dịch Server
Sử dụng `g++` (MinGW) hoặc Visual Studio:

g++ server_main.cpp storage.cpp -o Server.exe -lws2_32


#### 2. Chạy file Server.exe 

#### 3. Chạy file client_app.py
 
