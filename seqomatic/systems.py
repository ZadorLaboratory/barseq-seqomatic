"""
Author: Aixin Zhang
Description: Seq_o_Matics main system: Fluidics exchange system

"""
"""
Author: Aixin Zhang
Description: Seq_o_Matics main system: Imaging system

"""
import copy
import json
import math
import os
import shutil
import subprocess
import threading
import time

from concurrent.futures import ThreadPoolExecutor, wait
from pytz import timezone
from datetime import datetime
#from typing import List

import cv2

import numpy as np
import pandas as pd
import skimage
import tifffile
import warnings

from pycromanager import Acquisition, Core, multi_d_acquisition_events 

from device.Syringe_pump import Syringe_Pump
from device.Heatingstage import heat_stage_group
from device.Selector_2025 import ElveflowMux

warnings.filterwarnings("ignore")

####################################################
#
#                  common util functions
#  
####################################################

def get_file_name(path, kind):
    os.chdir(path)
    files = []
    for file in os.listdir():
        if file.endswith(kind):
            files.append(file)
    return files

def get_time():
    time_now = timezone('US/Pacific')
    time = str(datetime.now(time_now))[0:19] + "\n"
    return time

def sort_by(string):
    pos = np.array([int(s[s.find('Pos') + 3:s.find('.tif')]) for s in string])
    rearrange = np.argsort(pos)
    string = [string[i] for i in rearrange]
    return string

def clean_space(directory):
    for item in os.listdir(directory):
        if os.path.isdir(os.path.join(directory, item)):
            shutil.rmtree(os.path.join(directory, item))


####################################################
#
#                  common GUI functions/constants
#  
####################################################

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

def denoise(x):
    x[x<np.percentile(x, 85)]=0
    return x

def hattop_convert(x):
    filterSize = (10, 10)
    kernel=cv2.getStructuringElement(cv2.MORPH_RECT, filterSize)
    return cv2.morphologyEx(x, cv2.MORPH_TOPHAT, kernel)




