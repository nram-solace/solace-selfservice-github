########################################################################
# LogHandler
#  Log file handling
#
# Ramesh Natarajan (nram), Solace PSG (ramesh.natarajan@solace.com)
########################################################################

import os, sys, inspect, traceback
import logging
import time
import json


# custom levels
logging.TRACE = 5  # trace 
logging.ENTER = 6  # trace - enter function
logging.STATUS = 32  # status 
logging.NOTICE = 34  # positive yet important 
    

def ts(mode=1):
    if mode == 0:
        return 'now'
    return time.strftime("%Y%m%d-%H%M%S")
 
class colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
 
class ColoredFormatter(logging.Formatter):
    log_colors = {
       logging.TRACE: colors.WHITE,
       logging.ENTER: colors.MAGENTA,
       logging.DEBUG: colors.WHITE,
       logging.INFO: colors.BLUE,
       logging.STATUS: colors.GREEN,
       logging.NOTICE: colors.CYAN,
       logging.WARNING: colors.YELLOW,
       logging.ERROR: colors.RED,
       logging.CRITICAL: colors.RED,
       logging.FATAL: colors.RED
         
      }
   
    def format(self, record):
        log_color = colors.WHITE  # Default color for log messages

        if record.levelno == logging.DEBUG:
            log_color = colors.CYAN
        elif record.levelno == logging.INFO:
            log_color = colors.GREEN
        elif record.levelno == logging.WARNING:
            log_color = colors.YELLOW
        elif record.levelno == logging.ERROR or record.levelno == logging.CRITICAL:
            log_color = colors.RED
            
        log_color = self.log_colors[record.levelno]

        # Apply color to the log message
        message = super().format(record)
        colored_message = f"{log_color}{message}{colors.RESET}"
        return colored_message

