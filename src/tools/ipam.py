"""
NetBox IPAM Management Tools

This module provides MCP tools for managing and querying NetBox IPAM resources.
"""

import os
import logging
from typing import Dict, Any, Optional
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
        logger.info(" [ENVIRONMENT] NetBox API connection established for IPAM tools")
    except Exception as e:
        logger.error(f" [CONNECTION] Failed to connect to NetBox: {e}")
        nb = None


ipam_server = FastMCP (
    name = "NetBoxIPAM"
)
    
@ipam_server.tool(
        name="get_ip_addresses",
        description="Retrieve IP addresses from NetBox with comprehensive filtering capabilities. This tool allows you to query IP addresses by device, interface, subnet, prefix, VRF, and various other parameters. Use this tool to analyze IP address allocations, troubleshoot network connectivity, and manage IP address space. The tool returns minimal data to optimize performance while providing essential IP information. IMPORTANT: Use cached resources to find correct device names before calling this tool. For fuzzy matching, first search cached devices to find exact device names from user-provided aliases."
    )
def get_ip_addresses(
        device: Optional[str] = None,
        interface: Optional[str] = None,
        interface_id: Optional[int] = None,
        address: Optional[str] = None,
        parent: Optional[str] = None,
        family: Optional[int] = None,
        status: Optional[str] = None,
        role: Optional[str] = None,
        vrf: Optional[str] = None,
        vrf_id: Optional[int] = None,
        assigned_to_interface: Optional[bool] = None,
        limit: Optional[int] = 100
    ) -> Dict[str, Any]:
        """
        Get IP addresses from NetBox with optional filtering.
        
        Args:
            device: Filter by device name or slug
            interface: Filter by interface name
            interface_id: Filter by specific interface ID
            address: Filter by specific IP address (e.g., "192.168.1.1/24")
            parent: Filter by parent prefix (e.g., "192.168.1.0/24")
            family: Filter by IP family (4 for IPv4, 6 for IPv6)
            status: Filter by IP status ("active", "reserved", "deprecated", etc.)
            role: Filter by IP role
            vrf: Filter by VRF name or slug
            vrf_id: Filter by specific VRF ID
            assigned_to_interface: Filter by interface assignment status (True/False)
            limit: Maximum number of IP addresses to return (default: 100, max: 1000)
        
        Returns:
            Dictionary containing IP address information and metadata
        """
        if not nb:
            logger.error(f" [CONNECTION] NetBox connection not available. Check NETBOX_URL and NETBOX_API_TOKEN environment variables. {e}")
            return {
                "error": "NetBox connection not available. Check NETBOX_URL and NETBOX_API_TOKEN environment variables."
            }
        
        try:
            if limit and (limit < 1 or limit > 1000):
                return {"error": "Limit must be between 1 and 1000"}
            
            ip_filters = {}
            
            if device:
                ip_filters['device'] = device
            if interface:
                ip_filters['interface'] = interface
            if interface_id:
                ip_filters['interface_id'] = interface_id
            if address:
                ip_filters['address'] = address
            if parent:
                ip_filters['parent'] = parent
            if family:
                ip_filters['family'] = family
            if status:
                ip_filters['status'] = status
            if role:
                ip_filters['role'] = role
            if vrf:
                ip_filters['vrf'] = vrf
            if vrf_id:
                ip_filters['vrf_id'] = vrf_id
            if assigned_to_interface is not None:
                ip_filters['assigned_to_interface'] = assigned_to_interface
            
            logger.info(f" [TOOLS] Querying IP addresses with filters: {ip_filters}")
            ip_addresses = list(nb.ipam.ip_addresses.filter(**ip_filters))
            
            if limit:
                ip_addresses = ip_addresses[:limit]
            
            result_ips = []
            for ip in ip_addresses:
                try:
                    ip_info = {
                        'id': ip.id,
                        'address': str(ip.address),
                        'status': ip.status.value if ip.status else None,
                        'vrf': {
                            'id': ip.vrf.id if ip.vrf else None,
                            'name': ip.vrf.name if ip.vrf else None
                        } if hasattr(ip, 'vrf') and ip.vrf else None,
                        'assigned_object': None
                    }
                    
                    if hasattr(ip, 'assigned_object') and ip.assigned_object:
                        assigned_obj = ip.assigned_object
                        ip_info['assigned_object'] = {
                            'id': getattr(assigned_obj, 'id', None),
                            'name': getattr(assigned_obj, 'name', None)
                        }
                    
                    result_ips.append(ip_info)
                    
                except Exception as e:
                    logger.warning(f"Error processing IP address {getattr(ip, 'address', 'unknown')}: {e}")
                    result_ips.append({
                        'id': getattr(ip, 'id', None),
                        'address': str(getattr(ip, 'address', 'unknown')),
                        'error': f"Error processing IP: {str(e)}"
                    })
            
            response = {
                'ip_addresses': result_ips,
                'metadata': {
                    'filters_applied': {
                        'device': device,
                        'interface': interface,
                        'interface_id': interface_id,
                        'address': address,
                        'status': status,
                        'role': role,
                        'vrf': vrf,
                        'vrf_id': vrf_id,
                        'assigned_to_interface': assigned_to_interface
                    },
                    'limit': limit,
                    'truncated': len(ip_addresses) == limit if limit else False
                }
            }
            
            logger.info(f" [TOOLS] Returning {len(result_ips)} IP addresses")
            return response
            
        except Exception as e:
            logger.error(f"Error in get_ip_addresses: {e}")
            return {
                "error": f"Failed to retrieve IP addresses: {str(e)}",
                "ip_addresses": [],
                "metadata": {"total_count": 0}
            }
    
