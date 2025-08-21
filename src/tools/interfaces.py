"""
NetBox Interface Management Tools

This module provides MCP tools for managing and querying NetBox interfaces.
"""
from fastmcp import FastMCP
import os
import logging
from typing import List, Dict, Any, Optional
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
        logger.info(" [ENVIRONMENT] NetBox API connection established for interface tools")
    except Exception as e:
        logger.error(f" [CONNECTION] Failed to connect to NetBox: {e}")
        nb = None

interfaces_server = FastMCP(
    name = "NetBoxInterfaces"
)
    
@interfaces_server.tool(
        name="get_interfaces",
        description="Retrieve interfaces from NetBox with minimal token usage. Returns essential interface information: id, name, device_name, type, status, kind, and VLAN assignments. Use this tool to quickly analyze network interfaces and verify VLAN configurations. IMPORTANT: Use cached resources to find correct device names before calling this tool. For fuzzy matching, first search cached devices to find exact device names from user-provided aliases."
    )
def get_interfaces(
        device: Optional[str] = None,
        device_id: Optional[int] = None,
        name: Optional[str] = None,
        type: Optional[str] = None,
        kind: Optional[str] = None,
        enabled: Optional[bool] = None,
        cabled: Optional[bool] = None,
        connected: Optional[bool] = None,
        mgmt_only: Optional[bool] = None,
        lag: Optional[str] = None,
        mode: Optional[str] = None,
        limit: Optional[int] = 100
    ) -> Dict[str, Any]:
        """
        Get interfaces from NetBox with optional filtering.
        
        Args:
            device: Filter by device name or slug
            device_id: Filter by specific device ID
            name: Filter by interface name
            type: Filter by interface type (e.g., "1000base-t", "10gbase-x-sfpp")
            kind: Filter by interface kind ("physical", "virtual", "wireless")
            enabled: Filter by enabled status (True/False)
            cabled: Filter by cable connection status (True/False)
            connected: Filter by active connection status (True/False)
            mgmt_only: Filter by management interface status (True/False)
            lag: Filter by LAG (Link Aggregation Group) name
            mode: Filter by interface mode ("access", "tagged", etc.)
            limit: Maximum number of interfaces to return (default: 100, max: 1000)
        
        Returns:
            Dictionary containing minimal interface information (id, name, device_name, type, status, kind, vlan) and metadata
        """
        if not nb:
            logger.error(f" [CONNECTION] NetBox connection not available. Check NETBOX_URL and NETBOX_API_TOKEN environment variables.")
            return {
                "error": "NetBox connection not available. Check NETBOX_URL and NETBOX_API_TOKEN environment variables."
            }
        
        try:
            if limit and (limit < 1 or limit > 1000):
                return {"error": "Limit must be between 1 and 1000"}
            
            interface_filters = {}
            
            if device:
                interface_filters['device'] = device
            if device_id:
                interface_filters['device_id'] = device_id
            if name:
                interface_filters['name'] = name
            if type:
                interface_filters['type'] = type
            if kind:
                interface_filters['kind'] = kind
            if enabled is not None:
                interface_filters['enabled'] = enabled
            if cabled is not None:
                interface_filters['cabled'] = cabled
            if connected is not None:
                interface_filters['connected'] = connected
            if mgmt_only is not None:
                interface_filters['mgmt_only'] = mgmt_only
            if lag:
                interface_filters['lag'] = lag
            if mode:
                interface_filters['mode'] = mode
            
            logger.info(f" [TOOLS] Querying interfaces with filters: {interface_filters}")
            interfaces = list(nb.dcim.interfaces.filter(**interface_filters))
            
            if limit:
                interfaces = interfaces[:limit]
            
            result_interfaces = []
            for interface in interfaces:
                try:
                    connected = interface.cable is not None
                
                    untagged_vlan = None
                    tagged_vlans = []
                    
                    if interface.untagged_vlan:
                        untagged_vlan = {
                            'id': interface.untagged_vlan.id,
                            'name': interface.untagged_vlan.name,
                            'vid': interface.untagged_vlan.vid
                        }
                    
                    if interface.tagged_vlans:
                        for vlan in interface.tagged_vlans:
                            tagged_vlans.append({
                                'id': vlan.id,
                                'name': vlan.name,
                                'vid': vlan.vid
                            })
                    
                    status = "enabled" if interface.enabled else "disabled"
                    if interface.enabled and connected:
                        status = "connected"
                    elif interface.enabled and not connected:
                        status = "enabled"
                    else:
                        status = "disabled"
                    
                    vlan_info = None
                    if untagged_vlan:
                        vlan_info = f"untagged:{untagged_vlan['vid']}"
                    elif tagged_vlans:
                        vlan_ids = [str(vlan['vid']) for vlan in tagged_vlans]
                        vlan_info = f"tagged:{','.join(vlan_ids)}"
                    
                    interface_info = {
                        'id': interface.id,
                        'name': interface.name,
                        'device_name': interface.device.name if interface.device else None,
                        'type': interface.type.value if interface.type else None,
                        'status': status,
                        'kind': interface.kind.value if hasattr(interface, 'kind') and interface.kind else None,
                        'vlan': vlan_info
                    }
                    result_interfaces.append(interface_info)
                    
                except Exception as e:
                    logger.warning(f" [TOOLS] Error processing interface {getattr(interface, 'name', 'unknown')}: {e}")
                    result_interfaces.append({
                        'id': getattr(interface, 'id', None),
                        'name': getattr(interface, 'name', 'unknown'),
                        'device_name': getattr(interface.device, 'name', None) if hasattr(interface, 'device') and interface.device else None,
                        'type': None,
                        'status': 'error',
                        'kind': None,
                        'vlan': None,
                        'error': f"Error processing interface: {str(e)}"
                    })
            
            connection_summary = {
                'total': len(result_interfaces),
                'connected': len([i for i in result_interfaces if i.get('connected', False)])
            }
            
            response = {
                'interfaces': result_interfaces,
                'summary': connection_summary,
                'metadata': {
                    'total_count': len(result_interfaces),
                    'filters_applied': {
                        'device': device,
                        'device_id': device_id,
                        'name': name,
                        'type': type,
                        'kind': kind,
                        'enabled': enabled,
                        'cabled': cabled,
                        'connected': connected,
                        'mgmt_only': mgmt_only,
                        'lag': lag,
                        'mode': mode
                    },
                    'limit': limit,
                    'truncated': len(interfaces) == limit if limit else False
                }
            }
            
            logger.info(f" [TOOLS] Returning {len(result_interfaces)} interfaces")
            return response
            
        except Exception as e:
            logger.error(f" [TOOLS] Error in get_interfaces: {e}")
            return {
                "error": f"Failed to retrieve interfaces: {str(e)}",
                "interfaces": [],
                "metadata": {"total_count": 0}
            }
