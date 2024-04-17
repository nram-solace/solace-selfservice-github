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
    
    def read_inventory_dir(self, inv_dir):
        """ Read inventory files from inv_dir """
        log.enter ('Entering {}::{}'.format(__class__.__name__, inspect.stack()[0][3]))
        log.info ('Reading inventory files from {}'.format(inv_dir))
        yaml_h = YamlHandler.YamlHandler()

        inv = {}
        for file in os.listdir(inv_dir):
            if file.endswith(".yaml"):
                log.info ('Reading inventory file: {}'.format(file))
                inv_file = os.path.join(inv_dir, file)
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
                        inv[name]['environment'] = inv_file_data['inventory']['environment']
                        if 'sempPassword' not in host_data:
                            # ignore case in host name
                            pass_env_var = 'SEMP_PASSWORD_{}_{}'.format(host_data['host'].lower(), host_data['sempUser'].lower())
                            pass_env_var = pass_env_var.replace('.', '_').replace('-', '_')

                            # check if password is in the environment
                            if os.environ.get(pass_env_var) is None:
                                log.warning ('SEMP_PASSWORD environment variable ({}) not set for {}'.format(pass_env_var, name))
                            else:
                                log.info ('Found password for {} in environment'.format(name))
                                inv[name]['sempPassword'] = os.environ.get(pass_env_var)
                                
                    
        self.inv = inv
        log.info ('Inventory read from {} hosts'.format(len(inv)))

        return inv
    
    
    def dump_inventory(self):
        """ Dump inventory """
        log.enter ('Entering {}::{}'.format(__class__.__name__, inspect.stack()[0][3]))
        log.info ('Dumping inventory')
        log.info (self.inv)
        return self.inv
    