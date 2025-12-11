"""
Author: Aixin Zhang
Description: Seq_o_matic device MUX distributor

"""

from front_end.logwindow import *
import serial
import json
import math
import time
class ElveflowMux():
    def __init__(self, config):
            self.config = config
            with open(os.path.join("config_file", "Selector_Reagent_Components.json"), 'r') as r:
                  self.source_list= json.load(r)
            self.selector_reagent = [i['solution'] for i in self.source_list]
            self.address = [i['address'] for i in self.source_list]
            self.selector_fluidics_dict = dict(zip(self.selector_reagent, self.address))
            self.unit_port=11
            self.pass_though_port=12

            self.source_limit=self.unit_port*(math.ceil(len(self.source_list)/self.unit_port))
    def connect(self):
       self.selector1= serial.Serial(port = self.config[0]['port'],
                baudrate = 9600,
                parity= serial.PARITY_NONE,
                bytesize=serial.EIGHTBITS,
                stopbits=serial.STOPBITS_ONE)
    def disconnect(self):
        self.selector1.close()
    


    def set_path(self, reagent):
        selector_port = self.selector_fluidics_dict[reagent]
        print(f"selector port is {str(selector_port)}")
        self.move(self.selector1, selector_port)
        print(f"move the first one {str(selector_port)}")
        time.sleep(3)

    def config_selector(self):
        self.connect()
        self.set_path("gene oligos")
        self.set_path("Incorporation Buffer")
        self.disconnect()


    def move(self,device,position):
         valve_address=1 #default
         command = f"/{valve_address}B{position}R\r"
         print(command)
         device.write(command.encode())