@interfaces_server.tool(
        name="get_front_ports",
        description="Retrieve front ports from NetBox patch panels and modular devices. This tool is essential for analyzing patch panel connections and cable management infrastructure. Front ports are the visible ports on patch panels that connect to rear ports internally. Use this tool to map patch panel port assignments, trace cable connections through patch panels, and document cable management. IMPORTANT: Use cached resources to find correct device names before calling this tool. For fuzzy matching, first search cached devices to find exact device names from user-provided aliases."
    )
def get_front_ports(
        device: Optional[str] = None,
        device_id: Optional[int] = None,
        name: Optional[str] = None,
        type: Optional[str] = None,
        cabled: Optional[bool] = None,
        rear_port: Optional[str] = None,
        rear_port_id: Optional[int] = None,
        limit: Optional[int] = 100
    ) -> Dict[str, Any]:
        """
        Get front ports from NetBox with optional filtering.
        
        Args:
            device: Filter by device name or slug
            device_id: Filter by specific device ID
            name: Filter by front port name
            type: Filter by port type (e.g., "8p8c", "lc", "sc", "st", "mtrj")
            cabled: Filter by cable connection status (True/False)
            rear_port: Filter by connected rear port name
            rear_port_id: Filter by specific rear port ID
            limit: Maximum number of front ports to return (default: 100, max: 1000)
        
        Returns:
            Dictionary containing front port information and metadata
        """
        if not nb:
            return {
                "error": "NetBox connection not available. Check NETBOX_URL and NETBOX_API_TOKEN environment variables."
            }
        
        try:
            if limit and (limit < 1 or limit > 1000):
                return {"error": "Limit must be between 1 and 1000"}
            
            port_filters = {}
            
            if device:
                port_filters['device'] = device
            if device_id:
                port_filters['device_id'] = device_id
            if name:
                port_filters['name'] = name
            if type:
                port_filters['type'] = type
            if cabled is not None:
                port_filters['cabled'] = cabled
            if rear_port:
                port_filters['rear_port'] = rear_port
            if rear_port_id:
                port_filters['rear_port_id'] = rear_port_id
            
            logger.info(f" [TOOLS] Querying front ports with filters: {port_filters}")
            front_ports = list(nb.dcim.front_ports.filter(**port_filters))
            
            if limit:
                front_ports = front_ports[:limit]
            
            result_ports = []
            for port in front_ports:
                try:
                    connected = port.cable is not None
                    
                    port_info = {
                        'id': port.id,
                        'connected': connected,
                        'device_name': port.device.name if port.device else None,
                        'type': port.type.value if port.type else None,
                        'kind': 'front_port'
                    }
                    result_ports.append(port_info)
                    
                except Exception as e:
                    logger.warning(f" [TOOLS] Error processing front port {getattr(port, 'name', 'unknown')}: {e}")
                    result_ports.append({
                        'id': getattr(port, 'id', None),
                        'name': getattr(port, 'name', 'unknown'),
                        'device': {
                            'name': getattr(port.device, 'name', None) if hasattr(port, 'device') and port.device else None
                        },
                        'error': f"Error processing front port: {str(e)}"
                    })
            
            connection_summary = {
                'total': len(result_ports),
                'connected': len([p for p in result_ports if p.get('connected', False)])
            }
            
            response = {
                'front_ports': result_ports,
                'summary': connection_summary,
                'metadata': {
                    'total_count': len(result_ports),
                    'filters_applied': {
                        'device': device,
                        'device_id': device_id,
                        'name': name,
                        'type': type,
                        'cabled': cabled,
                        'rear_port': rear_port,
                        'rear_port_id': rear_port_id
                    },
                    'limit': limit,
                    'truncated': len(front_ports) == limit if limit else False
                }
            }
            
            logger.info(f" [TOOLS] Returning {len(result_ports)} front ports")
            return response
            
        except Exception as e:
            logger.error(f" [TOOLS] Error in get_front_ports: {e}")
            return {
                "error": f"Failed to retrieve front ports: {str(e)}",
                "front_ports": [],
                "metadata": {"total_count": 0}
            }
    
