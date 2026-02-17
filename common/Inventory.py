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
        """ Read inventory files from inv_dir. If team is specified, read only from inv_dir/team/ """
        log.enter ('Entering {}::{}'.format(__class__.__name__, inspect.stack()[0][3]))

        # If team is specified, scope to team-specific subdirectory
        if team:
            team_dir = os.path.join(inv_dir, team)
            if os.path.isdir(team_dir):
                log.info ('Reading team-specific inventory from {}'.format(team_dir))
                inv_dir = team_dir
            else:
                log.warning ('Team inventory dir {} not found, falling back to {}'.format(team_dir, inv_dir))

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
                # Get inventory/hosts/name as key 
                for host_data in inv_file_data['inventory']['hosts']:
                    name = host_data['name']
                    if name in inv:
                        log.error ('Duplicate host entry: {} ignored'.format(name))
                    else:
                        log.info ('Adding host: {} to the inventory'.format(name))
                        inv[name] = host_data
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
    