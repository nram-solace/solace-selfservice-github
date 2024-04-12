###########################################################################################
# ConfigParser
#    Solace Config Parser implementation
#
# Ramesh Natarajan (nram), Solace PSG (ramesh.natarajan@solace.com)
###########################################################################################

import sys, os, inspect
import inspect
import pathlib
from urllib.parse import unquote # for Python 3.7

sys.path.insert(0, os.path.abspath("."))
from common import JsonHandler

Verbose = 0
Cfg = {}
log = None
Stats = {'links': 0, 'data': 0, 'skipped': 0}

class ConfigParser:
    """ Solace Config Parser implementation """

    def __init__(self, cfg, verbose = 0):
        global Verbose
        global Cfg, log
        Verbose = verbose
        Cfg = cfg
        log = Cfg['log_handler'].get()
        log.enter ('Entering {}::{}'.format(__class__.__name__, inspect.stack()[0][3]))
        self.json_h = JsonHandler.JsonHandler(Cfg)

    def cfg_parse (self, obj, path, cfg) :
        """ parse cfg recursively """

        Stats['data'] += 1
        if 'links' not in cfg:
            log.info ("No links to process in cfg")
            return cfg
        links = cfg['links']
        log.trace ("Entering {}::{} obj = {} path = {}".format( __class__.__name__, inspect.stack()[0][3], obj, path))

        log.debug ('Processing object {} path: {}'. format(obj, path))
        log.debug ('Number of links: {}'. format(len(links)))
        Stats['links'] += len(links)

        # loop thru link and parse recursively
        if links:
            log.debug ("cfg_parse: Processing Links {}".format(links))
            if type(links) is list:
                for link in links:
                    self.parse_links ( obj,path, link, cfg)
            else:
                self.parse_links (obj, path, links, cfg)
        return cfg


    def parse_links (self, base_obj, base_path, links, cfg):
        """ parse list of links to broker with corresponding json payload """

        log.trace ("Entering {}::{} obj = {} path = {} ".format( __class__.__name__, inspect.stack()[0][3], base_obj, base_path))
        log.debug (f'Processing : {links}')

        for _, link in links.items():
            #op, obj_type = os.path.split(link)
            a = link.split('/')
            obj_type = unquote(a[len(a)-1])
            obj = unquote(a[len(a)-2])
            link = unquote(link)
            #print ('parse_links:Processing object: {} ({}) Link: {}'.format(obj, obj_type, link))

            # base path: ../out/json/localhost/test-vpn
            # link: http://localhost:8080/SEMP/v2/config/msgVpns/test-vpn/aclProfiles/#acl-profile/clientConnectExceptions
            # obj_type: clientConnectExceptions
            # obj: #acl-profile (can also be "test-vpn" in top level see HACK below)

            sys_cfg = Cfg["system"]
            # TODO: This ends looking for far too many json files that will never be found
            # some of them leading to invalid path. 
            # fix to prevent that -- need more tighter control.
            if obj in sys_cfg["semp"]['leafNode']:
                log.debug ('Skip Leaf object {}'.format(obj))
                #Stats['skipped'] += 1
                return

            log.debug ('Parsing object: {} {}'.format(obj, obj_type))
            log.debug ('link: {} base_bath: {}'.format(link, base_path))

            #if obj in SysCfg['skipObjects']:
            #    print ('   - Skipping object:  {}'.format(obj))
            #    continue
            path="{}/{}".format(base_path, obj_type)

            #json_file = unquote("{}/{}.json".format(path, obj))
            log.trace ('<1> Looking for <{}*.json> files in {} obj: {} type: {}'.format(obj_type, path, obj, obj_type))
            try:
                json_files = list(pathlib.Path(path).glob('{}*.json'.format(obj_type)))

                # HACK - try one level below
                if len(json_files) == 0:
                    path="{}/{}/{}".format(base_path, obj, obj_type)
                    log.trace ('<2> Looking for <{}*.json> files in {} obj: {} type: {}'.format(obj_type, path, obj, obj_type))

            # protect against unparsable path
            except Exception as e:
                log.error ('### Unable to read json files in {}'.format(path))
                log.error ('### Exception: {}'.format(e))
                return
            
            # files read .. process them
            json_files = list(pathlib.Path(path).glob('{}*.json'.format(obj_type)))

            log.debug ('Found {} {}/*.json files in {}'.format (len(json_files), obj_type, path))
            log.trace (f'List of json files : {json_files}')
            
            for json_file in sorted(json_files):
                # Wrap each file path in double quotes
                #quoted_file_path = f'"{json_file}"'
                log.info ('parse_links: ({}) Reading file {} ({})'.format(Stats['links'],json_file, obj))

                this_obj = self.json_h.read_json_data(json_file)

                # add this object to base object
                log.trace ('cfg keys: ', cfg.keys())
                    #print ('JSON:'); pp.pprint(cfg)
                if obj_type in cfg:
                    log.debug ('   + Adding {} {} to config'.format(obj, obj_type))
                    #pp.pprint(cfg[obj])
                    for d in this_obj['data']:
                        cfg[obj_type]['data'].append(d)
                    #for l in this_obj['links']:
                    #    cfg[obj_type]['links'].append(l)
                else:
                    log.debug  ('   > Creating {} {} in config'.format(obj, obj_type))
                    cfg[obj_type] = this_obj

                log.trace ('... This object'.format(this_obj))
                    #print('--- cfg: '); pp.pprint(cfg)

                if 'data' not in this_obj or (len(this_obj['data']) == 0 and len(this_obj['links']) == 0):
                    log.info ('Skipping {} with No data or links'.format(json_file))
                    Stats['skipped'] += 1
                    continue
                self.cfg_parse (base_obj, path, this_obj)
            #else:
            #    log.info("No JSON file %s", json_file)
            
    def print_stats(self):
        log.notice("ConfigParser Stats:")        
        for k, v in Stats.items():
            log.notice("{:>20} : {}".format(k, v))
