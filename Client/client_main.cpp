#include <iostream>
#include <winsock2.h>
#include <windows.h>
#include <string>
#include "../Common/protocol.h"
#include "ui_helpers.h"

#pragma comment(lib, "ws2_32.lib")

using namespace std;

SOCKET client_socket;
bool is_running = true;

DWORD WINAPI receive_thread(LPVOID param) {
    Message msg;
    while (is_running) {
        int bytes = recv(client_socket, (char*)&msg, sizeof(Message), 0);
        if (bytes <= 0) {
            print_system_msg("Mat ket noi Server!");
            is_running = false;
            break;
        }

        if (msg.type == MSG_CHAT) {
            print_user_msg(msg.name, msg.data);
        }
    }
    return 0;
}

int main() {
    SetConsoleTitleA("Chat Client - C++ Project"); // Đặt tên cửa sổ
    WSADATA wsaData;
    WSAStartup(MAKEWORD(2, 2), &wsaData);

    client_socket = socket(AF_INET, SOCK_STREAM, 0);
    sockaddr_in server_addr;
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = inet_addr(SERVER_IP);
    server_addr.sin_port = htons(SERVER_PORT);

    if (connect(client_socket, (sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
        print_system_msg("Khong the ket noi toi Server!");
        return 1;
    }

    // --- LOGIC ĐĂNG NHẬP ---
    Message msg;
    while (true) {
        system("cls"); // Xóa màn hình cho sạch
        print_system_msg("=== DANG NHAP HE THONG ===");
        
        cout << "Tai khoan: ";
        cin.getline(msg.name, NAME_LEN);
        
        cout << "Mat khau: ";
        cin.getline(msg.password, PASS_LEN);
        
        msg.type = MSG_LOGIN_REQ;
        send(client_socket, (char*)&msg, sizeof(Message), 0);

        // Chờ phản hồi từ Server
        Message response;
        recv(client_socket, (char*)&response, sizeof(Message), 0);
        
        if (response.type == MSG_LOGIN_SUCCESS) {
            print_system_msg(response.data);
            break; // Thoát vòng lặp login
        } else {
            print_system_msg(response.data);
            system("pause");
        }
    }

    // --- VÀO CHAT ---
    system("cls");
    set_console_color(COLOR_GREEN);
    cout << "Xin chao " << msg.name << "! Bat dau chat..." << endl;
    set_console_color(COLOR_WHITE);

    CreateThread(NULL, 0, receive_thread, NULL, 0, NULL);

    while (is_running) {
        string input;
        set_console_color(COLOR_GREEN);
        cout << "You: ";
        set_console_color(COLOR_WHITE);
        
        getline(cin, input);

        if (input == "exit") break;
        if (!is_running) break;

        msg.type = MSG_CHAT;
        strcpy(msg.data, input.c_str());
        send(client_socket, (char*)&msg, sizeof(Message), 0);
    }

    is_running = false;
    closesocket(client_socket);
    WSACleanup();
    return 0;
}