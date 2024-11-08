import logging
import os
import queue
import shutil
from uuid import uuid1

from common.ai.ai_assistant_service import chat, init_chat, init_workflow_chat, chat_workflow, mock_init_workflow_chat, \
    mock_chat_outline_entities, mock_chat_neg, mock_entities
from common.auth.auth import authenticate
from common.util.utils import parse_json
import json
import subprocess

from entity.state_machine import cyoda_state_machine

# I need an application that collects air quality data from various sensors and alerts when pollution levels are high.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

cyoda_state_machine
chat_id = uuid1()
question_queue = queue.Queue()
cyoda_token = authenticate()


# Background thread to simulate adding new questions periodically
def add_question(question: str):  # Add a new question every 60 seconds
    # new_question = f"New question at {time.strftime('%Y-%m-%d %H:%M:%S')}"
    question_queue.put(question)
    print(f"Added new question: {question}")


def _clone_repo():
    # URL of the GitHub repository
    repo_url = "https://github.com/Cyoda-platform/cyoda-client-applications.git"
    # Target directory
    target_directory = "/tmp/cyoda-client-applications"
    # Clone the repository into the specified target directory
    subprocess.run(["git", "clone", repo_url, target_directory])

def _copy_template_project():
    # Define source and base target directory
    source_dir = "/tmp/cyoda-client-applications/cyoda_template_project"
    base_target_dir = "/tmp/cyoda-client-applications"

    # Create the target directory path
    target_dir = os.path.join(base_target_dir, f"cyoda-client-test")

    # Copy the directory
    shutil.copytree(source_dir, target_dir)

    print(f"Copied to {target_dir}")


print("Repository cloned successfully to /tmp/cyoda-client-applications.")
def gather_requirement(meta, data):
    logger.info("gather_requirement")
    transitions = data["transitions"]
    question_to_user = transitions[-1]["question_to_user"]
    question_queue.put(question_to_user)
    #init_chat(meta["token"], chat_id)
    #_clone_repo()
    _copy_template_project()
    mock_init_workflow_chat(meta["token"], chat_id)


def analyze_requirement(meta, data):
    logger.info("analyze_requirement")
    transitions = data["transitions"]
    prompt: str = (transitions[-1]["prompt"]).format(transitions[-1]["user_answer"])
    #result = chat(meta["token"], chat_id, prompt)
    result = mock_chat_neg(meta["token"], chat_id, prompt)
    try:
        result_json = json.loads(parse_json(result['message']))
    except:
        #result = chat(meta["token"], chat_id,f"JSON parsing error for the response {result['message']}, please correct and return valid json.")
        result = mock_chat_neg(meta["token"], chat_id,f"JSON parsing error for the response {result['message']}, please correct and return valid json.")
        result_json = json.loads(parse_json(result['message']))
    # todo validate json
    data_transition = {
        "name": "analyze_requirement",
        "count": transitions[-1]["count"] if transitions[-1]["count"] < 3 else 3,
        "question_to_user": f"Hello, could you please elaborate on these questions: {result_json["questions_to_ask"]}",
        "user_answer": "",
        "prompt": "The user has provided the following answers to the questions {}, do you have enough information to outline entities and workflows? Return answer in json format {{ \"can_proceed\": \"false\", \"questions_to_ask\": [\"Could you elaborate on...\"] }}. questions_to_ask are empty if you are ready to proceed",
        "result": ""
    }
    data["transitions"].append(data_transition)
    data_transition["result"] = result['message']
    if result_json["can_proceed"] == "true" or transitions[-1]["count"] < 0:
        data["next_transition"] = "true"
        cyoda_state_machine.next_transition(data["next_transition"])
        outline_entities_and_workflow(meta, data)
    else:
        data["next_transition"] = "false"
        question_queue.put(data_transition["question_to_user"])
        transitions[-1]["count"] -= 1


