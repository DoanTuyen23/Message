#ifndef PROTOCOL_H
#define PROTOCOL_H

#define SERVER_PORT 8888
#define SERVER_IP "127.0.0.1"
#define NAME_LEN 32
#define PASS_LEN 32
#define BUFF_SIZE 1024

// Tự động đánh số từ 0 -> 17, khớp với Client Python
enum MessageType {
    MSG_LOGIN_REQ = 0,      // 0
    MSG_LOGIN_SUCCESS,      // 1
    MSG_LOGIN_FAIL,         // 2
    
    MSG_PRIVATE_CHAT,       // 3
    MSG_GROUP_CHAT,         // 4
    
    // --- KẾT BẠN & DANH SÁCH ---
    MSG_FRIEND_REQ,         // 5
    MSG_FRIEND_ACCEPT,      // 6
    MSG_ADD_FRIEND_SUCC,    // 7
    
    MSG_CREATE_GROUP_REQ,   // 8
    MSG_JOIN_GROUP_REQ,     // 9
    MSG_ADD_GROUP_SUCC,     // 10
    
    MSG_HISTORY,            // 11

    // --- CÁC TÍNH NĂNG MỚI (Khớp với logic Client) ---
    // Lưu ý: Kiểm tra kỹ thứ tự số bên Client Python
    MSG_CREATE_GROUP_FAIL,  // 13
    MSG_REQ_MEMBER_LIST,    // 14
    MSG_RESP_MEMBER_LIST,   // 15
    
    MSG_LEAVE_GROUP,        // 16
    MSG_UNFRIEND,           // 17
    MSG_REMOVE_CONTACT      // 18
};

// --- QUAN TRỌNG: BẮT BUỘC DÙNG #pragma pack(1) ---
// Lý do: Để đảm bảo Struct C++ có kích thước CHÍNH XÁC là 1156 bytes
// Không bị trình biên dịch tự chèn thêm byte rác vào giữa các biến.
#pragma pack(push, 1)

struct Message {
    int type;                  // 4 bytes
    char name[NAME_LEN];       // 32 bytes
    char password[PASS_LEN];   // 32 bytes
    char target[NAME_LEN];     // 32 bytes
    char group_pass[PASS_LEN]; // 32 bytes
    char data[BUFF_SIZE];      // 1024 bytes
};                             // TỔNG: 1156 bytes

#pragma pack(pop)

#endif