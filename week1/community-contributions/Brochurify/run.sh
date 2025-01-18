#!/bin/bash

if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo ".env file not found. Please create it with SOCKET_HOST and SOCKET_PORT."
    exit 1
fi

sed -i "s/SOCKET_HOST/$SOCKET_HOST/g" static/index.html
sed -i "s/SOCKET_PORT/$SOCKET_PORT/g" static/index.html

if lsof -i:$SOCKET_PORT > /dev/null 2>&1; then
    echo "Port $SOCKET_PORT is already in use. Please free the port or use a different one."
    exit 1
fi


echo "Starting the Python application on $SOCKET_HOST:$SOCKET_PORT..."
python main.py &
APP_PID=$!
sleep 2


STATIC_DIR="./static"
if [ ! -d "$STATIC_DIR" ]; then
    echo "Static directory not found at $STATIC_DIR. Please ensure it exists."
    exit 1
fi

cd $STATIC_DIR
echo "Starting the static server in $STATIC_DIR on $STATIC_HOST:$STATIC_PORT..."
python -m http.server $STATIC_PORT --bind $STATIC_HOST &
STATIC_PID=$!

cd ..


echo "Servers are running. Press Ctrl+C to stop."
trap "kill $STATIC_PID $APP_PID" SIGINT SIGTERM
wait