@ipam_server.tool(
        name="get_ip_prefixes",
        description="Retrieve IP prefixes from NetBox with comprehensive filtering capabilities. This tool allows you to query IP prefixes by network range, site, VRF, status, and various other parameters. Use this tool to analyze network address space, plan subnet allocations, and manage IP address ranges. The tool returns minimal data to optimize performance while providing essential prefix information. IMPORTANT: Use cached resources to find correct site names before calling this tool. For fuzzy matching, first search cached sites to find exact site slugs from user-provided aliases."
    )
def get_ip_prefixes(
        prefix: Optional[str] = None,
        within: Optional[str] = None,
        within_include: Optional[str] = None,
        contains: Optional[str] = None,
        family: Optional[int] = None,
        status: Optional[str] = None,
        role: Optional[str] = None,
        site: Optional[str] = None,
        vrf: Optional[str] = None,
        vrf_id: Optional[int] = None,
        tenant: Optional[str] = None,
        is_pool: Optional[bool] = None,
        limit: Optional[int] = 100
    ) -> Dict[str, Any]:
        """
        Get IP prefixes from NetBox with optional filtering.
        
        Args:
            prefix: Filter by specific prefix (e.g., "192.168.1.0/24")
            within: Filter prefixes within a parent prefix
            within_include: Filter prefixes within and including a parent prefix
            contains: Filter prefixes that contain a specific IP/prefix
            family: Filter by IP family (4 for IPv4, 6 for IPv6)
            status: Filter by prefix status ("active", "container", "deprecated", etc.)
            role: Filter by prefix role
            site: Filter by site name or slug
            vrf: Filter by VRF name or slug
            vrf_id: Filter by specific VRF ID
            tenant: Filter by tenant name or slug
            is_pool: Filter by pool status (True/False)
            limit: Maximum number of prefixes to return (default: 100, max: 1000)
        
        Returns:
            Dictionary containing prefix information and metadata
        """
        if not nb:
            logger.error(f" [CONNECTION] NetBox connection not available. Check NETBOX_URL and NETBOX_API_TOKEN environment variables. {e}")
            return {
                "error": "NetBox connection not available. Check NETBOX_URL and NETBOX_API_TOKEN environment variables."
            }
        
        try:
            if limit and (limit < 1 or limit > 1000):
                return {"error": "Limit must be between 1 and 1000"}
            
            prefix_filters = {}
            
            if prefix:
                prefix_filters['prefix'] = prefix
            if within:
                prefix_filters['within'] = within
            if within_include:
                prefix_filters['within_include'] = within_include
            if contains:
                prefix_filters['contains'] = contains
            if family:
                prefix_filters['family'] = family
            if status:
                prefix_filters['status'] = status
            if role:
                prefix_filters['role'] = role
            if site:
                prefix_filters['site'] = site
            if vrf:
                prefix_filters['vrf'] = vrf
            if vrf_id:
                prefix_filters['vrf_id'] = vrf_id
            if tenant:
                prefix_filters['tenant'] = tenant
            if is_pool is not None:
                prefix_filters['is_pool'] = is_pool
            
            logger.info(f" [TOOLS] Querying prefixes with filters: {prefix_filters}")
            prefixes = list(nb.ipam.prefixes.filter(**prefix_filters))
            
            if limit:
                prefixes = prefixes[:limit]
            
            result_prefixes = []
            for pfx in prefixes:
                try:
                    prefix_info = {
                        'id': pfx.id,
                        'prefix': str(pfx.prefix),
                        'status': pfx.status.value if pfx.status else None,
                        'site': {
                            'id': pfx.site.id if pfx.site else None,
                            'name': pfx.site.name if pfx.site else None
                        } if hasattr(pfx, 'site') and pfx.site else None,
                        'vrf': {
                            'id': pfx.vrf.id if pfx.vrf else None,
                            'name': pfx.vrf.name if pfx.vrf else None
                        } if hasattr(pfx, 'vrf') and pfx.vrf else None,
                        'vlan': {
                            'id': pfx.vlan.id if pfx.vlan else None,
                            'vid': pfx.vlan.vid if pfx.vlan else None,
                            'name': pfx.vlan.name if pfx.vlan else None
                        } if hasattr(pfx, 'vlan') and pfx.vlan else None
                    }
                    result_prefixes.append(prefix_info)
                    
                except Exception as e:
                    logger.warning(f"Error processing prefix {getattr(pfx, 'prefix', 'unknown')}: {e}")
                    result_prefixes.append({
                        'id': getattr(pfx, 'id', None),
                        'prefix': str(getattr(pfx, 'prefix', 'unknown')),
                        'error': f"Error processing prefix: {str(e)}"
                    })
            
            response = {
                'prefixes': result_prefixes,
                'metadata': {
                    'total_count': len(result_prefixes),
                    'filters_applied': {
                        'prefix': prefix,
                        'status': status,
                        'role': role,
                        'site': site,
                        'vrf': vrf,
                        'vrf_id': vrf_id
                    },
                    'limit': limit,
                    'truncated': len(prefixes) == limit if limit else False
                }
            }
            
            logger.info(f" [TOOLS] Returning {len(result_prefixes)} prefixes")
            return response
            
        except Exception as e:
            logger.error(f"Error in get_ip_prefixes: {e}")
            return {
                "error": f"Failed to retrieve prefixes: {str(e)}",
                "prefixes": [],
                "metadata": {"total_count": 0}
            }
    
