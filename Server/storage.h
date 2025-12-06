#ifndef STORAGE_H
#define STORAGE_H

// --- THÊM CÁC DÒNG NÀY ---
#include <string>
#include <vector>
#include <map>
using namespace std; 
// -------------------------

// Các khai báo hàm cũ của bạn
bool check_login(string username, string password);
void add_friend_db(string user1, string user2);
vector<string> get_friend_list(string user);
void create_group_db(string name, string pass);
void add_group_member_db(string group, string user);
vector<string> get_user_groups(string user);
void load_groups_to_memory(map<string, string>& groups_map); // Lưu ý: Cần thêm #include <map> nếu dùng map ở đây
void save_message(string sender, string target, string content, int type);
vector<string> get_user_history(string username);

// Hàm mới thêm
vector<string> get_group_members(string group_name);

#endif