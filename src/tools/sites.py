"""
NetBox Site Management Tools

This module provides MCP tools for managing and querying NetBox sites.
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
    logger.error(f" [ENVIRONMENT] NetBox configuration missing. Please set NETBOX_URL and NETBOX_API_TOKEN")
    nb = None
else:
    try:
        nb = pynetbox.api(url=NETBOX_URL, token=NETBOX_TOKEN, threading=True)
        logger.info(" [ENVIRONMENT] NetBox API connection established for site tools")
    except Exception as e:
        logger.error(f" [CONNECTION] Failed to connect to NetBox: {e}")
        nb = None


sites_server = FastMCP (
    name = "NetBoxSites"
)
    
@sites_server.tool(
        name="get_sites",
        description="Retrieve sites from NetBox with optional filtering by ID or slug. IMPORTANT: Use cached resources to find correct site slugs before calling this tool. For fuzzy matching, first search cached sites to find exact slugs from site names."
    )
def get_sites(
        id: Optional[int] = None,
        slug: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = 100
    ) -> Dict[str, Any]:
        """
        Get sites from NetBox with optional filtering.
        
        Args:
            id: Filter by specific site ID
            slug: Filter by site slug
            status: Filter by site status ("active", "planned", "staged", "decommissioned", etc.)
            limit: Maximum number of sites to return (default: 100, max: 1000)
        
        Returns:
            Dictionary containing site information and metadata
        """
        if not nb:
            logger.error(f" [CONNECTION] NetBox connection not available. Check NETBOX_URL and NETBOX_API_TOKEN environment variables. {e}")
            return {
                "error": "NetBox connection not available. Check NETBOX_URL and NETBOX_API_TOKEN environment variables."
            }
        
        try:
            if limit and (limit < 1 or limit > 1000):
                return {"error": "Limit must be between 1 and 1000"}
            
            site_filters = {}
            
            if id:
                site_filters['id'] = id
            if slug:
                site_filters['slug'] = slug
            if status:
                site_filters['status'] = status
            
            logger.info(f" [TOOLS] Querying sites with filters: {site_filters}")
            sites = list(nb.dcim.sites.filter(**site_filters))
            
            if limit:
                sites = sites[:limit]
            
            result_sites = []
            for site in sites:
                try:
                    site_info = {
                        'id': site.id,
                        'name': site.name,
                        'slug': site.slug,
                        'status': site.status.value if site.status else None
                    }
                    result_sites.append(site_info)
                    
                except Exception as e:
                    logger.warning(f"Error processing site {getattr(site, 'name', 'unknown')}: {e}")
                    result_sites.append({
                        'id': getattr(site, 'id', None),
                        'name': getattr(site, 'name', 'unknown'),
                        'slug': getattr(site, 'slug', None),
                        'error': f"Error processing site: {str(e)}"
                    })
            
            response = {
                'sites': result_sites,
                'metadata': {
                    'total_count': len(result_sites),
                    'filters_applied': {
                        'id': id,
                        'slug': slug,
                        'status': status
                    },
                    'limit': limit,
                    'truncated': len(sites) == limit if limit else False
                }
            }
            
            logger.info(f" [TOOLS] Returning {len(result_sites)} sites")
            return response
            
        except Exception as e:
            logger.error(f" [TOOLS] Error in get_sites: {e}")
            return {
                "error": f"Failed to retrieve sites: {str(e)}",
                "sites": [],
                "metadata": {"total_count": 0}
            }