@ipam_server.tool(
        name="get_ip_ranges",
        description="Retrieve IP ranges from NetBox with comprehensive filtering capabilities. This tool allows you to query IP ranges by address range, VRF, status, and various other parameters. Use this tool to analyze IP address ranges, plan address allocations, and manage contiguous IP address blocks. The tool returns minimal data to optimize performance while providing essential range information. IMPORTANT: This tool is useful for managing large blocks of IP addresses and understanding address space utilization."
    )
def get_ip_ranges(
        start_address: Optional[str] = None,
        end_address: Optional[str] = None,
        family: Optional[int] = None,
        status: Optional[str] = None,
        role: Optional[str] = None,
        vrf: Optional[str] = None,
        vrf_id: Optional[int] = None,
        tenant: Optional[str] = None,
        limit: Optional[int] = 100
    ) -> Dict[str, Any]:
        """
        Get IP ranges from NetBox with optional filtering.
        
        Args:
            start_address: Filter by start IP address
            end_address: Filter by end IP address
            family: Filter by IP family (4 for IPv4, 6 for IPv6)
            status: Filter by range status ("active", "reserved", "deprecated", etc.)
            role: Filter by range role
            vrf: Filter by VRF name or slug
            vrf_id: Filter by specific VRF ID
            tenant: Filter by tenant name or slug
            limit: Maximum number of ranges to return (default: 100, max: 1000)
        
        Returns:
            Dictionary containing IP range information and metadata
        """
        if not nb:
            logger.error(f" [CONNECTION] NetBox connection not available. Check NETBOX_URL and NETBOX_API_TOKEN environment variables. {e}")
            return {
                "error": "NetBox connection not available. Check NETBOX_URL and NETBOX_API_TOKEN environment variables."
            }
        
        try:
            if limit and (limit < 1 or limit > 1000):
                return {"error": "Limit must be between 1 and 1000"}
            
            range_filters = {}
            
            if start_address:
                range_filters['start_address'] = start_address
            if end_address:
                range_filters['end_address'] = end_address
            if family:
                range_filters['family'] = family
            if status:
                range_filters['status'] = status
            if role:
                range_filters['role'] = role
            if vrf:
                range_filters['vrf'] = vrf
            if vrf_id:
                range_filters['vrf_id'] = vrf_id
            if tenant:
                range_filters['tenant'] = tenant
            
            logger.info(f" [TOOLS] Querying IP ranges with filters: {range_filters}")
            ranges = list(nb.ipam.ip_ranges.filter(**range_filters))
            
            if limit:
                ranges = ranges[:limit]
            
            result_ranges = []
            for rng in ranges:
                try:
                    range_info = {
                        'id': rng.id,
                        'start_address': str(rng.start_address),
                        'end_address': str(rng.end_address),
                        'status': rng.status.value if rng.status else None,
                        'vrf': {
                            'id': rng.vrf.id if rng.vrf else None,
                            'name': rng.vrf.name if rng.vrf else None
                        } if hasattr(rng, 'vrf') and rng.vrf else None,
                        'utilization': getattr(rng, 'utilization', None)
                    }
                    result_ranges.append(range_info)
                    
                except Exception as e:
                    logger.warning(f"Error processing IP range {getattr(rng, 'display', 'unknown')}: {e}")
                    result_ranges.append({
                        'id': getattr(rng, 'id', None),
                        'display': str(getattr(rng, 'display', 'unknown')),
                        'error': f"Error processing range: {str(e)}"
                    })
            
            response = {
                'ip_ranges': result_ranges,
                'metadata': {
                    'total_count': len(result_ranges),
                    'filters_applied': {
                        'start_address': start_address,
                        'end_address': end_address,
                        'status': status,
                        'role': role,
                        'vrf': vrf,
                        'vrf_id': vrf_id
                    },
                    'limit': limit,
                    'truncated': len(ranges) == limit if limit else False
                }
            }
            
            logger.info(f" [TOOLS] Returning {len(result_ranges)} IP ranges")
            return response
            
        except Exception as e:
            logger.error(f" [TOOLS] Error in get_ip_ranges: {e}")
            return {
                "error": f"Failed to retrieve IP ranges: {str(e)}",
                "ip_ranges": [],
                "metadata": {"total_count": 0}
            }
    
