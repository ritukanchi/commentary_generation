FROM openjdk:17

RUN microdnf install -y util-linux && microdnf clean all

WORKDIR /opt/kafka
COPY . .

RUN chmod -R a+r /opt/kafka/config && \
    chmod -R a+rx /opt/kafka/bin && \
    chmod -R a+r /opt/kafka/libs && \
    chmod -R a+rw /opt/kafka/logs && \
    chmod +x /opt/kafka/entrypoint.sh /opt/kafka/bin/*.sh
    
ENTRYPOINT ["/opt/kafka/entrypoint.sh"]


