#include <iostream>
#include <winsock2.h>
#include <windows.h>
#include <vector>
#include <string>
#include "../Common/protocol.h"
#include "storage.h" // Nhớ phải có file storage.h và storage.cpp như hướng dẫn trước

#pragma comment(lib, "ws2_32.lib") 

using namespace std;

// Biến toàn cục
CRITICAL_SECTION client_cs; 
vector<SOCKET> clients;

// Hàm gửi tin cho mọi người (trừ người gửi)
void broadcast_message(Message msg, SOCKET sender_socket) {
    EnterCriticalSection(&client_cs);
    for (int i = 0; i < clients.size(); i++) {
        if (clients[i] != sender_socket) {
            send(clients[i], (char*)&msg, sizeof(Message), 0);
        }
    }
    LeaveCriticalSection(&client_cs);
    
    // Ghi log chat vào file
    if (msg.type == MSG_CHAT) {
        log_message(msg.name, msg.data);
    }
}

// Hàm xử lý từng Client (Chạy trên luồng riêng)
DWORD WINAPI handle_client(LPVOID param) {
    SOCKET client_socket = (SOCKET)param;
    Message msg;
    bool is_logged_in = false;
    char my_name[NAME_LEN] = "";
    
    while (true) {
        int bytes = recv(client_socket, (char*)&msg, sizeof(Message), 0);
        if (bytes <= 0) break;

        // --- 1. XỬ LÝ ĐĂNG NHẬP ---
        if (msg.type == MSG_LOGIN_REQ) {
            bool ok = check_login(msg.name, msg.password);
            Message response;
            
            if (ok) {
                // Phản hồi: Đăng nhập thành công
                response.type = MSG_LOGIN_SUCCESS;
                strcpy(response.data, "Dang nhap thanh cong!");
                send(client_socket, (char*)&response, sizeof(Message), 0);
                
                // Lưu trạng thái đăng nhập
                is_logged_in = true;
                strcpy(my_name, msg.name);
                cout << "[LOGIN] " << my_name << " is online." << endl;

                // Thêm socket vào danh sách quản lý
                EnterCriticalSection(&client_cs);
                clients.push_back(client_socket);
                LeaveCriticalSection(&client_cs);
            } else {
                // Phản hồi: Thất bại
                response.type = MSG_LOGIN_FAIL;
                strcpy(response.data, "Sai mat khau hoac loi he thong!");
                send(client_socket, (char*)&response, sizeof(Message), 0);
            }
        }
        // --- 2. XỬ LÝ CHAT ---
        else if (msg.type == MSG_CHAT) {
            if (is_logged_in) {
                cout << "[CHAT] " << msg.name << ": " << msg.data << endl;
                broadcast_message(msg, client_socket);
            }
        }
    }

    // Khi client ngắt kết nối
    if (is_logged_in) {
        EnterCriticalSection(&client_cs);
        for (int i = 0; i < clients.size(); i++) {
            if (clients[i] == client_socket) {
                clients.erase(clients.begin() + i);
                break;
            }
        }
        LeaveCriticalSection(&client_cs);
        cout << "[DISCONNECT] " << my_name << endl;
    }
    
    closesocket(client_socket);
    return 0;
}

// --- HÀM MAIN SERVER ---
int main() {
    // Khởi tạo khóa an toàn
    InitializeCriticalSection(&client_cs);

    // Khởi tạo Winsock
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        cerr << "WSAStartup failed!" << endl;
        return 1;
    }

    // Tạo socket lắng nghe
    SOCKET server_socket = socket(AF_INET, SOCK_STREAM, 0);
    sockaddr_in server_addr;
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(SERVER_PORT);

    // Bind và Listen
    if (bind(server_socket, (sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
        cerr << "Khong the Bind port " << SERVER_PORT << ". Port co the dang ban!" << endl;
        return 1;
    }
    listen(server_socket, 5);

    cout << "=== SERVER DATABASE STARTED ON PORT " << SERVER_PORT << " ===" << endl;
    cout << "Cho ket noi tu Client..." << endl;

    // Vòng lặp chính: Chấp nhận kết nối
    while (true) {
        SOCKET client_socket = accept(server_socket, NULL, NULL);
        if (client_socket != INVALID_SOCKET) {
            // Tạo luồng mới cho khách này
            CreateThread(NULL, 0, handle_client, (LPVOID)client_socket, 0, NULL);
        }
    }

    // Dọn dẹp (thực tế code server ít khi chạy tới đây vì vòng lặp while true)
    DeleteCriticalSection(&client_cs);
    closesocket(server_socket);
    WSACleanup();
    return 0;
}