## Deploying MQTT Listener
The follwing steps are needed when the code in the MQTT has changed: 

1. SSH into evhohub
2. Navigate to `/home/evohub/Workspace/evohub`
3. Run `git pull`
4. Run `make build_listener`
5. Open Portainer https://10.66.4.7:9443
6. Navigate to `stacks` > `monitor`. Click `Editor` and `Update Stack`

![image](https://github.com/user-attachments/assets/21850673-b033-427f-8a2a-f1aeb13d3037)
