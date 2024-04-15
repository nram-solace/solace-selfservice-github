########################################################################
# create-queues
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
#   python3 create-queues2.py --input input/queues.yaml
#
# Ramesh Natarajan (nram), Solace PSG (ramesh.natarajan@solace.com)
########################################################################

import sys, os
import argparse
import json
import pprint

sys.path.insert(0, os.path.abspath("."))
from common import LogHandler
from common import SempHandler
#from common import JsonHandler
from common import QueueConfig
from common import YamlHandler

pp = pprint.PrettyPrinter(indent=4)

me = "create-queues"
ver = 'v1.1'

# Define the minimum required Python version
MIN_PYTHON_VERSION = (3, 6)

def main(argv):
    """ program entry drop point """

    # print python version
    print ("Python version: ", sys.version)
    #print ("Python path: ", sys.path)
    # print program and args
    print ('Program: ', sys.argv[0], str(sys.argv[1:]))
    
    # parse command line arguments
    p = argparse.ArgumentParser()
    p.add_argument('--input', dest="input_file", required=True, 
                   help='user input Yaml file') 
    p.add_argument('--patch', dest="patch_it", action='store_true', required=False, default=False, 
                   help='user input csv file') 
    #p.add_argument('--subscriptions', '-s', dest="add_subscriptions", action='store_true', required=False, default=False,
    #               help='Add subscriptions to queues')
    p.add_argument( '--verbose', '-v', action="count",  required=False, default=0,
                help='Verbose output. use -vvv for tracing')
    r = p.parse_args()

    print ('{}-{} Starting\n'.format(me,ver))
    
    print ("http proxy: ", os.environ.get('http_proxy'))
    
    print ("Reading input file: {}".format(r.input_file))
    yaml_h = YamlHandler.YamlHandler()
    input_data = yaml_h.read_config_file(r.input_file)
    
    sys_cfg_file = input_data['system']['configFile']
    print ("Reading system config file: {}".format(sys_cfg_file))

    system_config_all = yaml_h.read_config_file (sys_cfg_file)
    if r.verbose > 2:
        print ('SYSTEM CONFIG'); pp.pprint (system_config_all)
        
    # create a single cfg file with all info
    cfg = {}
    cfg['script_name'] = me
    cfg['verbose'] = r.verbose
    cfg['system'] = system_config_all.copy() # store system cfg in the global Cfg dict
    run_params = system_config_all['run_params']
    verbose = run_params['verbose']
    action = run_params['action']
    if r.verbose:
        verbose = r.verbose
    # copy input data to Cfg
    cfg['router'] = input_data['router'].copy() 
    cfg['templates'] = input_data['templates'].copy()
    # read password from environment variable
    if os.environ.get('SEMP_PASSWORD') is None:
        print ('ERROR: SEMP_PASSWORD environment variable not set')
        sys.exit(1)
    print ('Using SEMP_PASSWORD from environment')
    cfg['router']['sempPassword'] = os.environ.get('SEMP_PASSWORD')
    

    log_h = LogHandler.LogHandler(cfg)
    log = log_h.get()
    log.info('Starting {}-{}'.format(me, ver))
    log.info ('SYSTEM CONFIG : {}'.format(json.dumps(system_config_all, indent=2)))
    log.info ('Input Data    : {}'.format(json.dumps(input_data, indent=2)))
    # add this after dumping Cfg. josn.dumps() can't handle log object
    cfg['log_handler'] = log_h

    # split input_df into regular queues and DLQs
    # Add your logic here
    q_list = input_data['queues']
    #dmqs = input_df[input_df['queueName'].str.contains('(_DLQ)')]

    #log.info ('REGULAR QUEUES : {}'.format(json.dumps(q_list, indent=2)))
    #log.info ('DMQS : {}'.format(json.dumps(dmqs['queueName'].to_dict(), indent=4)))

    # create semp handler -- see common/SimpleSempHandler.py
    semp_h = SempHandler.SempHandler(cfg, r.verbose)

    # create queue handlers
    queue_h = QueueConfig.Queues(semp_h, cfg, q_list, verbose)
    #dmqueue_h = QueueConfig.Queues(semp_h, Cfg, dmqs, Verbose)

    # create / update queues
    # Create DMQs followed by regular queues
    #dmqueue_h.create_or_update_dmqueue ( r.patch_it)
    queue_h.create_queues (input_data['queues'], r.add_subscriptions)
    
    #if r.subscriptions:
    #    # Add subscriptions to queues
    #    log.info ('Adding subscriptions to queues')
    #    queue_h.add_topic_subscriptions1(input_data['queue_subscriptions'])
    
    
# Program entry point
if __name__ == "__main__":
    """ program entry point - must be  below main() """
    # Check if the current Python version meets the requirement
    if sys.version_info < MIN_PYTHON_VERSION:
        print(f"This script requires Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]} or later.")
        print(f"Your Python version is {sys.version_info.major}.{sys.version_info.minor}.")
        sys.exit(1)  # Exit the script with a non-zero status code

    main(sys.argv[1:])
