#ifndef STORAGE_H
#define STORAGE_H

#include <string>

// Hàm kiểm tra đăng nhập (Trả về true nếu OK, false nếu sai pass)
// Nếu user chưa tồn tại -> Tự động tạo mới và trả về true
bool check_login(std::string username, std::string password);

// Hàm ghi log chat
void log_message(std::string sender, std::string content);

#endif