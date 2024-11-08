import inspect

from entity.app_gen_entity.workflow import workflow

process_dispatch = {
}
for name, func in inspect.getmembers(workflow, inspect.isfunction):
    # Optionally, filter out private or unwanted functions
    if not name.startswith("_"):
        process_dispatch[name] = func


def process_event(token, data, processor_name):
    meta = {"token": token, "entity_model": "ENTITY_PROCESSED_NAME", "entity_version": "ENTITY_VERSION"}
    # data = data['payload']['data']
    if processor_name in process_dispatch:
        response = process_dispatch[processor_name](meta, data)
    else:
        raise ValueError(f"Unknown processing step: {processor_name}")
    return response
