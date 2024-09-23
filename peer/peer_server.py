import os
import grpc
from concurrent import futures
import file_transfer_pb2
import file_transfer_pb2_grpc
import requests
import json
import signal
import sys
import socket
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

if len(sys.argv) != 3:
    print("Usage: peer_server.py <username> <password>")
    sys.exit(1)

USERNAME = sys.argv[1]
PASSWORD = sys.argv[2]
TOKEN = None
FILES_DIR = './files'

if not os.path.exists(FILES_DIR):
    os.makedirs(FILES_DIR)

class FileTransferServicer(file_transfer_pb2_grpc.FileTransferServicer):
    def GetFile(self, request, context):
        filename = os.path.join(FILES_DIR, request.filename)
        if os.path.exists(filename):
            with open(filename, 'rb') as f:
                content = f.read()
            return file_transfer_pb2.FileResponse(content=content)
        else:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('File not found!')
            return file_transfer_pb2.FileResponse()

# Define the event handler for directory changes
class DirectoryChangeHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        print("Directory change detected. Reindexing files...")
        index_files()

def start_grpc_server():
    grpc_port = int(os.getenv('GRPC_PORT', 50051))
    
    server = grpc.server(futures.ThreadPoolExecutor())
    file_transfer_pb2_grpc.add_FileTransferServicer_to_server(FileTransferServicer(), server)
    server.add_insecure_port(f'[::]:{grpc_port}')
    server.start()

    def signal_handler(sig, frame):
        print('Shutting down gRPC server...')
        logout()
        server.stop(0)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    global GRPC_PORT
    GRPC_PORT = grpc_port
    print(f'gRPC server running on port {grpc_port}')
    
    login()
    index_files()
    start_directory_monitoring()
    server.wait_for_termination()

def get_ip_address():
    """Dynamically determine if we should use localhost, container name, or the public IP."""
    try:
        if os.getenv('CLOUD_ENV', 'false') == 'true':
            try:
                public_ip = subprocess.check_output(['curl', '-s', 'ifconfig.me']).decode('utf-8').strip()
                return public_ip
            except subprocess.CalledProcessError as e:
                print(f"Failed to retrieve public IP: {e}")
                return 'localhost'

        if os.getenv('DOCKER', 'false') == 'true':
            container_name = os.getenv('HOSTNAME', 'localhost')
            return container_name

        return 'localhost'

    except Exception as e:
        print(f"Error getting IP address: {e}")
        return 'localhost'

def login():
    login_url = f'http://{host}:{port}/login'
    peer_ip = get_ip_address()
    peer_url = f"grpc://{peer_ip}:{GRPC_PORT}"
    data = {'username': USERNAME, 'password': PASSWORD, 'url': peer_url}
    
    response = requests.post(login_url, json=data)
    if response.status_code == 200:
        global TOKEN
        token = response.json().get('token')
        TOKEN = token
        print(f"Peer {USERNAME} logged in successfully with token: {token}")
    else:
        print(f"Login failed: {response.content}")
        sys.exit(1)

def index_files():
    files = [f for f in os.listdir(FILES_DIR) if os.path.isfile(os.path.join(FILES_DIR, f))]
    indice_url = f'http://{host}:{port}/indice'
    headers = {'Authorization': f'Bearer {TOKEN}'}
    data = {'username': USERNAME, 'archivos': files}

    response = requests.post(indice_url, json=data, headers=headers)
    if response.status_code == 200:
        print("Files indexed successfully.")
    else:
        print(f"File indexing failed: {response.content}")

def logout():
    logout_url = f'http://{host}:{port}/logout'
    headers = {'Authorization': f'Bearer {TOKEN}'}
    data = {'username': USERNAME}
    
    response = requests.post(logout_url, json=data, headers=headers)
    if response.status_code == 200:
        print(f"Peer {USERNAME} logged out successfully.")
    else:
        print(f"Logout failed: {response.content}")

def start_directory_monitoring():
    path = FILES_DIR
    event_handler = DirectoryChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()
    print("Directory monitoring started for /files.")

    try:
        while True:
            observer.join(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == '__main__':
    host = os.getenv('HOST', "localhost")
    port = os.getenv('PORT', "5000")
    start_grpc_server()