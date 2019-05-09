\clean:
	rm HB/*.pyc HB/*.out fuzzer/*.pyc fuzzer/._*  HB/*.txt fuzzer/*.txt

runTests:
	cd /ethracer/HB && python3.6 main.py --checkone ../tests/0xfbe0e9846bd736b84a0a973322ad2a1fc8d7e5ca.sol 0xfbe0e9846bd736b84a0a973322ad2a1fc8d7e5ca --blockchain --atblock 4999801 --owner 0x7dbd71b247a000b8db0bf9dc57467c3a06ec0a47
	cd /ethracer/HB && python3.6 main.py --checkone ../tests/0x325476448021c96c4bf54af304ed502bb7ad0675.sol 0x325476448021c96c4bf54af304ed502bb7ad0675 --blockchain --owner 0x056682f1cf0dc48266c1e47057297a64b58bb6fa
