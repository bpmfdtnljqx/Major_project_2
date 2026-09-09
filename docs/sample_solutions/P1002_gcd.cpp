// P1002 最大公约数 — C++ 样例（可直接提交，AC）
#include <bits/stdc++.h>
using namespace std;

int main() {
    long long a, b;
    cin >> a >> b;
    while (b) {
        long long t = a % b;
        a = b;
        b = t;
    }
    cout << a << endl;
    return 0;
}
