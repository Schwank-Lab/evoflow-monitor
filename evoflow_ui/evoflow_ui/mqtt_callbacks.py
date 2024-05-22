class EvohubTopics(TypedDict):
    topic: str
    script: Callable


mqtt_handlers: EvohubTopics = {
    "commands/experiment": lambda x: parse_experiment_commands(x),
    "commands/reactor": lambda x: parse_reactor_commands(x),
}


def parse_experiment_commands(data):
    pass


def parse_reactor_commands(data):
    pass