@ipam_server.tool(
        name="get_vrfs",
        description="Retrieve VRFs (Virtual Routing and Forwarding) from NetBox with comprehensive filtering capabilities. This tool allows you to query VRFs by name, route distinguisher, tenant, and various other parameters. Use this tool to analyze network segmentation, manage routing domains, and understand network virtualization. The tool returns minimal data to optimize performance while providing essential VRF information. IMPORTANT: VRFs are crucial for network segmentation and multi-tenant environments."
    )
def get_vrfs(
        name: Optional[str] = None,
        rd: Optional[str] = None,
        tenant: Optional[str] = None,
        enforce_unique: Optional[bool] = None,
        limit: Optional[int] = 100
    ) -> Dict[str, Any]:
        """
        Get VRFs from NetBox with optional filtering.
        
        Args:
            name: Filter by VRF name
            rd: Filter by Route Distinguisher
            tenant: Filter by tenant name or slug
            enforce_unique: Filter by unique enforcement status (True/False)
            limit: Maximum number of VRFs to return (default: 100, max: 1000)
        
        Returns:
            Dictionary containing VRF information and metadata
        """
        if not nb:
            return {
                "error": "NetBox connection not available. Check NETBOX_URL and NETBOX_API_TOKEN environment variables."
            }
        
        try:
            if limit and (limit < 1 or limit > 1000):
                return {"error": "Limit must be between 1 and 1000"}
            
            vrf_filters = {}
            
            if name:
                vrf_filters['name'] = name
            if rd:
                vrf_filters['rd'] = rd
            if tenant:
                vrf_filters['tenant'] = tenant
            if enforce_unique is not None:
                vrf_filters['enforce_unique'] = enforce_unique
            
            logger.info(f" [TOOLS] Querying VRFs with filters: {vrf_filters}")
            vrfs = list(nb.ipam.vrfs.filter(**vrf_filters))
            
            if limit:
                vrfs = vrfs[:limit]
            
            result_vrfs = []
            for vrf in vrfs:
                try:
                    vrf_info = {
                        'id': vrf.id,
                        'name': vrf.name
                    }
                    result_vrfs.append(vrf_info)
                    
                except Exception as e:
                    logger.warning(f"Error processing VRF {getattr(vrf, 'name', 'unknown')}: {e}")
                    result_vrfs.append({
                        'id': getattr(vrf, 'id', None),
                        'name': getattr(vrf, 'name', 'unknown'),
                        'error': f"Error processing VRF: {str(e)}"
                    })
            
            response = {
                'vrfs': result_vrfs,
                'metadata': {
                    'total_count': len(result_vrfs),
                    'filters_applied': {
                        'name': name,
                        'rd': rd,
                        'tenant': tenant,
                        'enforce_unique': enforce_unique
                    },
                    'limit': limit,
                    'truncated': len(vrfs) == limit if limit else False
                }
            }
            
            logger.info(f" [TOOLS] Returning {len(result_vrfs)} VRFs")
            return response
            
        except Exception as e:
            logger.error(f" [TOOLS] Error in get_vrfs: {e}")
            return {
                "error": f"Failed to retrieve VRFs: {str(e)}",
                "vrfs": [],
                "metadata": {"total_count": 0}
            }
    
