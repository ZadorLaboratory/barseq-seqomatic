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
######################################################

#
# https://github.com/clear-code-projects/tkinter-complete/tree/main 
# 

class Seqomatic(tk.Tk):
    '''
    Top-level front-end GUI code. 
    See: https://stackoverflow.com/questions/66249107/optimal-tkinter-file-structure
   
    '''        
    def __init__(self):
        super().__init__()       
        self.title("Seq-o-Matic")
        self.geometry("1500x800+100+100")
        self.color_array = COLOR_ARRAY
        img = tk.PhotoImage( file=os.path.join( get_resource_dir(), 'LOGO.png'))
        self.iconphoto(False, img)        

        # Top-level tabbed notebook
        self.notebook = tk.ttk.Notebook(self)
        #self.notebook.grid(row=0, column=0, sticky="nsew")
        self.notebook.pack(expand=True, fill='both')
        auto_frame = AutoTabFrame(self)
        auto_frame.pack(fill='both', expand=True)
        manual_frame = ManualTabFrame(self)
        manual_frame.pack(fill='both', expand=True)
        self.auto_image = tk.PhotoImage(file=os.path.join( get_resource_dir() , "auto_logo.png"))
        self.manual_image = tk.PhotoImage(file=os.path.join( get_resource_dir() , "hand.png"))       
        self.notebook.add(auto_frame, text='Auto System', image=self.auto_image, compound=tk.LEFT)
        self.notebook.add(manual_frame, text='Manual System', image=self.manual_image, compound=tk.LEFT)


###############################################################################
#           Main window Tabs, sub-frames
#           These do NOT self-layout.
#           Add all widgets here.
###############################################################################

class AutoTabFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.configure(borderwidth=1, relief='groove')
        self.cf = ConfigFrame(self)
        self.cf.pack(side='left', expand = True, fill = 'both')        
        
        wf =  WorkdirFrame(self.cf)
        #pf =  ProcessFrame(self.cf)

        self.lf = LogFrame(self)
        self.lf.pack(side='left', expand = True, fill = 'both')
        ef = WarningFrame(self.lf)


class ManualTabFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.configure(borderwidth=1, relief='groove')
        self.cf = ConfigFrame(self)
        self.cf.pack(side='left', expand = True, fill = 'both')        
        wf =  WorkdirFrame(self.cf)
        pf = ProcessFrame(self.cf)

        self.lf = LogFrame(self)
        self.lf.pack(side='left', expand = True, fill = 'both') 
        ef = WarningFrame(self.lf)
        #nf = NotificationFrame(self.lf)
        #lv = LiveViewFrame(self.lf)



class ConfigFrame(ttk.Frame):
    '''
    Contains widgets so configure and run processing.  
    '''
    def __init__(self, parent):
        super().__init__(parent)
        self.configure(borderwidth=1, relief='groove')

class LogFrame(ttk.Frame):
    '''
    Contains log output information and live views.  
    '''
    def __init__(self, parent):
        super().__init__(parent) 
        self.configure(borderwidth=1, relief='groove')

###############################################################################
#                   Widgets
#               These self-layout within their frames. 
###############################################################################

class WorkdirFrame(ttk.Frame):
    '''
    Section 1. Choose work directory. 
    '''
    def __init__(self, parent):
        super().__init__(parent)
        self.configure(borderwidth=1, relief='groove')
        self.lbf = ttk.LabelFrame(self, text="Section 1 Choose work directory", width=600)
        self.lbf.grid(row=0, column=0, padx=1, pady=1, sticky='n')
        
        self.path = tk.StringVar()
        self.work_path = tk.Label(self.lbf, 
                                        text="Select your work directory:", 
                                        borderwidth=1, 
                                        relief="flat", 
                                        width=20,
                                        fg=widget_attr.BLACK_COLOR, 
                                        font=("Arial", 10) )
        self.work_path.grid(row=0,column=0)

        self.work_path_field = tk.Entry(self.lbf, 
                                         relief="groove", 
                                         width=43)
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
        self.grid(row=0, column=0, sticky='nsew', padx=5, pady=5 )

    def browse_handler(self):
        logging.debug(f'browse_button...')
        self.tempdir = self.search_for_file_path()
        self.path.set(self.tempdir)
        self.work_path_field.config(textvariable=self.path)
    
    def search_for_file_path(self):
        self.currdir = os.getcwd()
        self.tempdir = tk.filedialog.askdirectory(parent=self, 
                                               initialdir=self.currdir, 
                                               title='Please select a directory')
        if len(self.tempdir) > 0:
            print("You chose: %s" % self.tempdir)
        return self.tempdir
    
    def exp_btn_handler(self):
        if self.work_path_field.get() == "":
            tk.messagebox.showinfo(title="Miss Input", message="Please fill the work dirctory first!")
        else:
            work_path = self.work_path_field.get()
            ExperimentProfile( work_path)


