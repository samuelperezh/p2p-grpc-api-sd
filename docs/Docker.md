# Pruebas y Despliegue en Docker
El proyecto se prueba localmente utilizando Docker. La configuración de Docker permite levantar múltiples peers en contenedores separados. El archivo `docker-compose.yml` define la estructura de red y los puertos expuestos para cada servicio.

### Configuración de la Red P2P
El archivo `docker-compose.yml` define una red `p2p_network` que conecta los contenedores de los peers y el servidor API. Cada peer tiene un volumen específico donde se almacenan los archivos locales que serán compartidos entre los nodos.