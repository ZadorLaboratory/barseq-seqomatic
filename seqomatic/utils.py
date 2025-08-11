import logging
import os 
import pprint

from configparser import ConfigParser

def get_default_config():
    dc = os.path.expanduser('~/git/barseq-processing/etc/barseq.conf')
    cp = ConfigParser()
    cp.read(dc)
    return cp

def get_resource_dir():
    '''
    Assume running from git for now. Go up two from script, and down to 'resource'

    '''
    script_file = os.path.abspath(__file__)
    (base, exe) = os.path.split(script_file)
    (libdir, script_dir) = os.path.split(base)
    rdir = os.path.join( libdir, 'resource'  )
    logging.debug(f'current script={script_file} libdir={libdir} resource_dir={rdir}')
    return rdir


def format_config(cp):
    '''
        Pretty print ConfigParser to standard string for logging.  
    '''
    cdict = {section: dict(cp[section]) for section in cp.sections()}
    s = pprint.pformat(cdict, indent=4)
    return s
