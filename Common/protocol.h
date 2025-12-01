#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <cstdint>

// Cấu hình chung
#define SERVER_PORT 8888
#define SERVER_IP "127.0.0.1"
#define BUFF_SIZE 1024
#define NAME_LEN 32
#define PASS_LEN 32  // <--- Mới thêm cái này

enum MessageType {
    MSG_LOGIN_REQ,      // <--- Đổi tên mới cho khớp code Server
    MSG_LOGIN_SUCCESS,  // <--- Mới thêm
    MSG_LOGIN_FAIL,     // <--- Mới thêm
    MSG_CHAT,
    MSG_DISCONNECT
};

struct Message {
    int type;
    char name[NAME_LEN];
    char password[PASS_LEN]; // <--- Mới thêm trường này
    char data[BUFF_SIZE];
};

#endif