def outline_entities_and_workflow(meta, data):
    logger.info("outline_entities_and_workflow")
    transitions = data["transitions"]
    prev_transition = transitions[-1]
    data_transition = {
        "name": "outline_entities_and_workflow",
        "count": prev_transition["count"] if prev_transition["name"].lower() == "outline_entities_and_workflow" else 3,
        "question_to_user": "",
        "user_answer": "",
        "iteration": 0,
        "prompt": "Hello, could you please outline entities and workflows for these entities "
                  "if this workflow is necessary for the entity (like in case with job entities)."
                  "At least one entity should have a workflow, that can be used as an entry point."
                  "An entity can have 0 or 1 workflow"
                  "Return the result in json format: { \"entities\": [ { \"entity_name\": \"some_name_here\", \"entity_workflow\": \"None -> .... (or return empty if workflow is not necessary)\" } ] }."
                  "Return only json - otherwise we'll get json parse error.",
        "result": "",
        "prev_transition_index": 0
    }
    data["transitions"].append(data_transition)
    if (prev_transition["name"].lower() == "outline_entities_and_workflow" and prev_transition["count"] < 0) or (
            prev_transition["name"].lower() == "outline_entities_and_workflow" and prev_transition[
        "user_answer"].lower() == "yes"):
        data["next_transition"] = "true"
        data_transition["question_to_user"] = "Let's proceed"
        question_queue.put(data_transition["question_to_user"])
        cyoda_state_machine.next_transition(data["next_transition"])
        data_transition["result"] = prev_transition["result"]
        data_transition["prev_transition_index"] = len(transitions) - 1
        generate_entities(meta, data)
        return

    if prev_transition["name"].lower() != "outline_entities_and_workflow":
        prompt = data_transition["prompt"]
    else:
        prompt = prev_transition["user_answer"]
    #result = chat(meta["token"], chat_id, prompt)
    result = mock_chat_outline_entities(meta["token"], chat_id, prompt)
    try:
        result_json = json.loads(parse_json(result['message']))
    except:
        result = mock_chat_outline_entities(meta["token"], chat_id,f"JSON parsing error for the response {result['message']}, please correct and return valid json.")
        #result = chat(meta["token"], chat_id, f"JSON parsing error for the response {result['message']}, please correct and return valid json.")
        result_json = json.loads(parse_json(result['message']))

    data_transition["result"] = json.dumps(result_json)
    data["next_transition"] = "false"
    data_transition["question_to_user"] = json.dumps(result_json) + ". Can we proceed with this design?"
    question_queue.put(data_transition["question_to_user"])
    transitions[-1]["count"] -= 1
    return


def generate_entities(meta, data):
    logger.info("generate_entities")
    transitions = data["transitions"]
    prev_transition = transitions[-1]
    entities = json.loads(transitions[prev_transition["prev_transition_index"]].get("result"))["entities"]
    iteration = prev_transition["iteration"]
    entity = entities[iteration]
    # entity_json_message = chat(meta["token"], chat_id, f"Generate json data example for this entity: {entity['name']}")['message']
    # entity_json = parse_json(entity_json_message)
    data_transition = {
        "name": "generate_entities",
        "iteration": iteration,
        "count": prev_transition["count"] - 1 if prev_transition["name"].lower() == "generate_entities" else 3,
        "question_to_user": "Would you like to specify the details for this entity: {}.",
        "user_answer": prev_transition["user_answer"],
        "prompt": "Generate entity data json example for entity {}, taking into account user recommendations {} if any. Return only json.",
        "result": "",
        "prev_transition_index": prev_transition["prev_transition_index"]
    }
    data["transitions"].append(data_transition)

    if prev_transition["name"].lower() != "generate_entities":
        data["next_transition"] = "false"
        question = data_transition["question_to_user"].format(entity["entity_name"])
        question_queue.put(question)
        return

    if (prev_transition["name"].lower() == "generate_entities" and prev_transition["count"] < 0) or (
            prev_transition["name"].lower() == "generate_entities" and prev_transition["user_answer"].lower() == "yes"):
        if iteration == len(entities) - 1:
            data["next_transition"] = "true"
            data_transition["iteration"] = 0
            data_transition["question_to_user"] = "Let's proceed"
            question_queue.put(data_transition["question_to_user"])
            cyoda_state_machine.next_transition(data["next_transition"])
            generate_workflows(meta, data)
            return

        else:
            data["next_transition"] = "false"
            data_transition["iteration"] += 1
            question = data_transition["question_to_user"].format(entities[data_transition["iteration"]]["entity_name"])
            question_queue.put(question)
            data_transition["count"] = 3
            return

    prompt = (data_transition["prompt"]).format(entity["entity_name"], data_transition["user_answer"])
    #result = chat(meta["token"], chat_id, prompt)
    result = mock_entities(meta["token"], chat_id, prompt)
    try:
        result_json = json.loads(parse_json(result['message']))
    except:
        #result = chat(meta["token"], chat_id,f"JSON parsing error for the response {result['message']}, please correct and return valid json.")
        result = mock_entities(meta["token"], chat_id,f"JSON parsing error for the response {result['message']}, please correct and return valid json.")
        result_json = json.loads(parse_json(result['message']))
    data_transition["result"] = json.dumps(result_json)
    data["next_transition"] = "false"
    question_queue.put(data_transition["result"])
    question_queue.put(data_transition["question_to_user"].format(entity["entity_name"]))
    question_queue.put("If you are ready to proceed to the next step answer 'yes'.")
    return


