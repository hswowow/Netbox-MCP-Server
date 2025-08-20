#!/usr/bin/env python3
"""
NetBox Resource Updater Script

This script fetches data from NetBox API and creates/updates JSON files
for MCP server resources including sites, device types, device roles, and manufacturers.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any
import pynetbox
from dotenv import load_dotenv, find_dotenv
import logging

logger = logging.getLogger(__name__)


class NetBoxResourceUpdater:
    """Handles fetching NetBox data and updating resource JSON files."""
    
    def __init__(self, resources_dir: str = "resources"):
        """
        Initialize the NetBox Resource Updater.
        
        Args:
            resources_dir: Directory to store resource JSON files
        """
        
        load_dotenv(find_dotenv())
        
        self.netbox_url = os.getenv('NETBOX_URL')
        self.netbox_token = os.getenv('NETBOX_API_TOKEN')
        self.update_interval_hours = int(os.getenv('NETBOX_RESOURCE_UPDATE_INTERVAL_HOURS', '24'))
        
        if not self.netbox_url:
            logger.error(" [ENVIRONMENT] NETBOX_URL environment variable is required")
            raise ValueError("NETBOX_URL environment variable is required")
        if not self.netbox_token:
            logger.error(" [ENVIRONMENT] NETBOX_API_TOKEN environment variable is required")
            raise ValueError("NETBOX_API_TOKEN environment variable is required")
        
        self.resources_dir = Path(resources_dir)
        self.resources_dir.mkdir(exist_ok=True)
        
        try:
            self.nb = pynetbox.api(
                url=self.netbox_url,
                token=self.netbox_token,
                threading=True  
            )
            logger.info(f" [CONNECTION] Connected to NetBox at {self.netbox_url}")
        except Exception as e:
            logger.error(f" [CONNECTION] Failed to connect to NetBox: {e}")
            raise
    
    def _serialize_netbox_record(self, record) -> Dict[str, Any]:
        """
        Convert a NetBox record to a minimal serializable dictionary.
        Only includes essential fields for AI agent context.
        
        Args:
            record: NetBox API record object
            
        Returns:
            Minimal dictionary representation of the record
        """
        try:
            record_dict = dict(record)
            
            if 'model' in record_dict:
                return {
                    'id': record_dict.get('id'),
                    'model': record_dict.get('model'),
                    'manufacturer': record_dict.get('manufacturer', {}).get('name') if record_dict.get('manufacturer') else None,
                    'part_number': record_dict.get('part_number')
                }
            elif 'color' in record_dict and 'vm_role' in record_dict:
                return {
                    'id': record_dict.get('id'),
                    'name': record_dict.get('name'),
                    'slug': record_dict.get('slug')
                }
            elif 'status' in record_dict and 'region' in record_dict:
                return {
                    'id': record_dict.get('id'),
                    'name': record_dict.get('name'),
                    'slug': record_dict.get('slug'),
                    'status': record_dict.get('status', {}).get('value') if record_dict.get('status') else None,
                    'region': record_dict.get('region', {}).get('name') if record_dict.get('region') else None
                }
            elif 'description' in record_dict and 'model' not in record_dict:
                return {
                    'id': record_dict.get('id'),
                    'name': record_dict.get('name'),
                    'slug': record_dict.get('slug')
                }
            else:
                return {
                    'id': record_dict.get('id'),
                    'name': record_dict.get('name'),
                    'slug': record_dict.get('slug')
                }
                
        except Exception as e:
            logger.warning(f" [SERIALIZE] Error serializing record: {e}")
            return {
                'id': getattr(record, 'id', None), 
                'name': getattr(record, 'name', None)
            }
    
    def fetch_sites(self) -> List[Dict[str, Any]]:
        """Fetch all sites from NetBox."""
        logger.info(" [FETCH] Fetching sites...")
        try:
            sites = list(self.nb.dcim.sites.all())
            return [self._serialize_netbox_record(site) for site in sites]
        except Exception as e:
            logger.error(f" [FETCH] Error fetching sites: {e}")
            return []
    
    def fetch_device_types(self) -> List[Dict[str, Any]]:
        """Fetch all device types from NetBox."""
        logger.info(" [FETCH] Fetching device types...")
        try:
            device_types = list(self.nb.dcim.device_types.all())
            return [self._serialize_netbox_record(dt) for dt in device_types]
        except Exception as e:
            logger.error(f" [FETCH] Error fetching device types: {e}")
            return []
    
    def fetch_device_roles(self) -> List[Dict[str, Any]]:
        """Fetch all device roles from NetBox."""
        logger.info(" [FETCH] Fetching device roles...")
        try:
            device_roles = list(self.nb.dcim.device_roles.all())
            return [self._serialize_netbox_record(role) for role in device_roles]
        except Exception as e:
            logger.error(f" [FETCH] Error fetching device roles: {e}")
            return []
    
    def fetch_manufacturers(self) -> List[Dict[str, Any]]:
        """Fetch all manufacturers from NetBox."""
        logger.info(" [FETCH] Fetching manufacturers...")
        try:
            manufacturers = list(self.nb.dcim.manufacturers.all())
            return [self._serialize_netbox_record(mfg) for mfg in manufacturers]
        except Exception as e:
            logger.error(f" [FETCH] Error fetching manufacturers: {e}")
            return []
    
    def save_resource_file(self, filename: str, data: List[Dict[str, Any]]) -> bool:
        """
        Save resource data to a JSON file.
        
        Args:
            filename: Name of the JSON file (without extension)
            data: List of resource dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        filepath = self.resources_dir / f"{filename}.json"
        try:
            resource_data = {
                'metadata': {
                    'count': len(data),
                    'last_updated': self._get_timestamp(),
                    'resource_type': filename
                },
                'data': data
            }
            
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(resource_data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f" [SAVE] Saved {len(data)} {filename} records to {filepath}")
            return True
        except Exception as e:
            logger.error(f" [SAVE] Error saving {filename}: {e}")
            return False
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def update_all_resources(self) -> Dict[str, bool]:
        """
        Update all resource files.
        
        Returns:
            Dictionary with resource names and their update status
        """
        logger.info(" [UPDATE] Starting resource update process...")
        
        resources = {
            'sites': self.fetch_sites,
            'device_types': self.fetch_device_types,
            'device_roles': self.fetch_device_roles,
            'manufacturers': self.fetch_manufacturers
        }
        
        results = {}
        
        for resource_name, fetch_func in resources.items():
            try:
                logger.info(f" [UPDATE] Updating {resource_name}...")
                data = fetch_func()
                success = self.save_resource_file(resource_name, data)
                results[resource_name] = success
                
                if success:
                    logger.info(f" [UPDATE] {resource_name}: {len(data)} records updated")
                else:
                    logger.error(f" [UPDATE] {resource_name}: Update failed")
                    
            except Exception as e:
                logger.error(f" [UPDATE] {resource_name}: {e}")
                results[resource_name] = False
        
        return results
    
    def should_update_resources(self) -> bool:
        """
        Check if resources should be updated based on time interval.
        
        Returns:
            True if resources need updating based on time interval, False otherwise
        """
        from datetime import datetime, timedelta
        
        resource_files = list(self.resources_dir.glob("*.json"))
        if not resource_files:
            logger.info(" [UPDATE] No resource files found - initial update needed")
            return True
        
        latest_update = None
        for resource_file in resource_files:
            try:
                with open(resource_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    update_time_str = data.get('metadata', {}).get('last_updated')
                    if update_time_str:
                        update_time = datetime.fromisoformat(update_time_str.replace('Z', '+00:00'))
                        if latest_update is None or update_time > latest_update:
                            latest_update = update_time
            except Exception as e:
                logger.warning(f" [UPDATE] Error reading {resource_file}: {e}")
                continue
        
        if latest_update is None:
            logger.info(" [UPDATE] No valid update timestamps found - update needed")
            return True
        
        now = datetime.now()
        time_since_update = now - latest_update
        hours_since_update = time_since_update.total_seconds() / 3600
        
        if hours_since_update >= self.update_interval_hours:
            logger.info(f" [UPDATE] Resources last updated {hours_since_update:.1f} hours ago (interval: {self.update_interval_hours}h) - update needed")
            return True
        else:
            logger.info(f" [UPDATE] Resources updated {hours_since_update:.1f} hours ago (interval: {self.update_interval_hours}h) - no update needed")
            return False
    
    def get_resource_summary(self) -> Dict[str, Any]:
        """
        Get summary of current resource files.
        
        Returns:
            Dictionary with resource file information
        """
        summary = {}
        
        for resource_file in self.resources_dir.glob("*.json"):
            try:
                with open(resource_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                summary[resource_file.stem] = {
                    'count': data.get('metadata', {}).get('count', 0),
                    'last_updated': data.get('metadata', {}).get('last_updated', 'Unknown'),
                    'file_size': resource_file.stat().st_size
                }
            except Exception as e:
                logger.warning(f" [SUMMARY] Error reading {resource_file}: {e}")
                summary[resource_file.stem] = {'error': str(e)}
        
        return summary


def main():
    """Main function to run the resource updater."""
    try:
        log_file = Path("netbox_resource_update.log")
        file_handler = logging.FileHandler(os.path.expanduser('~/netbox_mcp_server.log'))
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        logger.info("="*60)
        logger.info(" [STARTUP] STARTING NETBOX RESOURCE UPDATE")
        logger.info("="*60)
        
        updater = NetBoxResourceUpdater()
        
        if not updater.resources_dir.exists():
            logger.info(f" [STARTUP] Creating resources directory: {updater.resources_dir}")
            updater.resources_dir.mkdir(parents=True, exist_ok=True)
        
        if updater.should_update_resources():
            logger.info(f" [STARTUP] Resource update needed - updating every {updater.update_interval_hours} hours...")
            results = updater.update_all_resources()
        else:
            logger.info(f" [STARTUP] Resources are up to date - next update in {updater.update_interval_hours} hours")
            return 0
        
        logger.info("\n" + "="*50)
        logger.info(" [SUMMARY] RESOURCE UPDATE SUMMARY")
        logger.info("="*50)
        
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        expected_files = ['sites', 'device_types', 'device_roles', 'manufacturers']
        
        for resource in expected_files:
            success = results.get(resource, False)
            status = "✓ SUCCESS" if success else "✗ FAILED"
            logger.info(f" [SUMMARY] {resource:15} {status}")
            
            file_path = updater.resources_dir / f"{resource}.json"
            if file_path.exists():
                logger.info(f" [SUMMARY]   File created: {file_path}")
                logger.info(f" [SUMMARY]   File size: {file_path.stat().st_size} bytes")
            else:
                logger.error(f" [SUMMARY]   File NOT created: {file_path}")
        
        logger.info("-"*50)
        logger.info(f" [SUMMARY] Total: {success_count}/{total_count} resources updated successfully")
        
        missing_files = []
        for expected_file in expected_files:
            file_path = updater.resources_dir / f"{expected_file}.json"
            if not file_path.exists():
                missing_files.append(expected_file)
        
        if missing_files:
            logger.error(f" [SUMMARY] Missing expected files: {missing_files}")
            return 1
        
        if success_count == total_count:
            logger.info(" [SUMMARY] All 4 resource JSON files created/updated successfully!")
            return 0
        else:
            logger.error(f" [SUMMARY] {total_count - success_count} resources failed to update")
            return 1
            
    except Exception as e:
        logger.error(f" [FATAL] Fatal error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)