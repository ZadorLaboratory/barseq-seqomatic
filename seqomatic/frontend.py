"""
Author: Aixin Zhang
Description: Seqomatic Tk front end GUI application. 
"""
# system imports
import copy
import json
import logging
import math
import os
import shutil
import sys
import time

# external imports
import cv2
import tifffile

# external rename imports
import numpy as np
import pandas as pd

# sub-modules not importable via import as name
# but once imported, can be called via tk namespace, e.g. tk.Button
import tkinter as tk
from tkinter import ttk
import tkinter.scrolledtext as tkst
#from tkinter import ttk, Button, IntVar, StringVar, filedialog, messagebox, scrolledtext 

# external selective imports
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from pycromanager import Core, Acquisition, multi_d_acquisition_events
from PIL import ImageTk, Image

# local package imports
gitpath=os.path.expanduser("~/git/barseq-seqomatic/seqomatic")
sys.path.append(gitpath)

from utils import *
#from backend import Backend

#############################################################
#                  common GUI functions/constants  
#############################################################

COLOR_ARRAY=np.array([[0,4,4],[1.5,1.5,0],[1,0,1],[0,0,1.5]])

class widget_attr:
    NORMAL_EDGE=3
    DISABLE_EDGE = 0.9
    NORMAL_COLOR = '#0f0201'
    DISABLE_COLOR = '#bab8b8'
    WARNING_COLOR='#871010'
    BLACK_COLOR='#0a0000'
    YELLOW_COLOR="#e0c80b"

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END='\033[0m'

######################################################
#              GUI Classes
#              Main Application/Controller 
######################################################

#
# https://github.com/clear-code-projects/tkinter-complete/tree/main 
# 

class SeqomaticGUI(tk.Tk):
    '''
    Top-level front-end GUI code.  
    
    Handles Widget nesting and Layout, and widge-specific functions.  
    SeqomaticController handles pop-ups and global variables. 
    
    See: https://stackoverflow.com/questions/66249107/optimal-tkinter-file-structure
   
    Code should allow for eventual move to distinct Controller object. 
    https://stackoverflow.com/questions/48510894/shared-data-between-frames-tkinter
    https://www.youtube.com/watch?v=FCl6_Yd502k

      
    '''        
    def __init__(self):
        super().__init__()       
        
       
        ###############################################################################
        #  TKInter GUI variables. 
        ###############################################################################
        self.title("Seq-o-Matic")
        self.geometry("1500x800+100+100")
        self.color_array = COLOR_ARRAY
        img = tk.PhotoImage( file=os.path.join( get_resource_dir(), 'LOGO.png'))
        self.iconphoto(False, img) 

        # Global controller object
        # For now, make this root Tk() object the controller. 
        self.controller = SeqomaticController()
        logging.debug(f'controller initial:\n{self.controller}')

        # Top-level tabbed notebook
        self.notebook = tk.ttk.Notebook(self)
        #self.notebook.grid(row=0, column=0, sticky="nsew")
        self.notebook.pack(expand=True, fill='both')
        auto_frame = AutoTabFrame(self, self.controller)
        auto_frame.pack(expand=True, fill='both')
 
        manual_frame = ManualTabFrame(self, self.controller)
        manual_frame.pack(expand=True, fill='both')
        self.auto_image = tk.PhotoImage(file=os.path.join( get_resource_dir() , "auto_logo.png"))
        self.manual_image = tk.PhotoImage(file=os.path.join( get_resource_dir() , "hand.png"))       

        self.notebook.add(auto_frame, text='Auto System', image=self.auto_image, compound=tk.LEFT)
        self.notebook.add(manual_frame, text='Manual System', image=self.manual_image, compound=tk.LEFT)

        # Widget references filled in by relevant objects. 
        # 
        self.warning_frame = None
        self.notification_frame = None
        self.liveview_frame = None
        self.heater_dict = None

        logging.debug(f'controller final:\n{self.controller}')

    def cancel_manual_process(self):
        self.cancel = 1
        self.scope.cancel_process = 1

    def config_dev(self):
        device_group=self.device_dropdown.get()
        self.pos_path = self.controller.work_path.get()
        if self.pos_path == "":
            self.pos_path = "C://"
            self.fluidics = FluidicSystem( system_path=self.system_path,
                                          pos_path=self.pos_path,
                                          slide_heater_dictionary=self.heater_dict)
            if not os.path.exists(os.path.join(self.pos_path, "temp.txt")):
                open(os.path.join(self.pos_path, "temp.txt"), 'w')
            if not os.path.exists(os.path.join(self.pos_path, "log.txt")):
                open(os.path.join(self.pos_path, "log.txt"), 'w')

        if "syringe pump" in device_group:
            try:
                self.fluidics.config_syringe_pump()
                self.device_status["syringe_pump_group"]=1
                self.warning_dev.insert(tk.END, "Syringe groups works well!\n", 'normal')
                return
            except:
                self.warning_dev.insert(tk.END, "Please, reconnect Pump groups!\n", 'warning')
                return

        if "heater" in device_group:
            self.fluidics.config_heater()
            self.device_status["heater_group"] = 1
            self.warning_dev.insert(tk.END, "Heater groups works well!\n", 'normal')

        if "selector" in device_group:
            try:
                self.fluidics.config_selector()
                self.device_status["selector_group"] = 1
                self.warning_dev.insert(tk.END, "Selector groups works well!\n", 'normal')
            except:
                self.warning_dev.insert(tk.END, "Please, reconnect selector groups!\n", 'warning')
                return


















    def update_error(self, txt):
        self.warning_stw.insert(END, txt, 'warning')




