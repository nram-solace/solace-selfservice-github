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
            if resp == 'ALREADY_EXISTS':
                log.info (f'Client User {entry_name} exists. Skipping')
            else:
                log.info (f'Client User {entry_name} created')


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
            if resp != '200':
                log.warning (f'Delete Client User {entry_name} returned {resp}')
            else:
                log.info (f'Client User {entry_name} deleted')
                
    #--------------------------------------------------------------------
    # create_acl_profiles
    # Create ACL Profiles with http post. This does NOT patch existing queues
    #--------------------------------------------------------------------
    def create_acl_profiles (self, input_data_list):
        
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
                semp_data[k] = input_data[k]
            log.info ('Processing ACL Profile: {}'.format(entry_name))

            ###################################################
            # post to router
            #
            print ('\n')
            log.notice (f"Creating ACL Profile {n}/{num_entries}: {entry_name}")
            resp = semp_h.http_post (my_semp_config_url, semp_data)
            if resp == 'ALREADY_EXISTS':
                log.info (f'ACL Profile {entry_name} exists. Skipping')
            else:
                log.info (f'ACL Profile {entry_name} created')
                
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
                log.warning (f'Delete ACL Profile {entry_name} returned {resp}')
            else:
                log.info (f'ACL Profile {entry_name} deleted')
        
    #--------------------------------------------------------------------
    # create_client_profiles
    # Create Client Profiles with http post. This does NOT patch existing queues
    #--------------------------------------------------------------------
    def create_client_profiles (self, input_data_list):
            
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
                if resp == 'ALREADY_EXISTS':
                    log.info (f'Client Profile {entry_name} exists. Skipping')
                else:
                    log.info (f'Client Profile {entry_name} created')


                
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
                log.info (f'Client Profile {entry_name} deleted')