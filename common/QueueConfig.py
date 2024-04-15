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

    def __init__(self, semp_h, cfg, input_data, verbose = 0):
        global Verbose
        global log
        Verbose = verbose
        log = cfg['log_handler'].get()
        self.semp_h = semp_h
        self.cfg = cfg
        self.input_data = input_data
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
            queue = q_data['queue']
            semp_data=cfg['templates']['queue'].copy()
            # add required missing params
            semp_data['queueName'] = queue
            semp_data['msgVpnName'] = msg_vpn_name
            log.info ('Processing queue: {}'.format(queue))

            ###################################################
            # post to router - create queue
            #
            log.notice (f"Creating queue subscriptions {n}/{num_queues}: {queue}")
            if 'subscriptions' in q_data:
                self.add_topic_subscriptions(queue, q_data['subscriptions'])       
        
    #--------------------------------------------------------------------
    # create_queues
    # Create Queues with http post. This does NOT patch existing queues
    #--------------------------------------------------------------------
    def create_queues (self, input_data, add_subscriptions = False):

        semp_h = self.semp_h
        cfg = self.cfg
        sys_cfg = cfg['system']
        msg_vpn_name = cfg['router']['vpn']
        
        log.info ('Creating Queues in VPN: {} on router: {}'.format(msg_vpn_name, cfg['router']['sempUrl']))
        semp_config_url = '{}/{}/msgVpns'.format(cfg['router']['sempUrl'], sys_cfg['semp']['configUrl'])
        semp_queue_config_url = f"{semp_config_url}/{msg_vpn_name}/queues"
        
        num_queues = len(input_data)
        log.notice ('Creating {} Queues on {}'.format(num_queues, msg_vpn_name))
        queue_props = []
        # get list of tags from Cfg['queue']
        for k in cfg['templates']['queue']:
            queue_props.append(k)
        # add required tags
        queue_props.append('queueName')
        #queue_props.append('msgVpnName')
        if Verbose > 2:
            print ('Tags:', queue_props)    
        n = 0
        for q_data in input_data:
            n += 1
            queue = q_data['queue']
            semp_data=cfg['templates']['queue'].copy()
            # add required missing params
            semp_data['queueName'] = queue
            semp_data['msgVpnName'] = msg_vpn_name
            log.info ('Processing queue: {}'.format(queue))

            # enable queues
            semp_data['egressEnabled'] = True
            semp_data['ingressEnabled'] = True

            ###################################################
            # post to router - create queue
            #
            log.notice (f"Creating queue {n}/{num_queues}: {queue}")
            resp = semp_h.http_post (semp_queue_config_url, semp_data)
            if resp == 'ALREADY_EXISTS':
                log.info (f'Queue {queue} exists. Skipping')
            else:
                log.info (f'Queue {queue} created')
            if add_subscriptions and 'subscriptions' in q_data:
                self.add_topic_subscriptions(queue, q_data['subscriptions'])
                    
 
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
            log.notice  (f"Adding subscription topic {n}/{max_n}: {topic} - {queue_name}")
            semp_queue_sub_config_url = f"{semp_config_url}/{msg_vpn_name}/queues/{queue_safe}/subscriptions"
            semp_h.http_post (semp_queue_sub_config_url, data)
 

    #--------------------------------------------------------------------
    # create_or_update_queues
    # Create Queues with http post
    # If queue exists (http_post retunred ALREADY_EXISTS)
    #    disable it
    #    update using http_patch and enable it
    #  Add topic subscriptions list to queue
    #  In patch mode, remove existing subscriptions and reapply new
    #--------------------------------------------------------------------
    def create_or_update_queue_unused (self, input_data, patch_it):

        semp_h = self.semp_h
        cfg = self.cfg
        sys_cfg = cfg['system']
        #input_data = self.input_data
        
        log.notice  ('Creating Queues')
        
        msg_vpn_name = cfg['router']['vpn']
        if patch_it:
            log.info ('Patching Queues in VPN: {} on router: {}'.format(msg_vpn_name, cfg['router']['sempUrl']))
        else:
            log.info ('Creating Queues in VPN: {} on router: {}'.format(msg_vpn_name, cfg['router']['sempUrl']))

        # Loop through each row and generate obj for SEMP Req
        semp_config_url = '{}/{}/msgVpns'.format(cfg['router']['sempUrl'], sys_cfg['semp']['configUrl'])
        semp_queue_config_url = f"{semp_config_url}/{msg_vpn_name}/queues"
        num_queues = len(input_data)
        log.notice ('Number of queues: {}'.format(num_queues))
        n = 0

        queue_props = []
        # get list of tags from Cfg['queue']
        for k in cfg['templates']['queue']:
            queue_props.append(k)
        # add required tags
        queue_props.append('queueName')
        #queue_props.append('msgVpnName')
        if Verbose > 2:
            print ('Tags:', queue_props)    
        
        for qname in input_data:
            n = n + 1
            #print ('data read', d)
            #print (f"VPN name: [{d['msgVpnName']}]")
            data=cfg['templates']['queue'].copy()
            # add required missing params
            data['queueName'] = qname
            data['msgVpnName'] = msg_vpn_name
            log.info ('Processing queue: {} (Patch: {})'.format(qname, patch_it))

            # enable queues
            data['egressEnabled'] = True
            data['ingressEnabled'] = True
            #if Verbose > 2:
            #    print ('data enhanced'); pp.pprint(data)
            # remove subscriptionTopic
            sub_topic_saved = data['subscriptionTopic']
            data.pop('subscriptionTopic', None)
            ###################################################
            # post to router - create queue
            #
            log.notice (f"Creating queue: {qname} ({n}/{num_queues})")
            resp = semp_h.http_post (semp_queue_config_url, data)
            if patch_it and resp == 'ALREADY_EXISTS':
                #---------------------------------------------------
                # If Queue exists, patch it
                #
                log.info (f'Queue {qname} exists. Disable and patch it')
                # disable queue first
                data0 = {}
                data0['queueName'] = qname
                data0['msgVpnName'] = msg_vpn_name
                data0['egressEnabled'] = False
                #data0['ingressEnabled'] = False
                semp_h.http_patch (f"{semp_queue_config_url}/{qname}", data0)
                # Patch with new values and enable
                semp_h.http_patch (f"{semp_queue_config_url}/{qname}", data)

            if patch_it:
                # remove subscriptions first
                log.info (f'Reapplying subscriptions on Queue {qname} (PATCH)')
                semp_queue_sub_config_url = f"{semp_config_url}/{msg_vpn_name}/queues/{qname}/subscriptions"
                resp = semp_h.http_get(semp_queue_sub_config_url)
                for topic in self.get_topic_list (resp):
                    log.info (f'Deleting subscription topic: [{topic}]')
                    semp_queue_sub_delete_url = f"{semp_config_url}/{msg_vpn_name}/queues/{qname}/subscriptions/{quote(topic, safe='')}"
                    log.info(f'SEMP post url: {semp_queue_sub_delete_url}')
                    semp_h.http_delete (semp_queue_sub_delete_url)
            # now add subscription topics
            for topics in sub_topic_saved.split(':'):
                topic = topics.strip()
                if topic != "":
                    data = {}
                    data['msgVpnName'] = msg_vpn_name
                    data['queueName'] = qname
                    data['subscriptionTopic'] = topic
                    log.info (f'Adding subscription topic: [{topic}] on queue {qname}')
                    semp_queue_sub_config_url = f"{semp_config_url}/{msg_vpn_name}/queues/{qname}/subscriptions"
                    semp_h.http_post (semp_queue_sub_config_url, data)


    #--------------------------------------------------------------------
    # create_or_update_dmqueue
    # Special handling or DMQ. 
    # Get list of deadMsgQueue from input file and create them 
    # All of them are created with same properties (cfg['templates']['dmqueue'])
    # No subscriptions are supported for DMQ. 
    # If you really want a DMQ with override properties / subscriptions, 
    # then provision it as a regular queue
    #--------------------------------------------------------------------
    def create_or_update_dmqueue_unused (self, patch_it):

        semp_h = self.semp_h
        cfg = self.cfg
        sys_cfg = cfg['system']
        input_df = self.input_df
        if patch_it:
            log.info ('Patching DMQueues in VPN: {} on router: {}'.format(cfg['vpn']['msgVpnNames'][0], cfg['router']['sempUrl'])) 
        else:
            log.info ('Creating DMQueues in VPN: {} on router: {}'.format(cfg['vpn']['msgVpnNames'][0], cfg['router']['sempUrl']))

        # Loop through each row and generate obj for SEMP Req
        msg_vpn_name = cfg['vpn']['msgVpnNames'][0]
        semp_config_url = '{}/{}/msgVpns'.format(cfg['router']['sempUrl'], sys_cfg['semp']['configUrl'])
        semp_queue_config_url = f"{semp_config_url}/{msg_vpn_name}/queues"
        num_queues = len(input_df.index)
        n = 0

        queue_props = []
        # get list of tags from Cfg['queue']
        for k in cfg['templates']['dmqueue']:
            queue_props.append(k)
        # add required tags
        queue_props.append('deadMsgQueue')
        #queue_props.append('msgVpnName')
        if Verbose > 2:
            print ('Tags:', queue_props)
        
        for index, qdata in input_df.iterrows():
            n = n + 1
            #print ('data read', d)
            #print (f"VPN name: [{d['msgVpnName']}]")
            data={}
            data=cfg['templates']['dmqueue'].copy()
            #data['messageVpn'] = msg_vpn_name
            queue = qdata['queueName'].strip()
            log.info ('Processing DMQ queue: {} (Patch: {})'.format(queue, patch_it))

            # enable queues
            data['egressEnabled'] = True
            data['ingressEnabled'] = True
            data['msgVpnName'] = msg_vpn_name
            data['queueName'] = queue
            data.pop('subscriptionTopic', None)

            ###################################################
            # post to router - create queue
            #
            print (f"\n{n:2}/{num_queues:3} ) Creating queue: <{queue}>")
            resp = semp_h.http_post (semp_queue_config_url, data)
            if patch_it and resp == 'ALREADY_EXISTS':
                #---------------------------------------------------
                # If Queue exists, patch it
                #
                log.info (f'Queue {queue} exists. Disable and patch it')

                # Patch with new values and enable
                semp_h.http_patch (f"{semp_queue_config_url}/{queue}", data)
                
                

                    
    #--------------------------------------------------------------------
    # add_topic_subscriptions
    # Add topic subscriptions to queues
    #--------------------------------------------------------------------
               
    def add_topic_subscriptions_unused(self, input_data):
        log.notice  ('Adding topic subscriptions to queues')
        semp_h = self.semp_h
        cfg = self.cfg
        sys_cfg = cfg['system']
        msg_vpn_name = cfg['router']['vpn']
        semp_config_url = '{}/{}/msgVpns'.format(cfg['router']['sempUrl'], sys_cfg['semp']['configUrl'])
        semp_queue_config_url = f"{semp_config_url}/{msg_vpn_name}/queues"
        num_queues = len(input_data)
        for data in input_data:
            queue = data['queue']
            sub_topics = data['subscriptions']
            log.info ('Processing queue: {}'.format(queue))
            # now add subscription topics
            for topics in sub_topics:
                topic = topics.strip()
                data = {}
                data['msgVpnName'] = msg_vpn_name
                data['queueName'] = queue
                data['subscriptionTopic'] = topic
                log.info (f'Adding subscription topic: [{topic}] on queue {queue}')
                # Escape special characters in topic
                queue_safe = quote(queue, safe='')
                log.notice  ("Adding subscription topic: {} - {}".format(queue, topic))
                semp_queue_sub_config_url = f"{semp_config_url}/{msg_vpn_name}/queues/{queue_safe}/subscriptions"
                semp_h.http_post (semp_queue_sub_config_url, data)