
"""
Author: Aixin Zhang
Description: Mainwindow widgets and its functions

"""

import time
import json
import shutil
from front_end.logwindow import *
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from threading import *
from datetime import datetime
from pytz import timezone
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import tifffile as tif
import cv2
from system.fluidics_exchange_system import FluidicSystem
from system.image_acquisition_and_analysis_system import scope
from front_end.recipe_builder import process_builder
from tkinter import ttk, StringVar,filedialog,messagebox,scrolledtext,Button
from front_end.tissue_scanner import tissue_scan
from front_end.experiment_profile import Exp_profile
from PIL import Image, ImageTk


def clear_canvas(canvas):
    for item in canvas.get_tk_widget().find_all():
       canvas.get_tk_widget().delete(item)
def get_time():
    time_now = timezone('US/Pacific')
    time = str(datetime.now(time_now))[0:19] + "\n"
    return time
def get_date():
    time_now = timezone('US/Pacific')
    date = str(datetime.now(time_now))[0:10]
    return date
def create_folder_file(pos_path,name):
    if not os.path.exists(os.path.join(pos_path,name)):
        os.makedirs(os.path.join(pos_path,name))

filterSize =(10, 10)
kernel = cv2.getStructuringElement(cv2.MORPH_RECT,  filterSize)
color_array=np.array([[0,4,4],[1.5,1.5,0],[1,0,1],[0,0,1.5]])

def hattop_convert(x):
    return cv2.morphologyEx(x, cv2.MORPH_TOPHAT, kernel)
def denoise(x):
    x[x<np.percentile(x, 85)]=0
    return x
class widge_attr:
    normal_edge=3
    disable_edge = 0.9
    normal_color = '#0f0201'
    disable_color = '#bab8b8'
    warning_color='#871010'
    black_color='#0a0000'
    yellow_color="#e0c80b"


