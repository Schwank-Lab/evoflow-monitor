# Use Alpine Linux as the base image
FROM alpine:latest

# Install Mosquitto
RUN apk add --no-cache mosquitto mosquitto-clients

# Expose MQTT port
EXPOSE 1883

# Run Mosquitto in the foreground
CMD ["/usr/sbin/mosquitto", "-c", "/etc/mosquitto/mosquitto.conf"]