class FluidicSystem():

    def __init__(self, system_path, pos_path, slide_heater_dictionary):
        self.system_path = system_path
        with open(os.path.join(system_path,"config_file", "Tecan_syringe_pump.json"), 'r') as r:
            self.syringe_pump_cfg = json.load(r)
        self.syringe_pump_dictionary=self.syringe_pump_cfg [0]["Dict"]
        self.syringe_pump_speed_dict=self.syringe_pump_cfg [0]["speed_code"]

        with open(os.path.join(system_path,"config_file", "ElveflowMuxDevice_selector.json"), 'r') as r:
            self.selector_cfg = json.load(r)

        with open(os.path.join(system_path,"config_file", 'Selector_Reagent_Components.json'), 'r') as r:
            self.Fluidics_selector_components = json.load(r)
        self.selector_reagent=[i['solution'] for i in self.Fluidics_selector_components]
        self.address=[i['address'] for i in self.Fluidics_selector_components]
        self.selector_fluidics_dict = dict(zip(self.address, self.selector_reagent))

        self.slide_heater_dict = slide_heater_dictionary
        print(self.slide_heater_dict)
        with open(os.path.join(system_path,"config_file", "Heat_stage.json"), 'r') as r:
            self.Heater_cfg = json.load(r)
        self.Heater_cfg=[i for i in self.Heater_cfg if i['heat_stage'] in list(self.slide_heater_dict.values())]
        self.slide_number=len(self.slide_heater_dict)
        self.sequence_folder=str(self.slide_number)+"_chamber_system_sequence"
        self.start_fluidics =1
        self.sourceInfoList = []
        self.currentSpeed = 0.0
        self.currentSource = None
        self.sequenceStatus=0
        self.last_sequenceStatus = -2
        self.sequenceIndex = 0
        self.config_fluidics_sequences = {}
        self.sequenceStateEndTime = 0
        self.pos_path=pos_path
        self.cycle_done=0
        self.start_image=0
        self.mlToPump=0
        self.disconnect_device=0
        self.waiting_time=3
        self.heat_temp=5.6
        self.chamber1=0
        self.chamber2=1
        self.chamber3=2
        self.bufferms =3
        self.scale=1000 #unit ml to ul

        with open(os.path.join(self.system_path, "reagent_sequence_file",self.sequence_folder, 'Fluidics_sequence_flush_all.json'), 'r') as r:
            self.FLUSH_ALL_SEQUENCE = json.load(r)
        with open(os.path.join(self.system_path, "reagent_sequence_file",self.sequence_folder, 'Fluidics_sequence_fill_all.json'), 'r') as r:
            self.Fill_ALL_SEQUENCE = json.load(r)
        with open(os.path.join(self.system_path, "reagent_sequence_file", self.sequence_folder,
                               'Fluidics_sequence_flush_all_no_chamber.json'), 'r') as r:
            self.FLUSH_REAGENTS_SEQUENCE = json.load(r)


    def write_log(self, txt):
        f = open(os.path.join(self.pos_path, "log.txt"), "a")
        f.write(txt)
        f.close()
        
    def config_syringe_pump(self):
        self.syringe_pump=Syringe_Pump(self.syringe_pump_cfg)
        self.syringe_pump.connect_pump()
        self.syringe_pump.config_pump()
        time.sleep(1)
        self.syringe_pump.disconnect_pump()

    def config_heater(self):
        self.Heatingdevice=heat_stage_group(self.Heater_cfg, 5.7, self.pos_path)
        self.Heatingdevice.connect_heater_group()
        self.Heatingdevice.config()
        self.Heatingdevice.disconnect_heater_group()

    def connect_heater(self):
        self.Heatingdevice = heat_stage_group(self.Heater_cfg, self.heat_temp, self.pos_path)
        self.Heatingdevice.connect_heater_group()
        
    def disconnect_heater(self):
        self.Heatingdevice.disconnect_heater_group()
  

    def connect_syringe_pump(self):
        self.syringe_pump.connect_pump()
          
    def disconnect_syringe_pump(self):
        self.syringe_pump.disconnect_pump()
        
    def config_selector(self):
        self.selector = ElveflowMux(self.selector_cfg)
        self.selector.config_selector()

        


    def connect_selector(self):
        self.selector.connect()


    def disconnect_selector(self):
        self.selector.disconnect()

    def loadSequence(self,fluidicsSequence):
        self.fluidSequence=fluidicsSequence

    def cancelSequence(self):
        self.Heatingdevice.cancel=1
        self.sequenceStatus = -1
        self.sequenceIndex = 0
        self.cycle_done = 1
        self.start_image=0

    def setSource(self, selector_reagent,pump_reagent):
        if selector_reagent not in ["null", "", '','null',None]:
            self.selector.set_path(selector_reagent)
            txt=get_time()+"set Elveflow distributor to "+selector_reagent+"\n"
            self.write_log(txt)
            add_fluidics_status(txt)
        if pump_reagent not in ["null", "", '','null']:
            self.syringe_pump.set_path(pump_reagent)
            txt=get_time()+"set Pump distributor to "+pump_reagent+"\n"
            self.write_log(txt)
            add_fluidics_status(txt)
        time.sleep(2)

        
    def updateStatus(self):
        if self.sequenceStatus == -1:
            if self.sequenceStatus != self.last_sequenceStatus:
                txt=get_time()+"Status Check : fluidics sequence was cancelled \n"
                self.write_log(txt)
                add_fluidics_status(txt)
                print(bcolors.OKBLUE+"Status Check: fluidics sequence cancelled"+bcolors.END)
                self.last_sequenceStatus = self.sequenceStatus
                self.last_sequenceStatus=-1
            return
        elif self.sequenceStatus == -2:
            txt=get_time()+"Status Check:sequence finished successfully\n"
            add_fluidics_status(txt)
            self.write_log(txt)
            print(bcolors.OKBLUE+" Status Check:sequence finished successfully"+bcolors.END)
            self.last_sequenceStatus = -2
        elif self.sequenceStatus == 1:
            pass
            return
        
    def startSequence(self):
        if self.sequenceStatus == 1:
            txt="System is still running! \n"
            print('System is still running!')
            self.write_log(txt)
            add_fluidics_status(txt)
            return
        self.cycle_done = 0
        self.start_image=0
        self.idx=100/len(self.fluidSequence)
        update_process_bar(0)
        update_process_label("Fluidics exchanging")
        self.runSequence()

    def finishSequence(self):
        self.cycle_done = 1
        self.start_image=1
        self.sequenceIndex = 0
        self.sequenceStatus = 0
        self.last_sequenceStatus=-2



    def runSequence(self):
        if self.sequenceStatus == -1:
            print("system canceled (from runsequence tread)!")
            update_process_bar(0)
            update_process_label("Process")
            self.updateStatus()
            self.disconnect_syringe_pump()
            self.disconnect_selector()
            self.disconnect_heater()
            return

        if self.sequenceIndex >= len(self.fluidSequence):
            self.sequenceStatus=-2
            txt=get_time()+"sequence finished successfully!"+"\n"
            print(txt)
            self.write_log(txt)
            update_process_bar(0)
            update_process_label("Process")
            add_fluidics_reagent(get_time()+"sequence finished successfully!"+"\n")
            self.long_heat=0
            self.cycle_done = 1
            self.start_image=1
            self.sequenceIndex = 0
            self.sequenceStatus = 0
            self.last_sequenceStatus = -2
            time.sleep(5)
            return
        sequenceIndex = self.sequenceIndex
        sequenceState = self.fluidSequence[sequenceIndex]
        self.idx =self.idx+ 100 / len(self.fluidSequence)
        update_process_bar(self.idx)
        self.sequenceStatus = 1

        if sequenceState["device"] =="pump" :
            pumpRate=sequenceState["speed_code"]
            vol=sequenceState["unit_volume"]*self.scale
            print(self.selector_fluidics_dict)
            print(sequenceState["source"])
            if sequenceState["source"] !="null":
                reagent_selector=self.selector_fluidics_dict[int(sequenceState["source"])]
            else:
                reagent_selector ="null"
            pump_port_name=sequenceState['pump_port']
            self.setSource(reagent_selector,pump_port_name)
            if sequenceState["process"]=="import":
                add_fluidics_reagent(f"name: {sequenceState['Solution name']}\n")
                txt=get_time()+f"current in step {str(sequenceIndex+1)} importing to syringe: {sequenceState['Solution name']}\n"
                add_fluidics_reagent(txt)
                self.write_log(txt)
                txt = get_time() + f"Total Vol: {sequenceState['unit_volume']} ml\n"
                add_fluidics_reagent(txt)
                self.write_log(txt)
                print(bcolors.WARNING + txt+bcolors.END)
                self.syringe_pump.fillSyringe(vol, pumpRate)
            if sequenceState["process"]=="export":
                txt=get_time()+f"current in step {str(sequenceIndex+1)} exporting to chamber: {sequenceState['Solution name']}\n"
                add_fluidics_reagent(txt)
                self.write_log(txt)
                txt = get_time() + f"Total Vol: {sequenceState['unit_volume']} ml\n"
                add_fluidics_reagent(txt)
                self.write_log(txt)
                print(bcolors.WARNING + txt+bcolors.END)
                self.syringe_pump.dispense_pump(vol, pumpRate)

            self.updateStatus()
            if self.sequenceStatus != -1:
                self.sequenceIndex += 1
                self.run_sequence_thread = threading.Timer(self.waiting_time, self.runSequence)
                self.run_sequence_thread.start()

        elif sequenceState["device"] =="heat_device" :
            txt=get_time()+f"current in step {str(sequenceIndex+1)} heating: {str(sequenceState['time'])} seconds\n"
            add_fluidics_reagent(txt)
            self.write_log(txt)
            print(bcolors.WARNING + txt+bcolors.END)
            self.Heatingdevice.heat_for_3min(sequenceState["time"])
            self.updateStatus()
            if self.Heatingdevice.cancel==1 :
                txt = get_time() + "Heater is cancelled "+ "\n"
                add_fluidics_reagent(txt)
                self.write_log(txt)
                print(bcolors.WARNING + txt + bcolors.END)
            elif self.Heatingdevice.heat_status==0:
                txt = get_time() + "Heater is wrong " + "\n"
                add_fluidics_reagent(txt)
                self.write_log(txt)
                print(bcolors.WARNING + txt + bcolors.END)
                return
            else:
                self.sequenceIndex += 1
                self.run_sequence_thread = threading.Timer(self.waiting_time, self.runSequence)
                self.run_sequence_thread.start()

        elif sequenceState["device"] == "wait":
            txt = get_time() + "Incubating for " + str(sequenceState["time"])+" seconds."+"\n"
            add_fluidics_reagent(txt)
            self.write_log(txt)
            print(bcolors.WARNING + txt + bcolors.END)
            time_diff = 0
            start = datetime.now()
            self.updateStatus()
            self.sequenceIndex += 1
            expectedTime=sequenceState["time"]
            while time_diff <= expectedTime + self.bufferms:
                if self.sequenceStatus == -1:
                    break
                time.sleep(2)
                time_diff = (datetime.now() - start).total_seconds()
            if self.sequenceStatus != -1:
                self.run_sequence_thread = threading.Timer(self.waiting_time, self.runSequence)
                self.run_sequence_thread.start()
        else:
            print("skip step, the process is unknow!!")
            update_error("skip step, the process is unknow!!")
            self.sequenceIndex += 1
            self.run_sequence_thread = threading.Timer(0, self.runSequence)
            self.run_sequence_thread.start()
        return

    def find_protocol(self,type):
        if "geneseq" in type and "01" in type:
            with open(os.path.join("reagent_sequence_file",self.sequence_folder, "Fluidics_sequence_geneseq01.json"), 'r') as r:
                protocol = json.load(r)
            txt = get_time() + "load Fluidics_sequence_geneseq01.json protocol!\n"
            print(txt)
            add_fluidics_reagent(txt)
            self.write_log(txt)
            if not os.path.exists(os.path.join(self.pos_path, "Fluidics_sequence_geneseq01.json")):
                shutil.copyfile(os.path.join("reagent_sequence_file",self.sequence_folder, "Fluidics_sequence_geneseq01.json"), 
                                os.path.join(self.pos_path, "Fluidics_sequence_geneseq01.json"))
        elif "bcseq" in type and "01" in type:
            with open(os.path.join("reagent_sequence_file", self.sequence_folder,"Fluidics_sequence_bcseq01.json"), 'r') as r:
                protocol = json.load(r)
            txt=get_time()+"load Fluidics_sequence_bcseq01.json protocol!\n"
            print(txt)
            add_fluidics_reagent(txt)
            self.write_log(txt)
            if not os.path.exists(os.path.join(self.pos_path, "Fluidics_sequence_bcseq01.json")):
                shutil.copyfile(os.path.join( "reagent_sequence_file",self.sequence_folder, "Fluidics_sequence_bcseq01.json"), 
                                os.path.join(self.pos_path, "Fluidics_sequence_bcseq01.json"))
        elif "geneseq" in type  and "01" not in type:
            with open(os.path.join( "reagent_sequence_file",self.sequence_folder, "Fluidics_sequence_geneseq02+.json"), 'r') as r:
                protocol = json.load(r)
            txt = get_time() + "load Fluidics_sequence_geneseq02+.json protocol!\n"
            print(txt)
            add_fluidics_reagent(txt)
            self.write_log(txt)
            if not os.path.exists(os.path.join(self.pos_path, "Fluidics_sequence_geneseq02+.json")):
                shutil.copyfile(os.path.join( "reagent_sequence_file",self.sequence_folder, "Fluidics_sequence_geneseq02+.json"),
                                os.path.join(self.pos_path, "Fluidics_sequence_geneseq02+.json"))
        elif "bcseq" in type and "01" not in type:
            with open(os.path.join( "reagent_sequence_file", self.sequence_folder,"Fluidics_sequence_bcseq02+.json"), 'r') as r:
                protocol = json.load(r)
            txt = get_time() + "load Fluidics_sequence_bcseq02+.json protocol!\n"
            print(txt)
            add_fluidics_reagent(txt)
            self.write_log(txt)
            if not os.path.exists(os.path.join(self.pos_path, "Fluidics_sequence_bcseq02+.json")):
                shutil.copyfile(os.path.join( "reagent_sequence_file",self.sequence_folder, "Fluidics_sequence_bcseq02+.json"),
                                os.path.join(self.pos_path, "Fluidics_sequence_bcseq02+.json"))
        elif "user_defined" in type:
            file_name = type + ".json"
            with open(os.path.join("reagent_sequence_file",self.sequence_folder,file_name), 'r') as r:
                protocol = json.load(r)
            txt = get_time() + "load Fluidics_sequence_user_defined protocol\n!"
            print(txt)
            add_fluidics_reagent(txt)
            self.write_log(txt)
            if not os.path.exists(os.path.join("reagent_sequence_file",self.sequence_folder,file_name)):
                shutil.copyfile(os.path.join("reagent_sequence_file",self.sequence_folder,file_name),
                                os.path.join(self.pos_path, file_name))

        elif "HYB" in type and "rehyb" not in type:
            with open(os.path.join("reagent_sequence_file",self.sequence_folder, "Fluidics_sequence_HYB.json"), 'r') as r:
                protocol = json.load(r)
            txt = get_time() + "load Fluidics_sequence_HYB protocol\n!"
            print(txt)
            add_fluidics_reagent(txt)
            self.write_log(txt)
            if not os.path.exists(os.path.join(self.pos_path, "Fluidics_sequence_HYB.json")):
                shutil.copyfile(os.path.join( "reagent_sequence_file",self.sequence_folder, "Fluidics_sequence_HYB.json"),
                                os.path.join(self.pos_path, "Fluidics_sequence_HYB.json"))
        elif "add_gene_primer" in type and "rehyb" not in type:
            with open(os.path.join( "reagent_sequence_file", self.sequence_folder,"Fluidics_sequence_add_gene_primer.json"), 'r') as r:
                protocol = json.load(r)
            txt = get_time() + "load Fluidics_sequence_add_gene_primer protocol\n!"
            print(txt)
            add_fluidics_reagent(txt)
            self.write_log(txt)
            if not os.path.exists(os.path.join(self.pos_path, "Fluidics_sequence_add_gene_primer.json")):
                shutil.copyfile(os.path.join( "reagent_sequence_file",self.sequence_folder, "Fluidics_sequence_add_gene_primer.json"),
                                os.path.join(self.pos_path, "Fluidics_sequence_add_gene_primer.json"))
        elif "add_bc_primer" in type and "rehyb" not in type:
            with open(os.path.join("reagent_sequence_file",self.sequence_folder, "Fluidics_sequence_add_bc_primer.json"), 'r') as r:
                protocol = json.load(r)
            txt = get_time() + "load Fluidics_sequence_add_bc_primer protocol\n!"
            print(txt)
            add_fluidics_reagent(txt)
            self.write_log(txt)
            if not os.path.exists(os.path.join(self.pos_path, "Fluidics_sequence_add_bc_primer.json")):
                shutil.copyfile(os.path.join( "reagent_sequence_file",self.sequence_folder,"Fluidics_sequence_add_bc_primer.json"),
                                os.path.join(self.pos_path, "Fluidics_sequence_add_bc_primer.json"))


        elif "HYB" in type and "rehyb" in type:
            with open(os.path.join( "reagent_sequence_file", self.sequence_folder,"Fluidics_sequence_HYB_rehyb.json"), 'r') as r:
                protocol = json.load(r)
            txt = get_time() + "load Fluidics_sequence_HYB_rehyb protocol\n!"
            print(txt)
            add_fluidics_reagent(txt)
            self.write_log(txt)
            if not os.path.exists(os.path.join(self.pos_path, "Fluidics_sequence_HYB_rehyb.json")):
                shutil.copyfile(os.path.join("reagent_sequence_file",self.sequence_folder, "Fluidics_sequence_HYB_rehyb.json"),
                                os.path.join(self.pos_path, "Fluidics_sequence_HYB_rehyb.json"))
        elif "add_gene_primer" in type and "rehyb"  in type:
            with open(os.path.join("reagent_sequence_file", self.sequence_folder,"Fluidics_sequence_add_gene_primer_rehyb.json"), 'r') as r:
                protocol = json.load(r)
            txt = get_time() + "load Fluidics_sequence_add_gene_primer_rehyb protocol\n!"
            print(txt)
            add_fluidics_reagent(txt)
            self.write_log(txt)
            if not os.path.exists(os.path.join(self.pos_path, "Fluidics_sequence_add_gene_primer_rehyb.json")):
                shutil.copyfile(os.path.join( "reagent_sequence_file", self.sequence_folder,"Fluidics_sequence_add_gene_primer_rehyb.json"),
                                os.path.join(self.pos_path, "Fluidics_sequence_add_gene_primer_rehyb.json"))
        elif "add_bc_primer" in type and "rehyb"  in type:
            with open(os.path.join("reagent_sequence_file",self.sequence_folder, "Fluidics_sequence_add_bc_primer_rehyb.json"), 'r') as r:
                protocol = json.load(r)
            txt = get_time() + "load Fluidics_sequence_add_bc_primer_rehyb protocol\n!"
            print(txt)
            add_fluidics_reagent(txt)
            self.write_log(txt)
            if not os.path.exists(os.path.join(self.pos_path, "Fluidics_sequence_add_bc_primer_rehyb.json")):
                shutil.copyfile(os.path.join( "reagent_sequence_file", self.sequence_folder,"Fluidics_sequence_add_bc_primer_rehyb.json"),
                                os.path.join(self.pos_path, "Fluidics_sequence_add_bc_primer_rehyb.json"))
        elif "strip" in type:
            with open(os.path.join( "reagent_sequence_file",self.sequence_folder, "Fluidics_sequence_strip.json"),
                      'r') as r:
                protocol = json.load(r)
            txt = get_time() + "load Fluidics_sequence_strip protocol\n!"
            print(txt)
            add_fluidics_reagent(txt)
            self.write_log(txt)
            if not os.path.exists(os.path.join(self.pos_path, "Fluidics_sequence_strip.json")):
                shutil.copyfile(
                    os.path.join( "reagent_sequence_file",self.sequence_folder, "Fluidics_sequence_strip.json"),
                    os.path.join(self.pos_path, "Fluidics_sequence_strip.json"))

        return protocol


            
