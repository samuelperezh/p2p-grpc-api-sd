import grpc
import requests
import file_transfer_pb2
import file_transfer_pb2_grpc
import sys
import os

FILES_DIR = './files'

if not os.path.exists(FILES_DIR):
    os.makedirs(FILES_DIR)

def download_file(filename):
    api_host = os.getenv('HOST', "localhost")
    api_port = os.getenv('PORT', "5000")
    
    buscar_url = f'http://{api_host}:{api_port}/buscar'
    data = {'archivo': filename}

    response = requests.post(buscar_url, json=data)
    if response.status_code == 200:
        results = response.json().get('results', [])
        if results:
            peer_url = results[0]['url']
            
            grpc_address = peer_url.split('/download')[0].replace("grpc://", "")
            grpc_host, grpc_port = grpc_address.split(':')

            channel = grpc.insecure_channel(f'{grpc_host}:{grpc_port}')
            stub = file_transfer_pb2_grpc.FileTransferStub(channel)
            request = file_transfer_pb2.FileRequest(filename=filename)
            response = stub.GetFile(request)

            if response:
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
        print("Usage: peer_client.py <filename>")
        sys.exit(1)

    file_name = sys.argv[1]
    download_file(file_name)