class SeqomaticController(object):
    '''

    Global variable object. 
    Popup Components
    Some direct button/widget handlers (for now)
    
    '''

    def __init__(self):
        logging.info(f'controller created.')

        # Non-GUI central/controller variables. 
        self.device_status = {
            "syringe_pump_group": 0,
            "selector_group": 0,
            "heater_group": 0}
        self.scale=1000 #unit ml to ul
        self.assigned_heater=0

        self.error_frame = None
        self.notification_frame = None
        self.notes_frame = None

    def assign_cycle_detail(self):
        if not os.path.exists(os.path.join( self.pos_path,"protocol.csv")):
            txt=get_time()+"couldn't find protocol.csv file, please create protocol if choose using user defined protocol!"
            update_error(txt)
            return
        df=pd.read_csv(os.path.join(self.pos_path,"protocol.csv"))
        self.process_ls=df['process'].tolist()
        check=[1 for i in self.process_ls if "imagecycle" in i]
        if sum(check)>=1:
            if not "imagecycle00" in self.process_ls:
                if not os.path.exists(os.path.join(self.pos_path,"dicfocuscycle00")):
                    for i in range(len(self.process_ls)):
                        cycle=self.process_ls[i]
                        if "imagecycle" in cycle:
                            self.process_ls.insert(i, 'imagecycle00')
                            break
        self.notification_frame.add_highlight_mainwindow("protocol has beed assigned!"+"\n")
        self.write_log("protocol has beed assigned!")


    def cancel_btn_handler(self):
        self.cancel=1
        self.fluidics.Heatingdevice.cancel=1
        self.fluidics.sequenceStatus=-1
        self.scope.cancel_process = 1
        txt=get_time()+"Canceled current process\n"
        self.notification_frame.add_highlight_mainwindow(txt)
        self.write_log(txt)
        self.all_autobtn_normal()
        self.cancel_sequence_btn['state'] = "disable"

    def check_sequence_handler(self):
        t1 = Thread(target=self.check_sequence)
        t1.start()

    def clear_error(self):
        self.warning_stw.delete('1.0', tk.END)

    def config_device_popup(self):
        self.device_popup = tk.Tk()
        self.device_popup.geometry("500x170")
        self.device_popup.title("Device config")
        self.device_dropdown = ttk.Combobox(self.device_popup, width=35)
        self.device_dropdown['values'] = ["selector group","heater group","syringe pump"]
        self.device_dropdown.place(x=170,y=10)
        self.device_label=tk.Label(self.device_popup,text="Choose system devices:",width=20)
        self.device_label.place(x=15, y=10)
        self.device_config_button=tk.Button(self.device_popup, text="Config", command=self.config_dev)
        self.device_config_button.place(x=250,y=50)
        self.warning_dev = scrolledtext.ScrolledText(
            master=self.device_popup,
            wrap=tk.WORD,
            width=60,
            height=3,
        )
        self.warning_dev.place(x=15,y=80)
        self.warning_dev.tag_config('warning', foreground="red")
        self.warning_dev.tag_config('normal', foreground="black")

    def fill_single_reagent(self):
        if 0 in [self.device_status['selector_group'], self.device_status['syringe_pump_group']]:
            tk.messagebox.showinfo(title="Config device", message="Please config the device first!")
        else:
            t1 = Thread(target=self.pump_reagent)
            t1.start()

    def prime_btn_handler(self):
        if 0 in [self.device_status['selector_group'], self.device_status['syringe_pump_group']]:
            tk.messagebox.showinfo(title="Config device", message="Please config the device first!")
        else:
            self.all_autobtn_disable()
            self.cancel_sequence_btn['state'] = "normal"
            self.fluidics.sequenceStatus = 0
            self.fluidics.connect_syringe_pump()
            self.fluidics.connect_selector() 
            self.fluidics.loadSequence(self.fluidics.Fill_ALL_SEQUENCE)
            t1 = Thread(target=self.fluidics.startSequence)
            t1.start()
            txt = get_time() + "Fill reagents into tubes!\n"
            self.notification_frame.add_highlight_mainwindow(txt)
            self.write_log(txt)
            t2 = Thread(target=self.sensor_fluidics_process)
            t2.start()

    def scan_tissue(self):
        scanner = tissue_scan(self.pos_path)


    def slice_per_slide_reformat(self):
        try:
            a = self.slice_number_field.get()
            listOfChars = list()
            listOfChars.extend(a)
            num = [int(x) for x in listOfChars if x.isdigit()]
            self.slice_per_slide = num
        except:
            self.log_update=0
            tk.messagebox.showinfo(title="Wrong Input", message="Slice per slide is wrong!")
            self.slice_per_slide=None

    def start_btn_handler(self):
        if sum(self.device_status.values())!=len(self.device_status):
            tk.messagebox.showinfo(title="config", message="Please config all devis!")
        else:
            self.process_index=0
            self.process_index_limite=len(self.process_ls)-1
            self.process_cycle=self.process_ls[self.process_index]
            self.cancel=0
            self.fluidics.sequenceStatus=0
            self.check_files()
            if self.check_file==1:
                self.fluidics.connect_syringe_pump()
                self.fluidics.connect_selector()
                self.fluidics.connect_heater()
                self.all_autobtn_disable()
                self.cancel_sequence_btn['state'] = 'normal'
                tt=Thread(target=self.start_sequence)
                tt.start()
            else:
                print("Missing files!")

    def wash_btn_handler(self):
            if 0 in [self.device_status['selector_group'], self.device_status['syringe_pump_group']]:
                tk.messagebox.showinfo(title="Config device", message="Please config the device first!")
            else:
                self.all_autobtn_disable()
                self.fluidics.sequenceStatus=0
                self.fluidics.connect_syringe_pump()
                self.fluidics.connect_selector()
                if self.avoid_wash.get==0:
                    self.fluidics.loadSequence(self.fluidics.FLUSH_REAGENTS_SEQUENCE)
                else:
                    self.fluidics.loadSequence(self.fluidics.FLUSH_ALL_SEQUENCE)

                t1 = Thread(target=self.fluidics.startSequence)
                t1.start()
                txt = get_time() + "Wash with water\n"
                add_fluidics_status(txt)
                self.write_log(txt)
                t2=Thread(target=self.sensor_fluidics_process)
                t2.start()

    def write_log(self, txt):
        f = open(os.path.join(self.pos_path, "log.txt"), "a")
        f.write(txt)
        f.close()


    def focus_btn_handler(self):
        self.scope.cancel_process = 0
        self.parent_window.clear_error()
        t = Thread(target=self.do_focus_thread)
        t.start()

    def align_btn_handler(self):
        self.scope.cancel_process = 0
        self.scope.focus_status = 1
        self.parent_window.clear_error()
        t = Thread(target=self.align_and_draw_thread)
        t.start()

    def tile_btn_handler(self):
        self.scope.cancel_process = 0
        self.scope.alignment_status = 1
        self.parent_window.clear_error()
        t = Thread(target=self.tile_and_draw_thread)
        t.start()
    
    def max_btn_handler(self):
        self.cancel=0
        self.scope.cancel_process = 0
        self.scope.maketiles_status = 1
        self.parent_window.clear_error()
        df = pd.read_csv(os.path.join(self.pos_path, 'tiledregoffset' + self.current_cycle + '.csv'))
        self.max_name_ls = df['switched_Posinfo']
        self.min_x = df['X'].min() - 50
        self.max_x = df['X'].max() + 50
        self.min_y = df['Y'].min() - 50
        self.max_y = df['Y'].max() + 50
        t1 = Thread(target=self.maxprojection_thread)
        t1.start()
        t2 = Thread(target=self.plot_live_view_thread)
        t2.start()


    def clear_focus_canvas(self):
        plot=self.focusfigure.add_subplot(111)
        plot.get_xaxis().set_visible(False)
        plot.get_yaxis().set_visible(False)
        self.canvas_focus.draw()
        plt.close(self.focusfigure)

    def clear_align_canvas(self):
        plot=self.alignfigure.add_subplot(111)
        plot.get_xaxis().set_visible(False)
        plot.get_yaxis().set_visible(False)
        self.canvas_align.draw()
        plt.close(self.alignfigure)

    def clear_tile_canvas(self):
        plot=self.tilefigure.add_subplot(111)
        plot.get_xaxis().set_visible(False)
        plot.get_yaxis().set_visible(False)
        self.canvas_tile.draw()
        plt.close(self.tilefigure)

    def __repr__(self):
        '''
        Print known native Python attributes. 
        Also print found tk.Variable attributes. 
        
        tkinter.StringVar
        tkinter.IntVar
        tkinter.

        for e in dir(f2):
        x = getattr(f2, e)
         if type(x) is  tkinter.StringVar :
             print(f'{e} = yes')
         else:
             print(f'{e} = no')
        
        '''
        s = '\n'
        s += f'device_status = {self.device_status}\n'
        s += f'scale={self.scale}\n'
        s += f'assigned_heater = {self.assigned_heater}\n'
        return s

    #def __str__(self):
    #    s = self.__repr__()
    #    return s


###############################################################################
#           Main window Tabs/Sub-Frames
#           These do NOT self-layout.
#           Add all widgets here.
###############################################################################

class AutoTabFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(borderwidth=1, relief='groove')
        
        self.cf = ConfigFrame(self, self.controller)
        self.cf.pack(side='left',expand=True, fill='both')        
        
        wdirf =  WorkdirFrame(self.cf, self.controller)
        procf =  ProcessFrame(self.cf, self.controller)
        autof = AutomationFrame(self.cf, self.controller)
        calf = CalibrationFrame(self.cf, self.controller)

        self.lf = LogFrame(self, self.controller)
        self.lf.pack(side='left', expand=True, fill='both')

        errf = WarningFrame(self.lf, self.controller)
        notef = NotificationFrame(self.lf, self.controller)
        livef = LiveViewFrame(self.lf, self.controller)


class ManualTabFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(borderwidth=1, relief='groove')
        self.cf = ConfigFrame(self, controller)
        self.cf.pack(side='left', expand = True, fill = 'both')        
        #wf =  WorkdirFrame(self.cf, self.controller)
        #pf = ProcessFrame(self.cf, self.controller)

        self.lf = LogFrame(self, controller)
        self.lf.pack(side='left', expand = True, fill = 'both') 
        #ef = WarningFrame(self.lf, self.controller)
        #nf = NotificationFrame(self.lf, self.controller)
        #lv = LiveViewFrame(self.lf, self.controller)


class ConfigFrame(ttk.Frame):
    '''
    Contains widgets so configure and run processing.  
    '''
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(borderwidth=1, relief='groove')

class LogFrame(ttk.Frame):
    '''
    Contains log output information and live views.  
    '''
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller 
        self.configure(borderwidth=1, relief='groove')



###############################################################################
#                   Self-Contained Widgets
#               These self-layout within their frames. 
###############################################################################

class WorkdirFrame(ttk.Frame):
    '''
    Section 1. Choose work directory. 
    work_path

    
    '''
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(borderwidth=1, relief='groove')
        self.lbf = ttk.LabelFrame(self, text="Section 1 Choose work directory", width=600)
        self.lbf.grid(row=0, column=0, padx=1, pady=1, sticky='n')
        
        self.controller.work_path = tk.StringVar()
        self.controller.work_path.set(value=os.getcwd())

        self.work_path_lb = tk.Label(self.lbf, 
                                        text="Select your work directory:", 
                                        borderwidth=1, 
                                        relief="flat", 
                                        width=20,
                                        fg=widget_attr.BLACK_COLOR, 
                                        font=("Arial", 10) )
        self.work_path_lb.grid(row=0,column=0)

        self.work_path_field = tk.Entry( self.lbf, 
                                         relief="groove", 
                                         width=43,
                                         textvariable=self.controller.work_path)
        
        self.work_path_field.grid(row=0, column=1)

        self.browse_btn = tk.Button(self.lbf, 
                                         text="Browse", 
                                         bd=widget_attr.NORMAL_EDGE, 
                                         fg=widget_attr.NORMAL_COLOR,
                                         command=self.browse_handler)
        self.browse_btn.grid(row=0,column=2)

        self.exp_btn = tk.Button(self.lbf, 
                                      text="Fill experiment detail", 
                                      width=18,
                                      bd=widget_attr.NORMAL_EDGE, 
                                      fg=widget_attr.NORMAL_COLOR,
                                      command=self.exp_btn_handler)
        self.exp_btn.grid(row=0,column=3)
        self.pack(fill='x')

    def browse_handler(self):
        logging.debug(f'browse_button...')
        tempdir = self.search_for_file_path()
        self.controller.work_path.set(tempdir)
        self.work_path_field.config( textvariable=self.controller.work_path )

    def exp_btn_handler(self):
        work_path = self.controller.work_path.get()
        if work_path  == "":
            tk.messagebox.showinfo(title="Miss Input", 
                                   message="Please fill the work dirctory first!")
        else:
            ExperimentProfile(work_path, self.controller)

    def search_for_file_path(self):
        currdir = os.getcwd()
        logging.debug(f'initialdir={currdir}')
        tempdir = tk.filedialog.askdirectory(parent=self, 
                                                   initialdir=currdir, 
                                                   title='Please select a directory')
        logging.debug(f'user chose {tempdir}')
        if len(tempdir) > 0:
            print("You chose: %s" % tempdir)
        return tempdir
    