def single_createtiles(df,imwidth,overlap,pixelsize):
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
                imwidth * (1 -overlap / 100) * pixelsize)) + 1,
                         math.ceil(np.ptp(y) / (imwidth * (
                                 1 - overlap / 100) * pixelsize)) + 1]
        midpoint = [tileconfig[i][0] / 2 - 0.5, tileconfig[i][1] / 2 - 0.5]

        for n in range(0, tileconfig[i][0] * tileconfig[i][1]):
            grid_col, grid_row = ind2sub(tileconfig[i], np.array(n))
            # change LABEL
            LABEL = ['Pos' + str(i + 1) +
                     '_' + str(grid_col).zfill(3) +
                     '_' + str(grid_row).zfill(3)]
            # change XY positions
            Yoffset = (grid_row - midpoint[1]) * imwidth * (
                    1 - overlap / 100) * pixelsize;
            Xoffset = (grid_col - midpoint[0]) * imwidth * (
                    1 - overlap / 100) * pixelsize;
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
    sharpen1 = np.array(([0, 1, 0],
                         [-1, 5, -1],
                         [0, -1, 0]), dtype="int")
    pos_per_slice = 4;
    z_dir=1


def get_time():
    time_now = timezone('US/Pacific')
    time = str(datetime.now(time_now))[0:19] + "\n"
    return time


def get_col(image_file_name):
    start = image_file_name.find('_', 7) + 1
    end = start + 3
    return int(image_file_name[start:end])


def get_row(image_file_name):
    start = image_file_name.find('_') + 1
    end = start + 3
    return int(image_file_name[start:end])


def copy_dic(pos_path, focusfolder, dicfolder):
    directory = os.listdir(os.path.join(pos_path, focusfolder))
    for i in directory:
        if ".tif" in i:
            shutil.move(os.path.join(pos_path, focusfolder, i),
                        os.path.join(pos_path, dicfolder, i))


