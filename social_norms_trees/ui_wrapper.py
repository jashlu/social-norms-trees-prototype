import logging
import pathlib
from typing import Annotated, List
import click
from datetime import datetime
import json
import os
import uuid
import traceback
import time
import typer
import importlib.resources as pkg_resources

# from social_norms_trees.behavior_tree_library import Behavior, Sequence
# from social_norms_trees.atomic_mutations import remove, insert, move

# from social_norms_trees.interactive_ui import run_interactive_list

from behavior_tree_library import Behavior, Sequence
from atomic_mutations import remove, insert, move

from interactive_ui import run_interactive_list


SLEEP_TIME = 2


def load_db(db_file):
    if os.path.exists(db_file):
        with open(db_file, "r") as f:
            return json.load(f)
    else:
        return {}


def save_db(db, db_file):
    """Saves the Python dictionary back to db.json."""

    print(f"Writing results of simulation to {db_file}...")
    time.sleep(SLEEP_TIME)
    print("Done.")

    json_representation = json.dumps(db, indent=4)

    with open(db_file, "w") as f:
        f.write(json_representation)


def experiment_setup(db, resource_file):
    participant_name = participant_login()

    experiment_id = initialize_experiment_record(db, participant_name, resource_file)

    print("\nSetup Complete.\n")

    return participant_name, experiment_id


def participant_login():
    name = click.prompt("Please enter your name", type=str)

    return name


def deserialize_behaviors(behaviors):
    deserialized_behaviors = {}

    for behavior in behaviors:
        deserialized_behaviors[behavior["id"]] = Behavior(
            id=behavior["id"], name=behavior["name"]
        )

    return deserialized_behaviors


def build_tree(subtree, children, behaviors):
    children_behaviors = []

    parent_node = Sequence(
        name=subtree,
    )

    for behavior_id in children:
        behaviors[behavior_id].parent = parent_node
        children_behaviors.append(behaviors[behavior_id])

    return Sequence(name=subtree, children=children_behaviors)


def serialize_tree(behavior_tree):
    children_list = []

    for node in behavior_tree.children:
        children_list.append(node.id)
    return children_list


# behaviors = deserialized behavious
# behavior_list = array of all behaviors
def build_behavior_bank(behaviors, behavior_list):
    behavior_bank = []

    for behavior in behavior_list:
        if "in_behavior_bank" in behavior and behavior["in_behavior_bank"]:
            behavior_bank.append(behaviors[behavior["id"]])
    return behavior_bank


def display_tree(node, indent=0):
    """Recursively display the behavior tree in a readable format."""
    if isinstance(node, Sequence):
        print(" " * indent + node.name)
        if node.children:
            for child in node.children:
                display_tree(child, indent + 4)
    elif isinstance(node, Behavior):
        print(" " * indent + " -> " + node.name)


def load_resources(resource_file):
    try:
        print(f"\nLoading behavior tree and behavior library from {resource_file}...\n")
        # Use importlib.resources to access files within the package
        resource_file = pkg_resources.files("examples") / resource_file
        with resource_file.open() as f:
            resources = json.load(f)

    except (FileNotFoundError, ModuleNotFoundError):
        # Fallback to a local directory for development purposes
        local_dir = os.path.join(os.path.dirname(__file__), "../examples")
        resource_path = os.path.join(local_dir, resource_file)
        if not os.path.exists(resource_path):
            raise RuntimeError(f"Resource file not found: {resource_file}")
        with open(resource_path, "r") as f:
            resources = json.load(f)

    except json.JSONDecodeError:
        raise ValueError("Error")
    except Exception:
        raise RuntimeError("Error")

    all_resources = {}

    for subtree in resources:
        children = resources[subtree].get("children")
        behavior_list = resources[subtree].get("behavior_library")
        context_paragraph = resources[subtree].get("context")

        # deserialize behavior_list
        deserialized_behaviors = deserialize_behaviors(behavior_list)

        # then use it to build the subgoal behavior tree
        sub_tree = build_tree(subtree, children, deserialized_behaviors)

        behavior_bank = build_behavior_bank(deserialized_behaviors, behavior_list)

        all_resources[subtree] = {
            "context": context_paragraph,
            "behaviors": behavior_bank,
            "sub_tree": sub_tree,
        }

    return all_resources


def initialize_experiment_record(db, participant_name, resource_file):
    experiment_id = str(uuid.uuid4())

    experiment_record = {
        "participant_name": participant_name,
        "experiment_start_date": datetime.now().isoformat(),
        "experiment_progression": {},
        "resource_file": resource_file,
    }

    db[experiment_id] = experiment_record

    return experiment_id


def summarize_behaviors_check(subgoal_resources, db):
    print("Bot: Here are the actions, in order, that I will take to achieve this goal.")
    run_tree_manipulation(
        subgoal_resources["behaviors"], subgoal_resources["sub_tree"], db
    )


def display_tree_one_level(
    node,
    indent=0,
):
    print(" " * indent + node.name)

    if isinstance(node, Sequence):
        if node.children:
            for child in node.children:
                print(f" " * indent + f" -> {child.name}")


