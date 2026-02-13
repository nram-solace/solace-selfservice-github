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
    def create_queues (self, input_data_list, dmqueue = False):

        semp_h = self.semp_h
        cfg = self.cfg
        sys_cfg = cfg['system']
        msg_vpn_name = cfg['router']['vpn']
        
        label = 'Queues'
        if dmqueue:
            label = 'Dead Message Queues'
            
        log.info ('Creating {} in VPN: {} on router: {}'.format(label, msg_vpn_name, cfg['router']['sempUrl']))
        semp_config_url = '{}/{}/msgVpns'.format(cfg['router']['sempUrl'], sys_cfg['semp']['configUrl'])
        semp_queue_config_url = f"{semp_config_url}/{msg_vpn_name}/queues"
        
        num_queues = len(input_data_list)
        log.notice ('Creating {} {} on {}'.format(num_queues, label, msg_vpn_name))
        queue_props = []
        #if dmqueue:
        #    log.info ('Using Dead Message Queue properties')
        #    default_props = cfg['defaults']['dmqueue']
        #else: 
        #    default_props = cfg['defaults']['queue']
        ## get list of tags from Cfg['queue']
        #for k in default_props:
        #    queue_props.append(k)
        # add required tags
        queue_props.append('queueName')
        #queue_props.append('msgVpnName')
        if Verbose > 2:
            print ('Tags:', queue_props)    
        n = 0
        for input_data in input_data_list:
            n += 1
            entry_name = input_data['queueName']
            if dmqueue:
                log.info ('Using DMQ properties')
                semp_data=cfg['defaults']['dmqueue'].copy()
            else:
                semp_data=cfg['defaults']['queue'].copy()
            # add required missing params
            semp_data['queueName'] = entry_name
            semp_data['msgVpnName'] = msg_vpn_name
            for k in input_data:
                # skip subscriptions and jndiQueueName (not valid SEMP queue attributes)
                if k in ['subscriptions', 'jndiQueueName']:
                    continue
                semp_data[k] = input_data[k]
            # enable queues
            semp_data['egressEnabled'] = True
            semp_data['ingressEnabled'] = True
            
            log.info ('Processing {}: {}'.format(label, entry_name))
            ###################################################
            # post to router - create queue
            #
            print ('\n')
            log.notice (f"Creating {label} {n}/{num_queues}: {entry_name}")
            resp = semp_h.http_post (semp_queue_config_url, semp_data)
            if resp == 'OK':
                log.status (f'{label} {entry_name} created')
            elif resp == 'ALREADY_EXISTS':
                log.warning (f'{label} {entry_name} exists.')
            else:
                log.error (f'{label} {entry_name} create failed: {resp}')
            if dmqueue:
                log.info ('Queue is a Dead Message Queue. Skipping subscriptions and JNDI mapping')
                continue
            if 'subscriptions' in input_data:
                self.add_topic_subscriptions(entry_name, input_data['subscriptions'])

            # Handle JNDI mapping based on jndiQueueName field
            if 'jndiQueueName' in input_data:
                jndi_queue_name = input_data['jndiQueueName']
                if jndi_queue_name is None or str(jndi_queue_name).strip() == '':
                    # Empty value - skip JNDI mapping
                    log.info (f'No JNDI mapping specified for queue {entry_name}, skipping JNDI creation')
                elif str(jndi_queue_name).upper() == 'AUTO':
                    # AUTO - use auto-generated JNDI name
                    jndi_name = f'Q_{entry_name}'
            # replace "." with _ 
                    jndi_name = jndi_name.replace('.', '_')
                    log.info (f'Using auto-generated JNDI name {jndi_name} for queue {entry_name}')
                    self.add_jndi_queue (entry_name, jndi_name)
                else:
                    # Custom JNDI name provided
                    jndi_name = str(jndi_queue_name)
                    log.info (f'Using custom JNDI name {jndi_name} for queue {entry_name}')
                    self.add_jndi_queue (entry_name, jndi_name)
            else:
                # No jndiQueueName field - use legacy auto-generation for backward compatibility
                jndi_name = f'Q_{entry_name}'
                jndi_name = jndi_name.replace('.', '_')
                log.info (f'No jndiQueueName field found, using auto-generated JNDI name {jndi_name} for queue {entry_name}')
                self.add_jndi_queue (entry_name, jndi_name)
    
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
            queue_name = q_data['queueName']
            semp_data=cfg['defaults']['queue'].copy()
            # add required missing params
            semp_data['queueName'] = queue_name
            semp_data['msgVpnName'] = msg_vpn_name
            log.info ('Processing queue: {}'.format(queue_name))

            ###################################################
            # post to router - delete queue
            #
            print ('\n')
            log.notice (f"Deleting queue {n}/{num_queues}: {queue_name}")
            queue_safe = quote(queue_name, safe='')
            resp = semp_h.http_delete (f"{semp_queue_config_url}/{queue_safe}")
            if resp != 'OK':
                log.warning (f'Delete Queue {queue_name} failed {resp}')
            else:
                log.status (f'Queue {queue_name} deleted')

            # Handle JNDI deletion based on jndiQueueName field
            if 'jndiQueueName' in q_data:
                jndi_queue_name = q_data['jndiQueueName']
                if jndi_queue_name is None or str(jndi_queue_name).strip() == '':
                    # Empty value - skip JNDI deletion
                    log.info (f'No JNDI mapping specified for queue {queue_name}, skipping JNDI deletion')
                elif str(jndi_queue_name).upper() == 'AUTO':
                    # AUTO - use auto-generated JNDI name
                    jndi_name = f'Q_{queue_name}'
            # replace "." with _ 
                    jndi_name = jndi_name.replace('.', '_')
                    log.info (f'Deleting auto-generated JNDI name {jndi_name} for queue {queue_name}')
                    self.delete_jndi_queue (jndi_name)
                else:
                    # Custom JNDI name provided
                    jndi_name = str(jndi_queue_name)
                    log.info (f'Deleting custom JNDI name {jndi_name} for queue {queue_name}')
                    self.delete_jndi_queue (jndi_name)
            else:
                # No jndiQueueName field - use legacy auto-generation for backward compatibility
                jndi_name = f'Q_{queue_name}'
                jndi_name = jndi_name.replace('.', '_')
                log.info (f'No jndiQueueName field found, deleting auto-generated JNDI name {jndi_name} for queue {queue_name}')
                self.delete_jndi_queue (jndi_name)
        
    
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
            log.notice  (f"Adding subscription topic {n}/{max_n}: {topic} => {queue_name}")
            semp_queue_sub_config_url = f"{semp_config_url}/{msg_vpn_name}/queues/{queue_safe}/subscriptions"
            resp = semp_h.http_post (semp_queue_sub_config_url, data)
            if resp == 'OK':
                log.status (f'Subscription for Topic {topic} created')
            elif resp == 'ALREADY_EXISTS':
                log.warning (f'Subscription for Topic {topic} exists.')
            else:
                log.error (f'Subscription for Topic {topic} failed: {resp}')
 
    #--------------------------------------------------------------------
    # add jndi queue mapping
    #--------------------------------------------------------------------
    def add_jndi_queue (self, queue_name, jndi_name):
        log.info  (f'Adding JNDI queue mapping {jndi_name} to queue {queue_name}')
        semp_h = self.semp_h
        cfg = self.cfg
        sys_cfg = cfg['system']
        msg_vpn_name = cfg['router']['vpn']
        semp_config_url = '{}/{}/msgVpns'.format(cfg['router']['sempUrl'], sys_cfg['semp']['configUrl'])
        semp_queue_config_url = f"{semp_config_url}/{msg_vpn_name}/queues"
        data = {}
        data['msgVpnName'] = msg_vpn_name
        data['physicalName'] = queue_name
        data['queueName'] = jndi_name
        # Escape special characters in topic
        #queue_safe = quote(queue_name, safe='')
        print ('\n')
        log.notice  (f"Adding JNDI queue mapping: {jndi_name} -> {queue_name}")
        semp_jndi_queue_config_url = f"{semp_config_url}/{msg_vpn_name}/jndiQueues"
        resp = semp_h.http_post (semp_jndi_queue_config_url, data)
        if resp == 'OK':
            log.status (f'JNDI for Queue {queue_name} created') 
        elif resp == 'ALREADY_EXISTS':
            log.warning (f'JNDI for Queue {queue_name} exists.')
        else:
            log.error (f'JNDI for Queue {queue_name} failed: {resp}') 
            
    def delete_jndi_queue (self, jndi_name):
        log.info  (f'Deleting JNDI queue mapping {jndi_name} to queue {jndi_name}')
        semp_h = self.semp_h
        cfg = self.cfg
        sys_cfg = cfg['system']
        msg_vpn_name = cfg['router']['vpn']
        semp_config_url = '{}/{}/msgVpns'.format(cfg['router']['sempUrl'], sys_cfg['semp']['configUrl'])
        semp_queue_config_url = f"{semp_config_url}/{msg_vpn_name}/queues"

        # Escape special characters in topic
        queue_safe = quote(jndi_name, safe='')
        print ('\n')
        log.notice  (f"Deleting JNDI queue mapping: {jndi_name}")
        semp_jndi_queue = f"{semp_config_url}/{msg_vpn_name}/jndiQueues"
        resp = semp_h.http_delete (f"{semp_jndi_queue}/{queue_safe}")
        if resp != 'OK':
            log.warning (f'Delete JNDI Queue {jndi_name} failed {resp}')
        else:
            log.status (f'JNDI Queue {jndi_name} deleted')
