import json
import logging

from common.config.config import CYODA_AI_URL
from common.util.utils import send_post_request

logger = logging.getLogger(__name__)

def init_chat(token, chat_id):
    data = json.dumps({"chat_id": f"{chat_id}"})
    resp = send_post_request(token, CYODA_AI_URL, "api/v1/cyoda/initial", data)
    return resp.json()


def chat(token, chat_id, ai_question):
    data = json.dumps({"chat_id": f"{chat_id}", "question": f"{ai_question}"})
    resp = send_post_request(token, CYODA_AI_URL, "api/v1/cyoda/chat", data)
    return resp.json()

def init_workflow_chat(token, chat_id):
    data = json.dumps({"chat_id": f"{chat_id}"})
    resp = send_post_request(token, CYODA_AI_URL, "api/v1/workflows/initial", data)
    return resp.json()


def chat_workflow(token, chat_id, ai_question):
    data = json.dumps({"question": f"{ai_question}","return_object":"workflow","chat_id": f"{chat_id}","class_name":"com.cyoda.tdb.model.treenode.TreeNodeEntity"})
    resp = send_post_request(token, CYODA_AI_URL, "api/v1/workflows/chat", data)
    return resp.json()