# Descripción de los Microservicios
## Peer Cliente (PCliente)
El peer cliente es responsable de enviar solicitudes de localización de archivos a otros peers utilizando API REST o gRPC. Implementa la funcionalidad para interactuar con otros peers, permitiendo la descarga simulada de archivos.

## Peer Servidor (PServidor)
El peer servidor responde las solicitudes entrantes de otros peers, proporcionando una lista de archivos disponibles en su directorio y simulando la transferencia de archivos mediante servicios DUMMY. La transferencia real no se implementa, pero la lógica para realizar un "eco" de carga y descarga de archivos está presente.

## API REST
El servidor API se comunica con los peers a través de una API REST, actuando como un directorio centralizado que ayuda a los peers a localizar recursos en la red.