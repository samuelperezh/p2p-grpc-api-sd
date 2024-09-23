FROM python:3.11-slim

WORKDIR /peer

COPY . /peer

RUN pip install --no-cache-dir -r requirements.txt

ENV GRPC_PORT=50051
ENV USERNAME=peer
ENV PASSWORD=123
ENV HOST=api_rest
ENV PORT=5000
ENV DOCKER=true

EXPOSE ${GRPC_PORT}

CMD python peer_server.py ${USERNAME} ${PASSWORD}