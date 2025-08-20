"""
Cached Tools for NetBox MCP Server

This module provides tools that allow MCP clients to access resources and prompts
independently, providing cached data and prompt templates for network analysis.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from fastmcp import FastMCP

logger = logging.getLogger(__name__)

cached_tools_server = FastMCP(
    name="NetBoxCachedTools",
    version="1.0.0"
)

@cached_tools_server.tool(
    name="get_cached_resources",
    description="Retrieve cached NetBox resources (sites, device types, device roles, manufacturers) for fast access and fuzzy matching. This tool provides essential reference data that should be called first before any other operations. Use this tool to find correct slugs, IDs, and names for fuzzy matching user queries. The cached data includes sites, device types, device roles, and manufacturers with their exact names and slugs. IMPORTANT: This tool must be called first in every interaction to enable fuzzy matching capabilities."
)
def get_cached_resources(
    resource_type: Optional[str] = None,
    include_metadata: bool = True
) -> Dict[str, Any]:
    """
    Retrieve cached NetBox resources for fast access without hitting the NetBox API.
    
    Args:
        resource_type: Specific resource type to retrieve ('sites', 'device_types', 'device_roles', 'manufacturers', or None for all)
        include_metadata: Whether to include metadata about the cached data
    
    Returns:
        Dictionary containing cached resource data and metadata
    """
    logger.info(f" [CACHED] Retrieving cached resources, type: {resource_type or 'all'}")
    
    try:
        resources_dir = Path("resources")
        available_resources = {
            'sites': 'sites.json',
            'device_types': 'device_types.json', 
            'device_roles': 'device_roles.json',
            'manufacturers': 'manufacturers.json'
        }
        
        result_resources = {}
        total_count = 0
        
        if resource_type:
            if resource_type not in available_resources:
                return {
                    "error": f"Invalid resource type: {resource_type}. Available types: {list(available_resources.keys())}",
                    "resources": {},
                    "metadata": {"total_count": 0}
                }
            resources_to_fetch = {resource_type: available_resources[resource_type]}
        else:
            resources_to_fetch = available_resources
        
        for res_type, filename in resources_to_fetch.items():
            file_path = resources_dir / filename
            
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    resource_data = data.get('data', data)
                    count = len(resource_data) if isinstance(resource_data, list) else 1
                    total_count += count
                    
                    result_resources[res_type] = {
                        'data': resource_data,
                        'count': count,
                        'source': 'cached',
                        'file_path': str(file_path),
                        'last_updated': data.get('last_updated', 'unknown')
                    }
                    
                    logger.info(f" [CACHED] Loaded {count} {res_type} from cache")
                    
                except Exception as e:
                    logger.error(f" [CACHED] Error loading {res_type} from cache: {e}")
                    result_resources[res_type] = {
                        'error': f"Failed to load {res_type}: {str(e)}",
                        'data': [],
                        'count': 0
                    }
            else:
                logger.warning(f" [CACHED] Cache file not found for {res_type}: {file_path}")
                result_resources[res_type] = {
                    'error': f"Cache file not found: {filename}",
                    'data': [],
                    'count': 0
                }
        
        response = {
            'resources': result_resources,
            'metadata': {
                'total_count': total_count,
                'resource_types': list(result_resources.keys()),
                'source': 'cached',
                'include_metadata': include_metadata
            }
        }
        
        if include_metadata:
            response['metadata'].update({
                'cache_status': 'available',
                'resource_count': len(result_resources),
                'successful_loads': len([r for r in result_resources.values() if 'error' not in r])
            })
        
        logger.info(f" [CACHED] Successfully retrieved {total_count} cached resources")
        return response
        
    except Exception as e:
        logger.error(f" [CACHED] Error in get_cached_resources: {e}")
        return {
            "error": f"Failed to retrieve cached resources: {str(e)}",
            "resources": {},
            "metadata": {"total_count": 0}
        }


@cached_tools_server.tool(
    name="get_resource_summary",
    description="Get minimal summary of cached resources for quick reference and overview. This tool provides condensed summaries of cached resources including top sites, manufacturers, device types, and device roles. Use this tool to get a quick overview of available resources without loading full data. The summaries include counts and top entries for each resource type. IMPORTANT: This tool is useful for getting resource overviews and understanding available options for fuzzy matching."
)
def get_resource_summary(
    resource_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get minimal summary of cached resources for quick AI agent reference.
    
    Args:
        resource_type: Specific resource type to summarize ('sites', 'device_types', 'device_roles', 'manufacturers', or None for all)
    
    Returns:
        Dictionary containing minimal resource summaries
    """
    logger.info(f" [CACHED] Getting resource summary for: {resource_type or 'all'}")
    
    try:
        resources_dir = Path("resources")
        available_resources = {
            'sites': 'sites.json',
            'device_types': 'device_types.json', 
            'device_roles': 'device_roles.json',
            'manufacturers': 'manufacturers.json'
        }
        
        result_summaries = {}
        
        if resource_type:
            if resource_type not in available_resources:
                return {
                    "error": f"Invalid resource type: {resource_type}. Available types: {list(available_resources.keys())}",
                    "summaries": {},
                    "metadata": {"total_count": 0}
                }
            resources_to_summarize = {resource_type: available_resources[resource_type]}
        else:
            resources_to_summarize = available_resources
        
        for res_type, filename in resources_to_summarize.items():
            file_path = resources_dir / filename
            
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    resource_data = data.get('data', [])
                    
                    if res_type == 'sites':
                        summary = {
                            'count': len(resource_data),
                                            'sites': [{'name': site.get('name'), 'status': site.get('status')} for site in resource_data[:10]],
                'regions': list(set([site.get('region') for site in resource_data if site.get('region')]))[:5]
                        }
                    elif res_type == 'device_types':
                        summary = {
                            'count': len(resource_data),
                                            'manufacturers': list(set([dt.get('manufacturer') for dt in resource_data if dt.get('manufacturer')]))[:10],
                'models': [{'model': dt.get('model'), 'manufacturer': dt.get('manufacturer')} for dt in resource_data[:10]]
                        }
                    elif res_type == 'device_roles':
                        summary = {
                            'count': len(resource_data),
                            'roles': [{'name': role.get('name'), 'slug': role.get('slug')} for role in resource_data]
                        }
                    elif res_type == 'manufacturers':
                        summary = {
                            'count': len(resource_data),
                            'manufacturers': [{'name': mfg.get('name'), 'slug': mfg.get('slug')} for mfg in resource_data[:10]]
                        }
                    
                    result_summaries[res_type] = summary
                    logger.info(f" [CACHED] Generated summary for {res_type}: {len(resource_data)} items")
                    
                except Exception as e:
                    logger.error(f" [CACHED] Error summarizing {res_type}: {e}")
                    result_summaries[res_type] = {
                        'error': f"Failed to summarize {res_type}: {str(e)}",
                        'count': 0
                    }
            else:
                logger.warning(f" [CACHED] Cache file not found for {res_type}: {file_path}")
                result_summaries[res_type] = {
                    'error': f"Cache file not found: {filename}",
                    'count': 0
                }
        
        total_count = sum(summary.get('count', 0) for summary in result_summaries.values() if 'error' not in summary)
        
        response = {
            'summaries': result_summaries,
            'metadata': {
                'total_count': total_count,
                'resource_types': list(result_summaries.keys()),
                'source': 'cached_summary'
            }
        }
        
        logger.info(f" [CACHED] Successfully generated summaries for {len(result_summaries)} resource types")
        return response
        
    except Exception as e:
        logger.error(f" [CACHED] Error in get_resource_summary: {e}")
        return {
            "error": f"Failed to generate resource summaries: {str(e)}",
            "summaries": {},
            "metadata": {"total_count": 0}
        }

