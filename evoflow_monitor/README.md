# Notes 
The monitor needs a daemon that runs as severing on the pi to keep on listening on MQTT messages. 

At this point we have two options:
1. Once the message arrives we trigger a prefect flow that will write on db. 
    
   This is my preferred choise as prefect will eventually allow us to keep order and track on what's happening on the db

2. Once the message arrives we write data into the db direcly (this is the current version but I'd revert to point 1. rather soon!)