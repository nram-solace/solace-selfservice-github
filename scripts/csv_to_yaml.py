#!/usr/bin/env python3
"""
CSV to YAML Converter for Solace Configuration
Reads CSV files and generates YAML output for yaml_to_semp.py

CSV files must follow the layout:
    input/csv/<client>/<env>/<object>-<app>.csv

The client and env are taken from the directory path; the app name is taken
from the filename suffix. The matching inventory file is inventory/<client>/<env>.yml
and the entry with app: <app> selects the broker connection details.

Usage:
    python csv_to_yaml.py --csv-file <path/to/csv> [--env <environment>]

Example:
    python csv_to_yaml.py --csv-file input/csv/NRAM/dev/queues-xyz.csv
    python csv_to_yaml.py --csv-file input/csv/sample/uat/queues-team1.csv --env uat -v
"""

# Version information
VERSION = "5.0.0-0611"

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

    # Object type prefixes to match against (order matters - check longer prefixes first)
    type_prefixes = [
        (['client-username', 'client-usernames', 'client_user', 'client_users'], 'client-usernames'),
        (['client-profile', 'client-profiles', 'client_profile', 'client_profiles'], 'client-profiles'),
        (['acl-profile', 'acl-profiles', 'acl_profile', 'acl_profiles'], 'acl-profiles'),
        (['subscription', 'subscriptions'], 'subscriptions'),
        (['queue', 'queues'], 'queues'),
    ]
    
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
    
    def resolve_path_components(self, csv_file: str) -> tuple:
        """Extract (client, env, app) from CSV path.

        Paths must follow input/csv/<client>/<env>/<object>-<app>.csv:

            input/csv/NRAM/dev/queues-xyz.csv      -> ('NRAM', 'dev', 'xyz')
            input/csv/NT/uat/client-usernames-tla1.csv -> ('NT', 'uat', 'tla1')
            input/csv/team1/queues.csv             -> error
        """
        # Normalize path separators
        normalized = csv_file.replace('\\', '/')

        import re
        match = re.search(r'input/csv/([^/]+)/([^/]+)/([^/]+)\.csv$', normalized)
        if not match:
            raise ValueError(
                f"CSV file must be under input/csv/<client>/<env>/: {csv_file}\n"
                f"Example: input/csv/NRAM/dev/queues-xyz.csv"
            )

        client, env, filename = match.group(1), match.group(2), match.group(3)
        app = self.resolve_app_from_filename(filename)

        if self.verbose:
            self.log(f"Resolved client '{client}', env '{env}', app '{app}' from path: {csv_file}")
        return client, env, app

    def resolve_app_from_filename(self, name_without_ext: str) -> str:
        """Extract app name from filename: <object>-<app> -> <app>.

        e.g. 'queues-xyz' -> 'xyz', 'client-usernames-tla1' -> 'tla1'
        """
        object_type = self.get_object_type_from_filename(name_without_ext + '.csv')

        # Find the matched prefix and strip it (plus the separator)
        for prefixes, otype in self.type_prefixes:
            if otype != object_type:
                continue
            for prefix in prefixes:
                if name_without_ext.startswith(prefix + '-') or name_without_ext.startswith(prefix + '_'):
                    app = name_without_ext[len(prefix) + 1:]
                    if app:
                        return app

        raise ValueError(
            f"CSV filename must be <object>-<app>.csv (e.g. queues-xyz.csv): {name_without_ext}.csv"
        )

    def load_inventory_mapping(self, client: str, env: str) -> Dict[str, str]:
        """Load inventory/<client>/<env>.yml and create app->vpn mapping.

        Fails fast if the inventory file is missing.
        """
        inv_dir = 'inventory'
        inv_file = os.path.join(inv_dir, client, f'{env}.yml')
        if not os.path.isfile(inv_file):
            inv_file = os.path.join(inv_dir, client, f'{env}.yaml')
        if not os.path.isfile(inv_file):
            raise FileNotFoundError(
                f"Inventory file not found: {os.path.join(inv_dir, client, env)}.yml (or .yaml)\n"
                f"Expected one inventory file per environment: inventory/<client>/<env>.yml"
            )

        app_to_vpn = self._load_single_inventory_file(inv_file)
        if self.verbose:
            self.log(f"Loaded inventory from {inv_file}: {app_to_vpn}")
        return app_to_vpn

    def _load_single_inventory_file(self, inventory_file: str) -> Dict[str, str]:
        """Load a single inventory file and return app->vpn mapping."""
        inventory_config = self.yaml_handler.read_config_file(inventory_file)
        inventory = inventory_config.get('inventory', {})
        hosts = inventory.get('hosts', [])

        app_to_vpn = {}
        for host in hosts:
            app = host.get('app')
            vpn = host.get('vpn')
            if app and vpn:
                app_to_vpn[app] = vpn

        return app_to_vpn
    
    def log(self, message: str):
        """Log message with prefix"""
        print(f"{self.MAGENTA}[{self.SCRIPT_PREFIX}]{self.NC} {message}")
        
    def get_object_type_from_filename(self, csv_file: str) -> str:
        """Extract object type from CSV filename.

        Supports app-suffixed filenames like queues-xyz.csv, client-usernames-tla1.csv.
        The suffix after the object type is ignored.
        """
        filename = os.path.basename(csv_file)
        name_without_ext = os.path.splitext(filename)[0]

        for prefixes, object_type in self.type_prefixes:
            for prefix in prefixes:
                if name_without_ext == prefix or name_without_ext.startswith(prefix + '-') or name_without_ext.startswith(prefix + '_'):
                    return object_type

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
        # if self.verbose:
        #     self.log(f"Parsing value: '{value}' (type: {type(value)})")
        
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

        invalid_headers = []
        for header in headers:
            if header not in valid_tags_for_type:
                invalid_headers.append(header)

        if invalid_headers:
            error_msg = (f"Invalid column headers found in CSV file:\n"
                        f"Invalid headers: {invalid_headers}\n"
                        f"Valid headers for '{object_type}': {sorted(valid_tags_for_type)}")
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
                        # if self.verbose:
                        #     self.log(f"Raw CSV value for key '{key}': '{value}' (type: {type(value)}, repr: {repr(value)})")

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
    
    def resolve_app_and_prepare_objects(self, objects: List[Dict[str, Any]], client: str, env: str, app: str) -> tuple:
        """Resolve app to msgVpnName via inventory/<client>/<env>.yml and prepare objects.

        Args:
            objects: List of parsed CSV row dictionaries
            client: Client/org name from CSV path (e.g. NRAM, NT)
            env: Target environment from CSV path (e.g. dev, uat, prod)
            app: Application name from CSV filename suffix

        Returns:
            Tuple of (actual_msg_vpn_name, prepared_objects)
        """
        if not objects:
            raise ValueError("No objects to process")

        inventory_mapping = self.load_inventory_mapping(client=client, env=env)

        if app not in inventory_mapping:
            raise ValueError(
                f"App '{app}' not found in inventory/{client}/{env}.yml\n"
                f"Known apps: {sorted(inventory_mapping.keys())}"
            )

        actual_msg_vpn_name = inventory_mapping[app]
        if self.verbose:
            self.log(f"Resolved app '{app}' (env '{env}') -> msgVpnName '{actual_msg_vpn_name}' from inventory")

        # Prepare objects: strip env/inventoryKey if present, set msgVpnName
        prepared_objects = []
        for obj in objects:
            obj_copy = obj.copy()
            obj_copy.pop('env', None)
            obj_copy.pop('inventoryKey', None)
            obj_copy['msgVpnName'] = actual_msg_vpn_name
            prepared_objects.append(obj_copy)

        self.log(f"Processing {len(prepared_objects)} records for app '{app}' env '{env}' -> msgVpnName '{actual_msg_vpn_name}'")
        return actual_msg_vpn_name, prepared_objects
    
    def generate_yaml_output(self, verbose: bool, csv_file: str, env: Optional[str] = None) -> Dict[str, Any]:
        """Generate YAML output structure.

        Args:
            verbose: Enable verbose output
            csv_file: Path to CSV input file
            env: Optional target environment; must match the env from the CSV path
        """

        # Determine object type from CSV filename
        object_type = self.get_object_type_from_filename(csv_file)

        # Resolve client/env/app from CSV path (required)
        client, path_env, app = self.resolve_path_components(csv_file)

        # If --env was given, it must agree with the path
        if env and env != path_env:
            raise ValueError(
                f"--env '{env}' does not match env '{path_env}' from CSV path: {csv_file}"
            )
        env = path_env

        if self.verbose:
            self.log(f"Processing CSV file: {csv_file}")
            self.log(f"Detected object type: {object_type}")
            self.log(f"Client: {client}, Environment: {env}, App: {app}")

        # Read CSV data with header validation
        objects = self.read_csv_file(csv_file, object_type)

        if not objects:
            raise ValueError(f"No data found in CSV file: {csv_file}")

        # Resolve app to msgVpnName and prepare objects
        msg_vpn_name, valid_objects = self.resolve_app_and_prepare_objects(objects, client=client, env=env, app=app)

        # Read defaults
        defaults = self.read_defaults(object_type)

        # Merge with defaults
        if defaults:
            valid_objects = self.merge_with_defaults(valid_objects, defaults)

        # Build the output structure for yaml_to_semp.py:
        # client + env locate the inventory file, app selects the entry
        params = {
            'client': client,
            'env': env,
            'app': app,
            'verbose': verbose,
            'create': [object_type]
        }

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
    parser.add_argument('--verbose', '-v', action='count', default=0,
                       help='Verbose output. Use -vvv for more verbose output')
    parser.add_argument('--csv-file', required=True,
                       help='Path to CSV file (input/csv/<client>/<env>/<object>-<app>.csv)')
    parser.add_argument('--env', '-e', required=False, default=None,
                       help='Target environment (optional; must match the <env> directory in the CSV path)')
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
            csv_file=args.csv_file,
            env=args.env
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