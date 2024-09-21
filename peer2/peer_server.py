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
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# The username and password will now be passed as command-line arguments
if len(sys.argv) != 3:
    print("Usage: server.py <username> <password>")
    sys.exit(1)

USERNAME = sys.argv[1]
PASSWORD = sys.argv[2]

# Token will be set after login
TOKEN = None

# Directory for files
FILES_DIR = './files'

# Ensure the /files directory exists
if not os.path.exists(FILES_DIR):
    os.makedirs(FILES_DIR)

# Define the file transfer gRPC service
class FileTransferServicer(file_transfer_pb2_grpc.FileTransferServicer):
    def GetFile(self, request, context):
        filename = os.path.join(FILES_DIR, request.filename)  # Serve files from /files directory
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
        # Whenever a file is added, removed, modified, or renamed in /files, reindex the files
        print("Directory change detected. Reindexing files...")
        index_files()

def start_grpc_server():
    # Use environment variable for port, or default to 50051
    grpc_port = int(os.getenv('GRPC_PORT', 50051))
    
    # Start the gRPC server on the specified port
    server = grpc.server(futures.ThreadPoolExecutor())
    file_transfer_pb2_grpc.add_FileTransferServicer_to_server(FileTransferServicer(), server)
    server.add_insecure_port(f'[::]:{grpc_port}')  # Fixed port from environment variable
    server.start()

    # Register signal handler for stopping the server and logging out
    def signal_handler(sig, frame):
        print('Shutting down gRPC server...')
        logout()
        server.stop(0)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    global GRPC_PORT
    GRPC_PORT = grpc_port  # Store port for use in login
    print(f'gRPC server running on port {grpc_port}')
    
    login()  # Automatically log in the peer
    index_files()  # Automatically index files
    start_directory_monitoring()
    server.wait_for_termination()

def get_ip_address():
    """Dynamically determine if we should use localhost or the private IP."""
    try:
        # Attempt to detect if this is running in the cloud by checking environment variables or network info
        if os.getenv('DOCKER', 'false') == 'true' or os.getenv('CLOUD_ENV', 'false') == 'true':
            # Running in Docker or cloud: Use the machine's private IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))  # Google's public DNS
            ip = s.getsockname()[0]
            s.close()
            return ip
        else:
            # Local development: Use localhost
            return 'localhost'
    except Exception as e:
        print(f"Error getting IP address: {e}")
        return 'localhost'

# REST API interaction functions
def login():
    # Automatically log in the peer via REST API
    login_url = 'http://localhost:4040/login'
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
    # Index the files in the /files directory via REST API
    files = [f for f in os.listdir(FILES_DIR) if os.path.isfile(os.path.join(FILES_DIR, f))]
    indice_url = 'http://localhost:4040/indice'
    headers = {'Authorization': f'Bearer {TOKEN}'}
    data = {'username': USERNAME, 'archivos': files}

    response = requests.post(indice_url, json=data, headers=headers)
    if response.status_code == 200:
        print("Files indexed successfully.")
    else:
        print(f"File indexing failed: {response.content}")

def logout():
    # Log out the peer via REST API
    logout_url = 'http://localhost:4040/logout'
    headers = {'Authorization': f'Bearer {TOKEN}'}
    data = {'username': USERNAME}
    
    response = requests.post(logout_url, json=data, headers=headers)
    if response.status_code == 200:
        print(f"Peer {USERNAME} logged out successfully.")
    else:
        print(f"Logout failed: {response.content}")

# Function to start monitoring the /files directory for changes
def start_directory_monitoring():
    path = FILES_DIR  # Monitor the /files directory
    event_handler = DirectoryChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()
    print("Directory monitoring started for /files.")

    # Keep running the observer in the background
    try:
        while True:
            observer.join(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == '__main__':
    start_grpc_server()  # No port is specified here; the OS assigns one