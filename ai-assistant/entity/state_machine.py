import json

# State machine JSON definition
state_machine_json = {
    "workflow": [
        {
            "name": "gather_requirement",
            "description": "Obtain the business requirements.",
            "transitions": [
                {
                    "to": "analyze_requirement"
                }
            ]
        },
        {
            "name": "analyze_requirement",
            "description": "Review and analyze the collected business requirements.",
            "transitions": [
                {
                    "decision": "Enough information to generate entities and workflow?",
                    "yes": {
                        "to": "outline_entities_and_workflow"
                    },
                    "no": {
                        "to": "analyze_requirement"
                    }
                }
            ]
        },
        {
            "name": "outline_entities_and_workflow",
            "description": "Create necessary entities and workflows based on the requirements.",
            "transitions": [
                {
                    "decision": "Enough information to generate entities and workflow?",
                    "yes": {
                        "to": "generate_entities"
                    },
                    "no": {
                        "to": "outline_entities_and_workflow"
                    }
                }
            ]
        },
        {
            "name": "generate_entities",
            "description": "For each entity, generate the required data and finalize the workflow.",
            "transitions": [
                {
                    "decision": "Enough information to generate entities?",
                    "yes": {
                        "to": "generate_workflows"
                    },
                    "no": {
                        "to": "generate_entities"
                    }
                }
            ]
        },
        {
            "name": "generate_workflows",
            "description": "For each entity, generate the required data and finalize the workflow.",
            "transitions": [
                {
                    "decision": "Enough information to generate worflows?",
                    "yes": {
                        "to": "finish_workflow"
                    },
                    "no": {
                        "to": "generate_workflows"
                    }
                }
            ]
        }
        ,
        {
            "name": "finish_workflow",
            "description": "For each entity, generate the required data and finalize the workflow.",
            "transitions": [
            ]
        }
    ]
}


class StateMachine:
    def __init__(self, config):
        # Parse states from JSON config
        self.transitions = {state["name"]: state for state in config["workflow"]}
        # Start at the initial state
        self.current_transition = self.transitions["gather_requirement"]

    def get_state_description(self):
        return self.current_transition["name"]

    def next_transition(self, decision=None):
        transitions = self.current_transition.get("transitions", [])

        for transition in transitions:
            # If the transition has a decision, handle based on 'yes' or 'no' input
            if "decision" in transition:
                if decision == "true" and "yes" in transition:
                    self.current_transition = self.transitions[transition["yes"]["to"]]
                    return self.current_transition
                elif decision == "false" and "no" in transition:
                    self.current_transition = self.transitions[transition["no"]["to"]]
                    return self.current_transition
            # For straightforward transitions without decisions
            elif "to" in transition:
                self.current_transition = self.transitions[transition["to"]]
                return self.current_transition

    def is_final_state(self):
        return not self.current_transition.get("transitions")

cyoda_state_machine = StateMachine(state_machine_json)