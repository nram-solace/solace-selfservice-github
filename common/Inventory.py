###################################################################################################
# Inventory.py  
# Manage access to the inventory of Solace appliances.
#
# Ramesh Natarajan (nram), Solace PSG
###################################################################################################

import sys, os, inspect
import inspect
from common import YamlHandler
import pprint

pp = pprint.PrettyPrinter(indent=4)

log  = None
Verbose = 0
Cfg = {}

class Inventory:
    """ Solace Inventory implementation """

    def __init__(self, cfg, verbose = 0):
        global Verbose
        global Cfg, log
        Verbose = verbose
        Cfg = cfg
        log = Cfg['log_handler'].get()
        inv = {}
        log.enter ('Entering {}::{}'.format(__class__.__name__, inspect.stack()[0][3]))


    # Read inventory Yaml files from the inventory directory
    # add them to a dictionary
    
    def read_inventory_dir(self, inv_dir, team=None):
        """ Read inventory files from inv_dir. If team is specified, read only inventory/<team>.yaml """
        log.enter ('Entering {}::{}'.format(__class__.__name__, inspect.stack()[0][3]))

        # If team is specified, load team-specific inventory file directly
        if team:
            team_file = os.path.join(inv_dir, f'{team}.yaml')
            if not os.path.isfile(team_file):
                team_file = os.path.join(inv_dir, f'{team}.yml')
            if os.path.isfile(team_file):
                log.info ('Reading team-specific inventory from {}'.format(team_file))
                yaml_h = YamlHandler.YamlHandler()
                inv = {}
                inv_file_data = yaml_h.read_config_file(team_file)
                log.debug (f'Read from {team_file} {inv_file_data}')
                for host_data in inv_file_data['inventory']['hosts']:
                    environment = host_data['environment']
                    log.info ('Adding host: {} to the inventory'.format(environment))
                    inv[environment] = host_data
                self.inv = inv
                log.info ('Inventory read from {} hosts'.format(len(inv)))
                return inv
            else:
                log.warning ('Team inventory file {} not found, falling back to {}'.format(
                    os.path.join(inv_dir, f'{team}.yaml'), inv_dir))

        log.info ('Reading inventory files from {}'.format(inv_dir))
        yaml_h = YamlHandler.YamlHandler()

        inv = {}
        for root, dirs, files in os.walk(inv_dir):
            for file in files:
                if not file.endswith(".yaml") and not file.endswith(".yml"):
                    continue
                inv_file = os.path.join(root, file)
                log.info ('Reading inventory file: {}'.format(inv_file))
                inv_file_data = yaml_h.read_config_file(inv_file)
                log.debug (f'Read from {inv_file} {inv_file_data}')
                # Get inventory/hosts/environment as key
                for host_data in inv_file_data['inventory']['hosts']:
                    environment = host_data['environment']
                    if environment in inv:
                        log.error ('Duplicate host entry: {} ignored'.format(environment))
                    else:
                        log.info ('Adding host: {} to the inventory'.format(environment))
                        inv[environment] = host_data
                        # Password resolution is deferred to yaml_to_semp.py
                        # Only the target host's password is resolved (not all hosts)
                                
                    
        self.inv = inv
        log.info ('Inventory read from {} hosts'.format(len(inv)))

        return inv
    
    
    def dump_inventory(self):
        """ Dump inventory """
        log.enter ('Entering {}::{}'.format(__class__.__name__, inspect.stack()[0][3]))
        log.info ('Dumping inventory')
        log.info (self.inv)
        return self.inv
    