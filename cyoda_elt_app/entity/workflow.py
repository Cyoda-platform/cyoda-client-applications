from entity.open_data_ytj.workflow.workflow import process_data_source, notify_ingestion_complete

process_dispatch = {
     "process_data_source": process_data_source,
     "notify_ingestion_complete": notify_ingestion_complete,
}


def process_event(token, data, processor_name):

    meta = {"token":token, "entity_model": "ENTITY_PROCESSED_NAME", "entity_version": "ENTITY_VERSION"}
    data = data['payload']['data']
    if processor_name in process_dispatch:
        response = process_dispatch[processor_name](meta, data)
    else:
        raise ValueError(f"Unknown processing step: {processor_name}")
    return response
