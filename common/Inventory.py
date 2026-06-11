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


    # Read the per-environment inventory file for a client:
    # inventory/<client>/<env>.yml with entries keyed by app

    def read_inventory(self, inv_dir, client, env):
        """ Read inventory/<client>/<env>.yml and return a dict keyed by app """
        log.enter ('Entering {}::{}'.format(__class__.__name__, inspect.stack()[0][3]))

        inv_file = os.path.join(inv_dir, client, f'{env}.yml')
        if not os.path.isfile(inv_file):
            inv_file = os.path.join(inv_dir, client, f'{env}.yaml')
        if not os.path.isfile(inv_file):
            log.error ('Inventory file not found: {}/{}/{}.yml (or .yaml)'.format(inv_dir, client, env))
            sys.exit(1)

        log.info ('Reading inventory file: {}'.format(inv_file))
        yaml_h = YamlHandler.YamlHandler()
        inv = {}
        inv_file_data = yaml_h.read_config_file(inv_file)
        log.debug (f'Read from {inv_file} {inv_file_data}')
        for host_data in inv_file_data['inventory']['hosts']:
            app = host_data['app']
            if app in inv:
                log.error ('Duplicate app entry: {} ignored'.format(app))
            else:
                log.info ('Adding app: {} to the inventory'.format(app))
                inv[app] = host_data
                # Password resolution is deferred to yaml_to_semp.py
                # Only the target host's password is resolved (not all hosts)

        self.inv = inv
        log.info ('Inventory read from {}: {} apps'.format(inv_file, len(inv)))

        return inv
    
    
    def dump_inventory(self):
        """ Dump inventory """
        log.enter ('Entering {}::{}'.format(__class__.__name__, inspect.stack()[0][3]))
        log.info ('Dumping inventory')
        log.info (self.inv)
        return self.inv
    