class ProcessFrame(ttk.Frame):
    '''
    Section 2. Fill process details 
    '''
    def __init__(self, parent):
        super().__init__(parent)
        self.configure(borderwidth=1, relief='groove')
        self.lbf = tk.LabelFrame(self, 
                                 text="Section 2 Fill process details",
                                 width=600)
        self.lbf.grid(row=0, column=0, padx=3, pady=3,sticky="n")

        self.slice_per_slide_lb = tk.Label(self.lbf, 
                                                text="Slice per slide:", 
                                                bd=1, 
                                                relief="flat", 
                                                width=15,
                                                fg=widget_attr.BLACK_COLOR, 
                                                font=("Arial", 10))
        
        self.slice_number_field = tk.Entry(self.lbf, 
                                           relief="groove", width=10)

        self.mock_alignment = tk.IntVar()
        self.mock_alignment.set(0)
        self.mock_alignment_cbox = tk.Checkbutton(self.lbf, text="Skip Alignment",
                                               fg=widget_attr.NORMAL_COLOR, variable=self.mock_alignment, onvalue=1,
                                               offvalue=0)

        self.cycle_number = tk.Spinbox(self.lbf, from_=0, to=50, state="readonly", width=5)


        self.build_own_cycle_sequence_value = tk.IntVar()
        self.build_own_cycle_sequence_value.set(0)
        self.build_own_cycle_sequence = tk.Checkbutton(self.lbf, 
                                                       text="Use protocol in work directory",
                                                    fg=widget_attr.NORMAL_COLOR,
                                                    variable=self.build_own_cycle_sequence_value,
                                                    onvalue=1,
                                                    offvalue=0)

        self.current_c = tk.StringVar()
        self.current_cbox = tk.ttk.Combobox(self.lbf, 
                                            textvariable=self.current_c, width=8)
        self.current_cbox['value'] = ['geneseq', 'hyb', 'bcseq']
        self.current_cbox['state'] = "readonly"

        self.OR_lb = tk.Label(self.lbf, text="OR", bd=1, relief="flat", width=3,
                           fg=widget_attr.BLACK_COLOR, font=("Arial", 10))

        self.recipe_btn = tk.Button(self.lbf, 
                                    text="Create Protocol", 
                                    command=self.recipe_btn_handler,
                                    bd=widget_attr.NORMAL_EDGE, 
                                    fg=widget_attr.NORMAL_COLOR)
        self.assign_heater_btn = tk.Button(self.lbf, 
                                           text="Assign Heaters", 
                                           command=self.assign_heater,
                                           bd=widget_attr.NORMAL_EDGE, 
                                           fg=widget_attr.NORMAL_COLOR)


        self.change_pixel_value = tk.IntVar()
        self.change_pixel_value.set(0)
        self.change_pixel = tk.Checkbutton(self.lbf, 
                                           text="change pixel size", 
                                           fg=widget_attr.NORMAL_COLOR, variable=self.change_pixel_value, onvalue=1,
                                           offvalue=0,
                                           command=self.change_pixel_handler,)

        self.pixel_size = tk.StringVar()
        self.pixel_size.set("0.33")
        self.pixel_size_field = tk.Entry(self.lbf, relief="groove", width=6, textvariable=self.pixel_size)
        self.pixel_size_field.config(state=tk.DISABLED)

        self.change_server_value = tk.IntVar()
        self.change_server_value.set(0)
        self.change_server_auto_cb = tk.Checkbutton(self.lbf, text="change storage server",
                                              
                                              fg=widget_attr.NORMAL_COLOR, 
                                              variable=self.change_server_value, 
                                              onvalue=1,
                                              offvalue=0,
                                              command=self.change_server )

        self.server_account_lb = tk.Label(self.lbf, text="server account:", bd=1, relief="flat", width=10,
                                       fg=widget_attr.DISABLE_COLOR, font=("Arial", 10))
        self.account = tk.StringVar()
        self.account.set("imagestorage")
        self.account_field_auto = tk.Entry(self.lbf, relief="groove", width=15, textvariable=self.account)
        self.account_field_auto.config(state=tk.DISABLED)


        self.server_lb = tk.Label(self.lbf, text="server name:", bd=1, relief="flat", width=10,
                               fg=widget_attr.DISABLE_COLOR, font=("Arial", 10))

        self.server = tk.StringVar()
        self.server.set(r"N:\\")
        self.server_field_auto = tk.Entry(self, relief="groove", width=20, textvariable=self.server)
        self.server_field_auto.config(state=tk.DISABLED)

        self.upload_aws_value = tk.IntVar()
        self.upload_aws_value.set(0)
        self.upload_aws_auto = tk.Checkbutton(self, 
                                              text="upload to AWS", 
                                            fg=widget_attr.NORMAL_COLOR, 
                                            variable=self.upload_aws_value, 
                                            onvalue=1, 
                                            offvalue=0, 
                                            command=self.upload_to_aws,)
        
        self.aws_account_lb_auto = tk.Label(self, text="AWS account:", bd=1, relief="flat", width=12,
                                    fg=widget_attr.DISABLE_COLOR, font=("Arial", 10))

        self.aws = tk.StringVar()
        self.aws_account_field_auto = tk.Entry(self, relief="groove", width=20, textvariable=self.aws)
        self.aws_account_field_auto.config(state=tk.DISABLED)

        self.aws_password_lb_auto = tk.Label(self, text="AWS password:", bd=1, relief="flat", width=15,
                                     fg=widget_attr.DISABLE_COLOR, font=("Arial", 10))
        self.aws_pwd = tk.StringVar()
        self.aws_pwd_field_auto = tk.Entry(self, relief="groove", width=20, textvariable=self.aws_pwd)
        self.aws_pwd_field_auto.config(state=tk.DISABLED)


        self.info_btn_auto = tk.Button(self, 
                                       text="Create Your Experiment",
                                       command=self.create_exp,
                                       bd=widget_attr.NORMAL_EDGE, 
                                       fg="#1473cc")
        
        self.grid(row=0, column=0, sticky='nsew', padx=5, pady=5 )

    def assign_heater(self):
        self.heater_popup = tk.Tk()
        self.heater_popup.geometry("410x350")
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
        self.slide_heater1 = ttk.Combobox( self.heater_popup,textvariable=self.heater1, width=10)
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

        self.assign_heater_btn = Button(self.heater_popup, text="Confirm", command=self.assign_heater_to_slide,
                               bd=widget_attr.NORMAL_EDGE, fg="#1473cc")
        self.assign_heater_btn.grid(row=3,column=1,padx=10, pady=10, sticky="nsew")

    def assign_chamber1_heater(self):
            self.slide_heater1.config(state=tk.NORMAL)

    def assign_chamber2_heater(self):
            self.slide_heater2.config(state=tk.NORMAL)

    def assign_chamber3_heater(self):
            self.slide_heater3.config(state=tk.NORMAL)


    def assign_heater_to_slide(self):
        self.assigned_heater=1
        self.heater_dict={"chamber1":self.slide_heater1.get(),
                          "chamber2":self.slide_heater2.get(),
                          "chamber3":self.slide_heater3.get()}
        self.heater_dict={k: v for k, v in self.heater_dict.items() if v != ''}
        self.chamber_number=len(self.heater_dict)
        self.chamber_list=list(self.heater_dict.keys())
        self.heater_popup.destroy()

    def change_pixel_handler(self):
        if self.change_pixel_value.get() == 1:
            self.pixel_size_field.config(state=tk.NORMAL)
        else:
            t = self.pixel_size_field.get()
            self.pixel_size.set(t)
            self.pixel_size_field.config(state=tk.DISABLED)

    def change_server(self):
       if self.change_server_value.get() == 1:
            self.server_account_lb_auto.config(fg=widget_attr.NORMAL_COLOR)
            self.server_lb_auto.config(fg=widget_attr.NORMAL_COLOR)
            self.server_field_auto["state"]="normal"
            self.account_field_auto["state"]="normal"
       else:
           self.server_account_lb_auto.config(fg=widget_attr.DISABLE_COLOR)
           self.server_lb_auto.config(fg=widget_attr.DISABLE_COLOR)
           self.server_field_auto["state"] = "disable"
           self.account_field_auto["state"] = "disable"

    def create_exp(self):
        self.clear_error()
        tk.clear_log()
        self.clear_align_canvas()
        self.clear_tile_canvas()
        self.clear_focus_canvas()
        self.slice_per_slide_reformat()
        self.cancel = 0
        self.skip_alignment = self.mock_alignment.get()
        self.warning_stw.delete('1.0', tk.END)
        if self.work_path_field_auto.get() == "":
            tk.messagebox.showinfo(title="Wrong Input", message="work directory can't be empty")
            return
        self.pos_path = self.work_path_field_auto.get()
        if not os.path.exists(os.path.join(self.pos_path, "temp.txt")):
            open(os.path.join(self.pos_path, "temp.txt"), 'w')
        if not os.path.exists(os.path.join(self.pos_path, "log.txt")):
            open(os.path.join(self.pos_path, "log.txt"), 'w')
        #self.server = self.account_field_auto.get() + "@" + self.server_field_auto.get()
        self.server =  self.server_field_auto.get()
        self.assign_cycle_detail()
        with open(os.path.join("config_file", "scope.json"), 'r') as r:
            self.scope_cfg=json.load(r)
            self.imwidth = self.scope_cfg[0]["imwidth"]

        try:
            self.scope = scope(self.scope_cfg, 
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
        
        if self.assigned_heater==0:
            self.heater_dict={'chamber1': "heatstage1", 'chamber2': "heatstage2", 'chamber3': "heatstage3"}
            self.chamber_number=3
            self.chamber_list = list(self.heater_dict.keys())
        self.fluidics = FluidicSystem(system_path=self.system_path,pos_path=self.pos_path,slide_hearter_dictionary=self.heater_dict)
        self.all_autobtn_normal()


    def recipe_btn_handler(self):
        self.pb = ProcessBuilder( parent_window=self )
        self.pb.create_window( self.work_path_field_auto.get())

    def upload_to_aws(self):
        if self.upload_aws_value.get() == 1:
            self.aws_account_lb_auto.config(fg=widget_attr.NORMAL_COLOR)
            self.aws_password_lb_auto.config(fg=widget_attr.NORMAL_COLOR)
            self.aws_account_field_auto["state"] = "normal"
            self.aws_pwd_field_auto["state"] = "normal"
        else:
            self.aws_account_lb_auto.config(fg=widget_attr.DISABLE_COLOR)
            self.aws_password_lb_auto.config(fg=widget_attr.DISABLE_COLOR)
            self.aws_account_field_auto["state"] = "disable"
            self.aws_pwd_field_auto["state"] = "disable"


class AutomationFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)        
        self.configure(borderwidth=1, relief='groove')


        self.section3_lbf_auto = tk.LabelFrame(self.auto_tab, text="Section 3 Automation functions", width=600)
        self.section3_lbf_auto.pack_propagate(False)
        self.section3_lbf_auto.grid(row=3, column=0, padx=3, pady=3, sticky="n")

        self.device_btn = tk.Button(self.frame5, 
                                    text="Devices configuration", 
                                    command=self.config_device,
                                    bd=widget_attr.NORMAL_EDGE, 
                                    fg=widget_attr.NORMAL_COLOR)
        self.device_btn["state"] = "disable"
        self.brain_btn = tk.Button(self.frame5, 
                                   text="Tissue Scanner (optional)", 
                                   command=self.scan_tissue,
                                   bd=widget_attr.NORMAL_EDGE, 
                                   fg=widget_attr.NORMAL_COLOR)
        self.brain_btn["state"] = "disable"
        self.prime_btn = tk.Button(self.frame5, 
                                   text="Prime lines", 
                                   command=self.prime_btn_handler,
                                   bd=widget_attr.NORMAL_EDGE, 
                                   fg=widget_attr.NORMAL_COLOR)
        self.prime_btn["state"] = "disable"

        self.fill_lb=tk.Label(self.frame5, text="Reagent:", bd=1, relief="flat", width=6,
                                     fg=widget_attr.BLACK_COLOR, font=("Arial", 10))

        self.reagent = tk.StringVar()
        self.reagent_list_cbox = tk.ttk.Combobox(self.frame5, 
                                                 textvariable=self.reagent, width=8)
        self.reagent_ls=["water","PBST","IRM","CRM","USM","Incorporation Buffer",
                         "Iodoacetamide Blocker","FISH WASH","STRIP","DAPI","hyb oligos",
                        "bc oligos","gene oligos"]
        self.reagent_list_cbox['value'] = self.reagent_ls
        self.reagent_list_cbox['state'] = "readonly"

        self.reagent_amount = tk.Spinbox(self, 
                                         from_=0.5, 
                                         to=10, 
                                         state="readonly", 
                                         increment=0.5, 
                                         width=5)

        self.inchamber_path = tk.IntVar()
        self.inchamber_path.set(1)
        self.inchamber_path_cbox = tk.Checkbutton(self.frame5, text="To chamber",
                                               fg=widget_attr.NORMAL_COLOR, variable=self.inchamber_path, onvalue=1,
                                               offvalue=0)

        self.fill_single_btn = tk.Button(self.frame5, 
                                         text="Fill", 
                                         command=self.fill_single_reagent,
                                         bd=widget_attr.NORMAL_EDGE, 
                                         fg=widget_attr.NORMAL_COLOR)
        self.fill_single_btn["state"] = "disable"

        self.check_sequence_btn=tk.Button(self.frame6, text="Check Sequences", command=self.check_sequence_handler,
                                       bd=widget_attr.NORMAL_EDGE, fg=widget_attr.WARNING_COLOR)
        self.check_sequence_btn["state"] = "disable"

        self.start_sequence_btn = tk.Button(self.frame6, 
                                            text="Start Automation process",
                                            command=self.start_btn_handler,
                                            bd=widget_attr.NORMAL_EDGE, 
                                            fg=widget_attr.NORMAL_COLOR)
        self.start_sequence_btn["state"] = "disable"
        self.cancel_sequence_btn = tk.Button(self.frame6, text="Cancel Automation process", command=self.cancel_btn_handler,
                                          bd=widget_attr.NORMAL_EDGE, 
                                          fg=widget_attr.WARNING_COLOR)
        self.cancel_sequence_btn['state'] = "disable"
        
        self.wash_btn = tk.Button(self.frame6, text="wash tubes", command=self.wash_btn_handler,
                               bd=widget_attr.NORMAL_EDGE, fg=widget_attr.NORMAL_COLOR)
        self.wash_btn['state'] = "disable"

        self.avoid_wash= tk.IntVar()
        self.avoid_wash.set(0)
        self.avoid_wash_cbox=tk.Checkbutton(self.frame6, text="Avoid wash chambers",
                                               fg=widget_attr.NORMAL_COLOR, variable=self.avoid_wash, onvalue=1,
                                               offvalue=0)
        


class ManualFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.configure(borderwidth=1, relief='groove')

        self.section3_lbf_manual= tk.LabelFrame(self.manual_tab, text="Section 3 Manual functions", width=600)
        self.section3_lbf_manual.pack_propagate(False)
        self.section3_lbf_manual.grid(row=3, column=0, padx=3, pady=3, sticky="n")

        self.focus_btn = tk.Button(self.section3_lbf_manual, text="Step 1 Auto Focusing", command=self.focus_btn_handler,
                                bd=widget_attr.NORMAL_EDGE, fg="#1473cc")
        self.focus_btn["state"] = "disable"

        self.align_btn = tk.Button(self.section3_lbf_manual, text="Step 2 Align with Cycle00", command=self.align_btn_handler,
                                bd=widget_attr.NORMAL_EDGE, fg="#1473cc")
        self.align_btn["state"] = "disable"
        self.tile_btn = tk.Button(self.section3_lbf_manual, text="Step 3 Creat Tiles", command=self.tile_btn_handler,
                               bd=widget_attr.NORMAL_EDGE, fg="#1473cc")
        self.tile_btn["state"] = "disable"
        self.max_btn = tk.Button(self.section3_lbf_manual, text="Step 4 Image and Maxprojection", command=self.max_btn_handler,
                              bd=widget_attr.NORMAL_EDGE, fg="#1473cc")
        self.max_btn["state"] = "disable"

        self.cancel_image_btn = tk.Button(self.section3_lbf_manual, text="Cancel image process", command=self.cancel_manual_process,
                                       bd=widget_attr.NORMAL_EDGE, fg=widget_attr.WARNING_COLOR)
        self.cancel_image_btn["state"] = "disable"






class CalibrationFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.configure(borderwidth=1, relief='groove')

        self.focus_lb = tk.Label(self.frame7, text="Focus shift", bd=1, relief="flat", width=15,
                             fg=widget_attr.BLACK_COLOR, font=("Arial", 10))
        self.align_lb = tk.Label(self.frame7, text="XY-plane shift", bd=1, relief="flat", width=15,
                              fg=widget_attr.BLACK_COLOR, font=("Arial", 10))
        self.tile_lb = tk.Label(self.frame7, text="Tiles", bd=1, relief="flat", width=15,
                              fg=widget_attr.BLACK_COLOR, font=("Arial", 10))

        self.focusfigure = plt.Figure(figsize=(2.5, 2.5), dpi=100)
        self.canvas_focus = FigureCanvasTkAgg(self.focusfigure, master=self)
        self.alignfigure = plt.Figure(figsize=(2.5, 2.5), dpi=100)
        self.canvas_align = FigureCanvasTkAgg(self.alignfigure, master=self)
        self.tilefigure = plt.Figure(figsize=(2.5, 2.5), dpi=100)
        self.canvas_tile = FigureCanvasTkAgg(self.tilefigure, master=self)




class NotesFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.configure(borderwidth=1, relief='groove')


        self.section4_addtion_note = tk.LabelFrame(self.frame0, text="Section 4 Addition notes", width=600)
        self.section4_addtion_note.pack_propagate(False)
        self.section4_addtion_note.grid(row=5, column=0, padx=3, pady=3, sticky="n")

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
            self.parent_window.add_highlight_mainwindow(txt)

        except:
            txt=get_time()+"local note saved to experiment_detail.txt, upload to server is failed!"
            self.parent_window.add_highlight_mainwindow(txt)


class WarningFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.configure(borderwidth=1, relief='groove')
        self.warning_lb = tk.Label(self, 
                                   text="System warning", 
                                   bd=1, 
                                   relief="groove", 
                                   width=15,
                                   fg=widget_attr.BLACK_COLOR, 
                                   font=("Arial", 10))
        
        self.warning_lb.grid(row=0, column=0, pady=3,padx=3)
        self.warning_stw = tkst.ScrolledText(self, 
                                             wrap=tk.WORD,
                                             bd=1, 
                                             relief="groove",
                                             width=80,
                                             height=4)
        self.warning_stw.tag_config('warning', foreground="red")
        self.warning_stw.grid(row=1, column=0)
        self.grid(row=0, column=0, sticky='nsew', padx=1, pady=1 )

    def update_error(self, txt):
        self.warning_stw.insert(END, txt, 'warning')

    def clear_error(self):
        self.warning_stw.delete('1.0', tk.END)


class NotificationFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
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
        self.grid(row=0, column=0, sticky='nsew', padx=1, pady=1 )

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
    def __init__(self, parent):
        super().__init__(parent)
        self.configure(borderwidth=1, relief='groove')
        self.liveview_lb = tk.Label(self, 
                                    text="Live view of Barcodes", 
                                    bd=1, 
                                    relief="groove", 
                                    width=15,
                                    fg=widget_attr.BLACK_COLOR, 
                                    font=("Arial", 10))
        self.liveview_lb.grid(row=0, column=0,pady=3,padx=3)

        self.livefigure = plt.Figure(figsize=(4, 4), dpi=100)
        self.livefigure.subplots_adjust(left=0.01, 
                                        bottom=0.01, 
                                        right=0.99, 
                                        top=0.99, 
                                        wspace=0, 
                                        hspace=0)

        self.canvas_live = FigureCanvasTkAgg(self.livefigure, master=self)
        self.canvas_live.get_tk_widget().grid(row=1, 
                                              column=0, 
                                              padx=3, 
                                              pady=3, 
                                              sticky="w")

        self.grid(row=0, column=0, sticky='nsew', padx=1, pady=1 )

    def draw_liveview(self, img):
        self.plot1 = self.livefigure.add_subplot(111)
        self.plot1.imshow( img[500:1200, 500:1200, :])
        self.plot1.get_xaxis().set_visible(False)
        self.plot1.get_yaxis().set_visible(False)
        self.canvas_live.draw()
        plt.close(self.livefigure)
    
    def clear_liveview_canvas(self):
        self.livefigure = plt.Figure( figsize=(4, 4), dpi=100)
        self.livefigure.subplots_adjust(left=0.01, 
                                        bottom=0.01, 
                                        right=0.99, 
                                        top=0.99, 
                                        wspace=0, 
                                        hspace=0)
        self.canvas_live = FigureCanvasTkAgg(self.livefigure, 
                                             master=self.frame)
        plt.close(self.livefigure)