class ProcessFrame(ttk.Frame):
    '''
    Section 2. Fill process details 
    '''
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(borderwidth=1, relief='groove')
        self.lbf = tk.LabelFrame(self, 
                                 text="Section 2 Fill process details",
                                 width=600)
        #self.lbf.pack(side=tk.LEFT)
        self.lbf.grid(row=0,column=0)

        # Row One
        self.slice_per_slide_lb = tk.Label(self.lbf, 
                                                text="Slice per slide:", 
                                                bd=1, 
                                                relief="flat", 
                                                width=15,
                                                fg=widget_attr.BLACK_COLOR, 
                                                font=("Arial", 10))
        self.slice_per_slide_lb.grid(row=0,column=0)
        
        self.controller.slice_per_slide = tk.StringVar()
        self.slice_number_field = tk.Entry(self.lbf, 
                                           relief="groove", 
                                           width=10,
                                           textvariable=self.controller.slice_per_slide)
        self.slice_number_field.grid(row=0,column=1)

        self.controller.mock_alignment = tk.IntVar()
        self.controller.mock_alignment.set(0)
        self.mock_alignment_cbox = tk.Checkbutton( self.lbf, 
                                                   text="Skip Alignment",
                                                   fg=widget_attr.NORMAL_COLOR, 
                                                   variable=self.controller.mock_alignment, 
                                                   onvalue=1,
                                                   offvalue=0)
        self.mock_alignment_cbox.grid(row=0,column=2)

        self.controller.build_own_cycle_sequence_value = tk.IntVar()
        self.controller.build_own_cycle_sequence_value.set(0)
        self.build_own_cycle_sequence = tk.Checkbutton( self.lbf, 
                                                        text="Use existing protocol",
                                                        fg=widget_attr.NORMAL_COLOR,
                                                        variable=self.controller.build_own_cycle_sequence_value,
                                                        onvalue=1,
                                                        offvalue=0)
        self.build_own_cycle_sequence.grid(row=0,column=3)


        #self.current_cycle_lb = tk.Label(self.lbf, 
        #                                        text="Current Cycle:", 
        #                                        bd=1, 
        #                                        relief="flat", 
        #                                        width=15,
        #                                        fg=widget_attr.BLACK_COLOR)
        #self.current_cycle_lb.grid(row=0,column=4)



        #self.current_c = tk.StringVar()
        #self.current_cbox = tk.ttk.Combobox(self.lbf, 
        #                                    textvariable=self.current_c, 
        #                                    width=8)
        #self.current_cbox['value'] = ['geneseq', 'hyb', 'bcseq']
        #self.current_cbox['state'] = "readonly"
        #self.current_cbox.grid(row=0,column=5)


        #self.cycle_number = tk.Spinbox(self.lbf, from_=0, to=50, state="readonly", width=5)
        #self.cycle_number.grid(row=0,column=6)

        self.OR_lb = tk.Label(self.lbf, text="OR", bd=1, relief="flat", width=3,
                           fg=widget_attr.BLACK_COLOR,)
        self.OR_lb.grid(row=0,column=4)
        
        # Row Two
        self.recipe_btn = tk.Button(self.lbf, 
                                    text="Create Protocol", 
                                    command=self.recipe_btn_handler,
                                    bd=widget_attr.NORMAL_EDGE, 
                                    fg=widget_attr.NORMAL_COLOR)
        self.recipe_btn.grid(row=1,column=3)

        self.assign_heater_btn = tk.Button(self.lbf, 
                                           text="Assign Heaters", 
                                           command=self.assign_heater_popup,
                                           bd=widget_attr.NORMAL_EDGE, 
                                           fg=widget_attr.NORMAL_COLOR)
        self.assign_heater_btn.grid(row=1,column=4)

        # Row Three
        self.change_pixel_value = tk.IntVar()
        self.change_pixel_value.set(0)
        self.change_pixel = tk.Checkbutton(self.lbf, 
                                           text="change pixel size", 
                                           fg=widget_attr.NORMAL_COLOR, variable=self.change_pixel_value, onvalue=1,
                                           offvalue=0,
                                           command=self.change_pixel_handler,)
        self.change_pixel.grid(row=2,column=0)

        self.controller.pixel_size = tk.StringVar()
        self.controller.pixel_size.set("0.33")
        self.pixel_size_field = tk.Entry(self.lbf, 
                                         relief="groove", 
                                         width=6, 
                                         textvariable=self.controller.pixel_size)
        self.pixel_size_field.config(state=tk.DISABLED)
        self.pixel_size_field.grid(row=2,column=1)

        self.change_server_value = tk.IntVar()
        self.change_server_value.set(0)
        self.change_server_auto_cb = tk.Checkbutton(self.lbf, text="change storage server",
                                              
                                              fg=widget_attr.NORMAL_COLOR, 
                                              variable=self.change_server_value, 
                                              onvalue=1,
                                              offvalue=0,
                                              command=self.change_server )
        self.change_server_auto_cb.grid(row=2,column=2)

        self.server_account_lb = tk.Label( self.lbf, 
                                           text="server account:", 
                                           bd=1, 
                                           relief="flat", 
                                           width=10,
                                           fg=widget_attr.DISABLE_COLOR)
        self.server_account_lb.grid(row=2,column=3)

        self.account = tk.StringVar()
        self.account.set("imagestorage")
        self.account_field = tk.Entry(self.lbf, relief="groove", width=15, textvariable=self.account)
        self.account_field.config(state=tk.DISABLED)
        self.account_field.grid(row=2,column=4)

        self.server_lb = tk.Label(self.lbf, text="server name:", bd=1, relief="flat", width=10,
                               fg=widget_attr.DISABLE_COLOR)
        self.server_lb.grid(row=2,column=5)

        self.server = tk.StringVar()
        self.server.set(r"N:\\")
        self.server_field = tk.Entry(self.lbf, relief="groove", width=20, textvariable=self.server)
        self.server_field.config(state=tk.DISABLED)
        self.server_field.grid(row=2,column=6)

        # Row Four
        self.upload_aws_value = tk.IntVar()
        self.upload_aws_value.set(0)
        self.upload_aws = tk.Checkbutton(self.lbf, 
                                            text="upload to AWS", 
                                            fg=widget_attr.NORMAL_COLOR, 
                                            variable=self.upload_aws_value, 
                                            onvalue=1, 
                                            offvalue=0, 
                                            command=self.upload_to_aws)
        self.upload_aws.grid(row=3,column=0)

        self.aws_account_lb = tk.Label(self.lbf, text="AWS account:", bd=1, relief="flat", width=12,
                                    fg=widget_attr.DISABLE_COLOR)
        self.aws_account_lb.grid(row=3,column=1)

        self.aws = tk.StringVar()
        self.aws_account_field = tk.Entry(self.lbf, relief="groove", width=15, textvariable=self.aws)
        self.aws_account_field.config(state=tk.DISABLED)
        self.aws_account_field.grid(row=3, column=2)

        self.aws_password_lb = tk.Label(self.lbf, text="AWS password:", bd=1, relief="flat", width=15,
                                     fg=widget_attr.DISABLE_COLOR)
        self.aws_password_lb.grid(row=3, column=3)        
        
        self.aws_pwd = tk.StringVar()
        self.aws_pwd_field = tk.Entry(self.lbf, relief="groove", width=15, textvariable=self.aws_pwd)
        self.aws_pwd_field.config(state=tk.DISABLED)
        self.aws_pwd_field.grid(row=3, column=4)

        # Row Five
        self.info_btn = tk.Button(self.lbf, 
                                       text="Create Your Experiment",
                                       command=self.create_exp,
                                       bd=widget_attr.NORMAL_EDGE, 
                                       fg="#1473cc")
        self.info_btn.grid(row=4, column=3)
        self.pack(fill='x')

    def assign_heater_popup(self):
        self.heater_popup = tk.Tk()
        self.heater_popup.geometry("450x350")
        self.heater_popup.title("Assign heater")
 
        self.slide1_checked_value=tk.IntVar()
        self.slide1_cbox = tk.Checkbutton( self.heater_popup, 
                                        text="Slide 1 included", 
                                        command=self.assign_chamber1_heater, 
                                        fg=widget_attr.NORMAL_COLOR, 
                                        variable=self.slide1_checked_value, 
                                        onvalue=1,
                                        offvalue=0)

        self.slide1_cbox.grid(row=0, column=0,padx=10, pady=10, sticky="nsew")

        self.slide2_checked = tk.IntVar()
        self.slide2_checked.set(0)
        self.slide2_cbox = tk.Checkbutton(self.heater_popup, text="Slide 2 included",command=self.assign_chamber2_heater,
                                       fg=widget_attr.NORMAL_COLOR, variable=self.slide2_checked, onvalue=1,
                                       offvalue=0)
        self.slide2_cbox.grid(row=0, column=1,padx=10, pady=10, sticky="nsew")

        self.slide3_checked = tk.IntVar()
        self.slide3_checked.set(0)
        self.slide3_cbox = tk.Checkbutton(self.heater_popup, text="Slide3  included",command=self.assign_chamber3_heater,
                                       fg=widget_attr.NORMAL_COLOR, variable=self.slide3_checked, onvalue=1,
                                       offvalue=0)
        self.slide3_cbox.grid(row=0, column=2,padx=10, pady=10, sticky="nsew")

        figure = plt.Figure(figsize=(1, 2), dpi=100)
        slide_img1 = FigureCanvasTkAgg(figure, master=self.heater_popup)
        slide_img1.get_tk_widget().grid(row=1, column=0,padx=10, pady=10, sticky="nsew")
        slide_img2 = FigureCanvasTkAgg(figure, master=self.heater_popup)
        slide_img2.get_tk_widget().grid(row=1, column=1,padx=10, pady=10, sticky="nsew")
        slide_img3 = FigureCanvasTkAgg(figure, master=self.heater_popup)
        slide_img3.get_tk_widget().grid(row=1, column=2,padx=10, pady=10, sticky="nsew")
        slideimg= Image.open(os.path.join( get_resource_dir(),"slide.png"))
        plotslide1 = figure.add_subplot(111)
        plotslide1.imshow(slideimg)
        plotslide1.get_xaxis().set_visible(False)
        plotslide1.get_yaxis().set_visible(False)
        slide_img1.draw()
        slide_img2.draw()
        slide_img3.draw() 

        with open(os.path.join( get_resource_dir() ,"config_file", "Heat_stage.json"), 'r') as r:
            heater_list_cfg = json.load(r)
        heater_list=[i['heat_stage'] for i in heater_list_cfg]
        heater_list=heater_list+[""]

        self.heater1 = tk.StringVar()
        self.slide_heater1 = ttk.Combobox( self.heater_popup,
                                          textvariable=self.heater1, 
                                          width=10)
        self.slide_heater1['value'] = heater_list
        self.slide_heater1['state'] = "readonly"
        self.slide_heater1.grid(row=2,column=0,padx=10, pady=10, sticky="nsew")
        self.slide_heater1.config(state=tk.DISABLED)

        self.heater2 = tk.StringVar()
        self.slide_heater2 = ttk.Combobox(self.heater_popup, textvariable=self.heater2, width=10)
        self.slide_heater2['value'] = heater_list
        self.slide_heater2['state'] = "readonly"
        self.slide_heater2.grid(row=2, column=1,padx=10, pady=10, sticky="nsew")
        self.slide_heater2.config( state=tk.DISABLED )

        self.heater3 = tk.StringVar()
        self.slide_heater3 = ttk.Combobox(self.heater_popup, textvariable=self.heater3, width=10)
        self.slide_heater3['value'] = heater_list
        self.slide_heater3['state'] = "readonly"
        self.slide_heater3.grid(row=2, column=2,padx=10, pady=10, sticky="nsew")
        self.slide_heater3.config(state=tk.DISABLED)

        self.assign_heater_btn = tk.Button(self.heater_popup, 
                                           text="Confirm", 
                                           command=self.assign_heater_to_slide,
                                           bd=widget_attr.NORMAL_EDGE, 
                                           fg="#1473cc")
        self.assign_heater_btn.grid(row=3,column=1,padx=10, pady=10, sticky="nsew")

    def assign_chamber1_heater(self):
            self.slide_heater1.config(state=tk.NORMAL)

    def assign_chamber2_heater(self):
            self.slide_heater2.config(state=tk.NORMAL)

    def assign_chamber3_heater(self):
            self.slide_heater3.config(state=tk.NORMAL)

    def assign_heater_to_slide(self):
        self.assigned_heater=1
        self.controller.heater_dict={"chamber1": self.slide_heater1.get(),
                                     "chamber2": self.slide_heater2.get(),
                                     "chamber3": self.slide_heater3.get()}
        self.controller.heater_dict={k: v for k, v in self.controller.heater_dict.items() if v != ''}
        self.controller.chamber_number=len(self.controller.heater_dict)
        self.controller.chamber_list=list(self.controller.heater_dict.keys())
        logging.debug(f'assigned heaters to chambers: {self.controller.heater_dict}')
        self.heater_popup.destroy()

    def change_pixel_handler(self):
        if self.change_pixel_value.get() == 1:
            self.pixel_size_field.config(state=tk.NORMAL)
        else:
            t = self.pixel_size_field.get()
            self.controller.pixel_size.set(t)
            self.pixel_size_field.config(state=tk.DISABLED)

    def change_server(self):
       if self.change_server_value.get() == 1:
            self.server_account_lb.config(fg=widget_attr.NORMAL_COLOR)
            self.server_lb.config(fg=widget_attr.NORMAL_COLOR)
            self.server_field["state"]="normal"
            self.account_field["state"]="normal"
       else:
           self.server_account_lb.config(fg=widget_attr.DISABLE_COLOR)
           self.server_lb.config(fg=widget_attr.DISABLE_COLOR)
           self.server_field["state"] = "disable"
           self.account_field["state"] = "disable"

    def create_exp(self):
        self.controller.clear_error()
        # tk.clear_log()
        self.controller.clear_align_canvas()
        self.controller.clear_tile_canvas()
        self.controller.clear_focus_canvas()
        self.controller.slice_per_slide_reformat()
        self.cancel = 0
        self.controller.skip_alignment = self.controller.mock_alignment.get()
        self.controller.warning_stw.delete('1.0', tk.END)
        #if self.controller.work_path_field.get() == "":
        work_path = self.controller.work_path.get()
        logging.debug(f'retrieved work path: {work_path}')
        if work_path == "":
            tk.messagebox.showinfo(title="Wrong Input", message="work directory can't be empty")
            return
        self.controller.pos_path = work_path
        if not os.path.exists(os.path.join(self.controller.pos_path, "temp.txt")):
            open(os.path.join(self.controller.pos_path, "temp.txt"), 'w')
        if not os.path.exists(os.path.join(self.controller.pos_path, "log.txt")):
            open(os.path.join(self.controller.pos_path, "log.txt"), 'w')
        #self.server = self.account_field_auto.get() + "@" + self.server_field_auto.get()
        self.server =  self.server_field.get()
        
        self.controller.assign_cycle_detail()
        with open(os.path.join( get_resource_dir(), "config_file", "scope.json"), 'r') as r:
            self.scope_cfg=json.load(r)
            self.imwidth = self.scope_cfg[0]["imwidth"]

        try:
            self.scope = Microscope(self.scope_cfg, 
                               self.pos_path, 
                               self.slice_per_slide, 
                               self.server, 
                               self.skip_alignment, 
                               0 , 
                               system_path=self.system_path)
        except:
            tk.messagebox.showinfo(title="Config failure ",
                                message="Please run micromanager first!")
            update_error("Please run micromanager first!")
            return
        
        if self.assigned_heater == 0:
            self.controller.heater_dict={'chamber1': "heatstage1", 'chamber2': "heatstage2", 'chamber3': "heatstage3"}
            self.controller.chamber_number=3
            self.controller.chamber_list = list(self.heater_dict.keys())
        self.controller.fluidics = FluidicSystem( system_path=self.system_path,
                                       pos_path=self.pos_path,
                                       slide_heater_dictionary=self.heater_dict)
        self.all_autobtn_normal()

    def recipe_btn_handler(self):
        self.pb = ProcessBuilder(path=self.controller.work_path.get(),controller=self.controller )
        #self.pb.create_window( )

    def upload_to_aws(self):
        if self.upload_aws_value.get() == 1:
            self.aws_account_lb.config(fg=widget_attr.NORMAL_COLOR)
            self.aws_password_lb.config(fg=widget_attr.NORMAL_COLOR)
            self.aws_account_field["state"] = "normal"
            self.aws_pwd_field["state"] = "normal"
        else:
            self.aws_account_lb.config(fg=widget_attr.DISABLE_COLOR)
            self.aws_password_lb.config(fg=widget_attr.DISABLE_COLOR)
            self.aws_account_field["state"] = "disable"
            self.aws_pwd_field["state"] = "disable"




class AutomationFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller        
        self.configure(borderwidth=1, relief='groove')

        # Row One
        self.lbf = tk.LabelFrame(self, 
                                 text="Section 3 Automation functions", 
                                 width=600)
        self.lbf.grid(row=0, column=0, padx=3, pady=3, sticky="n")

        self.device_btn = tk.Button(self.lbf, 
                                    text="Devices configuration", 
                                    command=self.controller.config_device_popup,
                                    bd=widget_attr.NORMAL_EDGE, 
                                    fg=widget_attr.NORMAL_COLOR)
        self.device_btn["state"] = "disable"
        self.device_btn.grid(row=0,column=0)

        self.brain_btn = tk.Button(self.lbf, 
                                   text="Tissue Scanner (optional)", 
                                   command=self.controller.scan_tissue,
                                   bd=widget_attr.NORMAL_EDGE, 
                                   fg=widget_attr.NORMAL_COLOR)
        self.brain_btn["state"] = "disable"
        self.brain_btn.grid(row=0,column=1)

        self.prime_btn = tk.Button(self.lbf, 
                                   text="Prime lines", 
                                   command=self.controller.prime_btn_handler,
                                   bd=widget_attr.NORMAL_EDGE, 
                                   fg=widget_attr.NORMAL_COLOR)
        self.prime_btn["state"] = "disable"
        self.prime_btn.grid(row=0,column=2)

        self.fill_lb=tk.Label(self.lbf, text="Reagent:", bd=1, relief="flat", width=6,
                                     fg=widget_attr.BLACK_COLOR, font=("Arial", 10))
        self.fill_lb.grid(row=0,column=3)

        self.controller.reagent = tk.StringVar()
        self.reagent_list_cbox = tk.ttk.Combobox(self.lbf, 
                                                 textvariable=self.controller.reagent, width=8)
        self.reagent_ls=["water","PBST","IRM","CRM","USM","Incorporation Buffer",
                         "Iodoacetamide Blocker","FISH WASH","STRIP","DAPI","hyb oligos",
                        "bc oligos","gene oligos"]
        self.reagent_list_cbox['value'] = self.reagent_ls
        self.reagent_list_cbox['state'] = "readonly"
        self.reagent_list_cbox.grid(row=0, column=4)

        self.reagent_amount = tk.Spinbox(self.lbf, 
                                         from_=0.5, 
                                         to=10, 
                                         state="readonly", 
                                         increment=0.5, 
                                         width=5)
        self.reagent_amount.grid(row=0, column=5)

        self.inchamber_path = tk.IntVar()
        self.inchamber_path.set(1)
        self.inchamber_path_cbox = tk.Checkbutton(self.lbf, text="To chamber",
                                               fg=widget_attr.NORMAL_COLOR, variable=self.inchamber_path, onvalue=1,
                                               offvalue=0)
        self.inchamber_path_cbox.grid(row=0, column=6)

        self.fill_single_btn = tk.Button(self.lbf, 
                                         text="Fill", 
                                         command=self.controller.fill_single_reagent,
                                         bd=widget_attr.NORMAL_EDGE, 
                                         fg=widget_attr.NORMAL_COLOR)
        self.fill_single_btn["state"] = "disable"
        self.fill_single_btn.grid(row=0, column=7)


        # Row Two
        self.check_sequence_btn=tk.Button(self.lbf, 
                                          text="Check Sequences", 
                                          command=self.controller.check_sequence_handler,
                                          bd=widget_attr.NORMAL_EDGE, 
                                          fg=widget_attr.WARNING_COLOR)
        self.check_sequence_btn["state"] = "disable"

        self.start_sequence_btn = tk.Button(self.lbf, 
                                            text="Start Automation process",
                                            command=self.controller.start_btn_handler,
                                            bd=widget_attr.NORMAL_EDGE, 
                                            fg=widget_attr.NORMAL_COLOR)
        self.start_sequence_btn["state"] = "disable"
        self.cancel_sequence_btn = tk.Button(self.lbf, 
                                             text="Cancel Automation process", 
                                             command=self.controller.cancel_btn_handler,
                                             bd=widget_attr.NORMAL_EDGE, 
                                             fg=widget_attr.WARNING_COLOR)
        self.cancel_sequence_btn['state'] = "disable"
        
        self.wash_btn = tk.Button(self.lbf, 
                                  text="wash tubes", 
                                  command=self.controller.wash_btn_handler,
                                  bd=widget_attr.NORMAL_EDGE, 
                                  fg=widget_attr.NORMAL_COLOR)
        self.wash_btn['state'] = "disable"

        self.controller.avoid_wash= tk.IntVar()
        self.controller.avoid_wash.set(0)
        self.avoid_wash_cbox=tk.Checkbutton(self.lbf, text="Avoid wash chambers",
                                               fg=widget_attr.NORMAL_COLOR, 
                                               variable=self.controller.avoid_wash, 
                                               onvalue=1,
                                               offvalue=0)
        
        self.pack(fill='x')


class ManualFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.configure(borderwidth=1, relief='groove')

        self.section3_lbf_manual= tk.LabelFrame(self.manual_tab, text="Section 3 Manual functions", width=600)
        self.section3_lbf_manual.pack_propagate(False)
        self.section3_lbf_manual.grid(row=3, column=0, padx=3, pady=3, sticky="n")

        self.focus_btn = tk.Button(self.section3_lbf_manual, text="Step 1 Auto Focusing", command=self.controller.focus_btn_handler,
                                bd=widget_attr.NORMAL_EDGE, fg="#1473cc")
        self.focus_btn["state"] = "disable"

        self.align_btn = tk.Button(self.section3_lbf_manual, text="Step 2 Align with Cycle00", command=self.controller.align_btn_handler,
                                bd=widget_attr.NORMAL_EDGE, fg="#1473cc")
        self.align_btn["state"] = "disable"
        self.tile_btn = tk.Button(self.section3_lbf_manual, text="Step 3 Creat Tiles", command=self.controller.tile_btn_handler,
                               bd=widget_attr.NORMAL_EDGE, fg="#1473cc")
        self.tile_btn["state"] = "disable"
        self.max_btn = tk.Button(self.section3_lbf_manual, text="Step 4 Image and Maxprojection", command=self.controller.max_btn_handler,
                              bd=widget_attr.NORMAL_EDGE, fg="#1473cc")
        self.max_btn["state"] = "disable"

        self.cancel_image_btn = tk.Button(self.section3_lbf_manual, text="Cancel image process", command=self.controller.cancel_manual_process,
                                       bd=widget_attr.NORMAL_EDGE, fg=widget_attr.WARNING_COLOR)
        self.cancel_image_btn["state"] = "disable"


class CalibrationFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller 
        self.configure(borderwidth=1, relief='groove')

        self.lbf = tk.LabelFrame(self, 
                                 text="Section 4 Calibration Displays", 
                                 width=600)
        self.lbf.grid(row=0, column=0, padx=3, pady=3, sticky="n")
        self.focus_lb = tk.Label(self.lbf, 
                                 text="Focus shift", 
                                 bd=1, 
                                 relief="flat", 
                                 width=15,
                                 fg=widget_attr.BLACK_COLOR, 
                                 font=("Arial", 10))
        self.controller.focusfigure = plt.Figure( figsize=(2.5, 2.5), dpi=100)
        self.controller.canvas_focus = FigureCanvasTkAgg( self.controller.focusfigure, 
                                                          master=self.lbf)
        self.focus_lb.grid(row=0,column=0)
        self.controller.canvas_focus.get_tk_widget().grid(row=1,column=0) 

        self.align_lb = tk.Label(self.lbf, 
                                 text="XY-plane shift", 
                                 bd=1, 
                                 relief="flat", 
                                 width=15,
                                 fg=widget_attr.BLACK_COLOR, 
                                 font=("Arial", 10))
        self.controller.alignfigure = plt.Figure(figsize=(2.5, 2.5), dpi=100)
        self.controller.canvas_align = FigureCanvasTkAgg(self.controller.alignfigure, 
                                                         master=self.lbf)
        self.align_lb.grid(row=0,column=1)
        self.controller.canvas_align.get_tk_widget().grid(row=1,column=1)

        self.tile_lb = tk.Label(self.lbf, 
                                text="Tiles", 
                                bd=1, 
                                relief="flat", 
                                width=15,
                              fg=widget_attr.BLACK_COLOR, 
                              font=("Arial", 10))
        self.controller.tilefigure = plt.Figure(figsize=(2.5, 2.5), dpi=100)
        self.controller.canvas_tile = FigureCanvasTkAgg(self.controller.tilefigure, 
                                                        master=self.lbf)
        self.tile_lb.grid(row=0,column=2)
        self.controller.canvas_tile.get_tk_widget().grid(row=1,column=2)
        self.pack(fill='x')


class NotesFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(borderwidth=1, relief='groove')

        self.add_note = tk.LabelFrame(self.frame0, text="Section 4 Addition notes", width=600)
        #self.add_note.pack_propagate(False)
        self.add_note.grid(row=5, column=0, padx=3, pady=3, sticky="n")

        self.note_lb = tk.Label(self, text="Notes", bd=1, relief="flat", width=15,
                              fg=widget_attr.BLACK_COLOR, font=("Arial", 10))

        self.note_stw = tkst.ScrolledText( self,
            wrap=tk.WORD,
            width=60,
            height=2,
        )
        self.note_btn = tk.Button(self, 
                                  text="Send note to server",
                                  bd=widget_attr.NORMAL_EDGE, 
                                  fg=widget_attr.NORMAL_COLOR,
                                  command=self.save_to_note)
        self.pack(fill='x')

        
    def save_to_note(self):
        if not os.path.exists(os.path.join(os.getcwd(), "experiment_detail.txt")):
            open(os.path.join(os.getcwd(), "experiment_detail.txt"), 'a').close()
        txt=get_time()+self.note_stw.get("1.0", "end-1c")+"\n"
        f = open(os.path.join(os.getcwd(), "experiment_detail.txt"), "a")
        f.write(txt)
        f.close()
        server_path = '/mnt/imagestorage/' + self.pos_path[3:]
        self.linux_server=self.server
        try:
            cmd = "scp " + os.path.join(self.pos_path, "experiment_detail.txt") + " " + self.linux_server + ":" + server_path
            os.system(cmd)
            txt = get_time() + "local note saved to experiment_detail.txt, and uploaded to server!"+"\n"
            self.notification_frame.add_highlight_mainwindow(txt)

        except:
            txt=get_time()+"local note saved to experiment_detail.txt, upload to server is failed!"
            self.notification_frame.add_highlight_mainwindow(txt)


class WarningFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.controller.error_frame = self

        self.configure(borderwidth=1, relief='groove')
        self.warning_lb = tk.Label(self, 
                                   text="System warning", 
                                   bd=1, 
                                   relief="groove", 
                                   width=15,
                                   fg=widget_attr.BLACK_COLOR, 
                                   font=("Arial", 10))
        
        self.warning_lb.grid(row=0, column=0, pady=3, padx=3)
        self.controller.warning_stw = tkst.ScrolledText(self, 
                                             wrap=tk.WORD,
                                             bd=1, 
                                             relief="groove",
                                             width=80,
                                             height=4)
        self.controller.warning_stw.tag_config('warning', foreground="red")
        logging.debug(f'WarningFrame: layout out warning_stw.')
        self.controller.warning_stw.grid(row=1, column=0)
        logging.debug(f'WarningFrame: layout out WarningFrame.')
        self.pack(side='top')





class NotificationFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.controller.notification_frame = self
        self.configure(borderwidth=1, relief='groove')
        self.notification_lb = tk.Label(self, 
                                   text="System Notification", 
                                   bd=1, 
                                   relief="groove", 
                                   width=15,
                                   fg=widget_attr.BLACK_COLOR, 
                                   font=("Arial", 10))
        self.notification_lb.grid(row=2, column=0)

        self.notification_stw = tkst.ScrolledText( self,
                                                    wrap=tk.WORD,
                                                    width=45,
                                                    height=10)
        self.notification_stw.tag_config('highlight_from_scope', foreground='#3f51b5')  # <-- Change colors of texts tagged `name`
        self.notification_stw.tag_config('highlight_from_mainwindow', foreground='blue')
        self.notification_stw.tag_config('reagent_highlight_from_fluidics', foreground='#8a0788')
        self.notification_stw.tag_config('status_highlight_from_fluidics', foreground='#fcb900') # <-- Change colors of texts tagged `name`
        self.notification_stw.tag_config('device_highlight_from_device', foreground='black')
        self.notification_stw.grid(row=4, column=0)
        
        self.frame1 = ttk.Frame(self )
        self.process="Process"
        self.process_label = tk.Label(self.frame1, 
                                      text='Process', 
                                      bd=1, 
                                      relief="flat", 
                                      width=18,
                                      fg=widget_attr.BLACK_COLOR, 
                                      font=("Arial", 10))
        self.process_label.grid(row=0, column=0,pady=3)
        self.progressbar1 = ttk.Progressbar( self.frame1, 
                                                mode = 'indeterminate',
                                                length=250)
        self.progressbar1.grid(row=0, column=1, pady=3)
        self.frame1.grid(row=3, column=0, sticky="nsew")
        self.pack(side='top')


    def update_process_bar(self,i):
        self.progressbar1['value']=i
    
    def update_process_label(self, txt):
        self.process_label['text']=txt

    def clear_log(self):
        self.notification_stw.delete('1.0', tk.END)
    
    def add_highlight_from_scope(self, txt):
        self.notification_stw.insert(tk.END, txt, 'highlight_from_scope')
    
    def add_device_information(self, txt):
        self.notification_stw.insert(tk.END, txt, 'device_highlight_from_device')
    
    def add_fluidics_status(self, txt):
        self.notification_stw.insert(tk.END, txt, 'status_highlight_from_fluidics')
    
    def add_fluidics_reagent(self, txt):
        self.notification_stw.insert(tk.END, txt, 'reagent_highlight_from_fluidics')
    
    def add_highlight_mainwindow(self, txt):
        self.notification_stw.insert(tk.END, txt, 'highlight_from_mainwindow')


class LiveViewFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(borderwidth=1, relief='groove')
        self.liveview_lb = tk.Label(self, 
                                    text="Live view of Barcodes", 
                                    bd=1, 
                                    relief="groove", 
                                    width=15,
                                    fg=widget_attr.BLACK_COLOR, 
                                    font=("Arial", 10))
        self.liveview_lb.grid(row=0, column=0,pady=3,padx=3)

        self.controller.livefigure = plt.Figure(figsize=(4, 4), dpi=100)
        self.controller.livefigure.subplots_adjust(left=0.01, 
                                        bottom=0.01, 
                                        right=0.99, 
                                        top=0.99, 
                                        wspace=0, 
                                        hspace=0)

        self.controller.canvas_live = FigureCanvasTkAgg(self.controller.livefigure, master=self)
        self.controller.canvas_live.get_tk_widget().grid(row=1, 
                                              column=0, 
                                              padx=3, 
                                              pady=3, 
                                              sticky="w")

        self.pack(side='top')

    def draw_liveview(self, img):
        self.plot1 = self.controller.livefigure.add_subplot(111)
        self.plot1.imshow( img[500:1200, 500:1200, :])
        self.plot1.get_xaxis().set_visible(False)
        self.plot1.get_yaxis().set_visible(False)
        self.controller.canvas_live.draw()
        plt.close(self.controller.livefigure)
    
    def clear_liveview_canvas(self):
        self.controller.livefigure = plt.Figure( figsize=(4, 4), dpi=100)
        self.controller.livefigure.subplots_adjust(left=0.01, 
                                        bottom=0.01, 
                                        right=0.99, 
                                        top=0.99, 
                                        wspace=0, 
                                        hspace=0)
        self.controller.canvas_live = FigureCanvasTkAgg(self.livefigure, 
                                             master=self.frame)
        plt.close(self.controller.livefigure)


