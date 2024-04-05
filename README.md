# Monitor
EvoFlow Monitor is the monitor centre for the EvoFlow fleet.

## Responsibilities
EvoFlow Monitor centre will be responsible for:
1. Collect data about experiments 
2. Store data into DB 
3. Show info about the experiments status in a Grafana dashboard

## Basic System design
A machine will host the monitor centre with the following services:
1. MQTT Broker (Mosquito) 
2. A DB (PostgresSQL)
3. Grafana

Each reactor in the fleet publishes data on a schedule (say every 5m) identifying itself an the experiment. The monitor centre subscribes to the topics, receives and stores 
the data in the DB accordingly. 

Furthermore, each reactor will have its own cached data (say 1 day worth of data) that will be published (on a different topic) and analyzed by the control centre for missing data and history integrity. 

## Raspberry PI installation
We use [Raspberry Pi OS Lite]{https://wiki.alpinelinux.org/wiki/Raspberry_Pi} as base OS for the Raspberry Pi and install docker system on it. Furthermore, we use [PortainerIO]{https://www.portainer.io/} to handle images and containers. 

# TODO:
1. Write docker files for:
    a. Mosquito (mqtt broker)
   
    b. PostgresSQL (DB storing data and info about experiments and fleet)
   
    c. Grafana (dashboard)
3. Install raspberry pi 
4. Tests:
    a. mqtt comms
   
    b. data storing
   
    c. data retrieval
   
    d. Grafana
