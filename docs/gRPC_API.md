# gRPC y REST API
El proyecto utiliza gRPC para la comunicación entre peers y REST API para la localización de recursos.

## gRPC
El archivo `file_transfer.proto` define los servicios y mensajes utilizados en gRPC. El servidor gRPC implementa los servicios de localización y transferencia simulada de archivos, mientras que los clientes (otros peers) envían solicitudes de descarga de archivos.

## REST API
La API REST actúa como un directorio donde los peers pueden consultar información sobre los archivos almacenados en otros nodos. Utiliza Flask para manejar las solicitudes HTTP y devolver respuestas en formato JSON.
