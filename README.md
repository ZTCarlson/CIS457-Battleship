# CIS457-Battleship
### Zachary Carlson & Anthony Lazo

## References (for both client.py and server.py):
- https://www.geeksforgeeks.org/python-program-find-ip-address/
- https://github.com/katmfoo/python-client-server
- https://www.geeksforgeeks.org/how-to-validate-an-ip-address-using-regex/
- ChatGPT, for some initial code reference, bugfixes, and code cleanup

## Compile Instructions

Instructions are different depending on if you want to run the code on 2/3 hosts or just through localhost.

Also, it would be a good idea to ensure that any current instance of server or client running on the intended host(s) are closed before starting a new game to insure that there's no unintended overlap.

### Different hosts
Note that the code is not currently set up to run on hosts in different networks. Because of this, technically, this approach will still work for running the clients locally. It might just save some time to do the other approach, as you won't have to input the IP.

1. If it isn't already, set the `USE_LOCALHOST` variable to `False` in both `server.py` and `client.py`
2. On one host, open a terminal to the repository location and start the server
```
python3 server.py
```
3. If you're using 2 hosts, then the same host that the server is running on will also be 1 of the clients. If you're using 3 hosts, then the 2 other hosts are going to serve as the clients. Start the clients in a terminal to the repository on their respective hosts
```
python3 client.py
```
4. The client will ask the user for the server IP. Once the server starts, it will print an IP for the client to connect to. This is the private IP of the host. Input this IP address and press enter, and you should be good to go.

### Localhost
1. If it isn't already, set the `USE_LOCALHOST` variable to `True` in both `server.py` and `client.py`
2. Open 3 terminals to the repository location
3. Start the server in one terminal
```
python3 server.py
```
4. Start the clients in the other terminals
```
python3 client.py
```