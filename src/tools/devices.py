"""
NetBox Device Management Tools

This module provides MCP tools for managing and querying NetBox devices.
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
        logger.info(" [ENVIRONMENT] NetBox API connection established for device tools")
    except Exception as e:
        logger.error(f" [CONNECTION] Failed to connect to NetBox: {e}")
        nb = None


devices_server = FastMCP(
    name = "NetBoxDevices"
)
    
@devices_server.tool(
        name="get_devices",
        description="Retrieve devices from NetBox with optional filtering by site, device role, or device type. IMPORTANT: Use cached resources to find correct site/role/type slugs before calling this tool. For fuzzy matching, first search cached sites, device roles, and device types to find exact slugs."
    )
def get_devices(
        site: Optional[str] = None,
        device_role: Optional[str] = None,
        device_type: Optional[str] = None,
        limit: Optional[int] = 100
    ) -> Dict[str, Any]:
        """
        Get devices from NetBox with optional filtering.
        
        Args:
            site: Filter by site name or slug
            device_role: Filter by device role name or slug  
            device_type: Filter by device type model name or slug
            limit: Maximum number of devices to return (default: 100, max: 1000)
        
        Returns:
            Dictionary containing device information and metadata
        """
        if not nb:
            logger.error(f" [CONNECTION] NetBox connection not available. Check NETBOX_URL and NETBOX_API_TOKEN environment variables.")
            return {
                "error": "NetBox connection not available. Check NETBOX_URL and NETBOX_API_TOKEN environment variables."
            }
        
        try:
            if limit and (limit < 1 or limit > 1000):
                return {"error": "Limit must be between 1 and 1000"}
            
            device_filters = {}
            
            if site:
                device_filters['site'] = site
            if device_role:
                device_filters['role'] = device_role
            if device_type:
                device_filters['device_type'] = device_type
            
            logger.info(f" [TOOLS] Querying devices with filters: {device_filters}")
            devices = list(nb.dcim.devices.filter(**device_filters))
            
            if limit:
                devices = devices[:limit]
            
            result_devices = []
            for device in devices:
                try:
                    device_info = {
                        'id': device.id,
                        'name': device.name,
                        'slug': getattr(device, 'slug', None),
                        'type': device.device_type.model if device.device_type else None,
                        'role': device.role.name if device.role else None,
                        'rack': device.rack.name if device.rack else None
                    }
                    
                    if hasattr(device, 'custom_fields') and device.custom_fields:
                        custom_fields = {}
                        for key, value in device.custom_fields.items():
                            if value is not None:
                                custom_fields[key] = value
                        if custom_fields:
                            device_info['custom_fields'] = custom_fields
                    
                    result_devices.append(device_info)
                    
                except Exception as e:
                    logger.warning(f" [TOOLS] Error processing device {getattr(device, 'name', 'unknown')}: {e}")
                    result_devices.append({
                        'id': getattr(device, 'id', None),
                        'name': getattr(device, 'name', 'unknown'),
                        'error': f"Error processing device: {str(e)}"
                    })
            
            response = {
                'devices': result_devices,
                'metadata': {
                    'total_count': len(result_devices),
                    'filters_applied': {
                        'site': site,
                        'device_role': device_role,
                        'device_type': device_type
                    },
                    'limit': limit,
                    'truncated': len(devices) == limit if limit else False
                }
            }
            
            logger.info(f" [TOOLS] Returning {len(result_devices)} devices")
            return response
            
        except Exception as e:
            logger.error(f" [TOOLS] Error in get_devices: {e}")
            return {
                "error": f"Failed to retrieve devices: {str(e)}",
                "devices": [],
                "metadata": {"total_count": 0}
            }