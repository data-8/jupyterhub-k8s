#!/usr/bin/python3

"""Execute changes to the Kubernetes cluster"""

import heapq
import logging

from populate import populate

scale_logger = logging.getLogger("scale")
slack_logger = logging.getLogger("slack")  # used for slack message only


def __update_nodes(k8s, nodes, unschedulable):
    """Update given list of nodes with given
    unschedulable property"""

    updated = []
    for node in nodes:
        k8s.set_unschedulable(node.metadata.name, unschedulable)
        updated.append(node.metadata.name)
    return updated


def update_unschedulable(number_unschedulable, nodes, k8s, calculate_priority=None):
    """Attempt to make sure given number of
    nodes are blocked, if possible; 
    return number of nodes newly blocked; negative
    value means the number of nodes unblocked

    calculate_priority should be a function
    that takes a node and return its priority value
    for being blocked; smallest == highest
    priority; default implementation uses get_pods_number_on_node

    CRITICAL NODES SHOULD NOT BE INCLUDED IN THE INPUT LIST"""

    assert number_unschedulable >= 0
    number_unschedulable = int(number_unschedulable)

    scale_logger.info(
        "Updating unschedulable flags to ensure %i nodes are unschedulable", number_unschedulable)

    if calculate_priority == None:
        # Default implementation based on get_pods_number_on_node
        def calculate_priority(node): return k8s.get_pods_number_on_node(node)

    schedulable_nodes = []
    unschedulable_nodes = []

    priority = []

    # Analyze nodes status and establish blocking priority
    for count in range(len(nodes)):
        if nodes[count].spec.unschedulable:
            unschedulable_nodes.append(nodes[count])
        else:
            schedulable_nodes.append(nodes[count])
        priority.append(
            (calculate_priority(nodes[count]), count))

    # Attempt to modify property based on priority
    toBlock = []
    toUnBlock = []

    heapq.heapify(priority)
    for _ in range(number_unschedulable):
        if len(priority) > 0:
            _, index = heapq.heappop(priority)
            if nodes[index] in schedulable_nodes:
                toBlock.append(nodes[index])
        else:
            break
    for _, index in priority:
        if nodes[index] in unschedulable_nodes:
            toUnBlock.append(nodes[index])

    __update_nodes(k8s, toBlock, True)
    scale_logger.debug("%i nodes newly blocked", len(toBlock))
    __update_nodes(k8s, toUnBlock, False)
    scale_logger.debug("%i nodes newly unblocked", len(toUnBlock))
    if (len(toBlock) != 0 or len(toUnBlock) != 0) and (len(toBlock) != len(toUnBlock)) and not k8s.test:
        slack_logger.info(
            "%i nodes newly blocked, %i nodes newly unblocked", len(toBlock), len(toUnBlock))
    if len(toUnBlock) != 0:
        populate(k8s)

    return len(toBlock) - len(toUnBlock)