@interfaces_server.tool(
        name="get_rear_ports",
        description="Retrieve rear ports from NetBox patch panels and modular devices. This tool is crucial for understanding the internal structure of patch panels and modular devices. Rear ports are the internal ports that connect to front ports and can have multiple positions for different cable types. Use this tool to analyze patch panel internal wiring, understand port configurations, and trace connections through modular devices. IMPORTANT: Use cached resources to find correct device names before calling this tool. For fuzzy matching, first search cached devices to find exact device names from user-provided aliases."
    )
def get_rear_ports(
        device: Optional[str] = None,
        device_id: Optional[int] = None,
        name: Optional[str] = None,
        type: Optional[str] = None,
        positions: Optional[int] = None,
        cabled: Optional[bool] = None,
        limit: Optional[int] = 100
    ) -> Dict[str, Any]:
        """
        Get rear ports from NetBox with optional filtering.
        
        Args:
            device: Filter by device name or slug
            device_id: Filter by specific device ID
            name: Filter by rear port name
            type: Filter by port type (e.g., "8p8c", "lc", "sc", "st", "mtrj")
            positions: Filter by number of positions on the rear port
            cabled: Filter by cable connection status (True/False)
            limit: Maximum number of rear ports to return (default: 100, max: 1000)
        
        Returns:
            Dictionary containing rear port information and metadata
        """
        if not nb:
            return {
                "error": "NetBox connection not available. Check NETBOX_URL and NETBOX_API_TOKEN environment variables."
            }
        
        try:
            if limit and (limit < 1 or limit > 1000):
                return {"error": "Limit must be between 1 and 1000"}
            
            port_filters = {}
            
            if device:
                port_filters['device'] = device
            if device_id:
                port_filters['device_id'] = device_id
            if name:
                port_filters['name'] = name
            if type:
                port_filters['type'] = type
            if positions:
                port_filters['positions'] = positions
            if cabled is not None:
                port_filters['cabled'] = cabled
            
            logger.info(f" [TOOLS] Querying rear ports with filters: {port_filters}")
            rear_ports = list(nb.dcim.rear_ports.filter(**port_filters))
            
            if limit:
                rear_ports = rear_ports[:limit]
            
            result_ports = []
            for port in rear_ports:
                try:
                    connected = port.cable is not None
                    
                    port_info = {
                        'id': port.id,
                        'connected': connected,
                        'device_name': port.device.name if port.device else None,
                        'type': port.type.value if port.type else None,
                        'kind': 'rear_port'
                    }
                    result_ports.append(port_info)
                    
                except Exception as e:
                    logger.warning(f" [TOOLS] Error processing rear port {getattr(port, 'name', 'unknown')}: {e}")
                    result_ports.append({
                        'id': getattr(port, 'id', None),
                        'name': getattr(port, 'name', 'unknown'),
                        'device': {
                            'name': getattr(port.device, 'name', None) if hasattr(port, 'device') and port.device else None
                        },
                        'error': f"Error processing rear port: {str(e)}"
                    })
            
            connection_summary = {
                'total': len(result_ports),
                'connected': len([p for p in result_ports if p.get('connected', False)])
            }
            
            response = {
                'rear_ports': result_ports,
                'summary': connection_summary,
                'metadata': {
                    'total_count': len(result_ports),
                    'filters_applied': {
                        'device': device,
                        'device_id': device_id,
                        'name': name,
                        'type': type,
                        'positions': positions,
                        'cabled': cabled
                    },
                    'limit': limit,
                    'truncated': len(rear_ports) == limit if limit else False
                }
            }
            
            logger.info(f" [TOOLS] Returning {len(result_ports)} rear ports")
            return response
            
        except Exception as e:
            logger.error(f" [TOOLS] Error in get_rear_ports: {e}")
            return {
                "error": f"Failed to retrieve rear ports: {str(e)}",
                "rear_ports": [],
                "metadata": {"total_count": 0}
            }