class ExperimentProfile(tk.Tk):
    
    def __init__(self, path, controller):
        super().__init__()
        self.controller = controller
        self.work_path=path
        self.title("Experiment details")
        self.geometry("450x500")
        self.lb1=tk.Label(self,text="Folder name on file:",width=30)
        self.filed1= tk.Entry(self, relief="groove", width=30)
        self.lb2 = tk.Label(self, text="Brain name:", width=20)
        self.filed2 = tk.Entry(self, relief="groove", width=30)
        self.lb6 = tk.Label(self, text="Slide numbers:", width=20)
        self.filed6 = tk.Entry(self, relief="groove", width=30)
        self.lb3 = tk.Label(self, text="Padlock probes:", width=20)
        self.filed3 = tk.Entry(self, relief="groove", width=30)
        self.lb4 = tk.Label(self, text="Library preparation date:", width=30)
        self.filed4 = tk.Entry(self, relief="groove", width=30)
        self.lb5 = tk.Label(self, text="Technician:", width=20)
        self.filed5 = tk.Entry(self, relief="groove", width=30)

        self.lb7 = tk.Label(self, text="Additonal note:", width=20)
        self.stw = tkst.ScrolledText( self, 
            wrap=tk.WORD,
            width=30,
            height=10,
        )
        self.btn = tk.Button(self, 
                             text="Save", 
                             command=self.save_experiment_detail, 
                             width=20
                             )
        self.lb1.place(x=20,y=10)
        self.filed1.place(x=160,y=10)
        self.lb2.place(x=20, y=40)
        self.filed2.place(x=160, y=40)
        self.lb6.place(x=20, y=70)
        self.filed6.place(x=160, y=70)
        self.lb3.place(x=20, y=100)
        self.filed3.place(x=160, y=100 )
        self.lb4.place(x=20, y=130)
        self.filed4.place(x=160, y=130 )
        self.lb5.place(x=20, y=160)
        self.filed5.place(x=160, y=160)
        self.lb7.place(x=20, y=190)
        self.stw.place(x=160, y=190)
        self.btn.place(x=120, y=420)

    def save_experiment_detail(self):
        txt=get_time()+"Folder name on file:"+self.filed1.get()+"\n"+"Brain name:"+self.filed2.get()+"\n"+"Slide numbers:"+self.filed6.get()+"\n"+"Padlock probes:"+self.filed3.get()+"\n"+"Library preparation date:"+self.filed4.get()+"\n"+"Technician:"+self.filed5.get() + "\n" +"Additonal note:"+self.stw.get("1.0", tk.END)+ "\n"
        wdir = self.controller.work_path.get()
        edfile = "experiment_detail.txt" 
        edpath = os.path.join( wdir, edfile)
        logging.debug(f'experiment_detail file path: {edpath}')
        if not os.path.exists(edpath):
            open(edpath , 'w')
        f = open(edpath , "a")
        f.write(txt)
        logging.debug(f'exp detail saved: {edpath}')
        f.close()
        self.destroy()


class ProcessBuilder(tk.Tk):
    
    def __init__(self, path, controller):
        super().__init__()
        self.controller = controller
        self.pos_path = path
        self.geometry("600x600")
        self.title("Recipe Builder")

        self.recipe_list = [i[0:-5] for i in os.listdir(os.path.join( get_resource_dir(), "reagent_sequence_file")) ]
        self.recipe_list.extend(["imagecycle00", "imagecycle_geneseq", "imagecycle_bcseq", "imagecycle_hyb"])
        self.recipe_list = [i[0:-5] for i in os.listdir( os.path.join( get_resource_dir(), "reagent_sequence_file",
                                                                                          "3_chamber_system_sequence")) if (i not in ["Fluidics_sequence_flush_all.json","Fluidics_sequence_fill_all.json"]) and ("user_defined" not in i)]
        self.recipe_list.extend(["Fluidics_sequence_user_defined","imagecycle00", "imagecycle_geneseq", "imagecycle_bcseq", "imagecycle_hyb"])

        self.dropdown = ttk.Combobox(self, width=35)        
        self.dropdown['values'] = self.recipe_list
        self.dropdown.current(0)
        self.dropdown.place(x=180, y=10)
        self.label1=tk.Label(self, text="Choose your process:", width=20)
        self.label1.place(x=30, y=10)
        self.listbox = tk.Listbox(self, width=50, height=25)
        self.listbox.place(x=80, y=80)
        self.scrollbar = tk.Scrollbar(self)
        self.scrollbar.place(x=380, y=80, height=405)
        self.listbox.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.listbox.yview)
        self.add_button = tk.Button(self, text="Add to recipe", command=self.add_option)
        self.add_button.place(x=80, y=40)
        self.withdraw_button = tk.Button(self, text="Withdraw selection", command=self.withdraw_option)
        self.withdraw_button.place(x=200, y=40)
        self.clear_button = tk.Button(self, text="Clear all", command=self.clear_option)
        self.clear_button.place(x=400, y=380)
        self.confirm_button = tk.Button(self, text="Confirm", command=self.confirm_option)
        self.confirm_button.place(x=400, y=420)

    def add_option(self):
        selected_option = self.dropdown.get()
        if selected_option=="Fluidics_sequence_bcseq01" or selected_option=="Fluidics_sequence_geneseq01":
            self.listbox.insert(tk.END, selected_option)
        elif selected_option=="imagecycle00":
            self.listbox.insert(tk.END, selected_option)
        elif selected_option=="Fluidics_sequence_bcseq02+" or selected_option=="Fluidics_sequence_geneseq02+":
            selected_option =selected_option[0:-3]
            ls= self.listbox.get(0, tk.END)
            try:
                n = max([int(i[-2:]) for i in ls if selected_option in i])+1
                selected_option = selected_option + str(n).zfill(2)
            except:
                selected_option=selected_option+str(2).zfill(2)
            self.listbox.insert(tk.END, selected_option)
        else:
            ls = self.listbox.get(0, tk.END)
            n = len([i for i in ls if selected_option in i])
            n=n+1
            selected_option = selected_option + str(n).zfill(2)
            self.listbox.insert(tk.END, selected_option)

    def withdraw_option(self):
        selected_index = self.listbox.curselection()
        if selected_index:
            self.listbox.delete(selected_index)

    def clear_option(self):
        self.listbox.delete(0, tk.END)

    def confirm_option(self):
        self.recipe_final_list=self.listbox.get(0, tk.END)
        df = pd.DataFrame(columns=["process"])
        df["process"] = self.recipe_final_list
        df.to_csv(os.path.join(self.pos_path, "protocol.csv"), index=False)
        txt = get_time() + 'protocol.csv file created!\n'
        self.controller.notification_frame.add_highlight_mainwindow(txt)
        self.destroy()
       

 