class ExperimentProfile(tk.Tk):
    
    def __init__(self, path):
        super().__init__()
        self.pos_path=path
        self.title("Experiment details")
        self.geometry("450x500")
        self.lb1=tk.Label(self,text="Folder name on file:",width=20)
        self.filed1= tk.Entry(self, relief="groove", width=30)
        self.lb2 = tk.Label(self, text="Brain name:", width=20)
        self.filed2 = tk.Entry(self, relief="groove", width=30)
        self.lb3 = tk.Label(self, text="Padlock probes:", width=20)
        self.filed3 = tk.Entry(self, relief="groove", width=30)
        self.lb4 = tk.Label(self, text="Library preparation date:", width=20)
        self.filed4 = tk.Entry(self, relief="groove", width=30)
        self.lb5 = tk.Label(self, text="Technician:", width=20)
        self.filed5 = tk.Entry(self, relief="groove", width=30)
        self.lb6 = tk.Label(self, text="Slide numbers:", width=20)
        self.filed6 = tk.Entry(self, relief="groove", width=30)
        self.lb7 = tk.Label(self, text="Additonal note:", width=20)
        self.stw = tkst.ScrolledText( self, 
            wrap=tk.WORD,
            width=30,
            height=10,
        )
        self.btn = tk.Button(self, text="Save", command=self.save, width=20
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

    def save(self):
        txt=get_time()+"Folder name on file:"+self.filed1.get()+"\n"+"Brain name:"+self.filed2.get()+"\n"+"Slide numbers:"+self.filed6.get()+"\n"+"Padlock probes:"+self.filed3.get()+"\n"+"Library preparation date:"+self.filed4.get()+"\n"+"Technician:"+self.filed5.get() + "\n" +"Additonal note:"+self.stw.get("1.0", tk.END)+ "\n"
        if not os.path.exists(os.path.join(self.pos_path, "experiment_detail.txt")):
            open(os.path.join("E:\\",self.pos_path, "experiment_detail.txt"), 'w')
        f = open(os.path.join("E:\\",self.pos_path, "experiment_detail.txt"), "a")
        f.write(txt)
        f.close()
        self.destroy()


class ProcessBuilder(tk.Tk):
    
    def __init__(self, path):
        super().__init__()
        
        self.pos_path = path
        self.geometry("500x500")
        self.title("Recipe Builder")
        self.recipe_list = [i[0:-5] for i in os.listdir(os.path.join( get_resource_dir(), "reagent_sequence_file")) ]
        self.recipe_list.extend(["imagecycle00", "imagecycle_geneseq", "imagecycle_bcseq", "imagecycle_hyb"])
        
        self.dropdown = ttk.Combobox(self,width=35)
        self.recipe_list = [i[0:-5] for i in os.listdir( os.path.join( get_resource_dir(),"reagent_sequence_file","3_chamber_system_sequence")) if (i not in ["Fluidics_sequence_flush_all.json","Fluidics_sequence_fill_all.json"]) and ("user_defined" not in i)]
        self.recipe_list.extend(["Fluidics_sequence_user_defined","imagecycle00", "imagecycle_geneseq", "imagecycle_bcseq", "imagecycle_hyb"])
        self.dropdown['values'] = self.recipe_list
        self.dropdown.current(0)
        self.dropdown.place(x=180, y=10)
        self.label1=tk.Label(self,text="Choose your process:",width=20)
        self.label1.place(x=30,y=10)
        self.listbox = tk.Listbox(self, width=50, height=25)
        self.listbox.place(x=80,y=80)
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
        self.parent_window.add_highlight_mainwindow(txt)
        self.destroy()
        





###############################################################################
#
#                       OLD UNREFACTORED CODE
#
###############################################################################





# was WindowWidgets.py
class OldCode:
    def __init__(self, mainwindow, tkapp, path):
        self.device_status = {
            "syringe_pump_group": 0,
            "selector_group": 0,
            "heater_group": 0}
        self.scale=1000 #unit ml to ul
        self.assigned_heater=0

    def check_sequence_handler(self):
        t1 = Thread(target=self.check_sequence)
        t1.start()

    def check_sequence(self):
        self.parent_window.add_highlight_mainwindow("Start checking the sequences.....\n")
        self.all_autobtn_disable()
        fluidics_sequence=[i for i in self.process_ls if "Fluidics" in i]
        reagent_dict=[str(i) for i in list(self.fluidics.selector_fluidics_dict.keys())]
        reagent_dict.append("null")
        speed_dict=[int(i) for i in list(self.fluidics.syringe_pump_speed_dict.keys())]
        print(reagent_dict)
        print(speed_dict)

        reagent_used = {}
        for sequence in fluidics_sequence:
            Sequence=self.fluidics.find_protocol(sequence)
            Import=0
            Export=0
            for i in range(len(Sequence)):
                step=Sequence[i]
                if step['device']=="pump":
                    if not isinstance(step['source'],str):
                        update_error(f"Find error in source format in {sequence} step {i}\n")

                    if not step['source'] in reagent_dict:
                        update_error(f"Find unavailable reagent in {sequence} step {i}\n")

                    if  step['speed_code'] <=21:
                        update_error(f"One of speed code is too fast in {sequence} step {i}\n")

                    if not step['speed_code'] in speed_dict:
                        update_error(f"One of speed code is not coded {sequence} step {i}\n")

                    if not step['pump_port'] in list(self.fluidics.syringe_pump_dictionary.keys()):
                        update_error(f"One of pump port name is wrong {sequence} step {i}\n")

                    if step['process']=="export":
                        Export = Export+step['unit_volume']
                    if step['process'] == "import":
                        Import=Import+step['unit_volume']
                        if step['pump_port'] in ["IRM","CRM"]:
                            if step['pump_port'] not in reagent_used.keys():
                                reagent_used[step['pump_port']] = step['unit_volume']
                                print(f"Added new reagent: {step['pump_port']} = {step['unit_volume']} ml")
                            else:
                                reagent_used[step['pump_port']] += step['unit_volume']
                        elif step['pump_port']=="batch_reagents":
                            rname=self.fluidics.selector_fluidics_dict[int(step['source'])]
                            if rname not in reagent_used.keys():
                                reagent_used[rname] = step['unit_volume']
                                print(f"Added new reagent: {rname} = {step['unit_volume']} ml")
                            else:
                                reagent_used[rname] += step['unit_volume']
                        else:
                            pass
                else:
                    pass

            if Import != Export:
                update_error(f"The import amount and export amount is not equal in {sequence}\n")
        df = pd.DataFrame(list(reagent_used.items()),
                          columns=['Reagent_Name', 'Amount_ml'])
        df['Amount_ml']=df['Amount_ml']+1 #prime line
        df.to_csv(os.path.join(self.pos_path,'reagents.csv'), index=False)
        self.parent_window.add_highlight_mainwindow("reagent amount saved to reagents.csv")
        self.parent_window.add_highlight_mainwindow("Finish checking the sequences.....")
        self.all_autobtn_normal()

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







    def slice_per_slide_reformat(self):
        try:
            a = self.slice_number_field_auto.get()
            listOfChars = list()
            listOfChars.extend(a)
            num = [int(x) for x in listOfChars if x.isdigit()]
            self.slice_per_slide = num
        except:
            self.log_update=0
            tk.messagebox.showinfo(title="Wrong Input", message="Slice per slide is wrong!")
            self.slice_per_slide=None

    def slice_per_slide_reformat_manual(self):
        try:
            a = self.slice_number_field_manual.get()
            listOfChars = list()
            listOfChars.extend(a)
            num = [int(x) for x in listOfChars if x.isdigit()]
            self.slice_per_slide = num
        except:
            self.log_update=0
            tk.messagebox.showinfo(title="Wrong Input", message="Slice per slide is wrong!")
            self.slice_per_slide=None

    def create_exp_manual(self):
        self.parent_window.clear_error()
        tk.clear_log()
        self.clear_align_canvas()
        self.clear_tile_canvas()
        self.clear_focus_canvas()
        self.cycle_number = self.sb1_cycle_number.get()
        self.current_cycle = self.current_c.get() + self.sb1_cycle_number.get().zfill(2)
        if "00" in self.current_cycle:
            self.current_cycle="cycle00"

        self.skip_alignment = self.mock_alignment.get()
        self.protocol_list_index = 0
        self.server = self.account_field_manual.get() + "@" + self.server_field_manual.get()
        if self.work_path_field_manual.get() == "":
            tk.messagebox.showinfo(title="Wrong Input", message="work directory can't be empty")
            return
        self.pos_path = self.work_path_field_manual.get()
        if self.current_c.get() == "":
            tk.messagebox.showinfo(title="Wrong Input", message="current cycle type can't be empty")
            return
        if self.slice_number_field_manual.get() == "":
            tk.messagebox.showinfo(title="Wrong Input", message="slice per slide can't be empty")
            return
        self.slice_per_slide_reformat_manual()
        self.protocol_list = [self.current_cycle]
        if "00" in self.current_cycle:
            self.align_btn["state"] = "disable"
            self.tile_btn["state"] = "disable"
            self.max_btn["state"] = "disable"
        else:
            self.align_btn["state"] = "normal"
            self.tile_btn["state"] = "normal"
            self.max_btn["state"] = "normal"
        if not os.path.exists(os.path.join(self.pos_path, "log.txt")):
            open(os.path.join(self.pos_path, "log.txt"), 'a').close()
        
        with open(os.path.join(get_resource_dir(),"config_file", "scope.json"), 'r') as r:
            self.scope_cfg=json.load(r)
            self.imwidth = self.scope_cfg[0]["imwidth"]

        try:
            self.scope = scope(self.scope_cfg, self.pos_path, self.slice_per_slide, self.server, self.skip_alignment,0,system_path=self.system_path)

        except:
            tk.messagebox.showinfo(title="Config failure ",
                                message="Please run micromanager first!")
            update_error("Please run micromanager first!")
            return
        
        txt = get_time() + "\n" + "work directory: " + self.pos_path + "\n" + "Current cycle: " + self.protocol_list[
            self.protocol_list_index] + "\n"
        print(txt)
        
        self.write_log(txt)
        self.parent_window.add_highlight_mainwindow(txt)
        
        if not os.path.exists(os.path.join(self.pos_path, "manual_process_record.csv")):
            df = pd.DataFrame(columns=["protocol"])
            df["protocol"] = "imagecycle_" + self.current_cycle
            df.to_csv(os.path.join(self.pos_path, "manual_process_record.csv"), index=False)
        else:
            df = pd.read_csv(os.path.join(self.pos_path, "manual_process_record.csv"))
            df.loc[len(df.index)] = ["imagecycle_" + self.current_cycle]
            df.to_csv(os.path.join(self.pos_path, "manual_process_record.csv"), index=False)
        self.focus_btn["state"] = "normal"

 


    def assign_cycle_detail(self):
        if not os.path.exists(os.path.join(self.pos_path,"protocol.csv")):
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
        self.parent_window.add_highlight_mainwindow("protocol has beed assigned!"+"\n")
        self.write_log("protocol has beed assigned!")

    def write_log(self, txt):
        f = open(os.path.join(self.pos_path, "log.txt"), "a")
        f.write(txt)
        f.close()

    def config_device(self):
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

    def config_dev(self):
        device_group=self.device_dropdown.get()
        self.pos_path = self.work_path_field_auto.get()
        if self.pos_path == "":
            self.pos_path = "C://"
            self.fluidics = FluidicSystem(system_path=self.system_path,pos_path=self.pos_path,slide_hearter_dictionary=self.heater_dict)
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

    def scan_tissue(self):
        scanner = tissue_scan(self.pos_path)

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
            self.parent_window.add_highlight_mainwindow(txt)
            self.write_log(txt)
            t2 = Thread(target=self.sensor_fluidics_process)
            t2.start()

            
    def sensor_fluidics_process(self):
        check=self.fluidics.cycle_done
        while check!=1:
            time.sleep(2)
            check = self.fluidics.cycle_done
        txt = get_time() + "Prime/Wash line Done!\n"
        self.parent_window.add_highlight_mainwindow(txt)
        self.fluidics.disconnect_syringe_pump()
        self.fluidics.disconnect_selector()
        self.all_autobtn_normal()
        self.cancel_sequence_btn['state'] = "disable"


    def fill_single_reagent(self):
        if 0 in [self.device_status['selector_group'], self.device_status['syringe_pump_group']]:
            tk.messagebox.showinfo(title="Config device", message="Please config the device first!")
        else:
            t1 = Thread(target=self.pump_reagent)
            t1.start()

    def pump_reagent(self):
        reagent = self.reagent.get()
        print(reagent)
        if reagent=="":
            self.parent_window.add_highlight_mainwindow("Please select reagent!\n")
        else:
            if reagent in self.fluidics.selector_reagent:
                selector_reagent=reagent
                pump_port="batch_reagents"
                print(selector_reagent)
            else:
                selector_reagent="null"
                pump_port=reagent
                print(pump_port)
            self.all_autobtn_disable()
            self.fluidics.connect_syringe_pump()
            self.fluidics.connect_selector()
            self.fill_single_btn['state']='disable'
            vol=float(self.reagent_amount.get())*self.scale
            pumpRate=self.fluidics.syringe_pump.syringe_pump_speed_default

            self.fluidics.setSource(selector_reagent,pump_port)
            if self.inchamber_path.get()==1:
                self.fluidics.syringe_pump.fillSyringe(vol*len(self.chamber_list), pumpRate)
                time.sleep(1)
                for i in range(len(self.chamber_list)):
                    chamber = self.chamber_list[i]
                    self.fluidics.setSource("null",chamber)
                    txt = get_time() + "Pump " + reagent + " " + str(vol) + " ul to " + chamber + "\n"
                    self.parent_window.add_highlight_mainwindow(txt)
                    self.write_log(txt)
                    print(txt)
                    self.fluidics.syringe_pump.dispense_pump(vol, pumpRate)
            if self.inchamber_path.get() != 1:
                self.fluidics.syringe_pump.fillSyringe(vol * len(self.chamber_list), pumpRate)
                time.sleep(1)

                self.fluidics.setSource("null", "waste")
                txt = get_time() + "Pump " + reagent + " " + str(vol) + " ul to waste"  + "\n"
                self.parent_window.add_highlight_mainwindow(txt)
                self.write_log(txt)
                print(txt)
                self.fluidics.syringe_pump.dispense_pump(vol, pumpRate)

            time.sleep(3)
            self.fluidics.disconnect_syringe_pump()
            self.fluidics.disconnect_selector()
            self.all_autobtn_normal()
            txt = get_time() + "fill with " + reagent + " is done!\n"
            self.fill_single_btn['state'] = 'normal'
            self.parent_window.add_highlight_mainwindow(txt)
            self.write_log(txt)
                
            
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
                
    def cancel_btn_handler(self):
        self.cancel=1
        self.fluidics.Heatingdevice.cancel=1
        self.fluidics.sequenceStatus=-1
        self.scope.cancel_process = 1
        txt=get_time()+"Canceled current process\n"
        self.parent_window.add_highlight_mainwindow(txt)
        self.write_log(txt)
        self.all_autobtn_normal()
        self.cancel_sequence_btn['state'] = "disable"


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

    def all_autobtn_disable(self):
        self.browse_btn_auto['state']="disable"
        self.browse_btn_manual['state']="disable"
        self.exp_btn_manual['state']="disable"
        self.exp_btn_auto['state']="disable"
        self.recipe_btn['state']="disable"
        self.info_btn_auto['state']="disable"
        self.device_btn['state']="disable"
        self.brain_btn['state']="disable"
        self.prime_btn['state']="disable"
        self.start_sequence_btn['state']="disable"
        self.fill_single_btn['state']="disable"
        self.check_sequence_btn['state'] = "disable"
        self.wash_btn['state'] = "disable"

    def all_autobtn_normal(self):
        self.browse_btn_auto['state'] = "normal"
        self.browse_btn_manual['state'] = "normal"
        self.exp_btn_manual['state'] = "normal"
        self.exp_btn_auto['state'] = "normal"
        self.recipe_btn['state'] = "normal"
        self.info_btn_auto['state'] = "normal"
        self.device_btn['state'] = "normal"
        self.brain_btn['state'] = "normal"
        self.prime_btn['state'] = "normal"
        self.start_sequence_btn['state'] = "normal"
        self.fill_single_btn['state'] = "normal"
        self.cancel_sequence_btn['state'] = "normal"
        self.check_sequence_btn['state'] = "normal"
        self.wash_btn['state'] = "normal"

    def check_files(self):
       self.check_imagecycle00()
    
    def check_imagecycle00(self):
        if "imagecycle00" in self.process_ls:
            if not os.path.exists(os.path.join(self.pos_path, "cycle00.pos")):
                tk.messagebox.showinfo(title="Config failure ",
                                    message="Please create cycle00 coordinates first!")
                update_error("Please create cycle00 coordinates first!")
                return
            else:
                self.check_file=self.scope.check_cycle00()
        else:
            check = [1 for i in self.process_ls if "imagecycle" in i]
            if sum(check) == 0:
                self.check_file = 1
                return
            else:
                if not os.path.exists(os.path.join(self.pos_path, "dicfocuscycle00")):
                    update_error("Missing dicfocuscycle00")
                    return
                if not os.path.exists(os.path.join(self.pos_path, "pre_adjusted_pos.pos")):
                    update_error("Missing pre_adjusted_pos.pos")
                    return
                else:
                    self.check_file = 1

    def start_sequence(self):
        if self.process_index>self.process_index_limite:
            txt=get_time()+"All rounds finished!\n"
            self.write_log(txt)
            self.parent_window.add_highlight_mainwindow(txt)
            self.fluidics.disconnect_syringe_pump()
            self.fluidics.disconnect_selector()
            self.fluidics.disconnect_heater()
            self.all_autobtn_normal()
            self.cancel_sequence_btn['state']="disable"
            ##add transfer to server here
            self.scope.send_to_server(self.pos_path)
            return
        self.process_cycle = self.process_ls[self.process_index]
        txt=get_time()+"start "+self.process_cycle+"\n"
        self.write_log(txt)
        self.parent_window.add_highlight_mainwindow(txt)
        if "Fluidics_sequence" in self.process_cycle:
            try:
                self.protocol=self.fluidics.find_protocol(self.process_cycle)
            except:
                self.fluidics.disconnect_syringe_pump()
                self.fluidics.disconnect_selector()
                self.fluidics.disconnect_heater()
                self.all_autobtn_normal()
                self.cancel_sequence_btn['state'] = "disable"
                tk.messagebox.showinfo(title="Protocol issue", message="check protocol file, the format is wrong")
                return
            t = Thread(target=self.run_fluidics_cycle(self.protocol))
            t.start()
            check = self.fluidics.start_image
            while check != 1:
                if self.cancel==1:
                    break
                time.sleep(2)
                check = self.fluidics.start_image
            self.process_index = self.process_index + 1
            if self.cancel!=1:
                time.sleep(5)
                t1 = Thread(target=self.start_sequence)
                t1.start()
            else:
                pass
                return
        elif "imagecycle00" in self.process_cycle:
            self.scope=scope(self.scope_cfg,self.pos_path, self.slice_per_slide, self.server, self.skip_alignment,0,system_path=self.system_path)
            self.scope.move_to_image()
            self.scope.cancel_process = 0
            self.current_cycle = "imagecycle00"
            t = Thread(target=self.do_focus_thread)
            t.start()
            check=self.scope.focus_status
            while check != 1 :
                if self.cancel == 1:
                    break
                time.sleep(2)
                check = self.scope.focus_status
            self.process_index = self.process_index + 1
            if self.cancel!=1:
                time.sleep(5)
                t1 = Thread(target=self.start_sequence)
                t1.start()
            else:
                pass
                return
        else:
            self.scope=scope(self.scope_cfg,self.pos_path, self.slice_per_slide, self.server, self.skip_alignment,0,system_path=self.system_path)
            self.scope.move_to_image()
            self.scope.cancel_process = 0
            self.current_cycle = self.process_cycle[11:]
            self.image_auto()
            check = self.scope.max_projection_status
            while check != 1 :
                if self.cancel == 1:
                    break
                time.sleep(2)
                check = self.scope.max_projection_status
            self.process_index = self.process_index + 1
            if self.cancel!=1:
                time.sleep(10)
                t1 = Thread(target=self.start_sequence)
                t1.start()
            else:
                pass
                return

    def check_focus_file(self,path,file,msg):
        if not os.path.exists(os.path.join(path,file)):
            txt=get_time()+msg
            self.write_log(txt)
            update_error(txt)
            Pass=0
        else:
            Pass=1
        print(Pass)
        return Pass


    def do_focus_thread(self):
        if "00" in self.current_cycle:
            create_folder_file(self.pos_path, "dicfocuscycle00")
            create_folder_file(self.pos_path, "focuscycle00")
            check=self.check_focus_file(self.pos_path,"cycle00.pos","Missing cycle00.pos")
            if check==0:
                return
            else:
                self.focus_poslist = self.scope.pos_to_csv(self.current_cycle)
                diff = self.scope.focus_image("cycle00", self.focus_poslist)
        else:
            check = self.check_focus_file(self.pos_path, "dicfocuscycle00", " Abort, no archor coordinates folder found!")
            if check == 0:
                return
            else:
                status = self.check_focus_file(self.pos_path, "pre_adjusted_pos.pos"," Abort, no pre adjusted coordinate for current cycle!")
                if status ==0:
                    return
                else:
                    create_folder_file(self.pos_path, "dicfocus"+self.current_cycle)
                    create_folder_file(self.pos_path, "focus"+self.current_cycle)
                    with open(os.path.join(self.pos_path, "pre_adjusted_pos.pos")) as f:
                        d = json.load(f)
                    shutil.copy(os.path.join(self.pos_path, "pre_adjusted_pos.pos"), os.path.join(self.pos_path, self.current_cycle+".pos"))
                    self.focus_poslist = self.scope.pos_to_csv(self.current_cycle)
                    diff = self.scope.focus_image(self.current_cycle, self.focus_poslist)
        try:
            print(diff)
            plot1 = self.focusfigure.add_subplot(111)
            plot1.plot(diff)
            plot1.axhline(y=20, color='r')
            plot1.axhline(y=-20, color='r')
            plot1.get_xaxis().set_visible(False)
            plot1.get_yaxis().set_visible(False)
            self.canvas_focus.draw()
            plt.close(self.focusfigure)
            update_process_bar(0)
            update_process_label("Process")
            os.chdir(self.system_path)
        except:
            os.chdir(self.system_path)
            txt=get_time()+"focus is wrong or cancelled"
            update_error(txt)
    def image_auto(self):
        if self.cancel==1:
            pass
        else:
            self.do_focus_thread()
            self.align_and_draw_thread()
            self.tile_and_draw_thread()
        if self.cancel == 1:
            pass
        else:
            t1 = Thread(target=self.maxprojection_thread)
            t1.start()
            t2 = Thread(target=self.plot_live_view_thread)
            t2.start()

    def align_and_draw_thread(self):
        if "00" in self.current_cycle:
            self.parent_window.add_highlight_mainwindow("Cycle 00 doesn't need to run alignment!")
        else:
            self.scope.do_alignment(self.current_cycle)
            try:
                uniqslidenum = np.unique(self.scope.slidenum)
                data=pd.DataFrame(columns=['x', 'y', 'slidenum'])
                for i in uniqslidenum:
                    data1 = pd.DataFrame(columns=['x', 'y', 'slidenum'])
                    data1['x'] = np.round((self.scope.x_offset[np.where(self.scope.slidenum == i)]))
                    data1['y'] = np.round((self.scope.y_offset[np.where(self.scope.slidenum == i)]))
                    data1['slidenum'] = str(i)
                    data = pd.concat([data, data1], ignore_index=True)
                groups = data.groupby('slidenum')
                plot2 = self.alignfigure.add_subplot(111)
                for name, group in groups:
                    plot2.scatter(group.x, group.y, marker='o')
                plot2.set(ylim=(-200, 200))
                plot2.set(xlim=(-200, 200))
                plot2.get_xaxis().set_visible(False)
                plot2.get_yaxis().set_visible(False)
                self.canvas_align.draw()
                plt.close(self.alignfigure)
            except:
                txt=get_time()+"Aligmen is wrong or cancelled"
                update_error(txt)

    def tile_and_draw_thread(self):
        self.scope.make_tile(self.current_cycle)
        txt = get_time() + "created tiles for " + self.current_cycle + "\n"
        self.parent_window.add_highlight_mainwindow(txt)
        df = pd.read_csv(os.path.join(self.pos_path, 'tiledregoffset' + self.current_cycle + '.csv'))
        plot3 = self.tilefigure.add_subplot(111)
        plot3.scatter(df['X'],df['Y'],c='hotpink',s=4)
        plot3.axis('scaled')
        plot3.get_xaxis().set_visible(False)
        plot3.get_yaxis().set_visible(False)
        self.canvas_tile.draw()
        plt.close(self.tilefigure)


    def upload_aws(self):
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

    def maxprojection_thread(self):
        df = pd.read_csv(os.path.join(self.pos_path, 'tiledregoffset' + self.current_cycle + '.csv'))
        self.max_name_ls = df['switched_Posinfo']
        self.scope.image_and_maxprojection(self.current_cycle)
        os.chdir(self.system_path)

    def plot_live_view_thread(self):
        name = self.scope.maxprojection_name
        cycle=self.scope.cycle
        while name != 'end' and self.cancel != 1:
            print(name)
            if name != '':
                self.plot_maxprojection_liveview(name,cycle)
            time.sleep(5)
            name = self.scope.maxprojection_name
        txt = get_time() + "max_projection_finished!"
        self.parent_window.add_highlight_mainwindow(txt)

    def plot_maxprojection_liveview(self, name,cycle):
        disk = self.scope.maxprojection_drive
        img_name = name
        img = tif.imread(os.path.join(disk, self.pos_path[3:] + "_maxprojection", cycle, img_name))
        img_converted = np.array(list(map(hattop_convert, img)))
        img_converted_denoise = np.array(list(map(denoise, img_converted)))
        img_1 = np.stack((img_converted_denoise[0, :, :], img_converted_denoise[1, :, :],
                          img_converted_denoise[2, :, :], img_converted_denoise[3, :, :]), axis=-1)
        img_2 = np.reshape(img_1, (self.imwidth * self.imwidth, 4))
        img_3 = np.dot(img_2, color_array)
        img_4 = np.reshape(img_3, (self.imwidth, self.imwidth, 3))
        img_4 = np.where(img_4 > 255, 255, img_4).astype('uint8')
        draw_liveview(img_4)

    def upload_aws_handler(self):
        pass
        
    def run_fluidics_cycle(self,sequence):
        self.fluidics.loadSequence(sequence)
        self.fluidics.startSequence()


    
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

    def cancel_manual_process(self):
        self.cancel = 1
        self.scope.cancel_process = 1



class scope_constant():
    piezo_focus_start_pos = -30
    piezo_focus_end_pos = 30
    piezo_step = 1.5

    scope_start_pos = -15
    scope_end_pos = 15
    scope_focus_end_pos = 30
    scope_focus_start_pos = -30
    scope_step = 1.5

    piezo_maxpro_start_pos = -15
    piezo_maxpro_end_pos = 15

    ZDrive_safe_pos = 500
    XYStage_fluidics_safe_pos = [-56900.7, -3062.1]
    XYStage_image_safe_pos = [44198.6, -4834.5]

    scope_exposure_time_dict = {"G": 220, "T": 150, "A": 100, "C": 100, "DIC": 10, "GFP": 100, "TxRed": 100, "DAPI": 50}
    stack_num_focus = round(abs(piezo_focus_end_pos - piezo_focus_start_pos) / piezo_step)
    stack_num_maxpro = round(abs(piezo_maxpro_start_pos - piezo_maxpro_end_pos) / piezo_step)

    sharpen1 = np.array(([0, 1, 0],
                         [-1, 5, -1],
                         [0, -1, 0]), dtype="int")
    stage_x_dir = -1;  # -1: left is larger
    stage_y_dir = 1;  # 1: bottom is larger
    pos_per_slice = 4;
    pixelsize =0.33
    imwidth =3200
    overlap = 0

def get_position_piezo(pos):
    position_name = pos['Device']['scalar']
    position_value = pos['Position_um']['array']
    if position_name == 'ZDrive':
        return {'z': position_value[0]}
    elif position_name == 'XYStage':
        return {'x': position_value[0], 'y': position_value[1]}
    elif position_name == 'DA Z Stage':
        return {'piezo': position_value[0]}
    else:
        pass
    
def get_pos_data(item):
    positions = item['DevicePositions']['array']
    pos_data = {}
    for pos in positions:
        pos_data.update(get_position_piezo(
            pos))  # change to get_position_piezo(pos) if have piezo, change to get_position(pos) if no piezo
    pos_data.update({'position': item['Label']['scalar']})
    return pos_data

def createtiles(df):
    tileconfig = [None] * (math.floor(len(df) / 4))
    lablelist = []
    poslist = []
    Slide = []
    number = []
    pos = []
    for i in range(0, math.floor(len(df) / 4)):
        y = df['y'][i * 4:(i + 1) * 4].to_numpy(dtype=float)
        x = df['x'][i * 4:(i + 1) * 4].to_numpy(dtype=float)
        z = df['z'][i * 4:(i + 1) * 4].to_numpy(dtype=float)

        # calculate midpoint xy
        midpointx = np.ptp(x) / 2 + np.min(x)
        midpointy = np.ptp(y) / 2 + np.min(y)
        # regress z slope and midpoint on xy
        a = np.array([x - midpointx, y - midpointy, np.ones(len(x))])
        z1 = np.linalg.lstsq(a.T, np.array([z]).T, rcond=None)[0]
        zslopex = z1[0];
        zslopey = z1[1];
        midpointz = z1[2];
        # calculate tile config
        tileconfig[i] = [math.ceil(np.ptp(x) / (
                scope_constant.imwidth * (1 - scope_constant.overlap / 100) * scope_constant.pixelsize)) + 1,
                         math.ceil(np.ptp(y) / (scope_constant.imwidth * (
                                 1 - scope_constant.overlap / 100) * scope_constant.pixelsize)) + 1]
        midpoint = [tileconfig[i][0] / 2 - 0.5, tileconfig[i][1] / 2 - 0.5]

        for n in range(0, tileconfig[i][0] * tileconfig[i][1]):
            grid_col, grid_row = ind2sub(tileconfig[i], np.array(n))
            # change LABEL
            LABEL = ['Pos' + str(i + 1) +
                     '_' + str(grid_col).zfill(3) +
                     '_' + str(grid_row).zfill(3)]
            # change XY positions
            Yoffset = (grid_row - midpoint[1]) * scope_constant.imwidth * (
                    1 - scope_constant.overlap / 100) * scope_constant.pixelsize;
            Xoffset = (grid_col - midpoint[0]) * scope_constant.imwidth * (
                    1 - scope_constant.overlap / 100) * scope_constant.pixelsize;
            Y = round(midpointy + Yoffset);
            X = round(midpointx + Xoffset);
            # find the device of XYstage
            Zoffset = Yoffset * zslopey + Xoffset * zslopex;
            Z = midpointz + Zoffset;
            poslist.append([X, Y, Z[0]])
            lablelist.append(LABEL[0])
            Slide.append('slide_' + str(i + 1))
            pos.append('Pos' + str(i + 1))
            number.append(n)

    tilepos = pd.DataFrame(columns=['Slidenum', 'Posinfo', 'X', 'Y', 'Z'])
    tilepos['Slidenum'] = Slide
    tilepos['Posinfo'] = lablelist
    tilepos['Pos'] = pos
    tilepos['X'] = [pos[0] for pos in poslist]
    tilepos['Y'] = [pos[1] for pos in poslist]
    tilepos['Z'] = [pos[2] for pos in poslist]
    return tilepos

def get_col(image_file_name):
    start = image_file_name.find('_', 7) + 1
    end = start + 3
    return int(image_file_name[start:end])

def get_row(image_file_name):
    start = image_file_name.find('_') + 1
    end = start + 3
    return int(image_file_name[start:end])

def fix_Posinfo(tilepos):
    tilepos_new = pd.DataFrame(columns=['Slidenum', 'Posinfo', 'X', 'Y', 'Z', 'Pos', 'switched_Posinfo'])
    slice_ls = pd.unique(tilepos['Pos'])
    for s in slice_ls:
        image_name_df = tilepos[tilepos['Pos'] == s]
        image_name = image_name_df['Posinfo']
        col_list = [get_col(i) for i in image_name]
        row_list = [get_row(i) for i in image_name]
        row_list_new = [str(i).zfill(3) for i in row_list]
        col_list_new = [str(max(col_list) - i).zfill(3) for i in col_list]
        new_name = []
        for num in range(len(row_list_new)):
            name = s + "_" + row_list_new[num] + "_" + col_list_new[num]
            new_name.append(name)
        image_name_df['switched_Posinfo'] = new_name
        frames = [tilepos_new, image_name_df]
        tilepos_new = pd.concat(frames)
        return tilepos_new

def create_scan_even(XY):
    event = []
    for i in range(XY.shape[0]):
        event.append({'axes': {'channel': 'DIC'},'config_group': ['Channel', 'DIC'],'exposure':10,'X':XY[i][0],'Y':XY[i][1]})
    return event


class tissue_scan():

    def __init__(self, path):
        
        with open(os.path.join( get_resource_dir() , "tissue_scanner","slide1_chamber_coor.pos")) as f:
            self.slide1_coor = json.load(f)
        df = pd.DataFrame([get_pos_data(item) for item in self.slide1_coor['map']['StagePositions']['array']])[
            ['position', 'x', 'y', 'z', 'piezo']]
        tiles = createtiles(df)
        self.tiles = fix_Posinfo(tiles)
        self.path=path
        self.core=Core()
        self.coordinate=[]
        self.scan_popup = tk.Tk()
        self.scan_popup.title("Scan slides")
        self.scan_popup.geometry("680x120")
        self.dropdown = ttk.Combobox(self.scan_popup, width=25)
        self.dropdown['values'] = ['slide1']
        self.dropdown.place(x=90,y=10)
        self.scale_factor=0.1
        self.tile_width = round(3200*self.scale_factor)
        self.tile_height = round(3200*self.scale_factor)
        self.col =max([get_row(i) for i in self.tiles['Posinfo']])+1
        self.row  = max([get_col(i) for i in self.tiles['Posinfo']])+1
        self.scan_button = tk.Button(self.scan_popup, text="Scan slide", command=self.scan_slide,width=20)
        self.scan_button.place(x=510, y=10)
        self.label1=tk.Label(self.scan_popup,text="Choose slide:",width=10)
        self.label1.place(x=2, y=10)
        self.label2 = tk.Label(self.scan_popup, text="Z-plane:", width=10)
        self.label2.place(x=270, y=10)
        self.z_plane = tk.StringVar()
        self.z_plane.set(3228)
        self.z_plane_field = tk.Entry(self.scan_popup, relief="groove", width=10, textvariable=self.z_plane)
        self.z_plane_field.place(x=350, y=10)
        with open(os.path.join("device", "tissue_scanner","pos_temp.pos")) as f:
            self.temp = json.load(f)


    def run_scope(self,slide):
        if os.path.exists(os.path.join("device", "tissue_scanner", slide,"stack_1")):
            shutil.rmtree(os.path.join("device", "tissue_scanner", slide,"stack_1"))
        self.z=int(self.z_plane_field.get())
        self.core.set_position("ZDrive",self.z)
        with Acquisition(directory=os.path.join("device", "tissue_scanner", slide), name="stack",
                         show_display=False) as acq:
            events = multi_d_acquisition_events(channel_exposures_ms=10, xy_positions=self.xy_positions,channel_group=['Channel', "DIC"])
            acq.acquire(events)
    
    def stich_image(self,slide):
        img_list = [i for i in os.listdir(os.path.join(get_resource_dir(), "tissue_scanner", slide, 'stack_1')) if ".tif" in i]
        img = tifffile.imread(os.path.join(get_resource_dir(), "tissue_scanner", slide, 'stack_1', img_list[0]))
        self.stitched_image = np.zeros((self.row * self.tile_height, self.col * self.tile_width), dtype=np.uint8)

        print(self.tile_width)
        for i in range(self.row):
            for j in range(self.col):
                index = (self.row - i - 1) * self.col + j
                image = cv2.resize(img[index, :, :], None, fx=self.scale_factor, fy=self.scale_factor)
                x = j * self.tile_width
                y = i * self.tile_height
                self.stitched_image[y:y + self.tile_height, x:x + self.tile_width] = image
                self.stitched_image_rt=cv2.rotate(self.stitched_image, cv2.ROTATE_180)
        #cv2.imwrite(os.path.join( get_resource_dir() , "tissue_scanner", "stitched_image_check.png"), self.stitched_image_rt)
        cv2.imwrite(os.path.join( os.getcwd() , "stitched_image_check.png"), 
                    self.stitched_image_rt)


    def scan_slide(self):
        self.xy_positions = self.tiles[["X", "Y"]].to_numpy()
        print(self.xy_positions )
        self.run_scope(self.dropdown.get())
        self.stich_image(self.dropdown.get())
        self.subwindow = tk.Tk()
        collector = ImageCoordinateCollector(self.subwindow, self.stitched_image,self.stitched_image_rt,self.path,self.tile_width,self.tiles,self.z)
        self.subwindow.mainloop()



class ImageCoordinateCollector:
    def __init__(self, window, stitched_image,stitched_image_rt,path,width,tilesdf,z):
        self.window = window
        self.image=stitched_image
        self.window.title("Image Coordinate Collector")
        self.pos_path=path
        self.tile_width=width
        self.tilesdf=tilesdf
        self.fig, self.ax = plt.subplots()
        self.stitch_image=stitched_image
        self.stitch_image_rt=stitched_image_rt
        self.ax.imshow(self.stitch_image_rt, cmap="Greys")
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.window)
        self.canvas.draw()
        self.coordinates = []
        self.canvas.mpl_connect("button_press_event", self.on_click)
        self.canvas.get_tk_widget().pack()
        self.print_button = tk.Button(self.window, text="Save Coordinates", command=self.save_coordinates)
        self.print_button.pack()
        self.clear_button = tk.Button(self.window, text="Clear Points", command=self.clear_points)
        self.clear_button.pack()
        self.Z=z

    def on_click(self, event):
        if event.inaxes is not None:
            x, y = event.xdata, event.ydata
            self.coordinates.append((x, y))
            self.ax.plot(x, y, marker='x', color='red', markersize=10)
            self.canvas.draw()
    def find_original_coor(self,XY):
        coor = []
        for i in range(len(XY)):
            X = XY[i][0]
            Y = XY[i][1]
            row = math.floor(Y / self.tile_width)
            col=max([get_row(i) for i in self.tilesdf['Posinfo']])-math.floor(X / self.tile_width) #flip image

            name = "Pos1_" + str(col).zfill(3) + "_" + str(row).zfill(3)
            coor.append([self.tilesdf.loc[self.tilesdf["Posinfo"] == name]['X'].iloc[0],
                        self.tilesdf.loc[self.tilesdf["Posinfo"] == name]['Y'].iloc[0]])

        return coor
    def save_coordinates(self):
        self.ori_coor=self.find_original_coor(self.coordinates)
        with open(os.path.join("device", "tissue_scanner", "pos_temp.pos")) as f:
            temp = json.load(f)
        temp_coor = temp['map']['StagePositions']['array'][0]
        temp_coor['DevicePositions']['array'][0]['Position_um']['array'][0] = int(self.Z)
        temp_coor['DevicePositions']['array'][2]['Position_um']['array'] = copy.deepcopy(self.ori_coor[0])
        temp['map']['StagePositions']['array'][0] = temp_coor
        for i in range(1, len(self.ori_coor)):
            temp['map']['StagePositions']['array'].append(copy.deepcopy(temp_coor))
        for i in range(1, len(self.ori_coor)):
            temp['map']['StagePositions']['array'][i]['DevicePositions']['array'][2]['Position_um']['array'][0] = copy.deepcopy(self.ori_coor[i][0])
            temp['map']['StagePositions']['array'][i]['DevicePositions']['array'][2]['Position_um']['array'][1] = copy.deepcopy(self.ori_coor[i][1])
            temp['map']['StagePositions']['array'][i]['Label']['scalar'] =copy.deepcopy('Pos' + str(i))

        json_object = json.dumps(temp, indent=2)
        with open(os.path.join(self.pos_path,"auto_cycle00.pos"), "w") as outfile:
            outfile.write(json_object)
        messagebox.showinfo(title="Save", message="auto_cycle00 is saved!")
        self.window.destroy()


    def clear_points(self):
        self.coordinates.clear()
        self.ax.clear()
        self.ax.imshow(self.stitch_image_rt, cmap="Greys")
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.canvas.draw()