def ind2sub(array_shape, ind):
    # Gives repeated indices, replicates matlabs ind2sub
    cols = (ind.astype("int32") // array_shape[0])
    rows = (ind.astype("int32") % array_shape[0])
    return (rows, cols)


def save_offset_and_json(pos_path, file, dict, jsonfile,z_dir):
    pos_list = pd.read_csv(os.path.join(pos_path, file))
    for i in range(len(pos_list)):
        pos_list.loc[pos_list['position'] == 'Pos' + str(i), ['z_offset']] = dict['Pos' + str(i)]
    #pos_list['z_shift']=(pos_list['z_offset']-pos_list['z'])/1.5 # This is used if we don't have piezo
    pos_list['z_shift']=(pos_list['piezo']-pos_list['z_offset'])/1.5  # This is used if we  have piezo
    pos_list['z_offset'] = pos_list['z']+pos_list['z_shift']*z_dir*(1.5)# This is used if we  have piezo
    pos_list.to_csv(os.path.join(pos_path, "offset" + file))
    with open(os.path.join(pos_path, jsonfile)) as f:
        d = json.load(f)
    d2 = copy.deepcopy(d)
    for i in pos_list.index:
        d2['map']['StagePositions']['array'][i]['DevicePositions']['array'][0]['Position_um']['array'][0] = \
            pos_list.loc[
                i, 'z_offset']
    json_object = json.dumps(d2, indent=2)
    with open(os.path.join(pos_path, "offset" + jsonfile), "w") as outfile:
        outfile.write(json_object)

    with open(os.path.join(pos_path, "pre_adjusted_pos.pos"), "w") as outfile:
        outfile.write(json_object)
    diff = pos_list['z_shift'].values * 1.5
    return diff


def get_pos_data(item,piezo):
    positions = item['DevicePositions']['array']
    pos_data = {}
    if piezo==1:
        for pos in positions:
            pos_data.update(get_position_piezo(pos))
        pos_data.update({'position': item['Label']['scalar']})
    else:
        for pos in positions:
            pos_data.update(get_position(pos))
        pos_data.update({'position': item['Label']['scalar']})
    return pos_data


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

def get_position(pos):
    position_name = pos['Device']['scalar']
    position_value = pos['Position_um']['array']
    if position_name == 'ZDrive':
        return {'z': position_value[0]}
    elif position_name == 'XYStage':
        return {'x': position_value[0], 'y': position_value[1]}
    else:
        return None



class scope():
    def __init__(self, cfg, 
                       pos_path, 
                       slice_per_slide, 
                       server, 
                       mock_align, 
                       fine_align, 
                       system_path):
        
        self.system_path=system_path
        self.scope_cfg = cfg
        self.core = Core()
        self.pos_path = pos_path
        self.slicePerSlide = slice_per_slide
        self.focus_status = 0
        self.alignment_status = 0
        self.maketiles_status = 0
        self.max_projection_status = 0
        self.maxprojection_name =''
        self.cancel_process = 0
        self.live_plot=0
        self.focus_bad=0
        self.linux_server=server
        self.mock_align=mock_align
        self.ZDrive_safe_pos=self.scope_cfg[0]["ZDrive_safe_pos"]
        self.XYStage_fluidics_safe_pos=self.scope_cfg[0]["XYStage_fluidics_safe_pos"]
        self.piezo=self.scope_cfg[0]["piezo"]
        self.XYStage_image_safe_pos=self.scope_cfg[0]["XYStage_image_safe_pos"]
        self.scope_exposure_time_dict=self.scope_cfg[0]["scope_exposure_time_dict"]
        self.z_dir= self.scope_cfg[0]["z_dir"]
        self.stage_x_dir=self.scope_cfg[0]["stage_x_dir"]
        self.stage_y_dir=self.scope_cfg[0]["stage_y_dir"]
        self.pixelsize=self.scope_cfg[0]["pixel_size"]
        self.imwidth=self.scope_cfg[0]["imwidth"]
        self.overlap=self.scope_cfg[0]["overlap"]
        self.maxprojection_drive=self.scope_cfg[0]["maxproject_drive"]
        self.fine_align=fine_align
        self.gene_target_channel =self.scope_cfg[0]["geneseq_focus_target_channel"]
        self.hyb_target_channel=self.scope_cfg[0]["Hyb_focus_target_channel"]
        self.align_channel=self.scope_cfg[0]["align_channel"]
        self.thread_limiter = threading.Semaphore(10)

        if self.piezo==1:
            self.stack_num_focus = round(abs(scope_constant.piezo_focus_end_pos - scope_constant.piezo_focus_start_pos) / scope_constant.piezo_step)
            self.stack_num_maxpro = round(abs(scope_constant.piezo_maxpro_start_pos - scope_constant.piezo_maxpro_end_pos) / scope_constant.piezo_step)
        else:
            self.stack_num_focus = round(abs(scope_constant.scope_focus_end_pos - scope_constant.scope_focus_start_pos) / scope_constant.scope_step)
            self.stack_num_maxpro = round(abs(scope_constant.scope_start_pos - scope_constant.scope_end_pos) / scope_constant.scope_step)

    def move_to_fluidics(self):
        self.core.set_position("ZDrive", self.ZDrive_safe_pos)
        time.sleep(1)
        self.core.set_xy_position(self.XYStage_fluidics_safe_pos[0],
                                  self.XYStage_fluidics_safe_pos[1])

    def move_to_image(self):
        self.core.set_position("ZDrive", self.ZDrive_safe_pos)
        time.sleep(1)
        self.core.set_xy_position(self.XYStage_image_safe_pos[0],
                                  self.XYStage_image_safe_pos[1])

    def check_cycle00(self):
        with open(os.path.join(self.pos_path, "cycle00.pos")) as f:
            d = json.load(f)
        if self.piezo==1:
            focus_poslist = pd.DataFrame([get_pos_data(item,self.piezo) for item in d['map']['StagePositions']['array']])[
                ['position', 'x', 'y', 'z',
                 'piezo']]
        else:
            focus_poslist = pd.DataFrame([get_pos_data(item,self.piezo) for item in d['map']['StagePositions']['array']])[
                ['position', 'x', 'y', 'z']]

        if len(focus_poslist)!= sum(self.slicePerSlide) * 4:
            print(len(focus_poslist))
            print(sum(self.slicePerSlide) * 4)
            update_error("Slice per slide is not consistent with number of FOV!")
            check_file=0
        else:
            check_file=1
        return check_file


    def get_pixel(self, ind, dataset):
        pixels = dataset.read_image(**ind)
        return pixels

    def get_sharpness(self, f, sharpen):
        img = np.array(f)
        img_filter = cv2.medianBlur(img, 3)
        sharpen_img = cv2.filter2D(img_filter, -1, sharpen)
        gy, gx = np.gradient(sharpen_img)
        gnorm = np.sqrt(gx ** 2 + gy ** 2)
        return np.average(gnorm)

    def write_log(self, txt):
        f = open(os.path.join(self.pos_path, "log.txt"), "a")
        f.write(txt)
        f.close()

    def calculate_z_stack(self, start_pos, end_pos):
        df = pd.read_csv(os.path.join(self.pos_path, self.cycle + ".csv"))
        self.piezo_middle_pos = df['piezo'][0]
        piezo_event_pos = np.arange(self.piezo_middle_pos + start_pos, self.piezo_middle_pos + end_pos,
                                    scope_constant.piezo_step)
        return piezo_event_pos


    def create_piezo_event(self, channel, start_pos, end_pos):
        self.piezo_event_pos = self.calculate_z_stack(start_pos, end_pos)
        piezo_event = []
        self.channel=[]
        for c in channel:
            for z in range(0, len(self.piezo_event_pos)):
                piezo_event.append({'axes': {'channel': c, 'z': z},
                                    'config_group': ['Channel', c],
                                    'exposure': self.scope_exposure_time_dict.get(c),
                                    'z': self.piezo_event_pos[z]})
                self.channel.append(c)

        return piezo_event

    def calculate_z_stack_without_piezo(self, middle, start_pos, end_pos):
        scope_event_pos = np.arange(middle + start_pos, middle + end_pos,
                                    scope_constant.scope_step)
        return scope_event_pos

    def create_scope_event(self, channel,pos, start_pos, end_pos, middle_pos):
        self.scope_event_pos = self.calculate_z_stack_without_piezo(middle_pos,start_pos, end_pos)
        print(self.scope_event_pos)
        scope_event = []
        for c in channel:
            for z in range(0, len(self.scope_event_pos)):
                scope_event.append({'axes': {'channel': c, 'z': z,'Pos':pos},
                                    'config_group': ['Channel', c],
                                    'exposure': self.scope_exposure_time_dict.get(c),
                                    'z': self.scope_event_pos[z]})
        return scope_event

    def find_focus_plane(self,pos):
        img = tifffile.imread(os.path.join(self.pos_path, "focus" + self.cycle, pos+"_1", pos + "_NDTiffStack.tif"))
        if self.focus_channel[0]==self.focus_channel[1]:
            focusimg =img
            display_img = img
        else:
            img_reshaped_array = img.reshape(80, self.imwidth, self.imwidth)
            display_img=[img_reshaped_array[i] for i in range(len(self.channel)) if self.channel[i] == self.align_channel]
            focusimg=[img_reshaped_array[i] for i in range(len(self.channel)) if self.channel[i] == self.target_channel]
        sharpness = [self.get_sharpness(i[800:2400, 800:2400], scope_constant.sharpen1) for i in focusimg]
        max_index = np.argmax(sharpness)
        z_name = pos + ".tif"
        im = display_img[max_index]
        skimage.io.imsave(z_name, im, photometric='minisblack')
        dict = {pos: self.piezo_event_pos[max_index]}
        self.z_new_ls.update(dict)
        txt = get_time() + self.cycle + " Position " + str(pos) + ' is_finished \n'
        self.write_log(txt)
        add_highlight_from_scope(txt)

    def image_with_piezo(self,path,pos,piezo_event,x,y,z,piezo_z):
        self.core.set_xy_position(x, y)
        self.core.wait_for_device("XYStage")
        txt = get_time() + "XYStage ready"+"\n"
        self.write_log(txt)
        self.core.set_position("ZDrive", z)
        self.core.wait_for_device("ZDrive")
        txt = get_time() + "ZDrive ready"+"\n"
        self.write_log(txt)
        self.core.set_position("DA Z Stage", piezo_z)
        self.core.wait_for_device("DA Z Stage")
        txt = get_time() + "DA Z Stage"+"\n"
        self.write_log(txt)
        txt = get_time() + self.cycle + ' scope start acq.acquire ' + pos + "\n"
        self.write_log(txt)
        add_highlight_from_scope(txt)
        with Acquisition(directory=path, name=pos,
                         show_display=False) as acq:
            acq.acquire(piezo_event)
            acq.mark_finished()
        self.core.stop_stage_sequence('DA Z Stage')
        self.core.wait_for_device("DA Z Stage")
        self.core.set_position("DA Z Stage", 170)
        txt = get_time() + "Piezo reset"+"\n"
        self.write_log(txt)

    def image_with_scope(self,path,pos,piezo_event,x,y):
        pass


    def focus_image(self, cycle, poslist):
        self.cancel_process = 0
        self.cycle = cycle

        if "hyb" in self.cycle:
            self.focus_channel = [self.align_channel]+[self.hyb_target_channel]
            self.target_channel = self.hyb_target_channel

        else:
            self.focus_channel = [self.align_channel]+[self.gene_target_channel]
            self.target_channel = self.gene_target_channel
        print(self.focus_channel)
        self.z_new_ls = {}
        self.piezo_event = self.create_piezo_event(self.focus_channel, scope_constant.piezo_focus_start_pos,
                                                   scope_constant.piezo_focus_end_pos)
        threads = []
        os.chdir(os.path.join(self.pos_path, "focus" + self.cycle))
        clean_space(os.path.join(self.pos_path, "focus" + self.cycle))
        self.i=100/len(poslist)
        update_process_bar(0)
        update_process_label("Focusing")
        print(get_time()+"start focus image")
        add_highlight_from_scope(get_time()+"start focus image")
        self.core.set_shutter_open(False)
        for index, row in poslist.iterrows():
            update_process_bar(self.i)
            if self.cancel_process ==1:
                txt=get_time()+"process canceled!"
                print(txt)
                self.write_log(txt)
                self.core.set_position("DA Z Stage", self.piezo_middle_pos)
                add_highlight_from_scope(txt)
                break
            pos = row['position']
            if self.piezo==1:
                try:
                    self.image_with_piezo(os.path.join(self.pos_path, "focus" + self.cycle), pos, self.piezo_event, row['x'],
                                          row['y'], row['z'], self.piezo_event_pos[0])
                except Exception as e:
                    time.sleep(3)
                    self.image_with_piezo(os.path.join(self.pos_path, "focus" + self.cycle), pos, self.piezo_event, row['x'],
                                      row['y'], row['z'], self.piezo_event_pos[0])
            else:
                pass
            self.i=self.i+100/len(poslist)

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(self.find_focus_plane, pos) for pos in poslist["position"].tolist()]
        try:
            done, not_done = wait(futures)
            results = [future.result() for future in done]
        except Exception as e:
            print(f"Error processing position: {e}")
        try:
            copy_dic(self.pos_path, "focus" + self.cycle, "dicfocus" + self.cycle)
            diff = save_offset_and_json(self.pos_path, self.cycle + ".csv", self.z_new_ls, self.cycle + ".pos",self.z_dir)
            for i in range(len(diff)):
                if abs(diff[i]) >= 20:
                    #self.focus_status = 0
                    txt = get_time() + self.cycle + ' extrem focus change detected at ' + str(
                        i) + " position!\n"
                    update_error(txt)
                    self.write_log(txt)
                    self.focus_bad = 1
            if self.focus_bad == 0:
                self.focus_status = 1
                print(self.cycle+" focuse thread! I am finished!Thread closed!")
            self.focus_status = 1
            os.chdir(self.pos_path)
        except:
            txt=get_time()+"focus is wrong or cancelled"
            update_error(txt)
            diff=0
        os.chdir(self.pos_path)
        return diff

    def do_alignment(self,cycle):
        if self.mock_align==1:
            self.cycle = cycle
            self.pos_batch_size = [i * scope_constant.pos_per_slice for i in self.slicePerSlide]
            print(self.pos_batch_size)
            self.slidenum = np.zeros(sum(self.pos_batch_size))
            self.x_offset = np.zeros(self.pos_batch_size)
            self.y_offset = np.zeros(self.pos_batch_size)
            df = pd.read_csv(os.path.join(self.pos_path, 'offset' + self.cycle + '.csv'))
            df['x_adjust'] = df['x']
            df['y_adjust'] = df['y']
            df.to_csv(os.path.join(self.pos_path, 'regoffset' + self.cycle + '.csv'), index=False)
            filename = 'offset' + self.cycle + ".pos"
            new_filename = 'regoffset' + self.cycle + '.pos'
            with open(os.path.join(self.pos_path, filename)) as f:
                d = json.load(f)
            d2 = copy.deepcopy(d)
            for i in df.index:
                d2['map']['StagePositions']['array'][i]['DevicePositions']['array'][2]['Position_um']['array'][0] = \
                df.loc[
                    i, 'x_adjust']
                d2['map']['StagePositions']['array'][i]['DevicePositions']['array'][2]['Position_um']['array'][1] = \
                df.loc[
                    i, 'y_adjust']
            # switch to d2['map']['StagePositions']['array'][i]['DevicePositions']['array'][2] if you have piezo,d2['map']['StagePositions']['array'][i]['DevicePositions']['array'][1] if no piezo
            json_object = json.dumps(d2, indent=2)
            with open(os.path.join(self.pos_path, new_filename), "w") as outfile:
                outfile.write(json_object)
            with open(os.path.join(self.pos_path, "pre_adjusted_pos.pos"), "w") as outfile:
                outfile.write(json_object)
            txt = get_time() + self.cycle + " saved regoffset.pos for microscope review and next cycle\n"
            add_highlight_from_scope(txt)
            self.write_log(txt)
            print("saved regoffset.pos for microscope review and next cycle")
            self.alignment_status = 1
            return
        else:
            check_focus = self.focus_status
            self.cycle = cycle
            while check_focus == 0 and self.cancel_process!=1 :
                time.sleep(5)
                check_focus = self.focus_status
                print("Alignemt thread! I am waiting for focusing finished!")
            if self.cancel_process==1:
                return
            fname1 = self.get_file_name(os.path.join(self.pos_path, "dicfocuscycle00"), ".tif")  # reference image
            self.fname1 = sort_by(fname1)
            fname2 = self.get_file_name(os.path.join(self.pos_path, "dicfocus" + self.cycle), ".tif")
            self.fname2 = sort_by(fname2)

            if len(fname2) != len(fname1):
                self.alignment_status = 0
                txt = get_time() + "current cycle's image number in dicfouce folder is not consistent with pre cycle!"
                update_error(txt)
                self.write_log(txt)
                return
            else:
                self.pos_batch_size = [i * scope_constant.pos_per_slice for i in self.slicePerSlide]

                imref = []
                imcurr = []

                for i in self.fname1:
                    im = cv2.imread(os.path.join(self.pos_path, "dicfocuscycle00", i), cv2.IMREAD_UNCHANGED)
                    imref.append(im)
                for j in self.fname2:
                    im = cv2.imread(os.path.join(self.pos_path, "dicfocus" + self.cycle, j), cv2.IMREAD_UNCHANGED)
                    imcurr.append(im)
                self.imref = np.array(imref)
                self.imcurr = np.array(imcurr)
                self.slidenum = np.zeros(sum(self.pos_batch_size))
                self.slidenum[0:self.pos_batch_size[0]] = 1
                print(self.pos_batch_size)
                for i in range(1, len(self.pos_batch_size)):
                    self.slidenum[sum(self.pos_batch_size[0:i]):sum(self.pos_batch_size[0:i + 1])] = int(i + 1)
                self.slidenum=self.slidenum.astype(int)
                print(self.slidenum)
                if len(self.slidenum) != len(self.imcurr):
                    self.alignment_status = 0
                    txt = get_time() + self.cycle + " The number of images is different from slice numbers. Abort.\n"
                    update_error(txt)
                    self.write_log(txt)

                else:
                    self.calculate_shift()

    def calculate_shift_singlethread(self,i):
        add_highlight_from_scope("Image System start to alignment at " + str(i) + "th position\n")
        ref = self.imref[i]  # reference
        img = self.imcurr[i]
        xoffset, yoffset = self.imregcorr(img, ref)
        self.x_offset[i] = xoffset
        self.y_offset[i] = yoffset
        txt = get_time() + self.cycle + " finished " + str(i) + "th position\n"
        add_highlight_from_scope(txt)
        self.write_log(txt)
    def calculate_shift(self):
        threads = []
        add_highlight_from_scope(get_time() + "Image System start to alignment!\n")
        self.x_offset = np.zeros(sum(self.pos_batch_size))
        self.y_offset = np.zeros(sum(self.pos_batch_size))
        self.i=100/sum(self.pos_batch_size)
        update_process_bar(0)
        update_process_label("Aligning")
        # if self.fine_align==0
        #     align_list=[]

        for i in range(sum(self.pos_batch_size)):
            if self.cancel_process ==1:
                txt=get_time()+"process canceled!"
                print(txt)
                self.write_log(txt)
                add_highlight_from_scope(txt)
                break
            update_process_bar(self.i)
            t = threading.Thread(target=self.calculate_shift_singlethread, args=(i,))
            t.start()
            threads.append(t)
            time.sleep(3)
            self.i = self.i + 100 / sum(self.pos_batch_size)
        for t in threads:
            t.join()
        update_process_bar(0)
        self.sanity_check_alignment()
        self.update_regoffsetfile()
        return

    def update_regoffsetfile(self):
        df = pd.read_csv(os.path.join(self.pos_path, 'offset' + self.cycle + '.csv'))
        df['x_adjust'] = df['x'] + self.stage_x_dir * self.x_translation_pooled * self.pixelsize
        df['y_adjust'] = df['y'] + self.stage_y_dir * self.y_translation_pooled * self.pixelsize
        df.to_csv(os.path.join(self.pos_path, 'regoffset' + self.cycle + '.csv'), index=False)
        filename = 'offset' + self.cycle + ".pos"
        new_filename = 'regoffset' + self.cycle + '.pos'
        with open(os.path.join(self.pos_path, filename)) as f:
            d = json.load(f)
        d2 = copy.deepcopy(d)
        if self.piezo==1:
            for i in df.index:
                d2['map']['StagePositions']['array'][i]['DevicePositions']['array'][2]['Position_um']['array'][0] = df.loc[
                    i, 'x_adjust']
                d2['map']['StagePositions']['array'][i]['DevicePositions']['array'][2]['Position_um']['array'][1] = df.loc[
                    i, 'y_adjust']
        else:
            for i in df.index:
                d2['map']['StagePositions']['array'][i]['DevicePositions']['array'][1]['Position_um']['array'][0] = df.loc[
                    i, 'x_adjust']
                d2['map']['StagePositions']['array'][i]['DevicePositions']['array'][1]['Position_um']['array'][1] = df.loc[
                    i, 'y_adjust']
        json_object = json.dumps(d2, indent=2)
        with open(os.path.join(self.pos_path, new_filename), "w") as outfile:
            outfile.write(json_object)
        with open(os.path.join(self.pos_path, "pre_adjusted_pos.pos"), "w") as outfile:
            outfile.write(json_object)
        txt = get_time() + self.cycle + " saved regoffset.pos for microscope review and next cycle\n"
        add_highlight_from_scope(txt)
        self.write_log(txt)
        print("saved regoffset.pos for microscope review and next cycle")
        return

    def createBlackmanWindow(self, windowSize):
        M = windowSize[0]
        N = windowSize[1]
        a0 = 7938 / 18608;
        a1 = 9240 / 18608;
        a2 = 1430 / 18608;
        n = np.arange(1, N + 1, 1)
        m = np.arange(1, M + 1, 1)
        h1 = 1;
        h2 = 1;
        h1_part1 = a1 * np.cos(2 * math.pi * m / (M - 1))
        h1_part2 = a2 * np.cos(4 * math.pi * m / (M - 1))
        h2_part1 = a1 * np.cos(2 * math.pi * n / (N - 1))
        h2_part2 = a2 * np.cos(4 * math.pi * n / (N - 1))
        if M > 1:
            h1 = a0 - h1_part1 + h1_part2;
        if N > 1:
            h2 = a0 - h2_part1 + h2_part2;
        h1 = h1.reshape(len(h1), 1)
        h = np.multiply(h1, h2)
        return h

    def machineEpsilon(self, func=float):
        machine_epsilon = func(1)
        while func(1) + func(machine_epsilon) != func(1):
            machine_epsilon_last = machine_epsilon
            machine_epsilon = func(machine_epsilon) / func(2)
        return machine_epsilon_last

    def imregcorr(self, moving, fixed):
        if self.cancel_process == 1:
            return
        moving = moving.astype('single')
        fixed = fixed.astype('single')
        windowSize = moving.shape
        h = self.createBlackmanWindow(windowSize)
        moving_1 = moving * h
        fixed_1 = fixed * h
        A = fixed_1
        A_l = A.tolist()
        A = np.array([round(a, 3) for row in A_l for a in row]).reshape((2048, 2048))
        B = moving_1;
        B_l = B.tolist()
        B = np.array([round(b, 3) for row in B_l for b in row]).reshape((2048, 2048))
        size_A = np.array(A.shape)
        size_B = np.array(B.shape)
        outSize = size_A + size_B - 1;
        A_trans = np.fft.fft2(A, outSize)
        B_trans = np.fft.fft2(B, outSize)
        ABConj = A_trans * np.conj(B_trans);

        eps = self.machineEpsilon(float)

        denominator = abs(eps + ABConj)
        d = np.fft.ifft2(ABConj / denominator)
        d_shift = np.fft.fftshift(d)
        d_shift_flatten = d_shift.flatten()
        result = np.where(d_shift_flatten == np.amax(d_shift_flatten))
        peak = np.unravel_index(result, d_shift.shape)
        ypeak = peak[0][0][0]
        xpeak = peak[1][0][0]
        u = np.real(d_shift[ypeak - 1:ypeak + 2, xpeak - 1:xpeak + 2])
        u = u.T.flatten()
        x = np.array([-1, -1, -1, 0, 0, 0, 1, 1, 1])
        y = np.array([-1, 0, 1, -1, 0, 1, -1, 0, 1])
        X = np.empty((6, 9))
        X[0] = np.ones(9)
        X[1] = x
        X[2] = y
        X[3] = x * y
        X[4] = x ** 2
        X[5] = y ** 2
        A1 = np.real(np.linalg.lstsq(X.T, u.T, rcond=None)[0])
        x_offset = (-A1[2] * A1[3] + 2 * A1[5] * A1[1]) / (A1[3] ** 2 - 4 * A1[4] * A1[5])
        y_offset = -1 / (A1[3] ** 2 - 4 * A1[4] * A1[5]) * (A1[3] * A1[1] - 2 * A1[4] * A1[2])
        x_offset = round(10 * x_offset) / 10;
        y_offset = round(10 * y_offset) / 10;
        xpeak = xpeak + 1 + x_offset;
        ypeak = ypeak + 1 + y_offset;
        peakVal = np.dot(np.array([1, x_offset, y_offset, x_offset * y_offset, x_offset ** 2, y_offset ** 2]), A1.T);
        peakVal = float(abs(peakVal))
        gridYCenter = round(1 + (d.shape[0] - 1) / 2)
        gridXCenter = round(1 + (d.shape[1] - 1) / 2)
        xpeak_1 = xpeak - gridXCenter;
        ypeak_1 = ypeak - gridYCenter;
        if all((d == peakVal).flatten()):
            xpeak_1 = 0
            ypeak_1 = 0
        return xpeak_1, ypeak_1

    def sanity_check_alignment(self):
        self.x_translation_pooled = np.zeros(len(self.slidenum))
        self.y_translation_pooled = np.zeros(len(self.slidenum))
        uniqslidenum = np.unique(self.slidenum);
        for i in uniqslidenum:
            x_median = np.median(self.x_offset[np.where(self.slidenum == i)])
            y_median = np.median(self.y_offset[np.where(self.slidenum == i)])
            self.x_translation_pooled[np.where(self.slidenum == i)] = x_median
            self.y_translation_pooled[np.where(self.slidenum == i)] = y_median
        self.alignment_status = 1
        for i in uniqslidenum:
            x_sub = self.x_offset[np.where(self.slidenum == i)]
            y_sub = self.y_offset[np.where(self.slidenum == i)]
            max_range_xy = max(np.ptp(x_sub, axis=0), np.ptp(y_sub, axis=0))
            x_extreme_diff = np.median(x_sub[0:scope_constant.pos_per_slice]) - np.median(
                x_sub[-scope_constant.pos_per_slice:])
            y_extreme_diff = np.median(y_sub[0:scope_constant.pos_per_slice]) - np.median(
                y_sub[-scope_constant.pos_per_slice:])
            if x_extreme_diff > 50:
                txt = get_time() + self.cycle + " Slide " + str(i) + ' is tilted COUNTER CLOCKWISE.\n'
                update_error(txt)
                self.write_log(txt)
                #self.alignment_status = 0
            if x_extreme_diff < -50:
                txt = get_time() + self.cycle + " Slide " + str(i) + ' is tilted CLOCKWISE.\n'
                update_error(txt)
                self.write_log(txt)
                #self.alignment_status = 0
            if max_range_xy > 50:
                txt = get_time() + self.cycle + " Slide " + str(
                    i) + ' is tilted CLOCKWISEgrossly tilted and/or some registrations have failed. Double-check fixed positions.\n'
                update_error(txt)
                self.write_log(txt)
                #self.alignment_status = 0
            print(self.cycle+" alignmentthread finish!")
        return

    def get_file_name(self, path, kind):
        os.chdir(path)
        files = []
        for file in os.listdir():
            if file.endswith(kind):
                files.append(file)
        return files

    def make_tile(self, cycle):
        self.cycle = cycle
        check = self.alignment_status
        while check == 0:
            time.sleep(5)
            check = self.alignment_status
            print("Make tile thread! I am waiting alignment finished!")
        self.load_achor_regpos()
        self.createtiles()
        self.fix_Posinfo()
        self.maketiles_status=1
        print("Make tile thread! I am finished! Thread closed!")

    def load_achor_regpos(self):
        filename = 'regoffset' + self.cycle + '.pos'
        if os.path.isfile(os.path.join(self.pos_path, filename)):
            with open(os.path.join(self.pos_path, filename)) as f:
                d = json.load(f)
            if self.piezo==1:
                self.regoffset = pd.DataFrame([get_pos_data(item,self.piezo) for item in d['map']['StagePositions']['array']])[
                    ['position', 'x', 'y', 'z','piezo']]
                self.piezo_init = self.regoffset['piezo'][0]
            else:
                self.regoffset = pd.DataFrame([get_pos_data(item,self.piezo) for item in d['map']['StagePositions']['array']])[
                ['position', 'x', 'y', 'z']]
        else:
            self.regoffset = pd.DataFrame([])
        return
    def count_tiles(self):
        df = pd.read_csv(os.path.join(self.pos_path, 'cycle00.csv'))

    def createtiles(self):
        df = pd.read_csv(os.path.join(self.pos_path, 'cycle00.csv'))  # this pary is used when we have piezo
        self.piezo_init = df.iloc[0]['piezo']
        tileconfig = [None] * (math.floor(len(self.regoffset) / 4))
        lablelist = []
        poslist = []
        Slide = []
        number = []
        pos = []
        for i in range(0, math.floor(len(self.regoffset) / 4)):
            y = self.regoffset['y'][i * 4:(i + 1) * 4].to_numpy(dtype=float)
            x = self.regoffset['x'][i * 4:(i + 1) * 4].to_numpy(dtype=float)
            z = self.regoffset['z'][i * 4:(i + 1) * 4].to_numpy(dtype=float)

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
                    self.imwidth * (1 - self.overlap / 100) * self.pixelsize)) + 1,
                             math.ceil(np.ptp(y) / (self.imwidth * (
                                     1 - self.overlap / 100) * self.pixelsize)) + 1]
            midpoint = [tileconfig[i][0] / 2 - 0.5, tileconfig[i][1] / 2 - 0.5]

            for n in range(0, tileconfig[i][0] * tileconfig[i][1]):
                grid_col, grid_row = ind2sub(tileconfig[i], np.array(n))
                # change LABEL
                LABEL = ['Pos' + str(i + 1) +
                         '_' + str(grid_col).zfill(3) +
                         '_' + str(grid_row).zfill(3)]
                # change XY positions
                Yoffset = (grid_row - midpoint[1]) * self.imwidth * (
                        1 - self.overlap / 100) * self.pixelsize;
                Xoffset = (grid_col - midpoint[0]) * self.imwidth * (
                        1 - self.overlap / 100) * self.pixelsize;
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

        self.tilepos = pd.DataFrame(columns=['Slidenum', 'Posinfo', 'X', 'Y', 'Z'])
        self.tilepos['Slidenum'] = Slide
        self.tilepos['Posinfo'] = lablelist
        self.tilepos['Pos'] = pos
        self.tilepos['X'] = [pos[0] for pos in poslist]
        self.tilepos['Y'] = [pos[1] for pos in poslist]
        self.tilepos['Z'] = [pos[2] for pos in poslist]
        self.maketiles_status=1

    def fix_Posinfo(self):
        self.tilepos_new = pd.DataFrame(columns=['Slidenum', 'Posinfo', 'X', 'Y', 'Z', 'Pos', 'switched_Posinfo'])
        slice_ls = pd.unique(self.tilepos['Pos'])
        for s in slice_ls:
            image_name_df = self.tilepos[self.tilepos['Pos'] == s]
            image_name = image_name_df['Posinfo']
            col_list = [get_col(i) for i in image_name]
            row_list = [get_row(i) for i in image_name]
            row_list_new = [str(max(row_list) - i).zfill(3) for i in row_list]
            col_list_new = [str(max(col_list) - i).zfill(3) for i in col_list]
            new_name = []
            for num in range(len(row_list_new)):
                name = s + "_" + row_list_new[num] + "_" + col_list_new[num]
                new_name.append(name)
            image_name_df['switched_Posinfo'] = new_name
            frames = [self.tilepos_new, image_name_df]
            self.tilepos_new = pd.concat(frames)
        self.tilepos_new.to_csv(os.path.join(self.pos_path, 'tiledregoffset' + self.cycle + '.csv'), index=False)




    def image_and_maxprojection(self, cycle):
        self.live_plot=1
        check = self.maketiles_status
        while check == 0:
            time.sleep(5)
            check = self.maketiles_status
            print("maxprojection thread! I am waiting make tile finished!")
        self.cycle = cycle
        self.create_max_projection_folder()
        print(self.cycle )
        self.Assign_image_channel()
        self.start_max_imgage_cycle()
        print("maxprojection thread! I am finished! Thread closed!")
        txt=get_time()+""+self.cycle+" image and maxprojection finished!"+"\n"
        print(txt)
        self.write_log(txt)
        add_highlight_from_scope(txt)


    def create_max_projection_folder(self):
        if os.path.isfile(os.path.join(self.pos_path, 'tiledregoffset' + self.cycle + '.csv')):
            self.tilepos_new = pd.read_csv(os.path.join(self.pos_path, 'tiledregoffset' + self.cycle + '.csv'))
            self.maxproject_list =self.tilepos_new
        else:
            txt = get_time() + self.cycle + "Can't find tiledregoff" + self.cycle + " datafile! \n"
            update_error(txt)
            self.max_projection_status = 0
            return

        image_path = os.path.join(self.pos_path, self.cycle)
        if not os.path.exists(image_path):
            os.mkdir(image_path)
            txt = get_time() + self.cycle + ' maxprojection Folder is created!\n'
            add_highlight_from_scope(txt)
            self.write_log(txt)
            print(txt)
        if not os.path.exists(os.path.join(self.maxprojection_drive, self.pos_path[3:]+"_maxprojection")):
            os.mkdir(os.path.join(self.maxprojection_drive, self.pos_path[3:]+"_maxprojection"))
        # create folder on server




    def Assign_image_channel(self):
        if ('geneseq' in self.cycle or 'bcseq' in self.cycle or 'user_defined' in self.cycle) and '01' in self.cycle:
            self.channel_list = ["G", "T", "A", "C", "Hyb-DAPI"]
            channel_number = len(self.channel_list)
            self.maxprojection_stack = self.stack_num_maxpro * channel_number


        elif ('geneseq' in self.cycle or 'bcseq' in self.cycle or 'user_defined' in self.cycle) and ~(
                '01' in self.cycle):
            self.channel_list = ["G", "T", "A", "C"]
            channel_number = len(self.channel_list)
            self.maxprojection_stack = self.stack_num_maxpro * channel_number
        else:
            self.channel_list = ["Hyb-GFP", "Hyb-YFP", "Hyb-TxRed","Hyb-Cy5", "Hyb-DAPI", "DIC"]
            channel_number = len(self.channel_list)
            self.maxprojection_stack = self.stack_num_maxpro * channel_number
        self.timer=5*len(self.channel_list)
        return

    def start_max_imgage_cycle(self):
        if self.channel_list != ['']:
            start_time = time.time()
            os.chdir(os.path.join(self.pos_path, self.cycle))
            self.maxprojection_image_cycle()
            add_highlight_from_scope("--- %s seconds ---" % (time.time() - start_time))
            self.maxprojection_name='end'
            self.max_projection_status = 1
            self.fluidics = 1
        else:
            txt = get_time() + self.cycle + "Can not load image channel!"
            update_error(txt)
            self.maxprojection_name = 'end'
            self.write_log(txt)
            print("Can not load image channel!")
            self.max_projection_status = 0


    def maxprojection_image_cycle(self):
        if os.path.isfile(os.path.join(self.pos_path, 'tiledregoffset' + self.cycle + '.csv')):
            self.tilepos_new = pd.read_csv(os.path.join(self.pos_path, 'tiledregoffset' + self.cycle + '.csv'))
            self.maxproject_list =self.tilepos_new
        update_process_bar(0)
        update_process_label("maxprojection")
        threads=[]
        df = pd.read_csv(os.path.join(self.pos_path, 'cycle00.csv'))  # this pary is used when we have piezo
        self.piezo_init = df.iloc[0]['piezo']
        self.i = 100 / len(self.maxproject_list)
        self.write_log('Start maxprojection')
        self.piezo_middle_pos = self.piezo #This is used when we have piezo
        self.piezo_event = self.create_piezo_event(self.channel_list, scope_constant.piezo_maxpro_start_pos,
                                                   scope_constant.piezo_maxpro_end_pos)
        self.core.set_shutter_open(False)
        for index, row in self.maxproject_list.iterrows():
            update_process_bar(self.i)
            pos = row['switched_Posinfo']
            txt=get_time()+"prepare "+pos+" in "+self.cycle+"\n"
            print(index)
            self.write_log(txt)
            add_highlight_from_scope(txt)
            if self.cancel_process ==1:
                txt=get_time()+"process canceled!"
                print(txt)
                self.write_log(txt)
                add_highlight_from_scope(txt)
                update_process_bar(0)
                update_process_label("process")
                self.core.set_position("DA Z Stage", self.piezo_middle_pos) # This is used when we have piezo
                break
        #     #This part is used when we have piezo
            try:
                self.image_with_piezo(os.path.join(self.pos_path, self.cycle), pos, self.piezo_event, row['X'],
                                      row['Y'], row['Z'], self.piezo_event_pos[0])
            except Exception as e:
                time.sleep(2)
                txt = get_time() + self.cycle +" "+pos + ' Acq.acquire failed' +  "\n"
                self.write_log(txt)
                error_message = "An error occurred: " + str(e)+ "\n"
                self.write_log(error_message)
                update_error(error_message)
                txt = get_time() + self.cycle + ' System try to reimage!' + "\n"
                self.write_log(txt)
                try:
                    self.core=Core()
                    self.core.stop_stage_sequence('DA Z Stage')
                    self.image_with_piezo(os.path.join(self.pos_path, self.cycle), pos, self.piezo_event, row['X'],
                                          row['Y'], row['Z'], self.piezo_event_pos[0])
                    txt = get_time() + "Second Acquisition passed!"+ "\n"
                    self.write_log(txt)
                    update_error(txt)
                except Exception as e:
                    txt = get_time() + self.cycle + ' Second time Acq.acquire failed' + "\n"
                    self.write_log(txt)
                    error_message = "An error occurred: " + str(e) + "\n"
                    self.write_log(error_message)
                    self.core.set_position("DA Z Stage", self.piezo_event_pos[0])
                    self.core.wait_for_device("DA Z Stage")
                    txt = get_time() + "Piezo reset!"+ "\n"
                    self.write_log(txt)
            try:
                t = threading.Thread(target=self.process_scope_image, args=(row['switched_Posinfo'],))
                t.start()
                threads.append(t)
            except:
                update_error("Missing maxprojection")
                pass

        for t in threads:
            t.join()
        self.core.set_position("DA Z Stage", self.piezo_middle_pos)
        os.chdir(self.system_path)
        self.maxprojection_name = 'end'
        txt=get_time()+"image is finished!"
        print(txt)
        self.write_log(txt)
        add_highlight_from_scope(txt)
        time.sleep(3)
        self.max_projection_status=self.check_transfer_complete(self.maxprojection_drive)
        return
    def process_scope_image(self,pos):
        try:
            self.maxprojection(pos)
            self.maxprojection_name = 'MAX_' + pos+ '.tif'
            txt = get_time() + "Maxprojection finish " + pos + " in "+self.cycle +"\n"
            print(txt)
            self.write_log(txt)
            add_highlight_from_scope(txt)
        finally:
            self.thread_limiter.release()




    def maxprojection(self,pos):
        name = 'MAX_' + pos + '.tif'
        img = skimage.io.imread(os.path.join(self.pos_path, self.cycle, pos + '_1', pos+'_NDTiffStack.tif'))
        img_max = []
        for i in range(len(self.channel_list)):
            if self.channel_list[i]!='DIC':
                img_max.append(np.max(img[i, :], axis=(0)))
            else:
                img_max.append(img[i, 9,:,:])
        if not os.path.exists(os.path.join(self.maxprojection_drive,self.pos_path[3:]+"_maxprojection",self.cycle)):
            os.mkdir(os.path.join(self.maxprojection_drive,self.pos_path[3:]+"_maxprojection",self.cycle))
        tifffile.imwrite(os.path.join(self.maxprojection_drive,self.pos_path[3:]+"_maxprojection",self.cycle,name),np.array(img_max), photometric='minisblack')


    def send_protocol(self,pos_path):
        files = os.listdir(pos_path)
        f = [f for f in files if ".json" in f or ".txt" in f or ".csv" in f]
        server_path =  pos_path[3:]+ "_maxprojection"
        for i in f:
            shutil.copy(os.path.join(self.pos_path,i),os.path.join(self.linux_server,server_path,i))


    def send_to_server(self,pos_path):

        image_local_path = os.path.join(self.maxprojection_drive,pos_path[3:] + "_maxprojection")
        shutil.copy(image_local_path, os.path.join(self.linux_server,pos_path[3:] + "_maxprojection"))



    def live_view(self,img):
        img_converted = np.array(list(map(hattop_convert, img)))
        img_converted_denoise = np.array(list(map(denoise, img_converted)))
        img_1 = np.stack((img_converted_denoise[0, :, :], img_converted_denoise[1, :, :],
                          img_converted_denoise[2, :, :], img_converted_denoise[3, :, :]), axis=-1)
        img_2 = np.reshape(img_1, (2048 * 2048, 4))
        img_3 = np.dot(img_2, color_array)
        img_4 = np.reshape(img_3, (2048, 2048, 3))
        img_4 = np.where(img_4 > 255, 255, img_4).astype('uint8')
        draw_liveview(img_4)

    def check_transfer_complete(self,disk):
        print("check the transfer")
        file_number=len(self.maxproject_list)
        disk_directory=os.path.join(disk, self.pos_path[3:]+"_maxprojection",self.cycle)
        name_pattern=".tif"
        matched_files_disk  =[1 for j in os.listdir(disk_directory) if name_pattern in j]
        if len(matched_files_disk)!=file_number:
            txt = get_time() + "D drive doesn't have all FOV"
            print(txt)
            update_error(txt)
            self.write_log(txt)
            check = 0
        else:
             #shutil.rmtree(os.path.join(self.pos_path, self.cycle), ignore_errors=True)
             check = 1
        return check

    def check_transfer_server(self,disk):
        disk_directory = os.path.join(disk, self.pos_path[3:] + "_maxprojection")
        file_list = []
        for root, dirs, files in os.walk(disk_directory):
            for file in files:
                file_list.append(os.path.join(root, file))
        file_number_disk=len(file_list)
        txt = get_time() + "local: " + str(file_number_disk)
        self.write_log(txt)
        server_path = '/mnt/imagestorage/' + self.pos_path[3:] + "_maxprojection"
        cmd ="ssh "+ self.linux_server+' "find '+ server_path+' -type f | wc -l"'
        self.write_log(cmd)
        output = subprocess.check_output(cmd, shell=True, text=True)
        file_count = int(output.strip())
        txt = get_time() +"server: "+ str(file_count)
        self.write_log(txt)
        print(file_number_disk)
        print(file_count)
        print(cmd)




    def pos_to_csv(self,cycle):
        if cycle=="imagecycle00":
            with open(os.path.join(self.pos_path, "cycle00.pos")) as f:
                d = json.load(f)
        else:
            with open(os.path.join(self.pos_path, cycle+".pos")) as f:
                d = json.load(f)
        if self.piezo==1:
            poslist = pd.DataFrame([get_pos_data(item,self.piezo) for item in d['map']['StagePositions']['array']])[
                ['position', 'x', 'y', 'z',
                 'piezo']]
        else:
            poslist = pd.DataFrame([get_pos_data(item,self.piezo) for item in d['map']['StagePositions']['array']])[
                ['position', 'x', 'y', 'z']]
        if cycle == "imagecycle00":
            poslist.to_csv(os.path.join(self.pos_path, "cycle00.csv"), index=False)
        else:
            poslist.to_csv(os.path.join(self.pos_path, cycle+".csv"), index=False)
        return poslist