class window_widgets:
    def __init__(self,mainwindow,path):
        self.device_status = {
            "syringe_pump_group": 0,
            "selector_group": 0,
            "heater_group": 0}
        self.scale=1000 #unit ml to ul
        self.system_path=path
        self.main=mainwindow
        self.parent_window = mainwindow
        self.auto_image = PhotoImage(file=os.path.join( self.system_path,"logo", "auto_logo.png"))
        self.manual_image = PhotoImage(file=os.path.join(self.system_path,"logo", "hand.png"))
        self.frame0 = tk.Frame(self.main, bg=self.main.cget('bg'))
        self.frame0.grid(row=0, column=0, sticky="nsew")
        self.notebook = ttk.Notebook(self.frame0)
        self.notebook.grid(row=0, column=0)
        self.cwd=os.getcwd()


        self.auto_tab = ttk.Frame(self.notebook)
        self.manual_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.auto_tab, text='Auto System', image=self.auto_image, compound=tk.LEFT)
        self.notebook.add(self.manual_tab, text='Manual System', image=self.manual_image, compound=tk.LEFT)

        ## section
        self.section1_lbf_auto = tk.LabelFrame(self.auto_tab, text="Section 1 Choose work directory",width=600)
        self.section1_lbf_auto.pack_propagate(False)
        self.section1_lbf_auto.grid(row=0, column=0, padx=3, pady=3,sticky="n")




        self.section2_lbf_auto = tk.LabelFrame(self.auto_tab, text="Section 2 Fill process details",width=600)
        self.section2_lbf_auto.pack_propagate(False)
        self.section2_lbf_auto.grid(row=1, column=0, padx=3, pady=3,sticky="n")


        self.section3_lbf_auto = tk.LabelFrame(self.auto_tab, text="Section 3 Automation functions", width=600)
        self.section3_lbf_auto.pack_propagate(False)
        self.section3_lbf_auto.grid(row=3, column=0, padx=3, pady=3, sticky="n")

        self.section3_lbf_manual= tk.LabelFrame(self.manual_tab, text="Section 3 Manual functions", width=600)
        self.section3_lbf_manual.pack_propagate(False)
        self.section3_lbf_manual.grid(row=3, column=0, padx=3, pady=3, sticky="n")




        self.section4_addtion_note = tk.LabelFrame(self.frame0, text="Section 4 Addition notes", width=600)
        self.section4_addtion_note.pack_propagate(False)
        self.section4_addtion_note.grid(row=5, column=0, padx=3, pady=3, sticky="n")

        self.section1_lbf_manual = tk.LabelFrame(self.manual_tab, text="Section 1 Choose work directory", width=600)
        self.section1_lbf_manual.grid(row=0, column=0, padx=3, pady=3, sticky="n")
        #
        self.section2_lbf_manual = tk.LabelFrame(self.manual_tab, text="Section 2 Fill process details", width=600)

        self.section2_lbf_manual.grid(row=1, column=0, padx=3, pady=3, sticky="n")

        ##Frame

        self.frame1 = tk.Frame(self.section2_lbf_auto, bg=self.main.cget('bg'),width=500)
        self.frame1.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.frame1_1 = tk.Frame(self.section2_lbf_manual, bg=self.main.cget('bg'),width=500)
        self.frame1_1.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.frame2 = tk.Frame(self.section2_lbf_auto, bg=self.main.cget('bg'), width=500)
        self.frame2.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.frame2_2 = tk.Frame(self.section2_lbf_manual, bg=self.main.cget('bg'), width=500)
        self.frame2_2.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)


        self.frame3 = tk.Frame(self.section2_lbf_auto, bg=self.main.cget('bg'), width=500)
        self.frame3.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        self.frame3_3 = tk.Frame(self.section2_lbf_manual, bg=self.main.cget('bg'), width=500)
        self.frame3_3.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)

        self.frame5 = tk.Frame(self.section3_lbf_auto, bg=self.main.cget('bg'), width=500)
        self.frame5.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.frame6 = tk.Frame(self.section3_lbf_auto, bg=self.main.cget('bg'), width=500)
        self.frame6.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.frame7 = tk.Frame(self.frame0, bg=self.main.cget('bg'), width=500)
        self.frame7.grid(row=4, column=0, sticky="nsew", padx=5, pady=5)

        ##label group
        self.work_path_lb_auto = Label(self.section1_lbf_auto, text="Select your work directory:", bd=1, relief="flat", width=20,
                                  fg=widge_attr.black_color, font=("Arial", 10))
        self.work_path_lb_manual = Label(self.section1_lbf_manual, text="Select your work directory:", bd=1, relief="flat",
                                       width=20,fg=widge_attr.black_color, font=("Arial", 10))

        self.slice_per_slide_lb_auto = Label(self.frame1, text="Slice per slide:", bd=1, relief="flat", width=15,
                                        fg=widge_attr.black_color, font=("Arial", 10))

        self.slice_per_slide_lb_manual = Label(self.frame1_1, text="Slice per slide:", bd=1, relief="flat", width=15,
                                             fg=widge_attr.black_color, font=("Arial", 10))

        self.OR_lb = Label(self.frame1, text="OR", bd=1, relief="flat", width=3,
                           fg=widge_attr.black_color, font=("Arial", 10))

        self.server_account_lb_auto = Label(self.frame2, text="server account:", bd=1, relief="flat", width=10,
                                       fg=widge_attr.disable_color, font=("Arial", 10))

        self.server_lb_auto = Label(self.frame2, text="server name:", bd=1, relief="flat", width=10,
                               fg=widge_attr.disable_color, font=("Arial", 10))

        self.server_account_lb_manual = Label(self.frame2_2, text="server account:", bd=1, relief="flat", width=10,
                                            fg=widge_attr.disable_color, font=("Arial", 10))

        self.server_lb_manual = Label(self.frame2_2, text="server name:", bd=1, relief="flat", width=10,
                                    fg=widge_attr.disable_color, font=("Arial", 10))




        self.aws_account_lb_auto = Label(self.frame3, text="AWS account:", bd=1, relief="flat", width=12,
                                    fg=widge_attr.disable_color, font=("Arial", 10))
        self.aws_password_lb_auto = Label(self.frame3, text="AWS password:", bd=1, relief="flat", width=15,
                                     fg=widge_attr.disable_color, font=("Arial", 10))

        self.aws_account_lb_manual = Label(self.frame3_3, text="AWS account:", bd=1, relief="flat", width=12,
                                         fg=widge_attr.disable_color, font=("Arial", 10))
        self.aws_password_lb_manual = Label(self.frame3_3, text="AWS password:", bd=1, relief="flat", width=15,
                                          fg=widge_attr.disable_color, font=("Arial", 10))





        self.fill_lb=Label(self.frame5, text="Reagent:", bd=1, relief="flat", width=6,
                                     fg=widge_attr.black_color, font=("Arial", 10))

        self.focus_lb = Label(self.frame7, text="Focus shift", bd=1, relief="flat", width=15,
                             fg=widge_attr.black_color, font=("Arial", 10))
        self.align_lb = Label(self.frame7, text="XY-plane shift", bd=1, relief="flat", width=15,
                              fg=widge_attr.black_color, font=("Arial", 10))
        self.tile_lb = Label(self.frame7, text="Tiles", bd=1, relief="flat", width=15,
                              fg=widge_attr.black_color, font=("Arial", 10))
        self.note_lb = Label(self.section4_addtion_note, text="Notes", bd=1, relief="flat", width=15,
                              fg=widge_attr.black_color, font=("Arial", 10))

        self.current_cycle_lb=Label(self.frame1_1, text="Current Cycle:", bd=1, relief="flat", width=15,
                              fg=widge_attr.black_color, font=("Arial", 10))

        #button group
        self.browse_btn_auto = Button(self.section1_lbf_auto, text="Browse", command=self.browse_handler_auto,
                                 bd=widge_attr.normal_edge, fg=widge_attr.normal_color)
        self.exp_btn_auto = Button(self.section1_lbf_auto, text="Fill experiment detail", command=self.exp_btn_handler, width=18,
                              bd=widge_attr.normal_edge, fg=widge_attr.normal_color)
        self.browse_btn_manual = Button(self.section1_lbf_manual, text="Browse", command=self.browse_handler_manual,
                                      bd=widge_attr.normal_edge, fg=widge_attr.normal_color)
        self.exp_btn_manual = Button(self.section1_lbf_manual, text="Fill experiment detail", command=self.exp_btn_handler,
                                   width=18,bd=widge_attr.normal_edge, fg=widge_attr.normal_color)
        self.recipe_btn = Button(self.frame1, text="Create Protocol", command=self.recipe_btn_handler,
                                 bd=widge_attr.normal_edge, fg=widge_attr.normal_color)

        self.assign_heater_btn = Button(self.frame1, text="Assign Heaters", command=self.assign_heater,
                                 bd=widge_attr.normal_edge, fg=widge_attr.normal_color)

        self.info_btn_auto = Button(self.auto_tab, text="Create Your Experiment",command=self.create_exp_auto,
                               bd=widge_attr.normal_edge, fg="#1473cc")

        self.info_btn_manual = Button(self.manual_tab, text="Create Your Experiment", command=self.create_exp_manual,
                                    bd=widge_attr.normal_edge, fg="#1473cc")

        self.device_btn = Button(self.frame5, text="Devices configuration", command=self.config_device,
                                 bd=widge_attr.normal_edge, fg=widge_attr.normal_color)
        self.device_btn["state"] = "disable"
        self.brain_btn = Button(self.frame5, text="Tissue Scanner (optional)", command=self.scan_tissue,
                                bd=widge_attr.normal_edge, fg=widge_attr.normal_color)
        self.brain_btn["state"] = "disable"
        self.prime_btn = Button(self.frame5, text="Prime lines", command=self.prime_btn_handler,
                                bd=widge_attr.normal_edge, fg=widge_attr.normal_color)
        self.prime_btn["state"] = "disable"
        self.fill_single_btn = Button(self.frame5, text="Fill", command=self.fill_single_reagent,
                                      bd=widge_attr.normal_edge, fg=widge_attr.normal_color)
        self.fill_single_btn["state"] = "disable"

        self.start_sequence_btn = Button(self.frame6, text="Start Automation process",command=self.start_btn_handler,
                                         bd=widge_attr.normal_edge, fg=widge_attr.normal_color)
        self.start_sequence_btn["state"] = "disable"
        self.cancel_sequence_btn = Button(self.frame6, text="Cancel Automation process", command=self.cancel_btn_handler,
                                          bd=widge_attr.normal_edge, fg=widge_attr.warning_color)
        self.cancel_sequence_btn['state'] = "disable"
        
        self.wash_btn = Button(self.frame6, text="wash tubes", command=self.wash_btn_handler,
                               bd=widge_attr.normal_edge, fg=widge_attr.normal_color)
        self.wash_btn['state'] = "disable"

        self.note_btn = Button(self.section4_addtion_note, text="Send note to server", command=self.save_to_note,
                               bd=widge_attr.normal_edge, fg=widge_attr.normal_color)

        self.focus_btn = Button(self.section3_lbf_manual, text="Step 1 Auto Focusing", command=self.focus_btn_handler,
                                bd=widge_attr.normal_edge, fg="#1473cc")
        self.focus_btn["state"] = "disable"

        self.align_btn = Button(self.section3_lbf_manual, text="Step 2 Align with Cycle00", command=self.align_btn_handler,
                                bd=widge_attr.normal_edge, fg="#1473cc")
        self.align_btn["state"] = "disable"
        self.tile_btn = Button(self.section3_lbf_manual, text="Step 3 Creat Tiles", command=self.tile_btn_handler,
                               bd=widge_attr.normal_edge, fg="#1473cc")
        self.tile_btn["state"] = "disable"
        self.max_btn = Button(self.section3_lbf_manual, text="Step 4 Image and Maxprojection", command=self.max_btn_handler,
                              bd=widge_attr.normal_edge, fg="#1473cc")
        self.max_btn["state"] = "disable"

        self.cancle_image_btn = Button(self.section3_lbf_manual, text="Cancel image process", command=self.cancel_manual_process,
                                       bd=widge_attr.normal_edge, fg=widge_attr.warning_color)
        self.cancle_image_btn["state"] = "disable"


        self.check_sequence_btn=Button(self.frame6, text="Check Sequences", command=self.check_sequence_handler,
                                       bd=widge_attr.normal_edge, fg=widge_attr.warning_color)
        self.check_sequence_btn["state"] = "disable"

       

        ## Field
        self.path = tk.StringVar()
        self.work_path_field_auto = Entry(self.section1_lbf_auto, relief="groove", width=43)
        self.work_path_field_manual = Entry(self.section1_lbf_manual, relief="groove", width=35)

        self.pixel_size = tk.StringVar()
        self.pixel_size.set("0.33")
        self.pixel_size_field_auto = Entry(self.frame2, relief="groove", width=6, textvariable=self.pixel_size)
        self.pixel_size_field_auto.config(state=DISABLED)
        self.pixel_size_field_manual = Entry(self.frame2_2, relief="groove", width=6, textvariable=self.pixel_size)
        self.pixel_size_field_manual.config(state=DISABLED)

        self.slice_number_field_auto = Entry(self.frame1, relief="groove", width=10)
        self.slice_number_field_manual = Entry(self.frame1_1, relief="groove", width=10)

        self.account = tk.StringVar()
        self.account.set("imagestorage")
        self.account_field_auto = Entry(self.frame2, relief="groove", width=15, textvariable=self.account)
        self.account_field_auto.config(state=DISABLED)
        self.account_field_manual = Entry(self.frame2_2, relief="groove", width=15, textvariable=self.account)
        self.account_field_manual.config(state=DISABLED)

        self.server = tk.StringVar()
        self.server.set(r"N:\\")
        self.server_field_auto = Entry(self.frame2, relief="groove", width=20, textvariable=self.server)
        self.server_field_auto.config(state=DISABLED)
        self.server_field_manual = Entry(self.frame2_2, relief="groove", width=20, textvariable=self.server)
        self.server_field_manual.config(state=DISABLED)

        self.aws = tk.StringVar()
        self.aws_account_field_auto = Entry(self.frame3, relief="groove", width=20, textvariable=self.aws)
        self.aws_account_field_auto.config(state=DISABLED)
        self.aws_account_field_manual = Entry(self.frame3_3, relief="groove", width=20, textvariable=self.aws)
        self.aws_account_field_manual.config(state=DISABLED)

        self.aws_pwd = tk.StringVar()
        self.aws_pwd_field_auto = Entry(self.frame3, relief="groove", width=20, textvariable=self.aws_pwd)
        self.aws_pwd_field_auto.config(state=DISABLED)
        self.aws_pwd_field_manual = Entry(self.frame3_3, relief="groove", width=20, textvariable=self.aws_pwd)
        self.aws_pwd_field_manual.config(state=DISABLED)
        ##check box

  
        self.avoid_wash= IntVar()
        self.avoid_wash.set(0)
        self.avoid_wash_cbox=Checkbutton(self.frame6, text="Avoid wash chambers",
                                               fg=widge_attr.normal_color, variable=self.avoid_wash, onvalue=1,
                                               offvalue=0)
        
        self.mock_alignment = IntVar()
        self.mock_alignment.set(0)
        self.mock_alignment_cbox = Checkbutton(self.frame1, text="Skip Alignment",
                                               fg=widge_attr.normal_color, variable=self.mock_alignment, onvalue=1,
                                               offvalue=0)
        self.mock_alignment_cbox_manual = Checkbutton(self.frame1_1, text="Skip Alignment",
                                               fg=widge_attr.normal_color, variable=self.mock_alignment, onvalue=1,
                                               offvalue=0)

        self.build_own_cycle_sequence_value = IntVar()
        self.build_own_cycle_sequence_value.set(0)
        self.build_own_cycle_sequence = Checkbutton(self.frame1, text="Use protocol in work directory",
                                                    fg=widge_attr.normal_color,
                                                    variable=self.build_own_cycle_sequence_value,
                                                    onvalue=1,
                                                    offvalue=0)
        self.change_pixel_value = IntVar()
        self.change_pixel_value.set(0)
        self.change_pixel_auto = Checkbutton(self.frame2, text="change pixel size", command=self.change_pixel_handler_auto,
                                        fg=widge_attr.normal_color, variable=self.change_pixel_value, onvalue=1,
                                        offvalue=0)
        self.change_pixel_manual = Checkbutton(self.frame2_2, text="change pixel size",
                                             command=self.change_pixel_handler_manual,
                                             fg=widge_attr.normal_color, variable=self.change_pixel_value, onvalue=1,
                                             offvalue=0)


        self.change_server_value = IntVar()
        self.change_server_value.set(0)
        self.change_server_auto_cb = Checkbutton(self.frame2, text="change storage server",
                                              command=self.change_server_auto,
                                              fg=widge_attr.normal_color, variable=self.change_server_value, onvalue=1,
                                              offvalue=0)
        self.change_server_manual_cb = Checkbutton(self.frame2_2, text="change storage server",
                                              command=self.change_server_manual,
                                              fg=widge_attr.normal_color, variable=self.change_server_value, onvalue=1,
                                              offvalue=0)


        self.upload_aws_value = IntVar()
        self.upload_aws_value.set(0)
        self.upload_aws_auto = Checkbutton(self.frame3, text="upload to AWS", command=self.upload_to_aws_auto,
                                      fg=widge_attr.normal_color, variable=self.upload_aws_value, onvalue=1, offvalue=0)
        self.upload_aws_manual = Checkbutton(self.frame3_3, text="upload to AWS", command=self.upload_to_aws_manual,
                                           fg=widge_attr.normal_color, variable=self.upload_aws_value, onvalue=1,
                                           offvalue=0)

        self.inchamber_path = IntVar()
        self.inchamber_path.set(1)
        self.inchamber_path_cbox = Checkbutton(self.frame5, text="To chamber",
                                               fg=widge_attr.normal_color, variable=self.inchamber_path, onvalue=1,
                                               offvalue=0)

        ## Dropdown list
        self.reagent = StringVar()
        self.reagent_list_cbox = ttk.Combobox(self.frame5, textvariable=self.reagent, width=8)
        self.reagent_ls=["water","PBST","IRM","CRM","USM","Incorporation Buffer",
                         "Iodoacetamide Blocker","FISH WASH","STRIP","DAPI","hyb oligos",
                        "bc oligos","gene oligos"]
        self.reagent_list_cbox['value'] = self.reagent_ls
        self.reagent_list_cbox['state'] = "readonly"

        self.current_c = StringVar()
        self.current_cbox = ttk.Combobox(self.frame1_1, textvariable=self.current_c, width=8)
        self.current_cbox['value'] = ['geneseq', 'hyb', 'bcseq']
        self.current_cbox['state'] = "readonly"

        ## spinner
        self.reagent_amount = Spinbox(self.frame5, from_=0.5, to=10, state="readonly", increment=0.5, width=5)
        self.sb1_cycle_number = Spinbox(self.frame1_1, from_=0, to=50, state="readonly", width=5)
        # canvas
        self.focusfigure = plt.Figure(figsize=(2.5, 2.5), dpi=100)
        self.canvas_focus = FigureCanvasTkAgg(self.focusfigure, master=self.frame7)
        self.alignfigure = plt.Figure(figsize=(2.5, 2.5), dpi=100)
        self.canvas_align = FigureCanvasTkAgg(self.alignfigure, master=self.frame7)
        self.tilefigure = plt.Figure(figsize=(2.5, 2.5), dpi=100)
        self.canvas_tile = FigureCanvasTkAgg(self.tilefigure, master=self.frame7)

        ## text field
        self.note_stw = scrolledtext.ScrolledText(
            master=self.section4_addtion_note,
            wrap=tk.WORD,
            width=60,
            height=2,
        )
        self.assigned_heater=0
    def check_sequence_handler(self):
        t1 = Thread(target=self.check_sequence)
        t1.start()

    def check_sequence(self):
        add_highlight_mainwindow("Start checking the sequences.....\n")
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
        add_highlight_mainwindow("reagent amount saved to reagents.csv")
        add_highlight_mainwindow("Finish checking the sequences.....")
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
    def browse_handler_auto(self):
        self.tempdir = self.search_for_file_path()
        self.path.set(self.tempdir)
        self.work_path_field_auto.config(textvariable=self.path)

    def browse_handler_manual(self):
        self.tempdir = self.search_for_file_path()
        self.path.set(self.tempdir)
        self.work_path_field_manual.config(textvariable=self.path)
    def search_for_file_path(self):
        self.currdir = os.getcwd()
        self.tempdir = filedialog.askdirectory(parent=self.parent_window, initialdir=self.currdir, title='Please select a directory')
        if len(self.tempdir) > 0:
            print("You chose: %s" % self.tempdir)
        return self.tempdir
    def exp_btn_handler(self):
        if self.work_path_field_auto.get() == "":
            messagebox.showinfo(title="Miss Input", message="Please fill the work dirctory first!")
        else:
            work_path = self.work_path_field_auto.get()
            Exp_profile(work_path)

    def exp_btn_handler_manual(self):
        if self.work_path_field_manual.get() == "":
            messagebox.showinfo(title="Miss Input", message="Please fill the work dirctory first!")
        else:
            work_path = self.work_path_field_manual.get()
            Exp_profile(work_path)
    def recipe_btn_handler(self):
        self.pb=process_builder()
        self.pb.create_window(self.work_path_field_auto.get())
    def assign_heater(self):
        self.heater_popup = tk.Tk()
        self.heater_popup.geometry("410x350")
        self.heater_popup.title("Assign heater")


        self.slide1_checked_value=IntVar()
        self.slide1_cbox = Checkbutton(self.heater_popup, text="Slide 1 included",command=self.assign_chamber1_heater, fg=widge_attr.normal_color, variable=self.slide1_checked_value, onvalue=1,offvalue=0)

        self.slide1_cbox.grid(row=0, column=0,padx=10, pady=10, sticky="nsew")

        self.slide2_checked = IntVar()
        self.slide2_checked.set(0)
        self.slide2_cbox = Checkbutton(self.heater_popup, text="Slide 2 included",command=self.assign_chamber2_heater,
                                       fg=widge_attr.normal_color, variable=self.slide2_checked, onvalue=1,
                                       offvalue=0)
        self.slide2_cbox.grid(row=0, column=1,padx=10, pady=10, sticky="nsew")

        self.slide3_checked = IntVar()
        self.slide3_checked.set(0)
        self.slide3_cbox = Checkbutton(self.heater_popup, text="Slide3  included",command=self.assign_chamber3_heater,
                                       fg=widge_attr.normal_color, variable=self.slide3_checked, onvalue=1,
                                       offvalue=0)
        self.slide3_cbox.grid(row=0, column=2,padx=10, pady=10, sticky="nsew")

        figure = plt.Figure(figsize=(1, 2), dpi=100)
        slide_img1 = FigureCanvasTkAgg(figure, master=self.heater_popup)
        slide_img1.get_tk_widget().grid(row=1, column=0,padx=10, pady=10, sticky="nsew")
        slide_img2 = FigureCanvasTkAgg(figure, master=self.heater_popup)
        slide_img2.get_tk_widget().grid(row=1, column=1,padx=10, pady=10, sticky="nsew")
        slide_img3 = FigureCanvasTkAgg(figure, master=self.heater_popup)
        slide_img3.get_tk_widget().grid(row=1, column=2,padx=10, pady=10, sticky="nsew")
        slideimg=Image.open(os.path.join(self.cwd,"front_end","slide.png"))
        plotslide1 = figure.add_subplot(111)
        plotslide1.imshow(slideimg)
        plotslide1.get_xaxis().set_visible(False)
        plotslide1.get_yaxis().set_visible(False)
        slide_img1.draw()
        slide_img2.draw()
        slide_img3.draw()

        with open(os.path.join(self.system_path,"config_file", "Heat_stage.json"), 'r') as r:
            heater_list_cfg = json.load(r)
        heater_list=[i['heat_stage'] for i in heater_list_cfg]
        heater_list=heater_list+[""]

        self.heater1 = StringVar()
        self.slide_heater1 = ttk.Combobox( self.heater_popup,textvariable=self.heater1, width=10)
        self.slide_heater1['value'] = heater_list
        self.slide_heater1['state'] = "readonly"
        self.slide_heater1.grid(row=2,column=0,padx=10, pady=10, sticky="nsew")
        self.slide_heater1.config(state=DISABLED)

        self.heater2 = StringVar()
        self.slide_heater2 = ttk.Combobox(self.heater_popup, textvariable=self.heater2, width=10)
        self.slide_heater2['value'] = heater_list
        self.slide_heater2['state'] = "readonly"
        self.slide_heater2.grid(row=2, column=1,padx=10, pady=10, sticky="nsew")
        self.slide_heater2.config(state=DISABLED)

        self.heater3 = StringVar()
        self.slide_heater3 = ttk.Combobox(self.heater_popup, textvariable=self.heater3, width=10)
        self.slide_heater3['value'] = heater_list
        self.slide_heater3['state'] = "readonly"
        self.slide_heater3.grid(row=2, column=2,padx=10, pady=10, sticky="nsew")
        self.slide_heater3.config(state=DISABLED)

        self.assign_heater_btn = Button(self.heater_popup, text="Confirm", command=self.assign_heater_to_slide,
                               bd=widge_attr.normal_edge, fg="#1473cc")
        self.assign_heater_btn.grid(row=3,column=1,padx=10, pady=10, sticky="nsew")


    def assign_chamber1_heater(self):
            self.slide_heater1.config(state=NORMAL)


    def assign_chamber2_heater(self):
            self.slide_heater2.config(state=NORMAL)


    def assign_chamber3_heater(self):
            self.slide_heater3.config(state=NORMAL)


    def assign_heater_to_slide(self):
        self.assigned_heater=1
        self.heater_dict={"chamber1":self.slide_heater1.get(),
                          "chamber2":self.slide_heater2.get(),
                          "chamber3":self.slide_heater3.get()}

        self.heater_dict={k: v for k, v in self.heater_dict.items() if v != ''}
        self.chamber_number=len(self.heater_dict)
        self.chamber_list=list(self.heater_dict.keys())
        self.heater_popup.destroy()


    def change_pixel_handler_auto(self):
        if self.change_pixel_value.get() == 1:
            self.pixel_size_field_auto.config(state=NORMAL)
        else:
            t = self.pixel_size_field_auto.get()
            self.pixel_size.set(t)
            self.pixel_size_field_auto.config(state=DISABLED)

    def change_pixel_handler_manual(self):
        if self.change_pixel_value.get() == 1:
            self.pixel_size_field_manual.config(state=NORMAL)
        else:
            t = self.pixel_size_field_manual.get()
            self.pixel_size.set(t)
            self.pixel_size_field_manual.config(state=DISABLED)
    def change_server_auto(self):
       if self.change_server_value.get() == 1:
            self.server_account_lb_auto.config(fg=widge_attr.normal_color)
            self.server_lb_auto.config(fg=widge_attr.normal_color)
            self.server_field_auto["state"]="normal"
            self.account_field_auto["state"]="normal"
       else:
           self.server_account_lb_auto.config(fg=widge_attr.disable_color)
           self.server_lb_auto.config(fg=widge_attr.disable_color)
           self.server_field_auto["state"] = "disable"
           self.account_field_auto["state"] = "disable"

    def change_server_manual(self):
       if self.change_server_value.get() == 1:
            self.server_account_lb_manual.config(fg=widge_attr.normal_color)
            self.server_lb_manual.config(fg=widge_attr.normal_color)
            self.server_field_manual["state"]="normal"
            self.account_field_manual["state"]="normal"
       else:
           self.server_account_lb_manual.config(fg=widge_attr.disable_color)
           self.server_lb_manual.config(fg=widge_attr.disable_color)
           self.server_field_manual["state"] = "disable"
           self.account_field_manual["state"] = "disable"

    def upload_to_aws_auto(self):
        if self.upload_aws_value.get() == 1:
            self.aws_account_lb_auto.config(fg=widge_attr.normal_color)
            self.aws_password_lb_auto.config(fg=widge_attr.normal_color)
            self.aws_account_field_auto["state"] = "normal"
            self.aws_pwd_field_auto["state"] = "normal"
        else:
            self.aws_account_lb_auto.config(fg=widge_attr.disable_color)
            self.aws_password_lb_auto.config(fg=widge_attr.disable_color)
            self.aws_account_field_auto["state"] = "disable"
            self.aws_pwd_field_auto["state"] = "disable"

    def upload_to_aws_manual(self):
        if self.upload_aws_value.get() == 1:
            self.aws_account_lb_manual.config(fg=widge_attr.normal_color)
            self.aws_password_lb_manual.config(fg=widge_attr.normal_color)
            self.aws_account_field_manual["state"] = "normal"
            self.aws_pwd_field_manual["state"] = "normal"
        else:
            self.aws_account_lb_manual.config(fg=widge_attr.disable_color)
            self.aws_password_lb_manual.config(fg=widge_attr.disable_color)
            self.aws_account_field_manual["state"] = "disable"
            self.aws_pwd_field_manual["state"] = "disable"
    def slice_per_slide_reformat(self):
        try:
            a = self.slice_number_field_auto.get()
            listOfChars = list()
            listOfChars.extend(a)
            num = [int(x) for x in listOfChars if x.isdigit()]
            self.slice_per_slide = num
        except:
            self.log_update=0
            messagebox.showinfo(title="Wrong Input", message="Slice per slide is wrong!")
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
            messagebox.showinfo(title="Wrong Input", message="Slice per slide is wrong!")
            self.slice_per_slide=None

    def create_exp_manual(self):
        clear_error()
        clear_log()
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
            messagebox.showinfo(title="Wrong Input", message="work directory can't be empty")
            return
        self.pos_path = self.work_path_field_manual.get()
        if self.current_c.get() == "":
            messagebox.showinfo(title="Wrong Input", message="current cycle type can't be empty")
            return
        if self.slice_number_field_manual.get() == "":
            messagebox.showinfo(title="Wrong Input", message="slice per slide can't be empty")
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
        with open(os.path.join("config_file", "scope.json"), 'r') as r:
            self.scope_cfg=json.load(r)
            self.imwidth = self.scope_cfg[0]["imwidth"]

        try:
            self.scope = scope(self.scope_cfg,self.pos_path, self.slice_per_slide, self.server, self.skip_alignment,0,system_path=self.system_path)

        except:
            messagebox.showinfo(title="Config failure ",
                                message="Please run micromanager first!")
            update_error("Please run micromanager first!")
            return
        txt = get_time() + "\n" + "work directory: " + self.pos_path + "\n" + "Current cycle: " + self.protocol_list[
            self.protocol_list_index] + "\n"
        print(txt)
        self.write_log(txt)
        add_highlight_mainwindow(txt)
        if not os.path.exists(os.path.join(self.pos_path, "manual_process_record.csv")):
            df = pd.DataFrame(columns=["protocol"])
            df["protocol"] = "imagecycle_" + self.current_cycle
            df.to_csv(os.path.join(self.pos_path, "manual_process_record.csv"), index=False)
        else:
            df = pd.read_csv(os.path.join(self.pos_path, "manual_process_record.csv"))
            df.loc[len(df.index)] = ["imagecycle_" + self.current_cycle]
            df.to_csv(os.path.join(self.pos_path, "manual_process_record.csv"), index=False)
        self.focus_btn["state"] = "normal"

    def create_exp_auto(self):
        clear_error()
        clear_log()
        self.clear_align_canvas()
        self.clear_tile_canvas()
        self.clear_focus_canvas()
        self.slice_per_slide_reformat()
        self.cancel = 0
        self.skip_alignment = self.mock_alignment.get()
        Log_window.warning_stw.delete('1.0', END)
        if self.work_path_field_auto.get() == "":
            messagebox.showinfo(title="Wrong Input", message="work directory can't be empty")
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
            self.scope = scope(self.scope_cfg,self.pos_path, self.slice_per_slide, self.server, self.skip_alignment,0,system_path=self.system_path)
        except:
            messagebox.showinfo(title="Config failure ",
                                message="Please run micromanager first!")
            update_error("Please run micromanager first!")
            return
        if self.assigned_heater==0:
            self.heater_dict={'chamber1': "heatstage1", 'chamber2': "heatstage2", 'chamber3': "heatstage3"}
            self.chamber_number=3
            self.chamber_list = list(self.heater_dict.keys())
        self.fluidics = FluidicSystem(system_path=self.system_path,pos_path=self.pos_path,slide_hearter_dictionary=self.heater_dict)
        self.all_autobtn_normal()




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
        add_highlight_mainwindow("protocol has beed assigned!"+"\n")
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
                self.warning_dev.insert(END, "Syringe groups works well!\n", 'normal')
                return
            except:
                self.warning_dev.insert(END, "Please, reconnect Pump groups!\n", 'warning')
                return

        if "heater" in device_group:
            self.fluidics.config_heater()
            self.device_status["heater_group"] = 1
            self.warning_dev.insert(END, "Heater groups works well!\n", 'normal')



        if "selector" in device_group:
            try:
                self.fluidics.config_selector()
                self.device_status["selector_group"] = 1
                self.warning_dev.insert(END, "Selector groups works well!\n", 'normal')
            except:
                self.warning_dev.insert(END, "Please, reconnect selector groups!\n", 'warning')
                return



    def scan_tissue(self):
        scanner = tissue_scan(self.pos_path)

    def prime_btn_handler(self):
        if 0 in [self.device_status['selector_group'], self.device_status['syringe_pump_group']]:
            messagebox.showinfo(title="Config device", message="Please config the device first!")
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
            add_highlight_mainwindow(txt)
            self.write_log(txt)
            t2 = Thread(target=self.sensor_fluidics_process)
            t2.start()

            
    def sensor_fluidics_process(self):
        check=self.fluidics.cycle_done
        while check!=1:
            time.sleep(2)
            check = self.fluidics.cycle_done
        txt = get_time() + "Prime/Wash line Done!\n"
        add_highlight_mainwindow(txt)
        self.fluidics.disconnect_syringe_pump()
        self.fluidics.disconnect_selector()
        self.all_autobtn_normal()
        self.cancel_sequence_btn['state'] = "disable"


    def fill_single_reagent(self):
        if 0 in [self.device_status['selector_group'], self.device_status['syringe_pump_group']]:
            messagebox.showinfo(title="Config device", message="Please config the device first!")
        else:
            t1 = Thread(target=self.pump_reagent)
            t1.start()

    def pump_reagent(self):
        reagent = self.reagent.get()
        print(reagent)
        if reagent=="":
            add_highlight_mainwindow("Please select reagent!\n")
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
                    add_highlight_mainwindow(txt)
                    self.write_log(txt)
                    print(txt)
                    self.fluidics.syringe_pump.dispense_pump(vol, pumpRate)
            if self.inchamber_path.get() != 1:
                self.fluidics.syringe_pump.fillSyringe(vol * len(self.chamber_list), pumpRate)
                time.sleep(1)

                self.fluidics.setSource("null", "waste")
                txt = get_time() + "Pump " + reagent + " " + str(vol) + " ul to waste"  + "\n"
                add_highlight_mainwindow(txt)
                self.write_log(txt)
                print(txt)
                self.fluidics.syringe_pump.dispense_pump(vol, pumpRate)

            time.sleep(3)
            self.fluidics.disconnect_syringe_pump()
            self.fluidics.disconnect_selector()
            self.all_autobtn_normal()
            txt = get_time() + "fill with " + reagent + " is done!\n"
            self.fill_single_btn['state'] = 'normal'
            add_highlight_mainwindow(txt)
            self.write_log(txt)
                
            
    def start_btn_handler(self):
        if sum(self.device_status.values())!=len(self.device_status):
            messagebox.showinfo(title="config", message="Please config all devis!")
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
        add_highlight_mainwindow(txt)
        self.write_log(txt)
        self.all_autobtn_normal()
        self.cancel_sequence_btn['state'] = "disable"


    def wash_btn_handler(self):
        if 0 in [self.device_status['selector_group'], self.device_status['syringe_pump_group']]:
            messagebox.showinfo(title="Config device", message="Please config the device first!")
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
                messagebox.showinfo(title="Config failure ",
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
            add_highlight_mainwindow(txt)
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
        add_highlight_mainwindow(txt)
        if "Fluidics_sequence" in self.process_cycle:
            try:
                self.protocol=self.fluidics.find_protocol(self.process_cycle)
            except:
                self.fluidics.disconnect_syringe_pump()
                self.fluidics.disconnect_selector()
                self.fluidics.disconnect_heater()
                self.all_autobtn_normal()
                self.cancel_sequence_btn['state'] = "disable"
                messagebox.showinfo(title="Protocol issue", message="check protocol file, the format is wrong")
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
            add_highlight_mainwindow("Cycle 00 doesn't need to run alignment!")
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
        add_highlight_mainwindow(txt)
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
            self.aws_account_lb.config(fg=widge_attr.normal_color)
            self.aws_password_lb.config(fg=widge_attr.normal_color)
            self.aws_account_field["state"] = "normal"
            self.aws_pwd_field["state"] = "normal"
        else:
            self.aws_account_lb.config(fg=widge_attr.disable_color)
            self.aws_password_lb.config(fg=widge_attr.disable_color)
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
        add_highlight_mainwindow(txt)

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

    def save_to_note(self):
        if not os.path.exists(os.path.join(self.pos_path, "experiment_detail.txt")):
            open(os.path.join(self.pos_path, "experiment_detail.txt"), 'a').close()
        txt=get_time()+self.note_stw.get("1.0", "end-1c")+"\n"
        f = open(os.path.join(self.pos_path, "experiment_detail.txt"), "a")
        f.write(txt)
        f.close()
        server_path = '/mnt/imagestorage/' + self.pos_path[3:]
        self.linux_server=self.server
        try:
            cmd = "scp " + os.path.join(self.pos_path, "experiment_detail.txt") + " " + self.linux_server + ":" + server_path
            os.system(cmd)
            txt = get_time() + "local note saved to experiment_detail.txt, and uploaded to server!"+"\n"
            add_highlight_mainwindow(txt)

        except:
            txt=get_time()+"local note saved to experiment_detail.txt, upload to server is failed!"
            add_highlight_mainwindow(txt)
    def focus_btn_handler(self):
        self.scope.cancel_process = 0
        clear_error()
        t = Thread(target=self.do_focus_thread)
        t.start()

    def align_btn_handler(self):
        self.scope.cancel_process = 0
        self.scope.focus_status = 1
        clear_error()
        t = Thread(target=self.align_and_draw_thread)
        t.start()


    def tile_btn_handler(self):
        self.scope.cancel_process = 0
        self.scope.alignment_status = 1
        clear_error()
        t = Thread(target=self.tile_and_draw_thread)
        t.start()
    def max_btn_handler(self):
        self.cancel=0
        self.scope.cancel_process = 0
        self.scope.maketiles_status = 1
        clear_error()
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








