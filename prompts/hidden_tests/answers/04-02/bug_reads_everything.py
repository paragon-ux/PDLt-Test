# Wrong: reads the whole stream at once and builds the full tree with json.loads,
# then replays it as events.
import json


def parse(stream, handler):
    data = stream.read()
    if isinstance(data, bytes):
        data = data.decode()

    def walk(value):
        if isinstance(value, dict):
            handler.on_object_start()
            for k, v in value.items():
                handler.on_key(k)
                walk(v)
            handler.on_object_end()
        elif isinstance(value, list):
            handler.on_array_start()
            for v in value:
                walk(v)
            handler.on_array_end()
        else:
            handler.on_value(value)

    walk(json.loads(data))
