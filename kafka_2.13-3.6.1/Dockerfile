FROM openjdk:17

RUN microdnf install -y util-linux && microdnf clean all

WORKDIR /opt/kafka
COPY . .

RUN chmod +x /opt/kafka/bin/*.sh /opt/kafka/entrypoint.sh

ENTRYPOINT ["/opt/kafka/entrypoint.sh"]
