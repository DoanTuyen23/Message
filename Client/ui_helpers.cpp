#include "ui_helpers.h"
#include <iostream>
#include <windows.h>

using namespace std;

void set_console_color(int color_code) {
    HANDLE hConsole = GetStdHandle(STD_OUTPUT_HANDLE);
    SetConsoleTextAttribute(hConsole, color_code);
}

void print_system_msg(string msg) {
    set_console_color(COLOR_RED);
    cout << "[SYSTEM] " << msg << endl;
    set_console_color(COLOR_WHITE); // Reset về trắng
}

void print_user_msg(string name, string msg) {
    cout << "\r"; // Xóa dòng hiện tại
    set_console_color(COLOR_CYAN);
    cout << name << ": ";
    set_console_color(COLOR_WHITE);
    cout << msg << endl;
    
    // In lại dấu nhắc nhập liệu
    set_console_color(COLOR_GREEN);
    cout << "You: ";
    set_console_color(COLOR_WHITE);
}

void print_my_msg(string msg) {
    // Hàm này dùng để vẽ lại tin nhắn của chính mình cho đẹp (nếu cần)
    // Hiện tại main đang in trực tiếp, nhưng logic UI nên nằm ở đây
}