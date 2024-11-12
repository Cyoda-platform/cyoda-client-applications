import inspect
from entity.energy_consumption_data.workflow import workflow as workflow

workflows = [workflow]

process_dispatch = {}

# Iterate over each workflow module and collect functions
for workflow in workflows:
    for name, func in inspect.getmembers(workflow, inspect.isfunction):
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
