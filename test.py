import socket

HOST = '0.0.0.0' 
PORT = 5001

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(1)
    print(f"🔌 Listening on port {PORT}...")
    conn, addr = s.accept()
    print(f"✅ Connected by {addr}")
    with open("received_file.txt", "wb") as f:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            f.write(data)

    print("📄 File received successfully.")
    conn.close()
