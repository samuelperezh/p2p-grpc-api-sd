import grpc
import requests
import file_transfer_pb2
import file_transfer_pb2_grpc
import sys
import os

# Directory for saving files
FILES_DIR = './files'

# Ensure the /files directory exists
if not os.path.exists(FILES_DIR):
    os.makedirs(FILES_DIR)

def download_file(filename):
    # Query the REST API for the file location
    buscar_url = 'http://localhost:4040/buscar'
    data = {'archivo': filename}

    response = requests.post(buscar_url, json=data)
    if response.status_code == 200:
        results = response.json().get('results', [])
        if results:
            peer_url = results[0]['url']
            
            # Handle the grpc:// protocol correctly
            grpc_address = peer_url.split('/download')[0].replace("grpc://", "")
            port = grpc_address.split(':')[-1]

            # Connect to the peer's gRPC server and download the file
            channel = grpc.insecure_channel(f'{grpc_address}')
            stub = file_transfer_pb2_grpc.FileTransferStub(channel)
            request = file_transfer_pb2.FileRequest(filename=filename)
            response = stub.GetFile(request)

            if response:
                # Save the file in /files directory
                with open(os.path.join(FILES_DIR, filename), 'wb') as f:
                    f.write(response.content)
                print(f"File {filename} downloaded successfully.")
            else:
                print(f"Failed to download {filename}.")
        else:
            print(f"No peers found for {filename}.")
    else:
        print(f"Search failed: {response.content}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: client.py <filename>")
        sys.exit(1)

    file_name = sys.argv[1]
    download_file(file_name)