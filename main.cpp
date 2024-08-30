#include <iostream>
#include "logIn.h"
#include "register.h"

using namespace std;

void menu() {
    cout << "======================================================================" << endl;
    cout << "                                Menu                                  " << endl;
    cout << "======================================================================" << endl;
    cout << "                       1. Login Account                               " << endl;
    cout << "                       2. Register Account                            " << endl;
    cout << "                       0. Exit                                        " << endl;
    cout << "======================================================================" << endl;
}

int main() {
    system("cls");

    int op;
    do {
        menu();
        cout << "[+] Insert your option : "; cin >> op;
        switch(op) {
            case 1 : { // login
                system("cls");
                cout << "======================================================================" << endl;
                cout << "                            Login Account                             " << endl;
                cout << "======================================================================" << endl;
                Login user2;
                user2.loginUser();
                cout << "======================================================================" << endl;
                break;
            }
            case 2 : { // register
                system("cls");
                cout << "======================================================================" << endl;
                cout << "                          Register Account                            " << endl;
                cout << "======================================================================" << endl;
                Register user1;
                user1.setUserRegister();
                cout << "======================================================================" << endl;
                break;
            }
            default : {
                cout << "Exiting..." << endl;
            }
        }
    } while(op);

    return 0;
}