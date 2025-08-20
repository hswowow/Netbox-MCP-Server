"""
NetBox MCP Server

Main entry point and server file that imports and registers all tools and resources.
This file serves as both the server implementation and the primary entry point.
"""

from fastmcp import FastMCP
from dotenv import find_dotenv, load_dotenv
import logging
import os
from pathlib import Path
from datetime import datetime, timedelta

load_dotenv(find_dotenv())

log_file = Path("netbox_mcp_server.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.expanduser('~/netbox_mcp_server.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


devices_server = None
cables_server = None
ipam_server = None
sites_server = None
interfaces_server = None
prompts_server = None
resources_server = None
cached_tools_server = None

def should_update_resources():
    """Check if resources should be updated (once per day)"""
    timestamp_file = Path("resources/.last_update")
    
    if not timestamp_file.exists():
        logger.info(" [RESOURCES] No previous update timestamp found, updating resources...")
        return True
    
    try:
        with open(timestamp_file, 'r') as f:
            last_update_str = f.read().strip()
            last_update = datetime.fromisoformat(last_update_str)
        
        now = datetime.now()
        time_since_update = now - last_update
        
        if time_since_update >= timedelta(days=1):
            logger.info(f" [RESOURCES] Last update was {time_since_update.days} days ago, updating resources...")
            return True
        else:
            logger.info(f" [RESOURCES] Resources updated {time_since_update.days} days ago, skipping update...")
            return False
            
    except Exception as e:
        logger.warning(f" [RESOURCES] Error reading update timestamp: {e}, updating resources...")
        return True

def update_resources_if_needed():
    """Update resources only if needed (once per day)"""
    if not should_update_resources():
        return
    
    try:
        from resources.update_resources import NetBoxResourceUpdater
        
        logger.info(" [RESOURCES] Starting daily resource update...")
        updater = NetBoxResourceUpdater()
        results = updater.update_all_resources()
        
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        if success_count == total_count:
            logger.info(f" [RESOURCES] All {total_count} resource files updated successfully")
            
            timestamp_file = Path("resources/.last_update")
            timestamp_file.parent.mkdir(exist_ok=True)
            with open(timestamp_file, 'w') as f:
                f.write(datetime.now().isoformat())
            
            logger.info(" [RESOURCES] Update timestamp saved")
        else:
            logger.error(f" [RESOURCES] Only {success_count}/{total_count} resources updated successfully")
        
    except Exception as e:
        logger.error(f" [RESOURCES] Failed to update resources: {e}")
        logger.warning(" [RESOURCES] Continuing with existing resource files...")

update_resources_if_needed()

try:
    from tools.devices import devices_server
    from tools.cables import cables_server
    from tools.ipam import ipam_server
    from tools.sites import sites_server
    from tools.interfaces import interfaces_server
    from tools.cached_tools import cached_tools_server
    from prompts.prompts import prompts_server
    from resources.resources import resources_server
    
    logger.info(" [SERVER] All modules imported successfully")
    
except ImportError as e:
    logger.warning(f" [SERVER] Some modules could not be imported: {e}")
    logger.info(" [SERVER] Server will run with resources only")

mcp = FastMCP(
    name="netbox-mcp",
    instructions=f"""
    NetBox MCP Server provides access to NetBox DCIM and IPAM data.
    Resources, prompts and tools are provided.
    Use tools for dynamic queries and resources for cached reference data.
    """
)
if devices_server:
    mcp.mount(devices_server)
if sites_server:
    mcp.mount(sites_server)
if ipam_server:
    mcp.mount(ipam_server)
if cables_server:
    mcp.mount(cables_server)
if interfaces_server:
    mcp.mount(interfaces_server)
if cached_tools_server:
    mcp.mount(cached_tools_server)
if prompts_server:
    mcp.mount(prompts_server)
if resources_server:
    mcp.mount(resources_server)



def main():
    """Main entry point for the NetBox MCP server."""
    transport = os.getenv('MCP_TRANSPORT', 'streamable-http')
    host = os.getenv('MCP_HOST', '0.0.0.0')
    port = int(os.getenv('MCP_PORT', '8000'))
    
    logger.info(f" [SERVER] Starting NetBox MCP Server with {transport} transport...")
    logger.info(f" [SERVER] Host: {host}, Port: {port}")
    
    try:
        if transport == "stdio":
            mcp.run(transport="stdio")
        elif transport == "sse":
            mcp.run(transport="sse", host=host, port=port)
        elif transport == "streamable-http":
            mcp.run(transport="streamable-http", host=host, port=port)
        else:
            logger.error(f" [SERVER] Unknown transport: {transport}")
            return 1
        return 0
    except Exception as e:
        logger.error(f" [FATAL] Failed to start server: {e}")
        return 1



if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)