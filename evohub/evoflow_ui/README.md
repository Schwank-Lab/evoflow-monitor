## MQTT Messaging Protocol 
EvoHub mqtt messaging protocol is based on 3 main topics: status, commands and logs; and 2 sub-topic for each main one: experiment and reactor.

Finally, all the logs produced by the reactor fleet are published on the the main topic ```logs```.

### Monitoring exeriment state

Topic: `status/experiment`

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

Topic: `status/reactor`

Message: 
```
{
  reactor_id: 'reactor_id',
  state: 'running'| 'idle'
}
```


### Sending commands to the reactor

Topic: `commands/reactor`

Message: 
```
{
  reactor_id: 'reactor_id',
  command: 'update_reactor_config',
  reactor_config: json
}
```

### Sending commands to the experiments

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


### Monitoring reactor logs

Topic: `logs/reactor`

Message:
```
{
  reactor_id: 'reactor_id',
  log: string
}
```

Topic: `logs/experiment`

Message:
```
{
  reactor_id: 'reactor_id',
  experiment_id: 'experiment_id',
  log: string
}
```
