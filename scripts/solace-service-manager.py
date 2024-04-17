########################################################################
# solace-service-manager.py
#
# This program creates new or update existing queues on a Solace PubSub+ broker using SEMPv2
# While updating, Queue will be temporarily disabled.
# This version takes a single Yaml file as input with all required inputs
#
# Requirements:
#  Python 3
#  Modules: json, yaml, urllib3, requests
#
# Running:
# Create queues:
#   python3 solace-service-manager.py --input input/default.yaml
#
# Ramesh Natarajan (nram), Solace PSG (ramesh.natarajan@solace.com)
########################################################################
me = "solace-service-manager"
ver = 'v2.2.2-2024-04-17'

import sys, os
import argparse
import json
import pprint

sys.path.insert(0, os.path.abspath("."))
from common import LogHandler
from common import SempHandler
from common import YamlHandler
from common import QueueConfig
from common import ClientUserConfig
from common import Inventory

# Define the minimum required Python version
MIN_PYTHON_VERSION = (3, 6)
pp = pprint.PrettyPrinter(indent=4)

class CustomEncoder(json.JSONEncoder):
    def iterencode(self, obj, _one_shot=False):
        if isinstance(obj, dict):
            obj = {k: v if k != "sempPassword" else "*****" for k, v in obj.items()}
        return super().iterencode(obj, _one_shot)

