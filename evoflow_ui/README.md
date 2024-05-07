## MQTT Messaging Protocol 

### Monitoring exeriment state

Topic: `experiment_monitor`
Message: 
```
{
  reactor_id: 'reactor_id',
  experiment_id: 'experiment_id',
  timestamp: timestamp,
  inc_od: 1.0,
  inc_dilution: 154,
  inc_temp: 37.0,
  lagoon_temp: 37.0,
  lagoon_flow_rate: 3.0
}
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
  experiment_id: 'experiment_id',
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

