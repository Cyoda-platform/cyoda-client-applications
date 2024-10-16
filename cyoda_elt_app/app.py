from quart import Quart, request
import asyncio
import logging

from common.auth.auth import authenticate
from common.grpc_client.grpc_client import grpc_stream
from common.ingestion.data_ingestion import ingest_data_from_connection, get_data_ingestion_status, get_all_entities
from common.repository.cyoda.cyoda_init import init_cyoda

app = Quart(__name__)
logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

@app.before_serving
async def startup():
    token = authenticate()
    app.background_task = asyncio.create_task(grpc_stream(token))
    init_cyoda(token)

@app.after_serving
async def shutdown():
    app.background_task.cancel()
    await app.background_task

@app.route('/ingest/<string:entity_name>')
async def ingest_data(entity_name):
    token = request.headers.get('Authorization')
    return ingest_data_from_connection(token, entity_name)

@app.route('/get_ingestion_status/<string:request_id>', methods=['GET'])
async def get_ingestion_status(request_id):
    token = request.headers.get('Authorization')
    return get_data_ingestion_status(token, request_id)

@app.route('/get_entities/<string:entity_name>')
async def get_entities(entity_name):
    token = request.headers.get('Authorization')
    return get_all_entities(token, entity_name)

if __name__ == '__main__':
    app.run()