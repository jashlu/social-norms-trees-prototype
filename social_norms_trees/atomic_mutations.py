from collections import namedtuple
import inspect
from functools import partial, wraps
import logging
from types import GenericAlias
from typing import Callable, List, Mapping, NamedTuple, Tuple, TypeVar, Union, Dict

# from social_norms_trees.behavior_tree_library import Behavior, Composite, Sequence
from behavior_tree_library import Behavior, Composite, Sequence

from pprint import pprint

_logger = logging.getLogger(__name__)

# =============================================================================
# Argument types
# =============================================================================

ExistingNode = TypeVar("ExistingNode", bound=Behavior)
NewNode = TypeVar("NewNode", bound=Behavior)
CompositeIndex = TypeVar("CompositeIndex", bound=Tuple[Composite, int])
BehaviorIdentifier = TypeVar(
    "BehaviorIdentifier", bound=Union[ExistingNode, NewNode, CompositeIndex]
)
BehaviorTreeNode = TypeVar("BehaviorTreeNode", bound=Behavior)
BehaviorTree = TypeVar("BehaviorTree", bound=BehaviorTreeNode)
BehaviorLibrary = TypeVar("BehaviorLibrary", bound=List[BehaviorTreeNode])
TreeOrLibrary = TypeVar("TreeOrLibrary", bound=Union[BehaviorTree, BehaviorLibrary])


# =============================================================================
# Atomic operations
# =============================================================================

# The very top line of each operation's docstring is used as the
# description of the operation in the UI, so it's required.
# The argument annotations are vital, because they tell the UI which prompt
# to use.


# TODO: pass in the parent node, and do the action on the parent node directly.
def remove(node: ExistingNode, parent: Composite) -> ExistingNode:
    """Remove a node.
    Examples:
        >>> success_node = Behavior(name="Success")
        >>> failure_node = Behavior(name="Failure")

        >>> tree = Sequence("")
        >>> tree.add_child(success_node)
        >>> tree.add_child(failure_node)

        >>> pprint(tree)
        ... # doctest: +NORMALIZE_WHITESPACE
        Sequence(name='',
              children=[Behavior(name='Success', id=None),
                        Behavior(name='Failure', id=None)])

        >>> removed = remove(failure_node, tree)
        >>> pprint(tree)
        ... # doctest: +NORMALIZE_WHITESPACE
        Sequence(name='',
              children=[Behavior(name='Success', id=None)])
    """
    parent.remove_child(node)
    return node


def insert(node: NewNode, where: CompositeIndex) -> None:
    """Insert a new node.
    Examples:
        >>> success_node = Behavior(name="Success")
        >>> tree = Sequence("", children=[success_node])

        >>> pprint(tree)
        ... # doctest: +NORMALIZE_WHITESPACE
        Sequence(name='',
              children=[Behavior(name='Success', id=None)])

        >>> failure_node = Behavior(name="Failure")
        >>> insert(failure_node, (tree, 1))

        >>> pprint(tree)
        ... # doctest: +NORMALIZE_WHITESPACE
        Sequence(name='',
              children=[Behavior(name='Success', id=None),
                        Behavior(name='Failure', id=None)])

        >>> dummy_node = Behavior(name="Dummy")
        >>> insert(dummy_node, (tree, 0))
        >>> pprint(tree)
        ... # doctest: +NORMALIZE_WHITESPACE
        Sequence(name='',
            children=[Behavior(name='Dummy', id=None),
                    Behavior(name='Success', id=None),
                    Behavior(name='Failure', id=None)])
    """

    parent, index = where
    parent.insert_child(index, node)
    return


def move(
    node: ExistingNode,
    where: CompositeIndex,
) -> None:
    """Move a node.
    Examples:

        >>> success_node = Behavior(name="Success")
        >>> failure_node = Behavior(name="Failure")

        >>> tree = Sequence("")
        >>> tree.add_child(success_node)
        >>> tree.add_child(failure_node)

        >>> pprint(tree)
        ... # doctest: +NORMALIZE_WHITESPACE
        Sequence(name='',
            children=[Behavior(name='Success', id=None),
                    Behavior(name='Failure', id=None)])

        >>> move(failure_node, (tree, 0))
        >>> pprint(tree)
        ... # doctest: +NORMALIZE_WHITESPACE
        Sequence(name='',
            children=[Behavior(name='Failure', id=None),
                    Behavior(name='Success', id=None)])
    """
    parent, index = where
    insert(remove(node, parent), (parent, index))
    return


