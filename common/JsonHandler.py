##############################################################################
# JsonHandler
#   JSON Handling functions
#
# Ramesh Natarajan (nram), Solace PSG (ramesh.natarajan@solace.com)
##############################################################################

import sys, os, inspect
import json
import pprint
import inspect
from urllib.parse import unquote
import pathlib

pp = pprint.PrettyPrinter(indent=4)
Verbose = 0
log = None

class JsonHandler():
    """ JSON handling functions """

    # class /static vars
    ObjMap = {} # static map used to get unique file-names

    def __init__(self, cfg, verbose=0):
        global Verbose, log
        Verbose = verbose
        log = cfg['log_handler'].get()

        log.enter ('Entering {}::{}'.format(__class__.__name__, inspect.stack()[0][3]))

    def save_config_json (self,outfile, json_data):
        global Verbose
        """ save config json to file """

        outfile = unquote(outfile)
        log.enter ("Entering {}::{}  file: {}". format (__class__.__name__, inspect.stack()[0][3], outfile))
        if os.path.exists(outfile):
            #print ("   - Skiping {} (file exists)".format( outfile))
            log.info ("Skipping {} (file exists)".format( outfile))

            return
        path,fname = os.path.split(outfile)
        if not os.path.exists(path):
            log.trace ('outfile: {} path: {} fname: {}'. format(outfile, path, fname))
            log.trace ("makedir: {}".format(path))
            os.makedirs(path)
        log.info ("Writing to {}".format(outfile))
        with open(outfile, 'w') as fp:
            json.dump(json_data, fp, indent=4, sort_keys=True)

    def get_unique_fname (self,path,obj):
        """ helper fn to get a unique file name (eg: queue-1.json, queue-2.json) """   
        log.enter ("Entering {}::{}  file: {}". format (__class__.__name__, inspect.stack()[0][3], path))

        #obj1=urllib.parse.unquote(obj)
        obj1=unquote(obj)
        key=path+"/"+obj1
        if key not in JsonHandler.ObjMap:
            JsonHandler.ObjMap[key] = 0
            return "{}.json".format(obj1)
        JsonHandler.ObjMap[key] = JsonHandler.ObjMap[key]+1
        return ("{}-{}.json".format(obj1,JsonHandler.ObjMap[key]))

    def read_json_file(self,file):
        """ read json file and return data """
        global Verbose

        log.enter ("Entering {}::{}  file: {}".format(__class__.__name__, inspect.stack()[0][3], file))
        with open(file, "r") as fp:
            data = json.load(fp)
        return data

    def read_json_data (self, json_file) :
        """ parse json data & return parts """
        global Verbose

        log.enter ("Entering {}::{} JSON file: {} ({})".format (__class__.__name__, inspect.stack()[0][3], json_file, type(json_file)))
        #json_fname = "{}/{}".format(path, fname)
        # 2.7 doesn't handle PostfixPath to open(). Do an explicit cast
        if type(json_file) != "str":
            json_file = str(json_file)
        log.debug ("read_json_data: opening file {}".format(json_file))

        with open(json_file, "r") as fp:
            json_payload = json.load(fp) 
        log.debug ('read_json_data: json_data : {}'.format(json.dumps(json_payload, indent=2)))

        if 'data' not in json_payload:
            log.warn ("Unable to parse json file: {}. Skipping".format(json_file))
            log.info('No data element in json file')
            return {}
        json_data = json_payload['data']

        links = None
        if 'links' in json_payload:
            links = json_payload['links']

        # no need to save next-page-url since all data is being appended
        #next_pg = None
        meta_data = json_payload['meta']
        next_page_uri = None
        if 'paging' in meta_data:
            next_page_uri = meta_data['paging']['nextPageUri']
        obj = {}
        obj['data'] = json_data
        obj['links'] = links
        obj['next_page_uri'] = next_page_uri
        #obj['next_pg'] = next_pg
        log.trace ('read_json_data: Object:', json.dumps(obj, indent=2))
        return obj

    def save_json_file (self,outfile, json_data):
        """ save  json to file """
        global Verbose

        outfile = unquote(outfile)
        log.enter ("Entering {}::{}  file: {}". format (__class__.__name__, inspect.stack()[0][3], outfile))
        if os.path.exists(outfile):
            log.info ("Overwriting {}".format( outfile))
        else:
            log.info ("Writing to {}".format(outfile))
        with open(outfile, 'w') as fp:
            json.dump(json_data, fp, indent=4, sort_keys=True)
            
    # list_json_files:
    #   Look for json files in a path and retrurn list of files. 
    def list_json_files(self, path, obj):
        log.enter ("Entering {}::{}  file: {}". format (__class__.__name__, inspect.stack()[0][3], path))

        if Verbose > 2:
            print (f'list_json_files: Looking for {obj}*.json in {path}')
        json_files = list(pathlib.Path(path).glob(f'{obj}*.json'))
        if Verbose :
            print (f'Found {len(json_files)} {obj}*.json files in {path}')
        if Verbose > 2:
            pp.pprint(json_files)
        return json_files
