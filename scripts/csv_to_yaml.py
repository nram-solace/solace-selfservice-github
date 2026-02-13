#!/usr/bin/env python3
"""
CSV to YAML Converter for Solace Configuration
Reads CSV files and generates YAML output similar to nram-test.yaml

Usage:
    python csv_to_yaml.py --verbose <true|false> --csv-file <path/to/csv>
    
Example:
    python csv_to_yaml.py --verbose true --csv-file input/csv/queues.csv
    # Output: input/yaml/queues.yaml
"""

# Version information
VERSION = "2.5.2-1009"

import sys
import os
import csv
import yaml
import argparse
import pathlib
from typing import Dict, List, Any, Optional

# Add the project root to the path to import common modules
sys.path.insert(0, os.path.abspath("."))
from common.YamlHandler import YamlHandler


class CSVToYAMLConverter:
    """Convert CSV files to YAML configuration format"""
    
    # Script configuration
    SCRIPT_PREFIX = "CSV_to_YAML"
    
    # Colors for output
    MAGENTA = '\033[0;35m'
    NC = '\033[0m'  # No Color
    
    # Object type mapping based on CSV filename
    object_type_mapping = {
        'queues': 'queues',
        'client-usernames': 'client-usernames', 
        'client-profiles': 'client-profiles',
        'acl-profiles': 'acl-profiles',
        'subscriptions': 'subscriptions'
    }
    
    # Default configuration files
    default_configs = {
        'queues': 'config/defaults/queue.yaml',
        'client-usernames': 'config/defaults/client-user.yaml',
        'client-profiles': 'config/defaults/client-profile.yaml', 
        'acl-profiles': 'config/defaults/acl-profile.yaml'
    }
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.yaml_handler = YamlHandler(verbose=1 if verbose else 0)
        self.valid_tags = self.load_valid_tags()
        
    def load_valid_tags(self) -> Dict[str, List[str]]:
        """Load valid tags from config/system.yaml"""
        system_config_path = 'config/system.yaml'
        
        try:
            if not os.path.exists(system_config_path):
                if self.verbose:
                    self.log(f"Warning: System config file {system_config_path} not found")
                return {}
            
            system_config = self.yaml_handler.read_config_file(system_config_path)
            return system_config.get('valid-tags', {})
            
        except Exception as e:
            if self.verbose:
                self.log(f"Warning: Could not read system config {system_config_path}: {e}")
            return {}
    
    def resolve_team_from_path(self, csv_file: str) -> Optional[str]:
        """Extract team name from CSV path.

        input/csv/team1/queues.csv -> 'team1'
        input/csv/queues.csv -> None (flat/legacy)
        """
        # Normalize path separators
        normalized = csv_file.replace('\\', '/')

        # Match pattern: input/csv/<team>/<filename>.csv
        import re
        match = re.search(r'input/csv/([^/]+)/[^/]+\.csv$', normalized)
        if match:
            team = match.group(1)
            if self.verbose:
                self.log(f"Resolved team '{team}' from path: {csv_file}")
            return team

        if self.verbose:
            self.log(f"No team in path (legacy/flat): {csv_file}")
        return None

    def load_inventory_mapping(self, team: Optional[str] = None) -> Dict[str, str]:
        """Load inventory files and create name->vpn mapping.

        When team is specified, looks for inventory/<team>/*.yaml first.
        Falls back to scanning all inventory files for backward compatibility.
        """
        name_to_vpn = {}
        inv_dir = 'inventory'

        # If team specified, try team-specific inventory first
        if team:
            team_inv_dir = os.path.join(inv_dir, team)
            if os.path.isdir(team_inv_dir):
                name_to_vpn = self._scan_inventory_dir(team_inv_dir)
                if name_to_vpn:
                    if self.verbose:
                        self.log(f"Loaded team inventory from {team_inv_dir}: {name_to_vpn}")
                    return name_to_vpn
                elif self.verbose:
                    self.log(f"No hosts found in team inventory dir {team_inv_dir}, falling back to full scan")
            elif self.verbose:
                self.log(f"Team inventory dir {team_inv_dir} not found, falling back to full scan")

        # Fallback: scan all inventory files recursively
        if os.path.isdir(inv_dir):
            name_to_vpn = self._scan_inventory_dir(inv_dir, recursive=True)
            if self.verbose:
                self.log(f"Loaded inventory mapping from {inv_dir}: {name_to_vpn}")

        if not name_to_vpn:
            # Legacy fallback: try hardcoded paths
            for inventory_file in ['inventory/sample-inventory-local.yaml', 'sample-inventory-local.yaml']:
                if os.path.exists(inventory_file):
                    name_to_vpn = self._load_single_inventory_file(inventory_file)
                    if name_to_vpn:
                        break

        if not name_to_vpn and self.verbose:
            self.log("Warning: No inventory file found, using CSV values directly")

        return name_to_vpn

    def _scan_inventory_dir(self, inv_dir: str, recursive: bool = False) -> Dict[str, str]:
        """Scan an inventory directory for YAML files and build name->vpn mapping."""
        name_to_vpn = {}

        if recursive:
            for root, dirs, files in os.walk(inv_dir):
                for file in files:
                    if file.endswith('.yaml') or file.endswith('.yml'):
                        inv_file = os.path.join(root, file)
                        mapping = self._load_single_inventory_file(inv_file)
                        name_to_vpn.update(mapping)
        else:
            for file in os.listdir(inv_dir):
                if file.endswith('.yaml') or file.endswith('.yml'):
                    inv_file = os.path.join(inv_dir, file)
                    mapping = self._load_single_inventory_file(inv_file)
                    name_to_vpn.update(mapping)

        return name_to_vpn

    def _load_single_inventory_file(self, inventory_file: str) -> Dict[str, str]:
        """Load a single inventory file and return name->vpn mapping."""
        try:
            inventory_config = self.yaml_handler.read_config_file(inventory_file)
            inventory = inventory_config.get('inventory', {})
            hosts = inventory.get('hosts', [])

            name_to_vpn = {}
            for host in hosts:
                name = host.get('name')
                vpn = host.get('vpn')
                if name and vpn:
                    name_to_vpn[name] = vpn

            if self.verbose and name_to_vpn:
                self.log(f"Loaded inventory from {inventory_file}: {name_to_vpn}")
            return name_to_vpn

        except Exception as e:
            if self.verbose:
                self.log(f"Warning: Could not read inventory file {inventory_file}: {e}")
            return {}
    
    def log(self, message: str):
        """Log message with prefix"""
        print(f"{self.MAGENTA}[{self.SCRIPT_PREFIX}]{self.NC} {message}")
        
    def get_object_type_from_filename(self, csv_file: str) -> str:
        """Extract object type from CSV filename"""
        filename = os.path.basename(csv_file)
        name_without_ext = os.path.splitext(filename)[0]
        
        # Map common variations
        if name_without_ext in ['queue', 'queues']:
            return 'queues'
        elif name_without_ext in ['client-username', 'client-usernames', 'client_user', 'client_users']:
            return 'client-usernames'
        elif name_without_ext in ['client-profile', 'client-profiles', 'client_profile', 'client_profiles']:
            return 'client-profiles'
        elif name_without_ext in ['acl-profile', 'acl-profiles', 'acl_profile', 'acl_profiles']:
            return 'acl-profiles'
        elif name_without_ext in ['subscription', 'subscriptions']:
            return 'subscriptions'
        else:
            return name_without_ext
    
    def read_defaults(self, object_type: str) -> Dict[str, Any]:
        """Read default configuration for the given object type"""
        default_file = self.__class__.default_configs.get(object_type)
        
        if not default_file or not os.path.exists(default_file):
            if self.verbose:
                self.log(f"Warning: Default config file {default_file} not found for {object_type}")
            return {}
        
        try:
            return self.yaml_handler.read_config_file(default_file)
        except Exception as e:
            if self.verbose:
                self.log(f"Warning: Could not read default config {default_file}: {e}")
            return {}
    
    def parse_csv_value(self, value: str, field_name: str = None) -> Any:
        """Parse CSV value, handling lists and data types"""
        # Add debugging
        if self.verbose:
            self.log(f"Parsing value: '{value}' (type: {type(value)})")
        
        # Handle case where value is already a list (from CSV reader)
        if isinstance(value, list):
            if not value or (len(value) == 1 and not value[0].strip()):
                return None
            # Check if this is a list of single characters (indicating string was incorrectly split)
            if all(isinstance(item, str) and len(item) == 1 for item in value):
                # This looks like a string that was split into characters, join it back
                joined_value = ''.join(value)
                if self.verbose:
                    self.log(f"Detected character list, joining to: '{joined_value}'")
                # Recursively parse the joined value
                return self.parse_csv_value(joined_value)
            # If it's a list with a single string element, extract it
            if len(value) == 1 and isinstance(value[0], str):
                if self.verbose:
                    self.log(f"Extracting single string from list: '{value[0]}'")
                return self.parse_csv_value(value[0])
            return value
        
        # Ensure value is a string
        if not isinstance(value, str):
            value = str(value)
        
        if not value or value.strip() == '':
            return None
            
        value = value.strip()
        
        # Handle comma-separated lists (for subscriptions, etc.)
        if ',' in value:
            return [item.strip() for item in value.split(',') if item.strip()]
        
        # Handle fields that should always be lists even for single values
        list_fields = ['subscriptions', 'clientconnectexceptions', 'publishtopicexceptions', 'subscribetopicexceptions']
        if field_name and field_name.lower() in list_fields:
            return [value]
        
        # Handle boolean values
        if value.lower() in ['true', 'false']:
            return value.lower() == 'true'
        
        # Handle numeric values
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def validate_csv_headers(self, headers: List[str], object_type: str):
        """Validate CSV headers against valid tags from system.yaml"""
        if not self.valid_tags:
            if self.verbose:
                self.log("Warning: No valid tags loaded, skipping header validation")
            return
        
        valid_tags_for_type = self.valid_tags.get(object_type, [])
        
        if not valid_tags_for_type:
            if self.verbose:
                self.log(f"Warning: No valid tags found for object type '{object_type}', skipping header validation")
            return
        
        # Add inventoryKey and env as always valid (used for inventory lookup)
        valid_tags_with_inventory_key = valid_tags_for_type + ['inventoryKey', 'env']
        
        invalid_headers = []
        for header in headers:
            if header not in valid_tags_with_inventory_key:
                invalid_headers.append(header)
        
        if invalid_headers:
            error_msg = (f"Invalid column headers found in CSV file:\n"
                        f"Invalid headers: {invalid_headers}\n"
                        f"Valid headers for '{object_type}': {sorted(valid_tags_with_inventory_key)}")
            raise ValueError(error_msg)
        
        if self.verbose:
            self.log(f"CSV headers validated successfully for object type '{object_type}'")
    
    def read_csv_file(self, csv_file: str, object_type: str = None) -> List[Dict[str, Any]]:
        """Read CSV file and return list of dictionaries"""
        if not os.path.exists(csv_file):
            raise FileNotFoundError(f"CSV file not found: {csv_file}")
        
        objects = []
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            # Validate headers if object_type is provided
            if object_type and reader.fieldnames:
                self.validate_csv_headers(reader.fieldnames, object_type)
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 since row 1 is headers
                if self.verbose:
                    self.log(f"Processing row {row_num}: {row}")
                
                # Parse each value in the row
                parsed_row = {}
                for key, value in row.items():
                    try:
                        # Debug: Check what the CSV reader is actually returning
                        if self.verbose:
                            self.log(f"Raw CSV value for key '{key}': '{value}' (type: {type(value)}, repr: {repr(value)})")

                        parsed_value = self.parse_csv_value(value, key)
                        # Special handling for jndiQueueName - preserve empty string to indicate "no JNDI"
                        if key == 'jndiQueueName':
                            parsed_row[key] = parsed_value if parsed_value is not None else ''
                        elif parsed_value is not None:
                            parsed_row[key] = parsed_value
                    except Exception as e:
                        self.log(f"Error parsing value '{value}' for key '{key}': {e}")
                        raise
                
                if parsed_row:  # Only add non-empty rows
                    objects.append(parsed_row)
                    
                    if self.verbose:
                        self.log(f"Processed row {row_num}: {parsed_row}")
        
        return objects
    
    def merge_with_defaults(self, objects: List[Dict[str, Any]], defaults: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Merge objects with default values"""
        if not defaults:
            return objects
        
        merged_objects = []
        
        for obj in objects:
            merged_obj = defaults.copy()  # Start with defaults
            merged_obj.update(obj)  # Override with CSV values
            merged_objects.append(merged_obj)
        
        return merged_objects
    
    def validate_and_filter_inventory_keys(self, objects: List[Dict[str, Any]], team: Optional[str] = None) -> tuple[str, List[Dict[str, Any]]]:
        """Validate inventoryKeys/envs and filter objects, using inventory vpn field.

        Supports two modes:
        - env (new): Used with team-based paths. Team resolved from CSV path,
          env selects environment within team inventory.
        - inventoryKey (legacy): Direct inventory host name lookup.
        """
        if not objects:
            raise ValueError("No objects to process")

        # Determine which key column is in use: env (preferred) or inventoryKey (legacy)
        use_env_key = 'env' in objects[0]
        use_inventory_key = 'inventoryKey' in objects[0]
        key_column = 'env' if use_env_key else 'inventoryKey' if use_inventory_key else None

        if not key_column:
            raise ValueError("Neither 'env' nor 'inventoryKey' column found in CSV file")

        # Load inventory mapping (team-aware)
        inventory_mapping = self.load_inventory_mapping(team=team)

        # Get target key from first record
        target_key = objects[0].get(key_column)
        if not target_key or (isinstance(target_key, str) and target_key.strip() == ''):
            raise ValueError(f"{key_column} in first record is empty")
        if isinstance(target_key, str):
            target_key = target_key.strip()

        # Resolve actual msgVpnName from inventory
        if target_key in inventory_mapping:
            actual_msg_vpn_name = inventory_mapping[target_key]
            if self.verbose:
                self.log(f"Using msgVpnName '{actual_msg_vpn_name}' from inventory for {key_column} '{target_key}'")
        else:
            actual_msg_vpn_name = target_key
            if self.verbose:
                self.log(f"Inventory record not found for {key_column} '{target_key}', using CSV value as msgVpnName")

        valid_objects = []
        skipped_count = 0
        missing_key_count = 0

        for i, obj in enumerate(objects):
            current_key = None

            # Handle missing key column or empty value
            obj_key_val = obj.get(key_column)
            if not obj_key_val or (isinstance(obj_key_val, str) and obj_key_val.strip() == ''):
                current_key = target_key
                missing_key_count += 1
                if self.verbose:
                    self.log(f"Record {i+1}: Using {key_column} '{target_key}' from first record (missing/empty)")
            else:
                current_key = obj_key_val.strip() if isinstance(obj_key_val, str) else obj_key_val

            # Check if key matches the target
            if current_key != target_key:
                self.log(f"Warning: Record {i+1} has {key_column} '{current_key}' but expected '{target_key}', skipping")
                skipped_count += 1
                continue

            # Create a copy without env/inventoryKey and add msgVpnName from inventory
            obj_copy = obj.copy()
            if 'env' in obj_copy:
                del obj_copy['env']
            if 'inventoryKey' in obj_copy:
                del obj_copy['inventoryKey']
            obj_copy['msgVpnName'] = actual_msg_vpn_name
            valid_objects.append(obj_copy)

        if missing_key_count > 0:
            self.log(f"Applied default {key_column} '{target_key}' to {missing_key_count} records with missing/empty {key_column}")

        if skipped_count > 0:
            self.log(f"Skipped {skipped_count} records due to {key_column} mismatch")

        if not valid_objects:
            raise ValueError(f"No valid records found for {key_column} '{target_key}'")

        self.log(f"Processing {len(valid_objects)} records for {key_column} '{target_key}' -> msgVpnName '{actual_msg_vpn_name}'")
        return actual_msg_vpn_name, valid_objects, target_key
    
    def generate_yaml_output(self, verbose: bool, csv_file: str) -> Dict[str, Any]:
        """Generate YAML output structure with vpnName validation"""

        # Determine object type from CSV filename
        object_type = self.get_object_type_from_filename(csv_file)

        # Resolve team from CSV path (None for legacy flat paths)
        team = self.resolve_team_from_path(csv_file)

        if self.verbose:
            self.log(f"Processing CSV file: {csv_file}")
            self.log(f"Detected object type: {object_type}")
            if team:
                self.log(f"Team: {team}")

        # Read CSV data with header validation
        objects = self.read_csv_file(csv_file, object_type)

        if not objects:
            raise ValueError(f"No data found in CSV file: {csv_file}")

        # Validate and filter objects by env/inventoryKey (team-aware)
        msg_vpn_name, valid_objects, inventory_key = self.validate_and_filter_inventory_keys(objects, team=team)
        
        # Read defaults
        defaults = self.read_defaults(object_type)
        
        # Merge with defaults
        if defaults:
            valid_objects = self.merge_with_defaults(valid_objects, defaults)
        
        # Build the output structure - keep minimal params for yaml_to_semp.py compatibility
        params = {
            'vpnName': inventory_key,  # Use inventory key for yaml_to_semp.py lookup
            'verbose': verbose,
            'create': [object_type]
        }

        # Add team to params so yaml_to_semp.py can scope inventory loading
        if team:
            params['team'] = team

        output = {
            'params': params,
            'inputs': {
                object_type: valid_objects
            },
            'defaults': {},
            'system': {
                'configFile': 'config/system.yaml'
            }
        }
        
        # Add defaults to output if they exist
        if defaults:
            output['defaults'][object_type] = defaults
        
        return output
        
    
    def save_yaml_file(self, output: Dict[str, Any], output_file: str):
        """Save output to YAML file"""
        try:
            with open(output_file, 'w', encoding='utf-8') as file:
                yaml.dump(output, file, default_flow_style=False, sort_keys=False, indent=2)
            
            if self.verbose:
                self.log(f"YAML output saved to: {output_file}")
                
        except Exception as e:
            self.log(f"Error saving YAML file: {e}")
            raise


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Convert CSV files to YAML configuration')
    # TLA name is now read from CSV file, no longer a command line argument
    parser.add_argument('--verbose', '-v', action='count', default=0,
                       help='Verbose output. Use -vvv for more verbose output')
    parser.add_argument('--csv-file', required=True, help='Path to CSV file')
    parser.add_argument('--output-file', help='Output YAML file path (optional)')
    
    args = parser.parse_args()
    
    # Print version
    print(f"{CSVToYAMLConverter.MAGENTA}[{CSVToYAMLConverter.SCRIPT_PREFIX}]{CSVToYAMLConverter.NC} Version {VERSION}")
    
    # Convert verbose count to boolean
    verbose = args.verbose > 0
    
    # Create converter
    converter = CSVToYAMLConverter(verbose=verbose)
    
    try:
        # Generate YAML output
        output = converter.generate_yaml_output(
            verbose=verbose,
            csv_file=args.csv_file
        )
        
        # Determine output file path
        if args.output_file:
            output_file = args.output_file
        else:
            # Generate output filename with same name as CSV but in yaml directory
            csv_basename = os.path.splitext(os.path.basename(args.csv_file))[0]
            csv_dir = os.path.dirname(args.csv_file)
            
            # Replace 'csv' with 'yaml' in the path
            yaml_dir = csv_dir.replace('csv', 'yaml')
            output_file = f"{yaml_dir}/{csv_basename}.yaml"
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Save YAML file
        converter.save_yaml_file(output, output_file)
        
        print(f"{CSVToYAMLConverter.MAGENTA}[{CSVToYAMLConverter.SCRIPT_PREFIX}]{CSVToYAMLConverter.NC} Successfully converted {args.csv_file} to {output_file}")
        
    except Exception as e:
        print(f"{CSVToYAMLConverter.MAGENTA}[{CSVToYAMLConverter.SCRIPT_PREFIX}]{CSVToYAMLConverter.NC} Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 