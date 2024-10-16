import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_data_source(meta, data):
    logger.info("processing ")


def notify_ingestion_complete(meta, data):
    logger.info("notify_ingestion_complete ")