def main(argv):
    """ program entry drop point """
    
    # parse command line arguments
    p = argparse.ArgumentParser()
    p.add_argument('--input', dest="input_file", required=True, 
                   help='user input Yaml file') 
    #p.add_argument('--patch', dest="patch_it", action='store_true', required=False, default=False, 
    #               help='user input csv file') 
    #p.add_argument('--subscriptions', '-s', dest="add_subscriptions", action='store_true', required=False, default=False,
    #               help='Add subscriptions to queues')
    p.add_argument( '--verbose', '-v', action="count",  required=False, default=0,
                help='Verbose output. use -vvv for tracing')
    r = p.parse_args()

    print ('{}-{} Starting {} args: {}\n'.format(me,ver, sys.argv[0], str(sys.argv[1:])))

    if r.verbose:    
        print ("http proxy: ", os.environ.get('http_proxy'))
        print ("Python version: ", sys.version)
    
    # check if input file exists
    if not os.path.exists(r.input_file):
        print ('ERROR: input file {} not found'.format(r.input_file))
        sys.exit(1)
        
    print ("Reading input file: {}".format(r.input_file))
    yaml_h = YamlHandler.YamlHandler()
    input_data_all = yaml_h.read_config_file(r.input_file)
    #if r.verbose:
    #    print ('Input Data:'); pp.pprint (input_data_all)
    input_data = input_data_all['inputs']   
    
    sys_cfg_file = input_data_all['system']['configFile']
    print ("Reading system config file: {}".format(sys_cfg_file))

    system_config_all = yaml_h.read_config_file (sys_cfg_file)
    system_cfg = system_config_all['system']
        
    # create a single cfg file with all info
    cfg = input_data_all.copy()
    cfg['router'] = {}
    cfg['script_name'] = me
    cfg['system'] = system_config_all.copy() # store system cfg in the global Cfg dict
    # copy input data to Cfg
    run_params = input_data_all['params']
    verbose = run_params['verbose']
    #action = run_params['action']
    if r.verbose:
        verbose = r.verbose
    cfg['verbose'] = verbose
    #if verbose :
    #    print ('SYSTEM CONFIG'); pp.pprint (system_config_all)
                
    # read password from environment variable
    #if os.environ.get('SEMP_PASSWORD') is None:
    #    print ('ERROR: SEMP_PASSWORD environment variable not set')
    #    sys.exit(1)
    
    log_h = LogHandler.LogHandler(cfg)
    log = log_h.get()


    # add this after dumping Cfg. josn.dumps() can't handle log object
    cfg['log_handler'] = log_h

    # Read the inventory file
    print ('Reading inventory from {}'.format(system_cfg['inventoryDir']))
    inv = Inventory.Inventory(cfg, r.verbose)
    inv_data = inv.read_inventory_dir(system_cfg['inventoryDir'])
    
    log.info ('Starting {}-{}'.format(me, ver))
    log.info ('SYSTEM CONFIG : {}'.format(json.dumps(system_config_all, indent=2)))
    log.info ('USER INPUT    : {}'.format(json.dumps(input_data_all, indent=2)))
    log.info ('INVENTORY     : {} hosts'.format(len(inv_data)))

    #leaks password
    for k in inv_data:
        log.info ('{}     : {}'.format(k, json.dumps(inv_data[k], cls=CustomEncoder,indent=2)))            
    
    app_id = input_data_all['params']['application-id']
    if app_id not in inv_data:
        log.error ('Application ID: {} not found in inventory'.format(app_id))
        # print list of keys in the inventory
        log.info ('Inventory keys: {}'.format(str(inv_data.keys())))
        sys.exit(1)
    router = inv_data[app_id]
    log.notice (f'Got the router config for {app_id}\n\tURL     : {router["sempUrl"]}\n\tUSER    : {router["sempUser"]}\n\tVPN     : {router["vpn"]}\n\tPASSWORD: read from env' )


    cfg['router'] = router
    if 'sempPassword' not in router:
        log.error ('sempPassword not set in config nor found in inventory for {}'.format(app_id))
        log.info('Check the environment variable: {}'.format(router['SEMP_PASSWORD_ENV_VAR']))
        sys.exit(1)
        
    #cfg['router']['sempPassword'] = os.environ.get('SEMP_PASSWORD')

    # create semp handler -- see common/SimpleSempHandler.py
    semp_h = SempHandler.SempHandler(cfg, verbose)
    
    ##if 'admin_action' in run_params:
    #    for entry in action:
    #        action[entry] = run_params['admin_action']
    #---------------------------------------------------------------------
    #  Queues
    #
    queue_h = QueueConfig.Queues(semp_h, cfg, verbose)
    cluser_h = ClientUserConfig.ClientUserConfig(semp_h, cfg, verbose)    

    if 'create' in run_params and run_params['create'] is not None:
        for entry in run_params['create']:
            print ('------------------------------------------------------')
            log.notice ('Processing create {}'.format(entry))
            if entry == 'queues':
                queue_h.create_queues (input_data['queues'])
            if entry == 'subscriptions':
                queue_h.create_queue_subscriptions (input_data['queues'])
            if entry == 'client-profiles':
                cluser_h.create_client_profiles (input_data['client-profiles'])
            if entry == 'acl-profiles':
                cluser_h.create_acl_profiles (input_data['acl-profiles'])
            if entry == 'client-usernames':
                # auto create client profiles and acl profiles for client-usernames
                cluser_h.create_client_profiles (input_data['client-profiles'])
                cluser_h.create_acl_profiles (input_data['acl-profiles'])
                cluser_h.create_client_usernames (input_data['client-usernames'])
    if 'delete' in run_params and run_params['delete'] is not None:
        for entry in run_params['delete']:
            print ('------------------------------------------------------')
            log.notice ('Processing delete {}'.format(entry))
            if entry == 'queues':
                queue_h.delete_queues (input_data['queues'])
            if entry == 'subscriptions':
                log.error ('Not implemented - delete subscriptions')
                #queue_h.delete_queue_subscriptions (input_data['queues'])
            if entry == 'client-profiles':
                cluser_h.delete_client_profiles (input_data['client-profiles'])
            if entry == 'acl-profiles':
                cluser_h.delete_acl_profiles (input_data['acl-profiles'])
            if entry == 'client-usernames':
                cluser_h.delete_client_usernames (input_data['client-usernames'])

                
    log.info ('{}-{} Done'.format(me, ver))
    
# Program entry point
if __name__ == "__main__":
    """ program entry point - must be  below main() """
    # Check if the current Python version meets the requirement
    if sys.version_info < MIN_PYTHON_VERSION:
        print(f"This script requires Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]} or later.")
        print(f"Your Python version is {sys.version_info.major}.{sys.version_info.minor}.")
        sys.exit(1)  # Exit the script with a non-zero status code

    main(sys.argv[1:])
