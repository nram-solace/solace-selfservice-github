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
                        if 'sempPassword' not in host_data:
                            if os.environ.get('SEMP_PASSWORD') is not None:
                                log.info ('Using password from env {} for {}'.format('SEMP_PASSWORD', name))
                                inv[name]['sempPassword'] = os.environ.get('SEMP_PASSWORD')
                                    #inv[name]['SEMP_PASSWORD_ENV_VAR'] = semp_pass_env_var
                            else:
                                log.error ('Missing password for {}'.format(name))
                                log.info ('Check the environment variable: {}'.format('SEMP_PASSWORD'))
                            
                            # TLA based passwords is hard to implement with github work flow & Secrets management
                            # so we are going to use a single password for all TLAs.
                            # ignore case in host name
                            #semp_pass_env_var = 'SEMP_PASSWORD_{}_{}'.format(host_data['host'].upper(), host_data['sempUser'].upper())
                            #semp_pass_env_var = semp_pass_env_var.replace('.', '_').replace('-', '_')
                            #nv[name]['SEMP_PASSWORD_ENV_VAR'] = semp_pass_env_var
                            # check if password is in the environment
                            #if os.environ.get(semp_pass_env_var) is None:
                            #    log.warning ('SEMP_PASSWORD environment variable ({}) not set for {}'.format(semp_pass_env_var, name))
                            #    if os.environ.get('SEMP_PASSWORD') is not None:
                            #        log.notice ('Using password from env {} for {}'.format('SEMP_PASSWORD', name))
                            #        inv[name]['sempPassword'] = os.environ.get('SEMP_PASSWORD')
                            #        #inv[name]['SEMP_PASSWORD_ENV_VAR'] = semp_pass_env_var
                            #    else:
                            #        log.error ('Missing password for {}'.format(name))
                            #else:
                            #    log.info ('Using password from env {} for {} in environment'.format(semp_pass_env_var, name))
                            #    inv[name]['sempPassword'] = os.environ.get(semp_pass_env_var)
                                
                    
        self.inv = inv
        log.info ('Inventory read from {} hosts'.format(len(inv)))

        return inv
    
    
    def dump_inventory(self):
        """ Dump inventory """
        log.enter ('Entering {}::{}'.format(__class__.__name__, inspect.stack()[0][3]))
        log.info ('Dumping inventory')
        log.info (self.inv)
        return self.inv
    