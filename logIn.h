#pragma once

#include <iostream>
#include <vector>
#include "register.h"
using namespace std;

class Login{
    private :
        string emailOrUsername, password;

    public :    
        void loginUser(){
            cout << "Enter your email or username: ";
            cin.ignore();
            getline(cin, emailOrUsername);
            cout << "Enter your password : ";
            getline(cin, password);

            bool isFound = 0;
            for (int i = 0; i < usernames.size(); i++) {
                if ((usernames[i] == emailOrUsername || emails[i] == emailOrUsername) && passwords[i] == password) {
                    cout << "Login successfully." << endl;
                    isFound = 1;
                    break;
                }
            }
            if (!isFound) cout << "Login unsuccesfully..." << endl;
        };

};


