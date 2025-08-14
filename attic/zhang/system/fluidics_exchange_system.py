"""
Author: Aixin Zhang
Description: Seq_o_Matics main system: Fluidics exchange system

"""

#from device.Syringe_pump import Syringe_Pump
#from device.Heatingstage import heat_stage_group
#from device.Selector_2025 import ElveflowMux

#import threading
#import json
#import time
#from front_end.logwindow import *
#from pytz import timezone
#from datetime import datetime
#import shutil
   

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


def get_time():
    time_now = timezone('US/Pacific')
    time = str(datetime.now(time_now))[0:19] + "\n"
    return time


class FluidicSystem():
    def __init__(self,system_path,pos_path,slide_hearter_dictionary):
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

        self.slide_heater_dict = slide_hearter_dictionary
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
        self.Heatingdevice=heat_stage_group(self.Heater_cfg,5.7,self.pos_path)
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


