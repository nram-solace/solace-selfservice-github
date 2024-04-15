#####################################################################
# QueueConfig
#   Implements Queue provisioning functions
#
# Ramesh Natarajan (nram), Solace PSG (ramesh.natarajan@solace.com)
#
#####################################################################

import sys, os, inspect
import json
from urllib.parse import unquote, quote
import pprint

# Globals
pp = pprint.PrettyPrinter(indent=4)
Verbose = 0
log = None

class Queues():

    def __init__(self, semp_h, cfg, verbose = 0):
        global Verbose
        global log
        Verbose = verbose
        log = cfg['log_handler'].get()
        self.semp_h = semp_h
        self.cfg = cfg
    #--------------------------------------------------------------------
    # get_topic_list
    # Get list of topics from SEMP response
    #--------------------------------------------------------------------
    def get_topic_list (self, resp):

        resp_json = json.loads(resp.text)
        topic_list = []
        if 'data' in resp_json:
            for sub in resp_json['data']:
                topic_list.append(sub['subscriptionTopic'])
        return topic_list
    
    
    def create_queue_subscriptions(self, input_data):
        semp_h = self.semp_h
        cfg = self.cfg
        sys_cfg = cfg['system']
        msg_vpn_name = cfg['router']['vpn']
        
        log.info ('Creating Queue subscriptions in VPN: {} on router: {}'.format(msg_vpn_name, cfg['router']['sempUrl']))
        semp_config_url = '{}/{}/msgVpns'.format(cfg['router']['sempUrl'], sys_cfg['semp']['configUrl'])
        semp_queue_config_url = f"{semp_config_url}/{msg_vpn_name}/queues"
        
        num_queues = len(input_data)
        log.notice ('Processing {} Queues on {}'.format(num_queues, msg_vpn_name))   
        n = 0
        for q_data in input_data:
            n += 1
            queue = q_data['queueName']
            semp_data=cfg['defaults']['queue'].copy()
            # add required missing params
            semp_data['queueName'] = queue
            semp_data['msgVpnName'] = msg_vpn_name
            log.info ('Processing queue: {}'.format(queue))

            ###################################################
            # post to router - create queue
            #
            print ('\n')
            log.notice (f"Creating queue subscriptions {n}/{num_queues}: {queue}")
            if 'subscriptions' in q_data:
                self.add_topic_subscriptions(queue, q_data['subscriptions'])       
        
    #--------------------------------------------------------------------
    # create_queues
    # Create Queues with http post. This does NOT patch existing queues
    #--------------------------------------------------------------------
    def create_queues (self, input_data_list, add_subscriptions = False):

        semp_h = self.semp_h
        cfg = self.cfg
        sys_cfg = cfg['system']
        msg_vpn_name = cfg['router']['vpn']
        
        log.info ('Creating Queues in VPN: {} on router: {}'.format(msg_vpn_name, cfg['router']['sempUrl']))
        semp_config_url = '{}/{}/msgVpns'.format(cfg['router']['sempUrl'], sys_cfg['semp']['configUrl'])
        semp_queue_config_url = f"{semp_config_url}/{msg_vpn_name}/queues"
        
        num_queues = len(input_data_list)
        log.notice ('Creating {} Queues on {}'.format(num_queues, msg_vpn_name))
        queue_props = []
        # get list of tags from Cfg['queue']
        for k in cfg['defaults']['queue']:
            queue_props.append(k)
        # add required tags
        queue_props.append('queueName')
        #queue_props.append('msgVpnName')
        if Verbose > 2:
            print ('Tags:', queue_props)    
        n = 0
        for input_data in input_data_list:
            n += 1
            entry_name = input_data['queueName']
            semp_data=cfg['defaults']['queue'].copy()
            # add required missing params
            semp_data['queueName'] = input_data
            semp_data['msgVpnName'] = msg_vpn_name
            for k in input_data:
                # skip subscriptions
                if k == 'subscriptions':
                    continue
                semp_data[k] = input_data[k]
            # enable queues
            semp_data['egressEnabled'] = True
            semp_data['ingressEnabled'] = True
            
            log.info ('Processing queue: {}'.format(input_data))
            ###################################################
            # post to router - create queue
            #
            print ('\n')
            log.notice (f"Creating queue {n}/{num_queues}: {entry_name}")
            resp = semp_h.http_post (semp_queue_config_url, semp_data)
            if resp == 'ALREADY_EXISTS':
                log.info (f'Queue {entry_name} exists. Skipping')
            else:
                log.info (f'Queue {entry_name} created')
            if add_subscriptions and 'subscriptions' in input_data:
                self.add_topic_subscriptions(entry_name, input_data['subscriptions'])
    
    
    #--------------------------------------------------------------------
    # delete queues
    # Delete Queues with http delete
    #--------------------------------------------------------------------
    
    def delete_queues (self, input_data_list):
        semp_h = self.semp_h
        cfg = self.cfg
        sys_cfg = cfg['system']
        msg_vpn_name = cfg['router']['vpn']
        
        log.info ('Deleting Queues in VPN: {} on router: {}'.format(msg_vpn_name, cfg['router']['sempUrl']))
        semp_config_url = '{}/{}/msgVpns'.format(cfg['router']['sempUrl'], sys_cfg['semp']['configUrl'])
        semp_queue_config_url = f"{semp_config_url}/{msg_vpn_name}/queues"
        
        num_queues = len(input_data_list)
        log.notice ('Deleting {} Queues on {}'.format(num_queues, msg_vpn_name))   
        n = 0
        for q_data in input_data_list:
            n += 1
            queue = q_data['queueName']
            semp_data=cfg['defaults']['queue'].copy()
            # add required missing params
            semp_data['queueName'] = queue
            semp_data['msgVpnName'] = msg_vpn_name
            log.info ('Processing queue: {}'.format(queue))

            ###################################################
            # post to router - create queue
            #
            print ('\n')
            log.notice (f"Deleting queue {n}/{num_queues}: {queue}")
            resp = semp_h.http_delete (f"{semp_queue_config_url}/{queue}")
            if resp != 'OK':
                log.warning (f'Delete Queue {queue} returned {resp}')
            else:
                log.info (f'Queue {queue} deleted')
    
    #--------------------------------------------------------------------
    # add_topic_subscriptions
    # Add topic subscriptions to a queue
    #--------------------------------------------------------------------            
    def add_topic_subscriptions(self, queue_name, sub_topics):
        log.info  (f'Adding topic subscriptions to queue {queue_name}')
        semp_h = self.semp_h
        cfg = self.cfg
        sys_cfg = cfg['system']
        msg_vpn_name = cfg['router']['vpn']
        semp_config_url = '{}/{}/msgVpns'.format(cfg['router']['sempUrl'], sys_cfg['semp']['configUrl'])
        semp_queue_config_url = f"{semp_config_url}/{msg_vpn_name}/queues"
        max_n = len(sub_topics)
        log.notice (f'Got {max_n} topics to add to Queue {queue_name}')
        n = 0
        for topics in sub_topics:
            n += 1
            topic = topics.strip()
            data = {}
            data['msgVpnName'] = msg_vpn_name
            data['queueName'] = queue_name
            data['subscriptionTopic'] = topic
            # Escape special characters in topic
            queue_safe = quote(queue_name, safe='')
            print ('\n')
            log.notice  (f"Adding subscription topic {n}/{max_n}: {topic} - {queue_name}")
            semp_queue_sub_config_url = f"{semp_config_url}/{msg_vpn_name}/queues/{queue_safe}/subscriptions"
            semp_h.http_post (semp_queue_sub_config_url, data)
 