def run_tree_manipulation(behavior_library, tree, db):
    try:
        while True:
            print("\n")
            display_tree_one_level(tree)
            user_choice = click.prompt(
                "Would you like to make a change before I begin?",
                show_choices=True,
                type=click.Choice(["y", "n"], case_sensitive=False),
            )

            if user_choice == "y":
                action = click.prompt(
                    "\n1. move an existing node\n"
                    + "2. remove an existing node\n"
                    + "3. add a new node\n"
                    + "Please select an action to perform on the behavior tree",
                    type=click.IntRange(min=1, max=4),
                    show_choices=True,
                )

                if action == 1:
                    # Select node to be moved
                    selected_node = run_interactive_list(tree.children, mode="select")
                    # Select position of node
                    selected_index = run_interactive_list(
                        tree.children, mode="move", new_behavior=selected_node
                    )
                    # Perform operation
                    move(selected_node, (tree, selected_index))

                    action_log = {
                        "type": "move_node",
                        "nodes": [
                            {
                                "display_name": selected_node.name,
                            },
                        ],
                        "timestamp": datetime.now().isoformat(),
                    }
                    db["action_history"].append(action_log)

                elif action == 2:
                    # Select node to be removed
                    selected_node = run_interactive_list(tree.children, mode="select")
                    # Perform operation
                    remove(selected_node, tree)

                    action_log = {
                        "type": "remove_node",
                        "nodes": [
                            {"display_name": selected_node.name},
                        ],
                        "timestamp": datetime.now().isoformat(),
                    }
                    db["action_history"].append(action_log)

                elif action == 3:
                    # TODO: think about where the new action should originally show up in the list. It's original position could
                    # possible affect participant's decision making

                    # Select node to be add
                    selected_node = run_interactive_list(
                        behavior_library, mode="select"
                    )
                    # Select position of node
                    selected_index = run_interactive_list(
                        tree.children, mode="insert", new_behavior=selected_node
                    )
                    # Perform operation
                    insert(selected_node, (tree, selected_index))

                    action_log = {
                        "type": "add_node",
                        "node": {"name": selected_node.name},
                        "timestamp": datetime.now().isoformat(),
                    }
                    db["action_history"].append(action_log)

            else:
                break

    except Exception:
        print(
            "\nAn error has occured during the tree manipulation, the experiment will now end."
        )
        db["error_log"] = traceback.format_exc()

    finally:
        return


def run_milestone(subgoal_resources, title, db):
    db["start_time"] = datetime.now().isoformat()
    db["base_subtree"] = serialize_tree(subgoal_resources["sub_tree"])
    db["action_history"] = []

    # present context for this subgoal
    print("\n =========================================================")
    time.sleep(SLEEP_TIME)
    print("\n" + subgoal_resources["context"])

    print(f"\nBot: I am starting the following milestone: {title}\n")
    time.sleep(SLEEP_TIME)

    summarize_behaviors_check(subgoal_resources, db)

    time.sleep(SLEEP_TIME)
    print("\nBot: Okay, I will begin.")

    for action in subgoal_resources["sub_tree"].children:
        time.sleep(SLEEP_TIME)
        print(f"\nBot: I am about to {action.name}")

        if isinstance(action, Sequence):
            print(
                "Bot: This is a Sequence type node, would you like to see the sub-behaviors of this node?"
            )
        time.sleep(SLEEP_TIME)
        print(f"Action in progress..")

    db["final_subtree"] = serialize_tree(subgoal_resources["sub_tree"])
    db["end_time"] = datetime.now().isoformat()

    print(f"\nBot: The following milestone has been reached: {title}\n")


def sub_function():
    print("subfunction pressed.")


def run_experiment(db, all_resources, experiment_id):
    # Loop for the actual experiment part, which takes user input to decide which action to take

    for subgoal in all_resources:
        db[experiment_id]["experiment_progression"][subgoal] = {}
        run_milestone(
            all_resources[subgoal],
            subgoal,
            db[experiment_id]["experiment_progression"][subgoal],
        )

    return db


app = typer.Typer()


@app.command()
def main(
    robot: Annotated[
        str,
        typer.Argument(help="Name of the robot to run experiment on"),
    ],
    db_file: Annotated[
        pathlib.Path,
        typer.Option(help="file where the experimental results will be written"),
    ] = "experiment_results.json",
    verbose: Annotated[bool, typer.Option("--verbose")] = False,
    debug: Annotated[bool, typer.Option("--debug")] = False,
):
    if debug:
        logging.basicConfig(level=logging.DEBUG)
        _logger.debug("debug logging")
    elif verbose:
        logging.basicConfig(level=logging.INFO)
        _logger.debug("verbose logging")
    else:
        logging.basicConfig()

    print("AIT Prototype #1 Simulator")

    db = load_db(db_file)

    # load robot profile to run experiment on, and behavior library
    resource_file = f"{robot}-resource-file.json"
    all_resources = load_resources(resource_file)

    name, experiment_id = experiment_setup(db, resource_file)

    # TODO: update the colors of the instructions in the prompt toolkit, change the color
    # when we move from first to second interface
    print(
        f"Bot: Hello {name}, welcome to the agent iteractive training experiment! My name is {robot}. We will be working together to achieve a specific milestone. I will first provide you with a list of actions I plan to take to accomplish the goal. After reviewing the list, you will have the opportunity to make any adjustments to these actions. Once you're satisfied with the plan, I will perform the actions. Let's begin!"
    )
    time.sleep(SLEEP_TIME)
    db = run_experiment(db, all_resources, experiment_id)

    save_db(db, db_file)

    # TODO: Add more context to simulation ending
    print(
        f"\nThank you, {name}, for participating in the experiment. "
        f"The experiment has concluded, and the results have been recorded in the {db_file} file. "
        "We greatly appreciate your time and effort!"
    )

    # TODO: visualize the differences between old and new behavior trees after experiment.
    # Potentially use git diff


if __name__ == "__main__":
    app()
