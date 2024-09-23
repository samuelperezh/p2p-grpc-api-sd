# Ejecución del Proyecto
Para ejecutar el proyecto, asegúrese de tener Docker instalado y siga los siguientes pasos:

1. **Construir los contenedores Docker:**
   ```bash
   docker-compose build
   ```
2. **Levantar los servicios:**
   ```bash
   docker-compose up
   ```

Esto iniciará los contenedores para los peers y el servidor API. Los peers estarán escuchando en los puertos 50051 y 50052, mientras que el servidor API estará disponible en el puerto 5000【17†source】.
