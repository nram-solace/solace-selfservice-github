#####################################################################
# ClientUserConfig.py
#   Implements ClientUserName, ClientProfile and ACLProfile functions
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

class ClientUserConfig():

    def __init__(self, semp_h, cfg, verbose = 0):
        global Verbose
        global log
        Verbose = verbose
        log = cfg['log_handler'].get()
        self.semp_h = semp_h
        self.cfg = cfg

    
    #--------------------------------------------------------------------
    # create_client_usernames
    # Create Queues with http post. This does NOT patch existing queues
    #--------------------------------------------------------------------
    def create_client_usernames (self, input_data_list):

        semp_h = self.semp_h
        cfg = self.cfg
        sys_cfg = cfg['system']
        msg_vpn_name = cfg['router']['vpn']
        
        print ('\n')
        log.notice ('Creating Client Usernames')
        log.info ('Creating Client Usernames in VPN: {} on router: {}'.format(msg_vpn_name, cfg['router']['sempUrl']))
        semp_config_url = '{}/{}/msgVpns'.format(cfg['router']['sempUrl'], sys_cfg['semp']['configUrl'])
        my_semp_config_url = f"{semp_config_url}/{msg_vpn_name}/clientUsernames"
        
        num_entries = len(input_data_list)
        log.notice ('Creating {} Client Usernames on {}'.format(num_entries, msg_vpn_name))
        my_props = []
        # get list of tags from Cfg['queue']
        for k in cfg['defaults']['client-user']:
            my_props.append(k)
        # add required tags
        my_props.append('clientUsername')
        #queue_props.append('msgVpnName')
        if Verbose > 2:
            print ('Tags:', my_props)    
        n = 0
        for input_data in input_data_list:
            n += 1
            entry_name = input_data['clientUsername']
            semp_data=cfg['defaults']['client-user'].copy()
            # add required missing params
            semp_data['clientUsername'] = entry_name
            semp_data['msgVpnName'] = msg_vpn_name
            # copy the rest of the params from the input data
            for k in input_data:
                semp_data[k] = input_data[k]
            log.info ('Processing Client username: {}'.format(entry_name))

            ###################################################
            # post to router
            #
            print ('\n')
            log.notice (f"Creating Client username {n}/{num_entries}: {entry_name}")
            resp = semp_h.http_post (my_semp_config_url, semp_data)
            if resp == 'OK':
                log.status (f'Client User {entry_name} created')
            elif resp == 'ALREADY_EXISTS':
                log.warning (f'Client User {entry_name} exists.')
            else:
                log.error (f'Client User {entry_name} create failed with {resp}')


    #--------------------------------------------------------------------
    # delete_client_usernames
    # Delete Client Usernames with http delete. This does NOT patch existing queues
    #--------------------------------------------------------------------
    def delete_client_usernames (self, input_data_list):

        semp_h = self.semp_h
        cfg = self.cfg
        sys_cfg = cfg['system']
        msg_vpn_name = cfg['router']['vpn']
        
        log.info ('Deleting Client Usernames in VPN: {} on router: {}'.format(msg_vpn_name, cfg['router']['sempUrl']))
        semp_config_url = '{}/{}/msgVpns'.format(cfg['router']['sempUrl'], sys_cfg['semp']['configUrl'])
        my_semp_config_url = f"{semp_config_url}/{msg_vpn_name}/clientUsernames"
        
        num_entries = len(input_data_list)
        log.notice ('Deleting {} Client Usernames on {}'.format(num_entries, msg_vpn_name))
        my_props = []
        # get list of tags from Cfg['queue']
        for k in cfg['defaults']['client-user']:
            my_props.append(k)
        # add required tags
        my_props.append('clientUsername')
        #queue_props.append('msgVpnName')
        if Verbose > 2:
            print ('Tags:', my_props)    
        n = 0
        for input_data in input_data_list:
            n += 1
            entry_name = input_data['clientUsername']
            semp_data=cfg['defaults']['client-user'].copy()
            # add required missing params
            semp_data['clientUsername'] = entry_name
            semp_data['msgVpnName'] = msg_vpn_name
            # copy the rest of the params from the input data
            for k in input_data:
                semp_data[k] = input_data[k]
            log.info ('Processing Client username: {}'.format(entry_name))

            ###################################################
            # post to router
            #
            print ('\n')
            log.notice (f"Deleting Client username {n}/{num_entries}: {entry_name}")
            resp = semp_h.http_delete (f'{my_semp_config_url}/{entry_name}')
            if resp != 'OK':
                log.warning (f'Delete Client User {entry_name} failed {resp}')
            else:
                log.status (f'Client User {entry_name} deleted')
                
    #--------------------------------------------------------------------
    # create_acl_profiles
    # Create ACL Profiles with http post. This does NOT patch existing queues
    #--------------------------------------------------------------------
    def create_acl_profiles (self, input_data_list):
        print ('\n')
        log.notice ('Creating ACL Profiles')
        semp_h = self.semp_h
        cfg = self.cfg
        sys_cfg = cfg['system']
        msg_vpn_name = cfg['router']['vpn']
        log.info ('Creating ACL Profiles in VPN: {} on router: {}'.format(msg_vpn_name, cfg['router']['sempUrl']))
        semp_config_url = '{}/{}/msgVpns'.format(cfg['router']['sempUrl'], sys_cfg['semp']['configUrl'])
        my_semp_config_url = f"{semp_config_url}/{msg_vpn_name}/aclProfiles"
        
        num_entries = len(input_data_list)
        log.notice ('Creating {} ACL Profiles on {}'.format(num_entries, msg_vpn_name))
        my_props = []
        # get list of tags from Cfg['xxx']
        for k in cfg['defaults']['acl-profile']:
            my_props.append(k)
        # add required tags
        my_props.append('aclProfileName')
        #queue_props.append('msgVpnName')
        if Verbose > 2:
            print ('Tags:', my_props)
        n = 0
        
        for input_data in input_data_list:
            n += 1
            entry_name = input_data['aclProfileName']
            semp_data=cfg['defaults']['acl-profile'].copy()

            # add required missing params
            semp_data['aclProfileName'] = entry_name
            semp_data['msgVpnName'] = msg_vpn_name
            # copy the rest of the params from the input data
            for k in input_data:
                # drop the clientConnectExceptions, pubsubExceptions, and topicExceptions
                if k in ['clientConnectExceptions', 'publishTopicExceptions', 'subscribeTopicExceptions']:
                    continue
                semp_data[k] = input_data[k]
            log.info ('Processing ACL Profile: {}'.format(entry_name))

            ###################################################
            # post to router
            #
            print ('\n')
            log.notice (f"Creating ACL Profile {n}/{num_entries}: {entry_name}")
            resp = semp_h.http_post (my_semp_config_url, semp_data)
            if resp == 'OK':
                log.status (f'ACL Profile {entry_name} created')
            elif resp == 'ALREADY_EXISTS':
                log.warning (f'ACL Profile {entry_name} exists.')
            else:
                log.error (f'ACL Profile {entry_name} create failed with {resp}')
                return False
            
            # process exceptions
            if 'clientConnectExceptions' in input_data:
                self.add_client_connect_exceptions (entry_name, input_data['clientConnectExceptions'])
            if 'publishTopicExceptions' in input_data:
                self.add_publish_topic_exceptions (entry_name, input_data['publishTopicExceptions'])
            if 'subscribeTopicExceptions' in input_data:
                self.add_subscribe_topic_exceptions (entry_name, input_data['subscribeTopicExceptions'])
    
    def add_client_connect_exceptions (self, acl_profile_name, exp_list):
        log.info ('Adding Client Connect exceptions to ACL Profile: {}'.format(acl_profile_name))
        semp_h = self.semp_h
        cfg = self.cfg
        sys_cfg = cfg['system']
        msg_vpn_name = cfg['router']['vpn']
        semp_config_url = '{}/{}/msgVpns'.format(cfg['router']['sempUrl'], sys_cfg['semp']['configUrl'])
        my_semp_config_url = f"{semp_config_url}/{msg_vpn_name}/aclProfiles"
        n = len(exp_list)
        log.notice ('Adding {} client connect exceptions to ACL Profile: {}'.format(n, acl_profile_name))
        i = 0
        for exp in exp_list:
            i += 1
            log.info ('Adding client connect exception {}/{}: {} to {}'.format(i, n, exp, acl_profile_name))
            semp_data = {}
            semp_data['clientConnectExceptionAddress'] = exp
            semp_data['aclProfileName'] = acl_profile_name
            semp_data['msgVpnName'] = msg_vpn_name
            resp = semp_h.http_post (f'{my_semp_config_url}/{acl_profile_name}/clientConnectExceptions', semp_data)
            if resp == 'OK':
                log.status (f'Exception {exp} created')
            elif resp == 'ALREADY_EXISTS':
                log.warning (f'Exception {exp} exists.')
            else:
                log.error (f'Exception {exp} create failed with {resp}')
                return False
   
    def add_publish_topic_exceptions (self, acl_profile_name, exp_list):
        log.info ('Adding Publish Topic exceptions to ACL Profile: {}'.format(acl_profile_name))
        semp_h = self.semp_h
        cfg = self.cfg
        sys_cfg = cfg['system']
        msg_vpn_name = cfg['router']['vpn']
        semp_config_url = '{}/{}/msgVpns'.format(cfg['router']['sempUrl'], sys_cfg['semp']['configUrl'])
        my_semp_config_url = f"{semp_config_url}/{msg_vpn_name}/aclProfiles"
        n = len(exp_list)
        log.notice ('Adding {} publish topic exceptions to ACL Profile: {}'.format(n, acl_profile_name))
        i = 0
        for exp in exp_list:
            i += 1
            log.info ('Adding publish topic exception {}/{}: {} to {}'.format(i, n, exp, acl_profile_name))
            semp_data = {}
            semp_data['publishTopicException'] = exp
            semp_data['publishTopicExceptionSyntax'] = 'smf'
            semp_data['aclProfileName'] = acl_profile_name
            semp_data['msgVpnName'] = msg_vpn_name
            resp = semp_h.http_post (f'{my_semp_config_url}/{acl_profile_name}/publishTopicExceptions', semp_data)
            if resp == 'OK':
                log.status (f'Publish topic Exception {exp} created')
            elif resp == 'ALREADY_EXISTS':
                log.warning (f'Publish topic Exception {exp} exists.')
            else:
                log.error (f'Publish topic Exception {exp} create failed with {resp}')
                return False
            
    def add_subscribe_topic_exceptions (self, acl_profile_name, exp_list):
        log.info ('Adding Subscribe Topic exceptions to ACL Profile: {}'.format(acl_profile_name))
        semp_h = self.semp_h
        cfg = self.cfg
        sys_cfg = cfg['system']
        msg_vpn_name = cfg['router']['vpn']
        semp_config_url = '{}/{}/msgVpns'.format(cfg['router']['sempUrl'], sys_cfg['semp']['configUrl'])
        my_semp_config_url = f"{semp_config_url}/{msg_vpn_name}/aclProfiles"
        n = len(exp_list)
        log.notice ('Adding {} subscribe topic exceptions to ACL Profile: {}'.format(n, acl_profile_name))
        i = 0
        for exp in exp_list:
            i += 1
            log.info ('Adding subscribe topic exception {}/{}: {} to {}'.format(i, n, exp, acl_profile_name))
            semp_data = {}
            semp_data['subscribeTopicException'] = exp
            semp_data['subscribeTopicExceptionSyntax'] = 'smf'
            semp_data['aclProfileName'] = acl_profile_name
            semp_data['msgVpnName'] = msg_vpn_name
            resp = semp_h.http_post (f'{my_semp_config_url}/{acl_profile_name}/subscribeTopicExceptions', semp_data)
            if resp == 'OK':
                log.status (f'Subscribe topic Exception {exp} created')
            elif resp == 'ALREADY_EXISTS':
                log.warning (f'Subscribe topic Exception {exp} exists.')
            else:
                log.error (f'Subscribe topic Exception {exp} create failed with {resp}')
                return False  
        
    #--------------------------------------------------------------------
    # delete_acl_profiles
    # Delete ACL Profiles with http delete. This does NOT patch existing queues
    #--------------------------------------------------------------------
    def delete_acl_profiles (self, input_data_list):

        semp_h = self.semp_h
        cfg = self.cfg
        sys_cfg = cfg['system']
        msg_vpn_name = cfg['router']['vpn']
        
        log.info ('Deleting ACL Profiles in VPN: {} on router: {}'.format(msg_vpn_name, cfg['router']['sempUrl']))
        semp_config_url = '{}/{}/msgVpns'.format(cfg['router']['sempUrl'], sys_cfg['semp']['configUrl'])
        my_semp_config_url = f"{semp_config_url}/{msg_vpn_name}/aclProfiles"
        
        num_entries = len(input_data_list)
        log.notice ('Deleting {} ACL Profiles on {}'.format(num_entries, msg_vpn_name))
        my_props = []
        # get list of tags from Cfg['queue']
        for k in cfg['defaults']['acl-profile']:
            my_props.append(k)
        # add required tags
        my_props.append('aclProfileName')
        #queue_props.append('msgVpnName')
        if Verbose > 2:
            print ('Tags:', my_props)    
        n = 0
        for input_data in input_data_list:
            n += 1
            entry_name = input_data['aclProfileName']
            semp_data=cfg['defaults']['acl-profile'].copy()
            # add required missing params
            semp_data['aclProfileName'] = entry_name
            semp_data['msgVpnName'] = msg_vpn_name
            # copy the rest of the params from the input data
            for k in input_data:
                semp_data[k] = input_data[k]
            log.info ('Processing ACL Profile: {}'.format(entry_name))

            ###################################################
            # post to router
            #
            print ('\n')
            log.notice (f"Deleting ACL Profile {n}/{num_entries}: {entry_name}")
            resp = semp_h.http_delete (f'{my_semp_config_url}/{entry_name}')
            if resp != 'OK':
                log.warning (f'Delete ACL Profile {entry_name} failed {resp}')
            else:
                log.status (f'ACL Profile {entry_name} deleted')
        
    #--------------------------------------------------------------------
    # create_client_profiles
    # Create Client Profiles with http post. This does NOT patch existing queues
    #--------------------------------------------------------------------
    def create_client_profiles (self, input_data_list):
            print ('\n')
            log.notice ('Creating Client Profiles')
            semp_h = self.semp_h
            cfg = self.cfg
            sys_cfg = cfg['system']
            msg_vpn_name = cfg['router']['vpn']
            log.info ('Creating Client Profiles in VPN: {} on router: {}'.format(msg_vpn_name, cfg['router']['sempUrl']))
            semp_config_url = '{}/{}/msgVpns'.format(cfg['router']['sempUrl'], sys_cfg['semp']['configUrl'])
            my_semp_config_url = f"{semp_config_url}/{msg_vpn_name}/clientProfiles"
            
            num_entries = len(input_data_list)
            log.notice ('Creating {} Client Profiles on {}'.format(num_entries, msg_vpn_name))
            my_props = []
            # get list of tags from Cfg['queue']
            for k in cfg['defaults']['client-profile']:
                my_props.append(k)
            # add required tags
            my_props.append('clientProfileName')
            #queue_props.append('msgVpnName')
            if Verbose > 2:
                print ('Tags:', my_props)
            n = 0
            
            for input_data in input_data_list:
                n += 1
                entry_name = input_data['clientProfileName']
                semp_data=cfg['defaults']['client-profile'].copy()
                # add required missing params
                semp_data['clientProfileName'] = entry_name
                semp_data['msgVpnName'] = msg_vpn_name
                # copy the rest of the params from the input data
                for k in input_data:
                    semp_data[k] = input_data[k]
                log.info ('Processing Client Profile: {}'.format(entry_name))
    
                ###################################################
                # post to router
                #
                print ('\n')
                log.notice (f"Creating Client Profile {n}/{num_entries}: {entry_name}")
                resp = semp_h.http_post (my_semp_config_url, semp_data)
                if resp == 'OK':
                    log.status (f'Client Profile {entry_name} created')
                elif resp == 'ALREADY_EXISTS':
                    log.warning (f'Client Profile {entry_name} exists.')
                else:
                    log.error (f'Client Profile {entry_name} create failed with {resp}')


                
    #--------------------------------------------------------------------
    # delete_client_profiles
    # Delete Client Profiles with http delete. This does NOT patch existing queues
    #--------------------------------------------------------------------
    def delete_client_profiles (self, input_data_list):

        semp_h = self.semp_h
        cfg = self.cfg
        sys_cfg = cfg['system']
        msg_vpn_name = cfg['router']['vpn']
        
        log.info ('Deleting Client Profiles in VPN: {} on router: {}'.format(msg_vpn_name, cfg['router']['sempUrl']))
        semp_config_url = '{}/{}/msgVpns'.format(cfg['router']['sempUrl'], sys_cfg['semp']['configUrl'])
        my_semp_config_url = f"{semp_config_url}/{msg_vpn_name}/clientProfiles"
        
        num_entries = len(input_data_list)
        log.notice ('Deleting {} Client Profiles on {}'.format(num_entries, msg_vpn_name))
        my_props = []
        # get list of tags from Cfg['queue']
        for k in cfg['defaults']['client-profile']:
            my_props.append(k)
        # add required tags
        my_props.append('clientProfileName')
        #queue_props.append('msgVpnName')
        if Verbose > 2:
            print ('Tags:', my_props)    
        n = 0
        for input_data in input_data_list:
            n += 1
            entry_name = input_data['clientProfileName']
            semp_data=cfg['defaults']['client-profile'].copy()
            # add required missing params
            semp_data['clientProfileName'] = entry_name
            semp_data['msgVpnName'] = msg_vpn_name
            # copy the rest of the params from the input data
            for k in input_data:
                semp_data[k] = input_data[k]
            log.info ('Processing Client Profile: {}'.format(entry_name))

            ###################################################
            # post to router
            #
            print ('\n')
            log.notice (f"Deleting Client Profile {n}/{num_entries}: {entry_name}")
            resp = semp_h.http_delete (f'{my_semp_config_url}/{entry_name}')
            if resp != 'OK':
                log.warning (f'Delete Client Profile {entry_name} returned {resp}')
            else:
                log.status (f'Client Profile {entry_name} deleted')