class LogHandler :
   'Common Logger wrapper implementtion'

   # ------------------t
   # init
   #
   def __init__ (self, cfg):
         
         self.m_appname = 'noname'
         self.m_verbose = 0
         logdir = '/tmp'
         if 'script_name' in cfg :
            self.m_appname = cfg['script_name']
         if 'verbose' in cfg :
            self.m_verbose = cfg['verbose']
         logdir = cfg['system']['system']['logDir']

         #ts = 'now' # for testing
         self.m_logfile = './{}/{}-{}.log'.format(logdir, self.m_appname, ts())
         print (f'Opening log file for {self.m_appname} : {self.m_logfile}')
         self.m_init = False
         # create log dir if it doesn't exist
         os.makedirs(logdir, exist_ok=True)
         self.setup()

    #   def notice(self, message, *args, **kws):
    #   logger takes its '*args' as 'args'.
    #       if self.isEnabledFor(DEBUG_LEVELV_NUM):
    #           self._log(DEBUG_LEVELV_NUM, message, args, **kws) 
   
   # ------------------------------------------------------------------------------
   # setup logger 
   # logger levels:
   # CRIT   - 50 
   # ERROR  - 40 
   # NOTICE - 34 	(custom)
   # AUDIT -  33 	(custom)
   # STATUS - 32 	(custom)
   # WARN   - 30
   # INFO   - 20
   # DEBUG  - 10
   # ENTER  - 6	  (custom)
   # TRACE  - 5   (custom)
   # NOTSET - 0

   def setup(self):
      # custom levels

      #logging.AUDIT = 33  # audit log 
      logging.addLevelName(logging.TRACE, 'TRACE') 
      logging.addLevelName(logging.ENTER, 'ENTER') 
      logging.addLevelName(logging.STATUS, 'STATUS') 
      #logging.addLevelName(logging.STATUS, 'AUDIT') 
      logging.addLevelName(logging.NOTICE, 'NOTICE')
      logging.addLevelName(logging.CRITICAL, 'FATAL') # rename existing

      self.m_logger = logging.getLogger(self.m_appname)

      self.m_logger.trace = lambda msg, *args: self.m_logger._log(logging.TRACE, msg, args)
      # additional traces
      self.m_logger.dump_json = lambda msg, *args: self.m_logger._log(logging.TRACE, msg, json.dumps(args, indent=2))
      self.m_logger.dump_list = lambda msg, *args: self.m_logger._log(logging.TRACE, msg, json.dumps(list(args), indent=2))
      self.m_logger.dump_yaml = lambda msg, *args: self.m_logger._log(logging.TRACE, msg, json.dumps(args, indent=2))
      self.m_logger.dump_xml = lambda msg, *args: self.m_logger._log(logging.TRACE, msg, json.dumps(args, indent=2))

      #self.m_logger.audit = lambda msg, *args: self.m_logger._log(logging.AUDIT, msg, args)
      self.m_logger.notice = lambda msg, *args: self.m_logger._log(logging.NOTICE, msg, args)
      self.m_logger.status = lambda msg, *args: self.m_logger._log(logging.STATUS, msg, args)
      self.m_logger.enter = lambda msg, *args: self.m_logger._log(logging.ENTER, msg, args)
      self.m_logger.setLevel(logging.INFO)

      formatter = logging.Formatter('%(asctime)s : %(name)s [%(levelname)s] %(message)s')

      #stream_formatter = logging.Formatter('%(levelname)s: %(message)s')
      stream_formatter_color = ColoredFormatter(fmt='%(asctime)s %(levelname)s: %(message)s')


      #stream_formatter = logging.Formatter('%(message)s')

      # file handler
      fh = logging.FileHandler(self.m_logfile)
      fh.setLevel(logging.INFO)
      if self.m_verbose > 2 :
         print ("** Setting file log level to TRACE ***")
         fh.setLevel(logging.TRACE)
         self.m_logger.setLevel(logging.TRACE)
      elif self.m_verbose > 0 :
         print ("** Setting file log level to DEBUG ***")
         fh.setLevel(logging.DEBUG)
         self.m_logger.setLevel(logging.DEBUG)
      fh.setFormatter(formatter)
      self.m_logger.addHandler(fh)

      # stream handler -- log at higher level
      ch1 = logging.StreamHandler(sys.stdout)
      ch1.setLevel(logging.WARNING)
      
      ch2 = logging.StreamHandler(sys.stderr)
      ch2.setLevel(max(logging.DEBUG, logging.ERROR))

      if self.m_verbose > 0 :
         #print ("** Setting stream log level to INFO ***")
         ch1.setLevel(logging.INFO)
         #self.m_logger.setLevel(logging.INFO)
      ch1.setFormatter(stream_formatter_color)
      self.m_logger.addHandler(ch1)
      self.m_logger.addHandler(ch2)

      self.m_init = True

   # ------------------------------------------------------------------------------
   # Return logging.logger to apps
   #
   def get(self, name=None):
      if not self.m_init:
         print ("Logging not initialized")
         return None
      if name == None:
         #print "Returning saved logger"
         return self.m_logger
      #print "Returning logger for ", name
      return logging.getLogger(name)

   def logfile(self):
          return self.m_logfile ;
   
   # this should be called on log_h object, not log object
   # log_h.crit_exit ('string')  
   def crit_exit (self, s):
      log = self.log
      log.crit('*** Exiting on CRITICAL Error ***')
      log.error(s)
      log.debug('------------ STACK TRACE ------------')
      log.debug(' '.join(traceback.format_stack()))
      exit()
      
   def err_exit (self, s, e = None):
      log = self.m_logger
      log.error('*** Exiting on Error ***')

      log.error(s)
      if e:
         log.error(str(e))
         log.notice(f'Please see logfile {self.m_logfile} for trace info')
         log.debug('------------ CALL TRACE ------------')
         log.debug(' '.join(traceback.format_stack()))
         
         log.debug('------------ STACK TRACE ------------')
         fh = open(self.m_logfile, 'a')
         traceback.print_exc(file=fh)
         fh.close()

      sys.exit(2)