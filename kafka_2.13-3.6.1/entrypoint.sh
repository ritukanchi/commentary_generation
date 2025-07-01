#!/bin/bash
set -e

CONFIG="/opt/kafka/config/kraft/server${KAFKA_NODE_ID}.properties"
LOG_DIR=$(grep '^log.dirs=' "$CONFIG" | cut -d'=' -f2 | tr -d '[:space:]')
META_FILE="$LOG_DIR/meta.properties"

if [ ! -f "$META_FILE" ]; then
    echo "Formatting storage for node $KAFKA_NODE_ID..."
    echo "Using Cluster ID: $CLUSTER_ID"
    /opt/kafka/bin/kafka-storage.sh format -t "$CLUSTER_ID" -c "$CONFIG"
fi

echo "Starting Kafka node $KAFKA_NODE_ID..."
exec /opt/kafka/bin/kafka-server-start.sh "$CONFIG"
