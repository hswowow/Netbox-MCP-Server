from fastmcp import FastMCP
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

resources_server = FastMCP (
    name = "NetBoxResources"
)

try:
    @resources_server.resource("netbox://sites")
    def get_sites_resource() -> str:
        """Get all NetBox sites from cached JSON file."""
        try:
            sites_file = Path("resources/sites.json")
            if sites_file.exists():
                logger.info(" [RESOURCES] Loading sites resource from cache")
                with open(sites_file, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                logger.warning(" [RESOURCES] Sites resource file not found")
                return json.dumps({"error": "Sites resource file not found", "data": []}, indent=2)
        except Exception as e:
            logger.error(f" [RESOURCES] Failed to read sites file: {e}")
            return json.dumps({"error": f"Failed to read sites file: {str(e)}", "data": []}, indent=2)
    
    @resources_server.resource("netbox://device-types")  
    def get_device_types_resource() -> str:
        """Get all NetBox device types from cached JSON file."""
        try:
            device_types_file = Path("resources/device_types.json")
            if device_types_file.exists():
                logger.info(" [RESOURCES] Loading device types resource from cache")
                with open(device_types_file, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                logger.warning(" [RESOURCES] Device types resource file not found")
                return json.dumps({"error": "Device types resource file not found", "data": []}, indent=2)
        except Exception as e:
            logger.error(f" [RESOURCES] Failed to read device types file: {e}")
            return json.dumps({"error": f"Failed to read device types file: {str(e)}", "data": []}, indent=2)
    
    @resources_server.resource("netbox://device-roles")
    def get_device_roles_resource() -> str:
        """Get all NetBox device roles from cached JSON file.""" 
        try:
            device_roles_file = Path("resources/device_roles.json")
            if device_roles_file.exists():
                logger.info(" [RESOURCES] Loading device roles resource from cache")
                with open(device_roles_file, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                logger.warning(" [RESOURCES] Device roles resource file not found")
                return json.dumps({"error": "Device roles resource file not found", "data": []}, indent=2)
        except Exception as e:
            logger.error(f" [RESOURCES] Failed to read device roles file: {e}")
            return json.dumps({"error": f"Failed to read device roles file: {str(e)}", "data": []}, indent=2)
    
    @resources_server.resource("netbox://manufacturers")
    def get_manufacturers_resource() -> str:
        """Get all NetBox manufacturers from cached JSON file."""
        try:
            manufacturers_file = Path("resources/manufacturers.json")
            if manufacturers_file.exists():
                logger.info(" [RESOURCES] Loading manufacturers resource from cache")
                with open(manufacturers_file, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                logger.warning(" [RESOURCES] Manufacturers resource file not found")
                return json.dumps({"error": "Manufacturers resource file not found", "data": []}, indent=2)
        except Exception as e:
            logger.error(f" [RESOURCES] Failed to read manufacturers file: {e}")
            return json.dumps({"error": f"Failed to read manufacturers file: {str(e)}", "data": []}, indent=2)
    
    logger.info(" [RESOURCES] All 4 NetBox resources registered successfully")
    
except Exception as e:
    logger.error(f" [RESOURCES] Failed to register resources: {e}")