@cached_tools_server.tool(
    name="get_available_prompts",
    description="Retrieve available AI prompts for network analysis and troubleshooting. This tool provides access to 7 predefined analysis prompts that guide network infrastructure analysis, cable tracing, device interface analysis, and patch panel management. Use this tool to get structured guidance for common network analysis tasks. The prompts include detailed instructions for using other tools effectively. IMPORTANT: This tool should be called second in every interaction to provide analysis guidance and ensure proper tool usage patterns."
)
def get_available_prompts(
    prompt_type: Optional[str] = None,
    include_examples: bool = True
) -> Dict[str, Any]:
    """
    Retrieve available AI prompts for network analysis and troubleshooting.
    
    Args:
        prompt_type: Specific prompt type to retrieve ('TraceNetworkPath', 'DeviceInterfaces', 'SiteNetworkInfrastructure', or None for all)
        include_examples: Whether to include example usage for each prompt
    
    Returns:
        Dictionary containing available prompts and their descriptions
    """
    logger.info(f" [PROMPTS] Retrieving available prompts, type: {prompt_type or 'all'}")
    
    available_prompts = {
        'TraceNetworkPath': {
            'description': 'Builds a comprehensive network path between two devices using bidirectional search algorithm',
            'parameters': ['source_device', 'destination_device'],
            'category': 'Network Analysis',
            'example': 'Trace the complete network path from server-01 to switch-core-01',
            'use_case': 'Network troubleshooting and path analysis between devices'
        },
        'DeviceInterfaces': {
            'description': 'Analyzes device interfaces types, utilization, and connectivity using available tools',
            'parameters': ['device_name', 'interface_type', 'connection_status'],
            'category': 'Device Analysis',
            'example': 'Analyze all interfaces on core-switch-01 for connectivity issues',
            'use_case': 'Device interface monitoring and troubleshooting'
        },
        'SiteNetworkInfrastructure': {
            'description': 'Searches for all available devices at a site and builds network topology using cached resources',
            'parameters': ['site_name', 'device_role'],
            'category': 'Infrastructure Discovery',
            'example': 'Map the complete network infrastructure at datacenter-1',
            'use_case': 'Site infrastructure documentation and planning'
        },
        'PatchPanelAnalysis': {
            'description': 'Analyzes patch panel connections and cable management infrastructure',
            'parameters': ['site_name', 'device_name'],
            'category': 'Cable Management',
            'example': 'Analyze patch panel connections at datacenter-1',
            'use_case': 'Patch panel documentation and cable management'
        }
    }
    
    try:
        result_prompts = {}
        
        if prompt_type:
            if prompt_type not in available_prompts:
                return {
                    "error": f"Invalid prompt type: {prompt_type}. Available types: {list(available_prompts.keys())}",
                    "prompts": {},
                    "metadata": {"total_count": 0}
                }
            prompts_to_fetch = {prompt_type: available_prompts[prompt_type]}
        else:
            prompts_to_fetch = available_prompts
        
        for prompt_name, prompt_info in prompts_to_fetch.items():
            result_prompts[prompt_name] = {
                'description': prompt_info['description'],
                'parameters': prompt_info['parameters'],
                'category': prompt_info['category'],
                'use_case': prompt_info['use_case']
            }
            
            if include_examples:
                result_prompts[prompt_name]['example'] = prompt_info['example']
        
        response = {
            'prompts': result_prompts,
            'metadata': {
                'total_count': len(result_prompts),
                'prompt_types': list(result_prompts.keys()),
                'categories': list(set(p['category'] for p in result_prompts.values())),
                'include_examples': include_examples
            }
        }
        
        logger.info(f" [PROMPTS] Successfully retrieved {len(result_prompts)} prompts")
        return response
        
    except Exception as e:
        logger.error(f" [PROMPTS] Error in get_available_prompts: {e}")
        return {
            "error": f"Failed to retrieve prompts: {str(e)}",
            "prompts": {},
            "metadata": {"total_count": 0}
        }