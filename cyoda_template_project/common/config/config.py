import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
CYODA_AI_URL = os.getenv("CYODA_AI_URL")
API_URL = os.getenv("CYODA_API_URL") + "/api"
API_KEY = os.getenv("CYODA_API_KEY")
API_SECRET = os.getenv("CYODA_API_SECRET")
ENTITY_VERSION = os.getenv("ENTITY_VERSION", "1000")
GRPC_ADDRESS = os.environ["GRPC_ADDRESS"]
GRPC_PROCESSOR_TAG=os.getenv("GRPC_PROCESSOR_TAG", "elt")