"""
NetBox Cable Management Tools

This module provides MCP tools for managing and querying NetBox cables.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from fastmcp import FastMCP
import pynetbox
from dotenv import find_dotenv, load_dotenv

logger = logging.getLogger(__name__)

load_dotenv(find_dotenv())

NETBOX_URL = os.getenv('NETBOX_URL')
NETBOX_TOKEN = os.getenv('NETBOX_API_TOKEN')

if not NETBOX_URL or not NETBOX_TOKEN:
    logger.error(" [ENVIRONMENT] NetBox configuration missing. Please set NETBOX_URL and NETBOX_API_TOKEN")
    nb = None
else:
    try:
        nb = pynetbox.api(url=NETBOX_URL, token=NETBOX_TOKEN, threading=True)
        logger.info(" [ENVIRONMENT] NetBox API connection established for cable tools")
    except Exception as e:
        logger.error(f" [CONNECTION] Failed to connect to NetBox: {e}")
        nb = None


cables_server = FastMCP(
    name="NetBoxCables"
)


def _get_termination_info(termination):
    """Get minimal information about a cable termination (interface, front port, or rear port)"""
    if hasattr(termination, 'device') and termination.device:
        return {
            "type": "interface",
            "device": termination.device.name,
            "interface": termination.name if hasattr(termination, 'name') else None,
            "cable_id": termination.cable.id if termination.cable else None
        }
    elif hasattr(termination, 'rear_port'):
        return {
            "type": "front_port",
            "device": termination.device.name if termination.device else None,
            "port": termination.name if hasattr(termination, 'name') else None,
            "rear_port": termination.rear_port.name if termination.rear_port else None,
            "cable_id": termination.cable.id if termination.cable else None
        }
    elif hasattr(termination, 'front_ports'):
        front_ports = list(termination.front_ports) if termination.front_ports else []
        return {
            "type": "rear_port",
            "device": termination.device.name if termination.device else None,
            "port": termination.name if hasattr(termination, 'name') else None,
            "front_ports": [fp.name for fp in front_ports] if front_ports else [],
            "cable_id": termination.cable.id if termination.cable else None
        }
    else:
        return {
            "type": "unknown",
            "name": str(termination),
            "cable_id": termination.cable.id if termination.cable else None
        }

def _get_connected_terminations(termination):
    """
    Get all terminations connected to the same cable as the given termination.
    
    Args:
        termination: The termination object to find connections for
    
    Returns:
        List of connected termination objects
    """
    if not termination or not termination.cable:
        return []
    
    cable = termination.cable
    terminations = []
    
    if hasattr(cable, 'a_terminations') and cable.a_terminations:
        for term in cable.a_terminations + cable.b_terminations:
            if term != termination:
                terminations.append(term)
    
    return terminations

def _get_next_terminations(termination):
    """
    Get all possible next terminations including patch panel internal connections.
    
    Args:
        termination: The termination object to find next connections for
    
    Returns:
        List of next termination objects including internal patch panel connections
    """
    if not termination:
        return []
    
    next_terminations = []
    
    if termination.cable:
        connected = _get_connected_terminations(termination)
        for term in connected:
            next_terminations.append(term)
            
            if hasattr(term, 'rear_port') and term.rear_port:
                next_terminations.append(term.rear_port)
            elif hasattr(term, 'front_ports') and term.front_ports:
                front_ports = list(term.front_ports)
                if front_ports:
                    next_terminations.extend(front_ports)
    
    return next_terminations

@cables_server.tool(
    name="get_cable",
    description="Get detailed information about a specific cable by its ID. This tool provides comprehensive cable information including termination points, cable type, status, and connection details. Use this tool to analyze specific cable connections and verify cable documentation."
)
def get_cable(cable_id: int) -> Dict[str, Any]:
    """
    Get detailed information about a specific cable by its ID.
    
    Args:
        cable_id: ID of the cable to retrieve information for
    
    Returns:
        Dictionary containing cable information including type, status, and terminations
    """
    if not nb:
        return {"error": "NetBox connection not available"}
    
    try:
        cable = nb.dcim.cables.get(cable_id)
        if not cable:
            return {"error": f"Cable with ID {cable_id} not found"}
        
        terminations = []
        if hasattr(cable, 'a_terminations') and cable.a_terminations:
            for term in cable.a_terminations + cable.b_terminations:
                term_info = _get_termination_info(term)
                terminations.append(term_info)
        
        return {
            "cable_id": cable.id,
            "cable_type": cable.type.value if cable.type else None,
            "status": cable.status.value if hasattr(cable, 'status') and cable.status else None,
            "terminations": terminations
        }
        
    except Exception as e:
        logger.error(f"Error getting cable {cable_id}: {e}")
        return {"error": f"Failed to get cable: {str(e)}"}

def _expand_frontier(devices, visited, path_to_origin):
    """
    Expand the frontier of devices for bidirectional search algorithm.
    
    Args:
        devices: List of device names to expand from
        visited: Dictionary of already visited devices
        path_to_origin: Dictionary mapping devices to their paths from origin
    
    Returns:
        List of new device names discovered in this expansion
    """
    new_devices = []
    
    for device_name in devices:
        if device_name in visited:
            continue
            
        device = nb.dcim.devices.get(name=device_name)
        if not device:
            continue
            
        visited[device_name] = path_to_origin[device_name]
        
        interfaces = nb.dcim.interfaces.filter(device=device_name, cabled=True)
        for interface in interfaces:
            if not interface.cable:
                continue
                
            connected_terms = _get_connected_terminations(interface)
            for term in connected_terms:
                next_terminations = _get_next_terminations(term)
                
                for next_term in next_terminations:
                    if hasattr(next_term, 'device') and next_term.device:
                        next_device = next_term.device.name
                        if next_device not in visited:
                            new_path = path_to_origin[device_name].copy()
                            new_path.append({
                                "device": device_name,
                                "interface": interface.name,
                                "cable_id": interface.cable.id,
                                "next_device": next_device,
                                "next_interface": next_term.name if hasattr(next_term, 'name') else None
                            })
                            path_to_origin[next_device] = new_path
                            new_devices.append(next_device)
    
    return new_devices

def _find_intersection(source_visited, target_visited):
    """
    Find intersection between source and target visited devices.
    
    Args:
        source_visited: Dictionary of devices visited from source
        target_visited: Dictionary of devices visited from target
    
    Returns:
        Name of the first intersecting device or None if no intersection
    """
    for device in source_visited:
        if device in target_visited:
            return device
    return None

def _build_complete_path(meeting_device, source_visited, target_visited):
    """
    Build complete path from source to target through meeting point.
    
    Args:
        meeting_device: Name of the device where paths meet
        source_visited: Dictionary of devices visited from source with their paths
        target_visited: Dictionary of devices visited from target with their paths
    
    Returns:
        Dictionary containing complete path and meeting point information
    """
    source_path = source_visited[meeting_device]
    target_path = target_visited[meeting_device]
    
    target_path_reversed = list(reversed(target_path))
    
    complete_path = source_path + target_path_reversed[1:]
    
    return {
        "path": complete_path,
        "meeting_point": {
            "device": meeting_device,
            "source_hops": len(source_path),
            "target_hops": len(target_path)
        },
        "total_hops": len(source_path) + len(target_path) - 1
    }

@cables_server.tool(
    name="trace_devices_connection",
    description="Trace cable connections between two devices using bidirectional search algorithm. This tool efficiently finds the optimal path between devices by searching from both source and target simultaneously until a common meeting point is found. Algorithm: Start from both devices, expand frontiers in iterations, check for intersections, build complete path when meeting point found. Use this tool for network troubleshooting and path analysis between any two devices in your network."
)
def trace_devices_connection(
    source_device: str,
    target_device: str,
    max_iterations: int = 10
) -> Dict[str, Any]:
    """
    Trace cable connections between two devices using bidirectional search algorithm.
    
    Algorithm: Start from both source and target devices, expand frontiers in iterations
    by exploring connected interfaces and following cables to next devices. Check for
    intersections between source and target frontiers. When intersection found, build
    complete path by combining source path to meeting point with reversed target path.
    
    Args:
        source_device: Name of the source device
        target_device: Name of the target device
        max_iterations: Maximum number of iterations to search (default: 10)
    
    Returns:
        Dictionary containing complete path information and meeting point details
    """
    if not nb:
        return {"error": "NetBox connection not available"}
    
    try:
        source_dev = nb.dcim.devices.get(name=source_device)
        target_dev = nb.dcim.devices.get(name=target_device)
        
        if not source_dev:
            return {"error": f"Source device '{source_device}' not found"}
        if not target_dev:
            return {"error": f"Target device '{target_device}' not found"}
        
        source_frontier = [source_device]
        target_frontier = [target_device]
        source_visited = {}
        target_visited = {}
        source_paths = {source_device: []}
        target_paths = {target_device: []}
        
        for iteration in range(max_iterations):
            new_source_devices = _expand_frontier(source_frontier, source_visited, source_paths)
            
            intersection = _find_intersection(new_source_devices, target_visited)
            if intersection:
                return _build_complete_path(intersection, source_visited, target_visited)
            
            new_target_devices = _expand_frontier(target_frontier, target_visited, target_paths)
            
            intersection = _find_intersection(new_target_devices, source_visited)
            if intersection:
                return _build_complete_path(intersection, source_visited, target_visited)
            
            source_frontier = new_source_devices
            target_frontier = new_target_devices
            
            if not source_frontier and not target_frontier:
                break
        
        return {
            "error": f"No path found between '{source_device}' and '{target_device}' after {max_iterations} iterations",
            "source_devices_explored": len(source_visited),
            "target_devices_explored": len(target_visited)
        }
        
    except Exception as e:
        logger.error(f"Error tracing devices connection: {e}")
        return {"error": f"Failed to trace connection: {str(e)}"}

def _build_tree_node(termination, visited_terminations=None, current_depth=0, max_depth=10):
    """
    Recursively build tree node for network topology exploration.
    
    Args:
        termination: The termination object (interface, front port, or rear port)
        visited_terminations: Set of already visited terminations to prevent loops
        current_depth: Current depth in the tree
        max_depth: Maximum depth to explore
    
    Returns:
        Tree node dictionary or None if max depth reached or already visited
    """
    if visited_terminations is None:
        visited_terminations = set()
    
    if current_depth >= max_depth:
        return None
    
    term_id = f"{termination.device.name if hasattr(termination, 'device') and termination.device else 'unknown'}_{termination.name if hasattr(termination, 'name') else 'unknown'}"
    
    if term_id in visited_terminations:
        return None
    
    visited_terminations.add(term_id)
    
    node = {
        "device": termination.device.name if hasattr(termination, 'device') and termination.device else None,
        "interface": termination.name if hasattr(termination, 'name') else None,
        "type": "interface" if hasattr(termination, 'device') else "port",
        "cable_id": termination.cable.id if termination.cable else None,
        "depth": current_depth,
        "children": []
    }
    
    if termination.cable:
        connected_terms = _get_connected_terminations(termination)
        for term in connected_terms:
            child_node = _build_tree_node(term, visited_terminations, current_depth + 1, max_depth)
            if child_node:
                node["children"].append(child_node)
            
            if hasattr(term, 'rear_port') and term.rear_port:
                rear_node = _build_tree_node(term.rear_port, visited_terminations, current_depth + 1, max_depth)
                if rear_node:
                    node["children"].append(rear_node)
            elif hasattr(term, 'front_ports') and term.front_ports:
                front_ports = list(term.front_ports)
                for fp in front_ports:
                    front_node = _build_tree_node(fp, visited_terminations, current_depth + 1, max_depth)
                    if front_node:
                        node["children"].append(front_node)
    
    return node

@cables_server.tool(
    name="trace_from_interface",
    description="Trace cable connections from a specific interface using tree search algorithm. This tool builds a complete network tree starting from the specified interface, exploring all possible connections through devices, patch panels, and cables. Algorithm: Recursive tree building with left-middle-right traversal, handle all termination types (interfaces, front ports, rear ports), explore patch panel internal connections, build complete network topology as tree structure. Use this tool to map complete network topology from a starting point."
)
def trace_from_interface(
    device_name: str,
    interface_name: str,
    max_depth: int = 10
) -> Dict[str, Any]:
    """
    Trace cable connections from a specific interface using tree search algorithm.
    
    Algorithm: Recursive tree building with left-middle-right traversal. Start from
    specified interface, recursively explore all connected terminations (interfaces,
    front ports, rear ports). Handle patch panel internal connections by following
    front port to rear port relationships. Build complete network topology as tree
    structure with nodes representing devices/interfaces and edges representing cables.
    
    Args:
        device_name: Name of the device containing the interface
        interface_name: Name of the interface to start tracing from
        max_depth: Maximum depth for tree exploration (default: 10)
    
    Returns:
        Dictionary containing complete network tree and metadata
    """
    if not nb:
        return {"error": "NetBox connection not available"}
    
    try:
        interface = nb.dcim.interfaces.get(device=device_name, name=interface_name)
        if not interface:
            return {"error": f"Interface '{interface_name}' not found on device '{device_name}'"}
        
        if not interface.cable:
            return {
                "message": f"Interface '{interface_name}' on device '{device_name}' has no cable connected",
                "tree": {
                    "device": device_name,
                    "interface": interface_name,
                    "type": "interface",
                    "cable_id": None,
                    "children": []
                }
            }
        
        tree = _build_tree_node(interface, max_depth=max_depth)
        
        def count_nodes(node):
            count = 1
            for child in node.get("children", []):
                count += count_nodes(child)
            return count
        
        def count_cables(node):
            cables = set()
            if node.get("cable_id"):
                cables.add(node["cable_id"])
            for child in node.get("children", []):
                cables.update(count_cables(child))
            return cables
        
        total_nodes = count_nodes(tree)
        total_cables = len(count_cables(tree))
        
        return {
            "tree": tree,
            "metadata": {
                "start_device": device_name,
                "start_interface": interface_name,
                "total_nodes": total_nodes,
                "total_cables": total_cables,
                "max_depth": max_depth
            }
        }
        
    except Exception as e:
        logger.error(f"Error tracing from interface: {e}")
        return {"error": f"Failed to trace from interface: {str(e)}"}