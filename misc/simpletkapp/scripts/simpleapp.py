#!/usr/bin/env python
#    Simple TK test application, supporting config input.
#    
#    https://nazmul-ahsan.medium.com/how-to-organize-multi-frame-tkinter-application-with-mvc-pattern-79247efbb02b
#
# Naming Convetions
# 
#   Widget Class  Variable Name Prefix Example
#   Label             lbl               lbl_name
#   Button            btn               btn_submit
#   Entry             ent               ent_age
#   Text              txt               txt_notes
#   Frame             frm               frm_address
#
#
import argparse
import logging
import os
import pprint
import sys
import time

from configparser import ConfigParser

import tkinter as tk
from tkinter import ttk, Button, IntVar, StringVar, filedialog, messagebox, scrolledtext 


#######################################
#           EVENT HANDLERS
########################################
#
#  

def handle_button1(event):
    print(event.char)




class SimpleApp():
    
    def __init__(self):
        self.mainwindow = tk.Tk()
        label = tk.Label(
            text="Hello, Tkinter",
            fg="white",
            bg="black",
            width=10,
            height=10
            )
        button1 = tk.Button(text='Button1')
        button1.bind("<Button-1>", handle_button1 )
        
        label.pack()
        button1.pack()


#######################################################
#                 UTILS
#######################################################




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
   

if __name__ == '__main__':
    FORMAT='%(asctime)s (UTC) [ %(levelname)s ] %(filename)s:%(lineno)d %(name)s.%(funcName)s(): %(message)s'
    logging.basicConfig(format=FORMAT)
    logging.getLogger().setLevel(logging.WARN)
    
    parser = argparse.ArgumentParser()
      
    parser.add_argument('-d', '--debug', 
                        action="store_true", 
                        dest='debug', 
                        help='debug logging')

    parser.add_argument('-v', '--verbose', 
                        action="store_true", 
                        dest='verbose', 
                        help='verbose logging')

    parser.add_argument('-c','--config', 
                        metavar='config',
                        required=False,
                        default=os.path.expanduser('~/git/barseq-seqomatic/misc/simpletkapp/etc/simple.conf'),
                        type=str, 
                        help='config file.')
    
      
    args= parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        loglevel = 'debug'
    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)   
        loglevel = 'info'
    
    cp = ConfigParser()
    cp.read(args.config)
    cdict = format_config(cp)
    logging.debug(f'Running with config. {args.config}: {cdict}')

    app = SimpleApp()
    app.mainwindow.mainloop()