def set_windowwidgets(widgets):
    
    ##automation tab area
    widgets.work_path_lb_auto.grid(row=3, column=0, padx=15,sticky="w")
    widgets.work_path_field_auto.grid(row=3, column=3, padx=15, sticky="w")
    widgets.browse_btn_auto.grid(row=3, column=4, padx=15, sticky="w")
    widgets.exp_btn_auto.grid(row=3, column=7, padx=15, sticky="w")
    
    widgets.slice_per_slide_lb_auto.grid(row=0, column=0, padx=5,sticky="w")
    widgets.slice_number_field_auto.grid(row=0, column=1, padx=1,sticky="w")
    widgets.slice_per_slide_lb_manual.grid(row=0, column=0, padx=5,sticky="w")
    widgets.slice_number_field_manual.grid(row=0, column=1, padx=1,sticky="w")
    
    widgets.mock_alignment_cbox.grid(row=0, column=2, padx=5, sticky="w")
    widgets.mock_alignment_cbox_manual.grid(row=0, column=2, padx=5, sticky="w")
    widgets.current_cycle_lb.grid(row=0, column=3, padx=5, sticky="w")
    widgets.current_cbox.grid(row=0, column=4, padx=5, sticky="w")
    widgets.sb1_cycle_number.grid(row=0, column=5, padx=5, sticky="w")
    
    widgets.build_own_cycle_sequence.grid(row=0, column=3, padx=5, sticky="w")
    widgets.OR_lb.grid(row=0, column=4, padx=5, sticky="w")
    widgets.recipe_btn.grid(row=0, column=5, padx=5, sticky="w")
    widgets.assign_heater_btn.grid(row=0, column=6, padx=5, sticky="w")
    
    
    widgets.change_pixel_auto.grid(row=1, column=0, padx=5, sticky="w")
    widgets.change_pixel_manual.grid(row=1, column=0, padx=5, sticky="w")
    widgets.pixel_size_field_auto.grid(row=1, column=1, padx=5, sticky="w")
    widgets.pixel_size_field_manual.grid(row=1, column=1, padx=5, sticky="w")
    widgets.change_server_auto_cb.grid(row=1, column=2, padx=5, sticky="w")
    widgets.change_server_manual_cb.grid(row=1, column=2, padx=5, sticky="w")
    widgets.server_account_lb_auto.grid(row=1, column=3, padx=5, sticky="w")
    widgets.account_field_auto.grid(row=1, column=4, padx=5, sticky="w")
    widgets.server_lb_auto.grid(row=1, column=5, padx=5, sticky="w")
    widgets.server_field_auto.grid(row=1, column=6, padx=5, sticky="w")
    widgets.server_account_lb_manual.grid(row=1, column=3, padx=5, sticky="w")
    widgets.account_field_manual.grid(row=1, column=4, padx=5, sticky="w")
    widgets.server_lb_manual.grid(row=1, column=5, padx=5, sticky="w")
    widgets.server_field_manual.grid(row=1, column=6, padx=5, sticky="w")
    
    
    
    widgets.upload_aws_auto.grid(row=0, column=0, padx=5, sticky="w")
    widgets.aws_account_lb_auto.grid(row=0, column=1, padx=5, sticky="w")
    widgets.aws_account_field_auto.grid(row=0, column=2, padx=5,sticky="w")
    widgets.aws_password_lb_auto.grid(row=0, column=3, padx=5, sticky="w")
    widgets.aws_pwd_field_auto.grid(row=0, column=4, padx=5, sticky="w")
    
    widgets.upload_aws_manual.grid(row=0, column=0, padx=5, sticky="w")
    widgets.aws_account_lb_manual.grid(row=0, column=1, padx=5, sticky="w")
    widgets.aws_account_field_manual.grid(row=0, column=2, padx=5,sticky="w")
    widgets.aws_password_lb_manual.grid(row=0, column=3, padx=5, sticky="w")
    widgets.aws_pwd_field_manual.grid(row=0, column=4, padx=5, sticky="w")
    
    widgets.info_btn_auto.grid(row=2, column=0, padx=10, pady=5)
    widgets.info_btn_manual.grid(row=2, column=0, padx=10, pady=5)
    
    
    widgets.device_btn.grid(row=0, column=0, padx=10,sticky="w")
    widgets.brain_btn.grid(row=0, column=1, padx=10, sticky="w")
    widgets.prime_btn.grid(row=0, column=2, padx=10,sticky="w")
    widgets.fill_lb.grid(row=0, column=3, padx=10, sticky="w")
    widgets.reagent_list_cbox.grid(row=0, column=4, padx=10, sticky="w")
    widgets.reagent_amount.grid(row=0, column=5, padx=10, sticky="w")
    widgets.inchamber_path_cbox.grid(row=0, column=6, padx=10,sticky="w")
    widgets.fill_single_btn.grid(row=0, column=7, padx=10, sticky="w")
    
    widgets.start_sequence_btn.grid(row=0, column=1, padx=10, sticky="w")
    widgets.cancel_sequence_btn.grid(row=0, column=2, padx=10, sticky="w")
    widgets.wash_btn.grid(row=0, column=3, padx=10, sticky="w")
    widgets.avoid_wash_cbox.grid(row=0, column=4, padx=10, sticky="w")
    widgets.check_sequence_btn.grid(row=0, column=0, padx=10, sticky="w")
    
    widgets.canvas_focus.get_tk_widget().grid(row=1, column=0,padx=10,sticky="w")
    widgets.canvas_align.get_tk_widget().grid(row=1, column=1,padx=10,sticky="w")
    widgets.canvas_tile.get_tk_widget().grid(row=1, column=2,padx=10,sticky="w")
    
    widgets.focus_lb.grid(row=0, column=0,padx=5,pady=3)
    widgets.align_lb.grid(row=0, column=1,padx=5,pady=3)
    widgets.tile_lb.grid(row=0, column=2,padx=5,pady=3)
    
    widgets.note_lb.grid(row=0, column=0,padx=5,pady=3)
    widgets.note_stw.grid(row=0, column=1,padx=5,pady=3)
    widgets.note_btn.grid(row=0, column=2,padx=5,pady=3)
    ## manual tab area
    widgets.work_path_lb_manual.grid(row=0, column=0, padx=10,sticky="w")
    widgets.work_path_field_manual.grid(row=0, column=10, padx=10, sticky="w")
    
    widgets.browse_btn_manual.grid(row=0, column=15, padx=10, sticky="w")
    widgets.exp_btn_manual.grid(row=0, column=25, padx=10, sticky="w")
    
    widgets.focus_btn.grid(row=0, column=0, padx=10, pady=10)
    widgets.align_btn.grid(row=0, column=1, padx=10, pady=10)
    widgets.tile_btn.grid(row=0, column=2, padx=10, pady=10)
    widgets.max_btn.grid(row=0, column=3, padx=10, pady=10)
    widgets.cancel_image_btn.grid(row=0, column=4, padx=10, pady=10)


def clear_canvas(canvas):
    for item in canvas.get_tk_widget().find_all():
       canvas.get_tk_widget().delete(item)

 