@ipam_server.tool(
        name="get_vlans",
        description="Retrieve VLANs from NetBox with comprehensive filtering capabilities. This tool allows you to query VLANs by VLAN ID, name, site, group, and various other parameters. Use this tool to analyze network segmentation, manage VLAN assignments, and understand layer 2 network topology. The tool returns minimal data to optimize performance while providing essential VLAN information. IMPORTANT: Use cached resources to find correct site names before calling this tool. For fuzzy matching, first search cached sites to find exact site slugs from user-provided aliases."
    )
def get_vlans(
        vid: Optional[int] = None,
        name: Optional[str] = None,
        site: Optional[str] = None,
        group: Optional[str] = None,
        tenant: Optional[str] = None,
        status: Optional[str] = None,
        role: Optional[str] = None,
        limit: Optional[int] = 100
    ) -> Dict[str, Any]:
        """
        Get VLANs from NetBox with optional filtering.
        
        Args:
            vid: Filter by VLAN ID (e.g., 100)
            name: Filter by VLAN name
            site: Filter by site name or slug
            group: Filter by VLAN group name or slug
            tenant: Filter by tenant name or slug
            status: Filter by VLAN status ("active", "reserved", "deprecated", etc.)
            role: Filter by VLAN role
            limit: Maximum number of VLANs to return (default: 100, max: 1000)
        
        Returns:
            Dictionary containing VLAN information and metadata
        """
        if not nb:
            logger.error(f" [CONNECTION] NetBox connection not available. Check NETBOX_URL and NETBOX_API_TOKEN environment variables. {e}")
            return {
                "error": "NetBox connection not available. Check NETBOX_URL and NETBOX_API_TOKEN environment variables."
            }
        
        try:
            if limit and (limit < 1 or limit > 1000):
                return {"error": "Limit must be between 1 and 1000"}
            
            vlan_filters = {}
            
            if vid:
                vlan_filters['vid'] = vid
            if name:
                vlan_filters['name'] = name
            if site:
                vlan_filters['site'] = site
            if group:
                vlan_filters['group'] = group
            if tenant:
                vlan_filters['tenant'] = tenant
            if status:
                vlan_filters['status'] = status
            if role:
                vlan_filters['role'] = role
            
            logger.info(f" [TOOLS]Querying VLANs with filters: {vlan_filters}")
            vlans = list(nb.ipam.vlans.filter(**vlan_filters))
            
            if limit:
                vlans = vlans[:limit]
            
            result_vlans = []
            for vlan in vlans:
                try:
                    vlan_info = {
                        'id': vlan.id,
                        'vid': vlan.vid,
                        'name': vlan.name,
                        'site': {
                            'id': vlan.site.id if vlan.site else None,
                            'name': vlan.site.name if vlan.site else None
                        } if hasattr(vlan, 'site') and vlan.site else None,
                        'status': vlan.status.value if vlan.status else None
                    }
                    result_vlans.append(vlan_info)
                    
                except Exception as e:
                    logger.warning(f"Error processing VLAN {getattr(vlan, 'name', 'unknown')}: {e}")
                    result_vlans.append({
                        'id': getattr(vlan, 'id', None),
                        'vid': getattr(vlan, 'vid', None),
                        'name': getattr(vlan, 'name', 'unknown'),
                        'error': f"Error processing VLAN: {str(e)}"
                    })
            
            response = {
                'vlans': result_vlans,
                'metadata': {
                    'filters_applied': {
                        'vid': vid,
                        'name': name,
                        'site': site,
                        'group': group,
                        'tenant': tenant,
                        'status': status,
                        'role': role
                    },
                    'limit': limit,
                    'truncated': len(vlans) == limit if limit else False
                }
            }
            
            logger.info(f" [TOOLS] Returning {len(result_vlans)} VLANs")
            return response
            
        except Exception as e:
            logger.error(f" [TOOLS] Error in get_vlans: {e}")
            return {
                "error": f"Failed to retrieve VLANs: {str(e)}",
                "vlans": [],
                "metadata": {"total_count": 0}
            }