# # # =============================================================================
# # # Node and Position Selectors
# # # =============================================================================

from typing import Union, Generator


def iterate_nodes(tree: Union[Behavior, Sequence]):
    """
    Examples:
        >>> dummy_node = Behavior(name="Dummy")

        >>> list(iterate_nodes(dummy_node))
        ... # doctest: +ELLIPSIS
        [Behavior(name='Dummy', id=None)]

        >>> sequence = Sequence("", children=[dummy_node])
        >>> pprint(list(iterate_nodes(sequence)))
        ... # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        [Sequence(name='', children=[Behavior(name='Dummy', id=None)]),
        Behavior(name='Dummy', id=None)]

        >>> dummy_node_2 = Behavior(name="Dummy")
        >>> dummy_node_3 = Behavior(name="Dummy")
        >>> sequence_2 = Sequence("", children=[dummy_node_3])
        >>> sequence_3 = Sequence("", children=[dummy_node, dummy_node_2, sequence_2])
        >>> pprint(list(iterate_nodes(sequence_3)))
        ... # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        [Sequence(name='',
            children=[Behavior(name='Dummy', id=None),
                    Behavior(name='Dummy', id=None),
                    Sequence(name='',
                                children=[Behavior(name='Dummy', id=None)])]),
        Behavior(name='Dummy', id=None),
        Behavior(name='Dummy', id=None),
        Sequence(name='', children=[Behavior(name='Dummy', id=None)]),
        Behavior(name='Dummy', id=None)]
    """
    yield tree

    # Check if the node is a Sequence and has children to iterate over
    if hasattr(tree, "children"):
        for child in tree.children:
            yield from iterate_nodes(child)


def enumerate_nodes(tree: Behavior):
    """
    Examples:
        >>> dummy_node = Behavior(name="Dummy")
        >>> print(list(enumerate_nodes(dummy_node)))
        [(0, Behavior(name='Dummy', id=None))]

        >>> sequence = Sequence("", children=[dummy_node])
        >>> print(list(enumerate_nodes(sequence)))
        ... # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        [(0, Sequence(name='', children=[Behavior(name='Dummy', id=None)])), (1, Behavior(name='Dummy', id=None))]

        >>> success_node = Behavior(name="Success")
        >>> dummy_node_2 = Behavior(name="Dummy")
        >>> failure_node = Behavior(name="Failure")
        >>> success_node_2 = Behavior(name="Success")
        >>> sequence_2 = Sequence("", children=[dummy_node_2, success_node_2])
        >>> sequence_3 = Sequence("", children=[failure_node])
        >>> sequence_1 = Sequence("", children=[success_node, sequence_2, sequence_3])
        >>> print(list(enumerate_nodes(sequence_1)))
        ... # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        [(0, Sequence(name='', children=[Behavior(name='Success', id=None), Sequence(name='', children=[Behavior(name='Dummy', id=None), Behavior(name='Success', id=None)]), Sequence(name='', children=[Behavior(name='Failure', id=None)])])), (1, Behavior(name='Success', id=None)), (2, Sequence(name='', children=[Behavior(name='Dummy', id=None), Behavior(name='Success', id=None)])), (3, Behavior(name='Dummy', id=None)), (4, Behavior(name='Success', id=None)), (5, Sequence(name='', children=[Behavior(name='Failure', id=None)])), (6, Behavior(name='Failure', id=None))]
    """
    return enumerate(iterate_nodes(tree))


# # =============================================================================
# # Utility functions
# # =============================================================================


class QuitException(Exception):
    pass


def end_experiment():
    """I'm done, end the experiment."""
    raise QuitException("User ended the experiment.")
