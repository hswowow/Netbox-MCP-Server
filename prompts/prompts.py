from fastmcp import FastMCP
import logging

logger = logging.getLogger(__name__)

prompts_server = FastMCP(
    name = "NetBoxPrompts"
)

@prompts_server.prompt(
    name = "TraceNetworkPath",
    description = "Builds a comprehensive network path between two devices using bidirectional search algorithm"
) 
def trace_network_path (
    source_device: str,
    destination_device: str
) -> str:
    """Generate a comprehensive network path trace between two devices."""
    logger.info(f" [PROMPTS] Generating network path trace from {source_device} to {destination_device}")
    return f"""
    Trace the complete network path from {source_device} to {destination_device} using the enhanced cable tracing tools.
    
    **Recommended Tool Usage:**
    1. **Primary Method (Recommended):** Use `trace_devices_connection` to automatically find the optimal path using bidirectional search
    2. **Alternative Method:** If you need more detailed analysis:
       - Use `get_devices` to find both {source_device} and {destination_device}
       - Use `get_interfaces` to identify available interfaces on both devices
       - Use `trace_from_interface` to trace from a specific interface for detailed topology
    3. Use `get_cable` for detailed cable information when needed
    
    **Bidirectional Search Algorithm:**
    - The `trace_devices_connection` tool uses bidirectional search for optimal path finding
    - It searches from both source and target devices simultaneously
    - Finds the shortest path by meeting at a common device/interface
    - Handles complex network topologies efficiently
    
    **Path Analysis Guidelines:**
    - Follow the complete hop-by-hop path including patch panels
    - Identify front port ↔ rear port connections in patch panels
    - Note cable types and IDs for each segment
    - Map the complete topology from source to destination
    - Analyze path efficiency and meeting points
    
    **Expected Output:**
    - Complete path with device names and interfaces
    - Patch panel connections (front/rear ports)
    - Cable information (IDs, types)
    - Total path length and number of hops
    - Meeting point information
    - Path efficiency metrics
    
    **Enhanced Features:**
    - Bidirectional search for optimal path discovery
    - Automatic interface discovery eliminates the need to know interface names
    - Efficient algorithm for complex network topologies
    - Comprehensive error handling for missing devices or interfaces
    """

@prompts_server.prompt(
    name = "DeviceInterfaces",
    description = "Analyzes device's interfaces types, utilization, and connectivity using available tools"
)
def analyze_device_interfaces(
    device_name: str,
    interface_type: str = "all",
    connection_status: str = "connected"
) -> str:
    """Generate analysis guidance for device interface inspection."""
    logger.info(f" [PROMPTS] Generating device interface analysis for {device_name}")
    return f"""
    Analyze interfaces for device: {device_name} using the interface tools.
    
    **Recommended Tool Usage:**
    1. Use `get_devices` to verify {device_name} exists and get basic info
    2. Use `get_interfaces` with filters:
       - device: {device_name}
       - type: {interface_type}
       - connected: {connection_status}
    3. Use `get_front_ports` and `get_rear_ports` for patch panel analysis
    4. Use `trace_from_interface` to follow connections from specific interfaces
    
    **Analysis Focus:**
    - Interface connectivity status and types
    - Connected vs disconnected interface summary
    - Patch panel connections (front/rear ports)
    - Direct device-to-device connections
    - Uplink/downlink identification
    
    **Expected Output:**
    - Interface inventory with connection status
    - Patch panel port mappings
    - Connection path analysis
    - Network topology insights
    - Troubleshooting recommendations
    
    **Available Tools:** Interface tools provide comprehensive analysis with optimized data retrieval for performance.
    """

@prompts_server.prompt(
    name = "SiteNetworkInfrastructure",
    description = "Searches for all available devices at a site and builds network topology using cached resources"
)
def discover_network_infrastructure(
    site_name: str,
    device_role: str = "all"
) -> str:
    """Guide discovery of network infrastructure at a site."""
    logger.info(f" [PROMPTS] Generating network infrastructure discovery for site {site_name}")
    return f"""
    Discover network infrastructure at site: {site_name} using the comprehensive tool set.
    
    **Recommended Tool Usage:**
    1. Use `get_cached_resources` to access site, device type, and device role data
    2. Use `get_devices` with site filter to find all devices at {site_name}
    3. Use `get_interfaces` to map device connections
    4. Use `get_front_ports` and `get_rear_ports` for patch panel inventory
    5. Use `trace_from_interface` for detailed path analysis
    6. Use `trace_devices_connection` for device-to-device path analysis
    
    **Infrastructure Analysis:**
    - Core switches and their uplink connections
    - Distribution switches by area/zone
    - Access switches and end device connections
    - Patch panel locations and port mappings
    - Cable management and documentation
    
    **Expected Output:**
    - Complete device inventory by role
    - Network topology map (core → distribution → access)
    - Patch panel port assignments
    - Connection path analysis
    - Infrastructure recommendations
    
    **Optimization Tips:**
    - Use cached resources for faster access to reference data
    - Leverage available tools for efficient analysis
    - Combine multiple tools for comprehensive topology mapping
    """


@prompts_server.prompt(
    name = "PatchPanelAnalysis",
    description = "Analyzes patch panel connections and cable management infrastructure"
)
def analyze_patch_panels(
    site_name: str = None,
    device_name: str = None
) -> str:
    """Generate analysis guidance for patch panel and cable management inspection."""
    logger.info(f" [PROMPTS] Generating patch panel analysis for site: {site_name}, device: {device_name}")
    return f"""
    Analyze patch panel infrastructure and cable management using the specialized port tools.
    
    **Recommended Tool Usage:**
    1. Use `get_devices` to find patch panel devices (filter by device_type: patch-panel)
    2. Use `get_front_ports` to inventory front panel connections
    3. Use `get_rear_ports` to map rear panel terminations
    4. Use `trace_from_interface` to follow cable paths from specific interfaces
    5. Use `get_cable` for detailed cable analysis by cable ID
    
    **Analysis Focus:**
    - Front port to rear port mappings
    - Cable connection status and types
    - Patch panel port utilization
    - Cable management and documentation
    - Connection path analysis through patch panels
    
    **Expected Output:**
    - Patch panel inventory with port assignments
    - Front/rear port connection mappings
    - Cable connection status and types
    - Port utilization analysis
    - Cable management recommendations
    
    **Patch Panel Features:**
    - Front ports: External connections (cables from devices)
    - Rear ports: Internal connections (cables to other patch panels or equipment)
    - Internal routing: Front port ↔ Rear port relationships
    - Cable tracing: Complete path through patch panel infrastructure
    
    **Available Tools:** Port tools provide comprehensive connection information for efficient analysis.
    """
