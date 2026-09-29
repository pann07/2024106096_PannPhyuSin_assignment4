import socket
import os
from datetime import datetime


HOST = "127.0.0.1"
PORT = 8000

REQUEST_DIR = "request"
IMAGE_DIR = "image"

os.makedirs(REQUEST_DIR, exist_ok=True)
os.makedirs(IMAGE_DIR, exist_ok=True)


def receive_request(client_socket):
    data = b""

    # HTTP header 받기
    while b"\r\n\r\n" not in data:
        chunk = client_socket.recv(4096)

        if not chunk:
            break

        data += chunk

    header_end = data.find(b"\r\n\r\n")

    if header_end == -1:
        return data

    header = data[:header_end]
    body = data[header_end + 4:]

    # Content-Length 확인
    content_length = 0

    for line in header.split(b"\r\n"):
        if line.lower().startswith(b"content-length:"):
            content_length = int(line.split(b":", 1)[1].strip())
            break

    # body 전체 받기
    while len(body) < content_length:
        chunk = client_socket.recv(4096)

        if not chunk:
            break

        body += chunk

    return header + b"\r\n\r\n" + body


def save_request(data):
    now = datetime.now()
    filename = now.strftime("%Y-%m-%d-%H-%M-%S") + ".bin"

    filepath = os.path.join(REQUEST_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(data)

    print("Request saved:", filepath)

    return filepath


def get_boundary(header):
    header_text = header.decode("latin-1")

    for line in header_text.split("\r\n"):
        if line.lower().startswith("content-type:"):
            if "multipart/form-data" in line:
                parts = line.split("boundary=", 1)

                if len(parts) == 2:
                    boundary = parts[1].strip()

                    if boundary.startswith('"') and boundary.endswith('"'):
                        boundary = boundary[1:-1]

                    return boundary.encode("latin-1")

    return None


def save_image(data):
    header_end = data.find(b"\r\n\r\n")

    if header_end == -1:
        return

    header = data[:header_end]
    body = data[header_end + 4:]

    boundary = get_boundary(header)

    if boundary is None:
        print("Multipart boundary not found.")
        return

    boundary_marker = b"--" + boundary

    parts = body.split(boundary_marker)

    for part in parts:

        if b"Content-Disposition:" not in part:
            continue

        if b"name=\"image\"" not in part:
            continue

        part_header_end = part.find(b"\r\n\r\n")

        if part_header_end == -1:
            continue

        part_header = part[:part_header_end]
        image_data = part[part_header_end + 4:]

        # 마지막 \r\n 제거
        if image_data.endswith(b"\r\n"):
            image_data = image_data[:-2]

        # filename 확인
        part_header_text = part_header.decode("latin-1")

        filename = "image.jpg"

        for line in part_header_text.split("\r\n"):
            if "filename=" in line:
                filename_part = line.split("filename=", 1)[1]
                filename = filename_part.strip('"')

        # 안전한 파일명
        filename = os.path.basename(filename)

        filepath = os.path.join(IMAGE_DIR, filename)

        with open(filepath, "wb") as f:
            f.write(image_data)

        print("Image saved:", filepath)
        print("Image size:", len(image_data), "bytes")


def send_response(client_socket):
    response_body = b"OK"

    response = (
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Type: text/plain\r\n"
        b"Content-Length: 2\r\n"
        b"Connection: close\r\n"
        b"\r\n"
        + response_body
    )

    client_socket.sendall(response)


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_socket.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )

    server_socket.bind((HOST, PORT))
    server_socket.listen(5)

    print(f"Server started: http://{HOST}:{PORT}")

    while True:
        client_socket, client_address = server_socket.accept()

        print("\nClient connected:", client_address)

        try:
            request_data = receive_request(client_socket)

            # 실습 1
            save_request(request_data)

            # 실습 2
            save_image(request_data)

            # Client에게 응답
            send_response(client_socket)

        except Exception as e:
            print("Error:", e)

        finally:
            client_socket.close()
            print("Client disconnected")


if __name__ == "__main__":
    main()