def generate_workflows(meta, data):
    logger.info("generate_workflows")
    transitions = data["transitions"]
    prev_transition = transitions[-1]
    entities = json.loads(transitions[prev_transition["prev_transition_index"]].get("result"))["entities"]
    entities = [entity for entity in entities if entity["entity_workflow"] not in (None, "null", "", "None")]
    iteration = prev_transition["iteration"]
    entity = entities[iteration]
    # entity_json_message = chat(meta["token"], chat_id, f"Generate json data example for this entity: {entity['name']}")['message']
    # entity_json = parse_json(entity_json_message)
    data_transition = {
        "name": "generate_workflows",
        "iteration": iteration,
        "count": prev_transition["count"] - 1 if prev_transition["name"].lower() == "generate_workflows" else 3,
        "question_to_user": "Would you like to specify any details for this entity {} workflow: {}.",
        "user_answer": prev_transition["user_answer"],
        "prompt": "Generate code for entity {}, workflow {}, taking into account user recommendations {}. You should return static methods which take meta and data as args, like some_method(meta, data).",
        "result": "",
        "prev_transition_index": prev_transition["prev_transition_index"]
    }
    data["transitions"].append(data_transition)

    if prev_transition["name"].lower() != "generate_workflows":
        data["next_transition"] = "false"
        question = data_transition["question_to_user"].format(entity["entity_name"], entity["entity_workflow"])
        question_queue.put(question)
        return

    if (prev_transition["name"].lower() == "generate_workflows" and prev_transition["count"] < 0) or (
            prev_transition["name"].lower() == "generate_workflows" and prev_transition["user_answer"].lower() == "yes"):
        if iteration == len(entities) - 1:
            data["next_transition"] = "true"
            cyoda_state_machine.next_transition(data["next_transition"])
            data_transition["question_to_user"] = "Let's proceed"
            question_queue.put(data_transition["question_to_user"])
            finish_workflow(meta, data)
            return

        else:
            data["next_transition"] = "false"
            data_transition["iteration"] += 1
            question = data_transition["question_to_user"].format(entities[data_transition["iteration"]]["entity_name"], entities[data_transition["iteration"]]["entity_workflow"])
            question_queue.put(question)
            data_transition["count"] = 3
            return

    prompt = (data_transition["prompt"]).format(entity["entity_name"], entity["entity_workflow"], data_transition["user_answer"])
    #result = chat(meta["token"], chat_id, prompt)
    result = mock_entities(meta["token"], chat_id, prompt)
    data_transition["result"] = result["message"]
    data["next_transition"] = "false"
    question_queue.put(data_transition["result"])
    question_queue.put(data_transition["question_to_user"].format(entity["entity_name"], entity["entity_workflow"]))
    question_queue.put("If you are ready to proceed to the next step answer 'yes'.")
    return


def finish_workflow(meta, data):
    question_queue.put("Finished workflow")


# analyze_requirement


# =======================================


def process_outline_entities_workflows(meta, entity_job):
    process_name = 'outline_entities_workflows'
    logger.info("outline_entities_workflows ")
    questions = entity_job['transitions'][process_name]
    question = questions[len(questions) - 1]
    prompt = question["prompt"]
    result = chat(meta["token"], chat_id, prompt)
    try:
        entities_json = json.loads(parse_json(result['message']))
    except:
        result = chat(meta["token"], chat_id,
                      f"JSON parsing error for the response {result['message']}, please correct and return valid json.")
        entities_json = json.loads(parse_json(result['message']))
    question["result"] = result['message']
    print(question["result"])
    entities = entities_json['entities']
    entities_resp = []
    for entity in entities:
        entity_json_message = \
        chat(meta["token"], chat_id, f"Generate json data example for this entity: {entity['name']}")['message']
        entity_json = parse_json(entity_json_message)
        entities_resp.append(entity_json)
        if (entity.get('workflow') is None or entity.get('workflow') == "None" or entity.get(
                'workflow') == "null" or entity.get('workflow') == ""):
            pass
        else:
            init_workflow_chat(meta["token"], chat_id)
            workflow_id = chat_workflow(meta["token"], chat_id,
                                        f"Generate workflow for {entity.get('workflow')}. Add processes which correspond to the function names.")
            entities_resp.append(workflow_id)
    if question["count"] >= 0:
        transition_questions = entity_job['transitions'][process_name]
        additional_question = {
            "name": process_name,
            "count": question["count"] - 1,
            "question_to_user": entities_resp,
            "user_answer": "",
            "prompt": "",
            "result": ""
        }
        transition_questions.append(additional_question)
        return [additional_question]
    return None


def process_entities(meta, entity):
    logger.info("process_entities ")
    process_name = 'process_entities'
    logger.info("process_entities ")
    questions = entity['transitions'][process_name]
    question = questions[len(questions) - 1]
    prompt = question["prompt"].format(question["user_answer"])
    if not prompt:
        return None
    result = chat(meta["token"], chat_id, prompt)
    question["result"] = result['message']
    print(question["result"])
    entities = []
    for i in range(int(question["result"])):
        entity_result = chat(meta["token"], chat_id, f"Generate json example for entity number {i}")
        entities.append(entity_result)

    additional_question = {
        "name": process_name,
        "count": question["count"] - 1,
        "question_to_user": str(entities),
        "user_answer": "",
        "prompt": "",
        "result": ""
    }
    return [additional_question]
