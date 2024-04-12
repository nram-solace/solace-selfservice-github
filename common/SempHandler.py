##############################################################################
# SempHandler
#   SEMPv2 protocol handler
#   Supports GET, POST, PATCH, PUT, DELETE
#   
# Ramesh Natarajan (nram), Solace PSG (ramesh.natarajan@solace.com)
##############################################################################

import sys, os, inspect
import pprint
import json
import requests
from requests.auth import HTTPBasicAuth
from urllib.parse import unquote # for Python 3.7

sys.path.insert(0, os.path.abspath("."))
from common import JsonHandler
from collections import defaultdict

pp = pprint.PrettyPrinter(indent=4)
Verbose = 0
Cfg = {}
json_h = None
log = None
Stats = {'get': 0, 'post': 0, 'patch': 0, 'delete': 0 }

#-----------------------------------------------------------------------
# Object to convert custom json to python object
# Used in returning prematurely from semp_apply
# This mimics the json object structure in HTTP response
class DummyResponse:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if isinstance(value, dict):
                setattr(self, key, DummyResponse(**value))
            else:
                setattr(self, key, value)

class SempHandler:
    """ Solace SEMPv2 Parser implementation """
    
    def __init__(self, cfg, vpn="default", outdir = "output/default", verbose = 0):
        global Verbose, Cfg, log, json_h
        Verbose = verbose
        log = cfg['log_handler'].get()
        Cfg = cfg
        json_h = JsonHandler.JsonHandler(Cfg)

        self.vpn = vpn
        self.out_dir = outdir


    #-------------------------------------------------------------  
    # http_get
    #  
    def http_get(self, url, params=None):
        global Stats
        log.enter ("Entering {}:{} url: {} params: {}".format( __class__.__name__, inspect.stack()[0][3], url, params))

        Stats['get'] += 1
        n = Stats['get']

        log.info  (f'GET URL ({n}): {url}')
        verb = 'get'
        semp_user = Cfg["router"]["sempUser"]
        semp_pass = Cfg["router"]["sempPassword"]
        hdrs = {"content-type": "application/json"}
        auth = HTTPBasicAuth(semp_user, semp_pass)
        if params:
            resp = getattr(requests, verb)(url, 
                headers=hdrs,
                auth=auth,
                params=params,
                data=None,
                verify=True)
        else:
            resp = getattr(requests, verb)(url, 
                headers=hdrs,
                auth=auth,
                data=None,
                verify=True)
        #log.info ('SEMP GET returned: {}'.format(resp))
        #log.info ('SEMP GET returned: {}'.format(json.dump(resp, indent=4, sort_keys=True)))
        log.info ('http_get {} returned:\n{}'.format(url,resp))
        #log.trace ('http_get returned: {}'.format(json.dumps(resp, indent=4)))
        log.trace ('http_get returned: {}'.format(resp))


        return resp

    #-------------------------------------------------------------  
    # http_post
    #
    def http_post(self, url, json_data):
        log.enter ("Entering {}:{} url = {}".format( __class__.__name__, inspect.stack()[0][3], url))
        log.info('SEMP POST url: {}'.format(url))
        log.info ('SEMP posting json-data: {}'.format (json.dumps(json_data, indent=4, sort_keys=True)))
        verb = 'post'
        semp_user = Cfg["router"]["sempUser"]
        semp_pass = Cfg["router"]["sempPassword"]
        resp = getattr(requests, verb)(url, 
            headers={"content-type": "application/json"},
            auth=(semp_user, semp_pass),
            data=(json.dumps(json_data) if json_data != None else None),
            verify=True)
        log.trace ('http_post resp : {}'.format(resp))
        log.trace ("resp text : {}".format(resp.text))
        json_resp = json.loads(resp.text)

        log.info ('SEMP POST returned: {}'.format(json.dumps(json_resp, indent=4, sort_keys=True)))

        if json_resp['meta']['responseCode'] == 200:
            log.debug (' http_post returned {}'. format(json_resp['meta']['responseCode']))
            return "OK"          
        else:
            log.error  ("http_post returned {} ({})".format(json_resp['meta']['responseCode'],
                                            json_resp['meta']['error']['status']))
            log.debug (json_resp['meta']['error']['description'])
            return json_resp['meta']['error']['status']

        #return resp
    
    #-------------------------------------------------------------  
    # http_patch
    #
    def http_patch (self, url, json_data):
        log.enter ("Entering {}:{} url = {}".format( __class__.__name__, inspect.stack()[0][3], url))
        log.info('SEMP PATCH url: {}'.format(url))
        log.info ('SEMP patching json-data: {}'.format(json.dumps(json_data, indent=4, sort_keys=True)))
        log.trace ('patching json-data:\n', json.dumps(json_data, indent=4, sort_keys=True))

        verb = 'patch'
        semp_user = Cfg["router"]["sempUser"]
        semp_pass = Cfg["router"]["sempPassword"]
        resp = getattr(requests, verb)(url, 
            headers={"content-type": "application/json"},
            auth=(semp_user, semp_pass),
            data=(json.dumps(json_data) if json_data != None else None),
            verify=False)
        log.trace ('http_patch resp : {}'.format(resp))
        log.trace ("resp text : {}".format(resp.text))
        json_resp = json.loads(resp.text)

        #log.info ('SEMP PATCH returned: {}'.format(json_resp))

        log.info ('SEMP PATCH returned: {}'.format(json.dumps(json_resp, indent=4, sort_keys=True)))

        if json_resp['meta']['responseCode'] == 200:
            log.debug (' http_patch returned ', json_resp['meta']['responseCode'])            
        else:
            log.debug ("         http_patch returned {} ({}) : {}".format(json_resp['meta']['responseCode'],
                                                          json_resp['meta']['error']['status'],
                                                          json_resp['meta']['error']['description']))

        return resp
    
    #-------------------------------------------------------------  
    # http_put
    #
    def http_put(self, url, json_data):
        log.enter ("Entering {}:{} url = {}".format( __class__.__name__, inspect.stack()[0][3], url))
        log.info('SEMP PUT url: {}'.format(url))
        log.info('SEMP putting json-data: {}'.format(json.dumps(json_data, indent=4, sort_keys=True)))
        log.trace ('posting json-data:\n', json.dumps(json_data, indent=4, sort_keys=True))
        verb = 'put'
        semp_user = Cfg["router"]["sempUser"]
        semp_pass = Cfg["router"]["sempPassword"]
        resp = getattr(requests, verb)(url, 
            headers={"content-type": "application/json"},
            auth=(semp_user, semp_pass),
            data=(json.dumps(json_data) if json_data != None else None),
            verify=True)
        
        #log.info ('SEMP PUT returned: {}'.format(json.dump(resp.json(), indent=4, sort_keys=True)))
        log.info ('SEMP PUT returned: {}'.format(resp.json()))

        log.enter ('http_put returning : {}'.format(resp))
        return resp
    
    #-------------------------------------------------------------  
    # http_delete
    #
    def http_delete (self, url):
        log.enter ("Entering {}:{} url = {}".format( __class__.__name__, inspect.stack()[0][3], url))
        ignore_status = ['INVALID_PATH']


        semp_user = Cfg["router"]["sempUser"]
        semp_pass = Cfg["router"]["sempPassword"]
        
        log.info('SEMP DELETE url: {}'.format(url))

        log.debug ("   DELETE URL {} ({})".format(unquote(url), semp_user))
   
        resp = requests.delete(url, 
            headers={"content-type": "application/json"},
            auth=(semp_user, semp_pass),
            data=(None),
            verify=False)
        
        log.info ('SEMP DELETE returned: {}'.format(resp))
        log.debug ('http_delete returning : {}'.format(json.dump(resp.json(), indent=4, sort_keys=True)))
        log.trace ('Response:\n%s',resp.json())
        if (resp.status_code != 200):
            log.error ('Non-200 Response text: {}'.format(resp.text))
            status = resp.json()['meta']['error']['status']
            desc = resp.json()['meta']['error']['description']

            if status in ignore_status:
                log.notice (f'Ignoring non success status {status}')
        return resp
    
    #-------------------------------------------------------------
    # Higher order functions for get
    #-------------------------------------------------------------

    def get_vpn_config_json (self, url):
        """ get vpn config json """
        log.enter ("Entering {}::{}  file: {}". format (__class__.__name__, inspect.stack()[0][3], url))

        return self.get_config_json(url)

    def get_config_json (self, url, collections=False, paging=True):
        """ get vpn object config json """
        log.enter ('Entering {}::{} url = {}'.format(__class__.__name__, inspect.stack()[0][3], url))
        verb='get'

        sys_cfg = Cfg['system']
        page_size = sys_cfg["semp"]["pageSize"]
        no_paging = sys_cfg["semp"]["noPaging"]

        u_url = unquote(url)
        if collections:
            if int(page_size) == 0:
                paging = False
            # some elements throw 400 not supported if page count is sent
            if os.path.split(url)[1] in no_paging:
                paging = False
                log.debug ("Skipping paging for element {}".format(os.path.split(u_url)[1]))
            if paging :
                log.debug ("   Get URL {} [{}] (*)".format(u_url, page_size))
                params = {'count':page_size}
                resp = self.http_get(url, params)
            else:
                log.debug ("   Get URL {} (*)".format(u_url))
                resp = self.http_get(url)
        else:
            # No paging for non-collection objects
            log.debug ("   Get URL {}".format(u_url))
            resp = self.http_get(url) 

            log.trace ("Get: req.json(): {}".format(resp.json()))
        if (resp.status_code != 200):
            log.warn (f'Unable to parse URL {u_url}. Skipping')
            log.debug (resp.text)
            return resp.json()

            #raise RuntimeError
        else:
            return resp.json()

    def process_page_links (self, json_data):
        """ given json data, traverse thur all links in meta section 
            calls itself recursively  
        """
        log.enter ("Entering {}::{}".format( __class__.__name__, inspect.stack()[0][3]))
        log.trace (json_data)

        if 'links' not in json_data:
            log.debug ("No Links")
            return

        if type(json_data['links']) is list:
            for link_list in json_data['links']:
                link_keys = list(link_list.keys())
                #print ("   got {:d} link-lists: {:s}". format(len(lkeys), lkeys))
                if 'uri' in link_keys:
                    link_keys.remove('uri') 
                if len(link_keys) == 0 :
                    log.trace ("No non-uri links in list")
                    return       
                #print ("   processing {:d} links: {:s}".format(len(lkeys), lkeys))
                for l in link_keys:
                    lurl = link_list[l]
                    link_data = self.get_link_data (lurl, True)
                    self.process_page_links(link_data)
        else:
            link_keys = list(json_data['links'].keys())
            #print ("   got {:d} links: {:s}". format(len(lkeys), lkeys))
            if 'uri' in link_keys:
                link_keys.remove('uri') 
            if len(link_keys) == 0 :
                log.trace ("No non-uri links in non-list")
                return       
            #print ("   processing {:d} links: {:s}".format(len(lkeys), lkeys))
            for link_key in link_keys:
                link_url = json_data['links'][link_key]
                link_data = self.get_link_data (link_url, True)
                self.process_page_links (link_data)

    def get_link_data (self, url, collection, paging=True, follow_links=True):
        """ process one link url, calls get_config_json() & save_config_json """

        log.enter ("Entering {}::{} url = {}, collection = {}, links = {}".format( __class__.__name__, inspect.stack()[0][3], url, collection, follow_links))
        #ph,obj = os.path.split(url)

        #path=url[url.find('/msgVpns/')+8:]
        #if path.rfind('?')>0:
        #    path=path[:path.rfind('?')]
        #_,obj = os.path.split(path)
        #path=urllib.parse.unquote(path)

        p = url.partition(self.vpn)
        path=p[2]
        if path.rfind('?')>0:
            path=path[:path.rfind('?')]
        _,obj = os.path.split(path)
        #print (f'p: {p}')
        #print (f'old url: {url} path: {path} obj: {obj}')

        log.debug ("Processing link {}".format(url))  
        json_data = self.get_config_json (url, collection, paging)

        # Write data to file
        fname = json_h.get_unique_fname(path, obj)
        log.trace ('fname: {} path: {} outdir: {}'.format(fname, path, self.out_dir))
        outfile = '{}/{}/{}'.format(self.out_dir,path,fname)

        log.debug ("Save json to file: {}".format (outfile))
        json_h.save_config_json (outfile, json_data )

        # Process meta - look for cursor/paging
        meta_data = json_data['meta']
        if 'paging' in meta_data:
            log.trace  ("paging : {}".format(meta_data['paging']))
            next_page_uri = meta_data['paging']['nextPageUri']
            log.debug ("Processing Next Page URI : %s", unquote(next_page_uri))
            # process nextPageUri - recursively
            next_page_data = self.get_link_data (next_page_uri, False, False, follow_links) # don't use collection for nextPage
                                                                        # don't add page count either. Its part of nextPage URL already
            # for next-page-uri, call parent process_page_links() *** deep recursion ***
            self.process_page_links (next_page_data)
            #why wouldn't you follow links ???
            #if follow_links:
            #    if Verbose > 1:
            #        print ('following links')
            #    self.process_page_links (json_data)
            #else:
            #    print ('follow-links is off. Not following the link')
        else:
            log.debug ('No paging in meta-data')
        return json_data
    
    def print_stats(self):
        log.notice ("SEMP Stats:")
        for k,v in Stats.items():
            log.notice("{:>20} : {}".format(k, v))
            
            
    #-------------------------------------------------------------
    # Higher order functions for apply
    #-------------------------------------------------------------
    
    #--------------------------------------------------------------------
    # semp_apply
    #   process semp post from top level (vpn.json)
    #   and calls itself recursively for child objects and links
    #
    def semp_apply (self, url, obj, path, json_data=None, links=None, next_page_uri=None) :
        """ post semp to broker - mostly calls other helper functions """

        log.enter ("Entering {}::{} url = {} obj = {} path = {}".format( __class__.__name__, inspect.stack()[0][3], url, obj, path))

        sys_cfg = Cfg['system']

        if type(json_data) is list:
            log.debug ('json_data is list')
            for json_data_e in json_data:
                resp = self.apply_json(url, json_data_e)
                log.debug ('semp-apply : list post returned {}'.format(resp))

        else:
            log.debug('semp-apply: json_data is obj')
            resp = self.apply_json(url, json_data)
            log.debug ('resp: ({}) {}'.format(type(resp), resp))
            log.debug ('semp-apply: obj post returned {}'.format(resp))

        # We are done posting with json_data
        # loop thru link and Post recursively
        if links:
            log.debug ("semp-apply: Processing Links ", json.dumps(links, indent=2))
            if type(links) is list:
                for link in links:
                    self.apply_links (url, obj,path, link)
            else:
                self.apply_links (url, obj, path, links)

        log.debug ('semp-apply: response {} ({}): '.format (resp, type(resp)))
        return resp

    #-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
    # apply_json:
    #   post / patch to semp url - uses http_post / http_patch below
    #
    def apply_json (self, url, json_data):
        """ just do it """

        log.enter ("Entering {}:{} url = {}".format( __class__.__name__, inspect.stack()[0][3], url))
        sys_cfg = Cfg['system']

        # check if object needs to be skipped
        _,obj1 = os.path.split(url)
        if obj1 in sys_cfg['skipObjects']:
            log.notice ('Skipping object:  {} - User skipped'.format(obj1))
            resp = requests.models.Response()
            resp.status_code = sys_cfg['status']['statusSkip']   
            return resp
        
        # check if obj should be ignored
        my_keys = set(json_data.keys())
        ignore_keys = sys_cfg['skipTags'].keys()
        s = my_keys.intersection(ignore_keys)
        # debug
        #print ('my_keys = ', my_keys)
        #print ('ignore_keys = ', ignore_keys)
        #print ('s = ', s)

        if (len(s) > 0):
            t = s.pop()
            v = json_data[t]
            if v in sys_cfg ['skipTags'][t] :
                log.notice ('Skipping {} : {} (in skip)'.format(t,v))
                resp = requests.models.Response()
                resp.status_code = sys_cfg['status']['statusSkip']   
                #rs = f'{t} : {v} being skipped. See ignore_list'
                #resp.text =  rs # can't set text
                #print ('skip returning :', resp)
                return resp
            apply_filter = Cfg["applyFilter"]
            if apply_filter :
                if v not in apply_filter[t] :
                    log.notice ('Skipping {} : {} (not in apply filter)'.format(t,v))
                    resp = requests.models.Response()
                    resp.status_code = sys_cfg['status']['statusSkip']   
                    #rs = f'{t} : {v} being skipped. See ignore_list'
                    #resp.text =  rs # can't set text
                    #print ('skip returning :', resp)
                    return resp
            else:
                log.debug ('No apply filter')
            log.info ('apply-json Processing {} : {}'.format(t,v))


        # update vpn-name if different
        target_vpn = self.vpn
        if json_data['msgVpnName'] != target_vpn :
            src_vpn = json_data['msgVpnName']
            log.debug ('Target VPN Name {} differs from {}'.format(target_vpn,src_vpn))
            ps = '/{}/'.format(src_vpn)
            p = url.partition(ps)
            log.debug ('url: ', url, 'ps : ', ps, 'p  : ', p)

            if p[1] == ps:
                url = '{}/{}/{}'.format(p[0],target_vpn,p[2])
                log.debug ('Target url (1): {}'.format(url))
            json_data['msgVpnName'] = target_vpn

            #print ('------------ JSON to post ----------------'); pp.pprint(json_data)
            #_,urlp = os.path.split(url)
            #print ('URL ', url, urlp)

        # Handle deletion
        if Cfg['deleting']:
            # patch needs object name (eg: queueus/queue1)
            _,vpn_obj = os.path.split(url)
            if vpn_obj in Cfg['items']:
                patch_url = '{}/{}'.format(url, v)
                log.debug ('Deletion for {}, URL: {}'.format(vpn_obj, patch_url))
                return self.http_delete(patch_url)
            else:
                log.notice ('Deletion not enabled for {}'.format(vpn_obj))
                if vpn_obj in sys_cfg['skipObjects']:
                    log.notice ('Skipping object:  {} - Not enabled for Patch'.format(vpn_obj))
                    resp = sys_cfg['status']['123']
                    return DummyResponse (**resp)
                    #return SysCfg['status']['123']
                    #return json.dumps(SysCfg['status']['123'], indent=4, sort_keys=True)

        # Check if patching instead of post
        if Cfg['patching']:
            # patch needs object name (eg: queueus/queue1)
            _,vpn_obj = os.path.split(url)
            if vpn_obj in Cfg['items']:
                patch_url = '{}/{}'.format(url, v)
                log.debug ('Patching for {}, URL: {}'.format(vpn_obj, patch_url))
                return self.http_patch(patch_url, json_data)
            else:
                log.notice ('Patching not enabled for {}'.format(vpn_obj))
                if vpn_obj in sys_cfg['skipObjects']:
                    log.notice ('Skipping object:  {} - Not enabled for Patch'.format(vpn_obj))
                    resp = sys_cfg['status']['123']
                    return DummyResponse (**resp)
                    #return SysCfg['status']['123']
                    #return json.dumps(SysCfg['status']['123'], indent=4, sort_keys=True)

        # Check if posting subset of items
        if Cfg['items']:
            # check if object is in Items list
            log.debug ('Posting subset of objects {}'.format(Cfg['items']))

            _,vpn_obj = os.path.split(url)
            if vpn_obj in Cfg['items']:
                log.debug ('Posting for {}, URL: {}'.format(vpn_obj, url))
                return self.http_post(url, json_data)
            else:
                log.notice ('Skipping object:  {} - Not included in user arg'.format(vpn_obj))
                resp = sys_cfg['status']['123']
                return DummyResponse (**resp)
        else:
            # process whole VPN
            log.debug ('Posting all objects, URL: {}'.format(url))
            return self.http_post (url, json_data)
            #return self.http_post_or_patch (url, json_data)

    #------------------------------------------------------------
    # apply_links
    #   This calls semp_apply (recursively) for each link in the list
    #
    def apply_links (self, target_url, target_obj, src_path,links):
        """ post list of links to broker with corresponding json payload """

        log.enter ("Entering {}::{}".format( __class__.__name__, inspect.stack()[0][3]))

        # target_url: http://localhost:8080/SEMP/v2/config/msgVpns/<target-vpn>/aclProfiles
        # target_obj: <target-object-name> 
        # src_path: ../out/json/localhost/<src-vpn>/aclProfiles
        log.debug (f" target_url: {target_url} target_obj: {target_obj} src_path: {src_path}")
        log.debug  ('LINKS:', links)

        json_h = JsonHandler.JsonHandler(Cfg)

        # links: http://localhost:8080/SEMP/v2/config/msgVpns/sys-test-vpn1/queues
        # http://localhost:8080/SEMP/v2/config/msgVpns/sys-test-vpn1/queues/sys-q1 
        # http://localhost:8080/SEMP/v2/config/msgVpns/sys-test-vpn1/aclProfiles/sys-acl1/clientConnectExceptions
        for _, src_link in links.items():
            log.debug ('src link: {}'.format(src_link))
            # src_url_path: http://localhost:8080/SEMP/v2/config/msgVpns/sys-test-vpn1/, obj = queues
            # or  http://localhost:8080/SEMP/v2/config/msgVpns/sys-test-vpn1/aclProfiles/sys-acl1/ & clientConnectExceptions
            src_link_tails1,obj1 = os.path.split(src_link)
            sys_cfg = Cfg['system']

            log.debug  (f'src_url_path: {src_link_tails1} src_obj: {obj1}')
            if obj1 in sys_cfg['skipObjects']:
                log.notice  ('Skipping object:  {} - User skipped'.format(obj1))
                continue
            path="{}/{}".format(src_path, obj1)
            log.debug  (f'looking for {path}/*.json (1)')

            #json_file = unquote("{}/{}.json".format(path, obj))
            url = "{}/{}/{}".format(target_url,target_obj,obj1)
            json_files = json_h.list_json_files (path, obj1) 
            
            # look for link-2 format 'http://localhost:8080/SEMP/v2/config/msgVpns/sys-test-vpn1/aclProfiles/sys-acl1/clientConnectException 
            if len(json_files) == 0 :
                log.debug  (f"No {obj1} JSON files found in {path}. Try another level")
                # src_obj2 : sys-acl1
                src_link_tails2,obj2 = os.path.split(src_link_tails1)
                path="{}/{}/{}".format(src_path, obj2, obj1)
                json_files = json_h.list_json_files (path, obj1)
                log.debug  (f'looking for path: {path} obj1: {obj1}')

                if len(json_files) > 0 :
                    # obj_type : aclProfiles (src link: http://localhost:8080/SEMP/v2/config/msgVpns/sys-test-vpn1/aclProfiles/sys-acl1/clientConnectExceptions)
                    _,obj3 = os.path.split(src_link_tails2)
                    url = "{}/{}/{}".format(target_url, obj2, obj1)
                    #print (f'new url : {url}')

            for json_file in json_files:
                log.info  ('Reading JSON file  {}'.format(json_file))
                js_obj = json_h.read_json_data(json_file)
                json_data = js_obj['data']
                links = js_obj['links']
                next_page_uri = js_obj['next_page_uri']
        
                if len(json_data) == 0 and len(links) == 0:
                    log.debug  ('No data or links in {}'.format(json_file))
                    continue
                try:
                    log.debug  (f'Processing target_obj: {target_obj} url: {url} path: {path} json_file: {json_file}')
                    self.semp_apply (url, target_obj, path, json_data, links, next_page_uri)
                except Exception as e:
                    #print (f'Exception: {e}')
                    log.error  (f'apply-links: Failed to process {json_file}')
                    # exit 
                    #log.error('EXITING')
                    #sys.exit(1)
                    
                    continue
            #else:
            #    log.info("No JSON file %s", json_file)
            
            
    def response_status_unused (self, resp):
        """ parse out response-status from json semp response """

        # check if the object is skipped by user
        system_cfg = Cfg['system']
        status_cfg = system_cfg['status']
        c = status_cfg['statusSkip'] 
        if resp.status_code == c :
            return status_cfg[c]["status"], status_cfg[c]["description"]

        d = status_cfg['statusUnknown']
        rd = status_cfg[d]["status"]
        rs = status_cfg[d]["description"]
        resp_json = json.loads(resp.text)
        if 'meta' in resp_json:
            if 'error' in resp_json['meta']:
                if 'status' in resp_json['meta']['error'] :
                    rs =  resp_json['meta']['error']['status']
                if 'description' in resp_json['meta']['error'] :
                    rd =  resp_json['meta']['error']['description']
        return rs, rd