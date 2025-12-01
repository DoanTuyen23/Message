#include "storage.h"
#include <fstream>
#include <iostream>
#include <vector>

using namespace std;

const string ACCOUNT_FILE = "Server/accounts.txt";
const string LOG_FILE = "Server/chat_history.log";

bool check_login(string username, string password) {
    ifstream file(ACCOUNT_FILE);
    string line, u, p;
    bool found = false;

    // 1. Kiểm tra xem user đã tồn tại chưa
    if (file.is_open()) {
        while (getline(file, line)) {
            size_t delimiterPos = line.find("|");
            if (delimiterPos != string::npos) {
                u = line.substr(0, delimiterPos);
                p = line.substr(delimiterPos + 1);
                if (u == username) {
                    found = true;
                    if (p == password) return true; // Đúng pass
                    else return false; // Sai pass
                }
            }
        }
        file.close();
    }

    // 2. Nếu chưa có -> Tạo tài khoản mới
    if (!found) {
        ofstream outfile(ACCOUNT_FILE, ios::app);
        outfile << username << "|" << password << endl;
        outfile.close();
        cout << "[DB] Tao tai khoan moi: " << username << endl;
        return true;
    }

    return false;
}

void log_message(string sender, string content) {
    ofstream file(LOG_FILE, ios::app);
    if (file.is_open()) {
        // Bạn có thể thêm timestamp vào đây nếu muốn
        file << "[" << sender << "]: " << content << endl;
        file.close();
    }
}