#!/usr/bin/env python
#
#   https://nazmul-ahsan.medium.com/how-to-organize-multi-frame-tkinter-application-with-mvc-pattern-79247efbb02b
#
#
#
#
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

# custom application imports
gitpath=os.path.expanduser("~/git/barseq-seqomatic/seqomatic")
sys.path.append(gitpath)

from frontend import *
from utils import *





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
                        default=os.path.expanduser('~/git/barseq-seqomatic/etc/seqomatic.conf'),
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

    
    mainwindow = MainWindow()
    wwidgets = WindowWidgets(mainwindow=mainwindow, 
                             tkapp=mainwindow.mainwindow, 
                             path=os.getcwd())
    wwidgets.set_widget_state()

    mainwindow.mainwindow.mainloop()
    

 