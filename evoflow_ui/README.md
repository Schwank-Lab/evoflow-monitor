## MQTT Messaging Protocol 

### Monitoring exeriment state

Topic: `experiment_monitor`
Message: 
```
{ reactor_id: 'reactor_id', state: json}
```

### Montiroing reactor state

Topic: `reactor_monitor`
Message: 
```
{
  reactor_id: 'reactor_id',
  state: 'running'| 'idle'
}
```

### Monitoring reactor logs

Topic: `logs`
Message:
```
{ reactor_id: 'reactor_id', log: string }
```
### Sending commands to the reactor

Topic: `commands`
Message:
```
{
  reactor_id: 'reactor_id', 
  command: 'start' | 'stop' | 'pause'
}
```
Message:
```
{
  reactor_id: 'reactor_id',
  command: 'new_experiment' | 'update_experiment_config',
  experiment_config: json
} 
```

Message: 
```
{
  reactor_id: 'reactor_id',
  command: 'update_reactor_config',
  reactor_config: json
}

