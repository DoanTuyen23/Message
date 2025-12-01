#ifndef UI_HELPERS_H
#define UI_HELPERS_H

#include <string>

// Các mã màu
#define COLOR_RED 12
#define COLOR_GREEN 10
#define COLOR_CYAN 11
#define COLOR_WHITE 7

void set_console_color(int color_code);
void print_system_msg(std::string msg);
void print_user_msg(std::string name, std::string msg);
void print_my_msg(std::string msg);

#endif