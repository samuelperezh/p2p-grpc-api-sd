# Componentes del Proyecto
Los componentes principales del proyecto están estructurados en varias capas, cada una con responsabilidades específicas.

1. **peer_client.py:** Implementa la lógica del cliente, permitiendo a los peers enviar solicitudes a otros peers para buscar y descargar archivos.
2. **peer_server.py:** Define el servidor gRPC que escucha las solicitudes entrantes de otros peers y responde con información sobre los archivos almacenados en el nodo.
3. **file_transfer.proto:** Define el protocolo gRPC utilizado para la comunicación entre peers, especificando los mensajes y servicios.
4. **app.py:** Implementa el microservicio de API REST que facilita la localización de archivos en el sistema.
5. **docker-compose.yml:** Archivo de configuración para el despliegue de contenedores Docker que define la estructura de red y servicios del sistema P2P【17†source】.
6. **Dockerfile:** Define el entorno y las dependencias necesarias para construir y ejecutar los contenedores Docker que albergan los peers.
