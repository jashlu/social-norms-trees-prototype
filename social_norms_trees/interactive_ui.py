from prompt_toolkit import Application
from prompt_toolkit.layout import Layout, HSplit, VSplit, Window
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style

from typing import Optional, List, Callable

from social_norms_trees.behavior_tree_library import Behavior


def run_interactive_list(
    nodes: List, mode: str, new_behavior: Optional[Behavior] = None
):
    """
    Runs an interactive list UI to insert a new action.
    """
    selected_index = 0

    fontColors = {"move": "ff0000", "select": "0080ff", "insert": "00ff80"}

    if mode == "move":
        selected_index = nodes.index(new_behavior)
        nodes.remove(new_behavior)

    def get_display_text_insert():
        result = []
        for i in range(len(nodes) + 1):
            if i == selected_index:
                result.append(
                    (f"fg:#{fontColors[mode]}", f"-> {{{new_behavior.name}}}\n")
                )
            elif i < selected_index:
                result.append(("fg:white", f"-> {nodes[i].name}\n"))
            else:
                # now that selected index has moved behind this behavior, index is index-1
                result.append(("fg:white", f"-> {nodes[i - 1].name}\n"))
        return FormattedText(result)

    def get_display_text_select():
        result = []
        for i in range(len(nodes)):
            if i == selected_index:
                result.append((f"fg:#{fontColors[mode]}", f"-> {nodes[i].name}\n"))
            else:
                result.append(("fg:white", f"-> {nodes[i].name}\n"))

        return FormattedText(result)

    instructions_set = {
        "insert": "Use the Up/Down arrow keys to select where to insert the action. ",
        "select": "Use the Up/Down arrow keys to select the desired action to operate on. ",
        "move": "Use the Up/Down arrow keys to select the new position for the action. ",
    }

    # FormattedText used to define text and also text styling
    instructions = FormattedText(
        [
            (
                f"fg:#{fontColors[mode]} bold",
                instructions_set[mode]
                + "Press Enter to confirm. Press esc to exit at anytime.",
            )
        ]
    )

    instructions_window = Window(
        content=FormattedTextControl(instructions), height=1, align="center"
    )

    # initial window display
    display_mode = {
        "insert": get_display_text_insert,
        "move": get_display_text_insert,
        "select": get_display_text_select,
    }

    display = Window(
        content=FormattedTextControl(display_mode[mode]),
        style="class:output",
        height=10,
        align="center",
    )

    # Key bindings
    kb = KeyBindings()

    @kb.add("up")
    def move_up(event):
        nonlocal selected_index
        if selected_index > 0:
            selected_index -= 1
            if mode == "insert" or mode == "move":
                display.content.text = get_display_text_insert()
            elif mode == "select":
                display.content.text = get_display_text_select()

    @kb.add("down")
    def move_down(event):
        nonlocal selected_index

        if mode == "insert" or mode == "move":
            if selected_index < len(nodes):
                selected_index += 1
                display.content.text = get_display_text_insert()
        elif mode == "select":
            if selected_index < len(nodes) - 1:
                selected_index += 1
                display.content.text = get_display_text_select()

    @kb.add("enter")
    def select_action(event):
        if mode == "insert" or mode == "move":
            # nodes.insert(selected_index, new_behavior)
            app.exit(result=selected_index)
            # app.exit(result=nodes)
        elif mode == "select":
            app.exit(result=nodes[selected_index])

    @kb.add("escape")
    def exit_without_changes(event):
        app.exit(result=None)

    # For styling the "box"
    root_container = HSplit(
        [
            Window(height=5),  # top padding
            VSplit(
                [
                    Window(),  # Left padding
                    HSplit(
                        [instructions_window, Window(height=1), display], align="center"
                    ),
                    Window(),  # Right padding
                ],
                align="center",
            ),
            Window(height=2),  # Bottom padding
        ]
    )
    layout = Layout(root_container)

    style = Style.from_dict(
        {
            "output": "bg:#282c34 #ffffff bold",  # Dark grey background, text bold
            "instructions": f"fg:#{fontColors[mode]} bold",
        }
    )

    app = Application(layout=layout, key_bindings=kb, full_screen=True, style=style)
    return app.run()
