
"""

Author: Aixin Zhang
Description: Seq_o_matic device: Syringe pump

"""

import serial
import numpy as np
from datetime import datetime
import os
import time
from pytz import timezone
import math
import json
def get_time():
    time_now = timezone('US/Pacific')
    time = str(datetime.now(time_now))[0:16] + "\n"
    return time


class Syringe_Pump():
    def __init__(self, config):
        self.config = config[0]
        self.com = self.config['port']
        self.dictionary = self.config['Dict']
        self.speed_dict = self.config['speed_code']
        self.syringe_vol = self.config['volume']
        self.buffer_time = 3
        self.syringe_pump_speed_default=26
        self.pump_address=1 ##default


    def connect_pump(self):
        self.pump = serial.Serial(
            port=self.com,
            baudrate=9600,
            bytesize=8,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=2
        )

    def disconnect_pump(self):
        self.pump.close()

    def check_pump_status(self):
        error_descriptions = {
                            0: "No Error",
                            1: "Initialization Error",
                            2: "Invalid Command", 
                            3: "Invalid Operand",
                            7: "Device Not Initialized",
                            8: "Invalid Valve Configuration",
                            9: "Plunger Overload",
                            10: "Valve Overload",
                            11: "Plunger Move Not Allowed",
                            12: "Extended Error Present",
                            13: "NVRAM Access Failure",
                            14: "Command Buffer Empty or Not Ready",
                            15: "Command Buffer Overflow"
                        }
        time.sleep(5)
        command = f"/1Q\r"
        ready_bit = 0

        
        max_retries=3
        check=0
        while True:
            if check==0:
                self.pump.write(command.encode())
                time.sleep(2)
                if self.pump.in_waiting > 0:
                    response = self.pump.read(self.pump.in_waiting)           
                    for byte in response:
                        if (byte & 0b11010000) == 0b01000000:
                            ready_bit = (byte >> 5) & 0x01
                    status_byte = response[2]
                    error_code = status_byte & 0x0F
                    if ready_bit == 1 and error_code == 0:
                            print("Pump is ready for operation")
                            return True
                    elif ready_bit == 0 and error_code == 0:
                            print("Pump is busy, waiting...")
                            continue  
                    else:
                        error_msg = error_descriptions.get(error_code, f"Unknown error: {error_code}")
                        print(f"ERROR: {error_msg}")
                        check=1
                        continue    
            else:
                continue
        
        #while ready_bit == 0:
        #    self.pump.write(command.encode())
        #    time.sleep(2)
        #    if self.pump.in_waiting > 0:
        #        response = self.pump.read(self.pump.in_waiting)
        #        for byte in response:
        #            if (byte & 0b11010000) == 0b01000000:
        #                ready_bit = (byte >> 5) & 0x01
        #                print(ready_bit)

    def config_pump(self):
        self.set_path("waste")
        time.sleep(2)
        command = '/1ZR\r'
        self.pump.write(command.encode())

    def set_speed(self, speed_code):
        command = '/1S' + str(speed_code) + 'R\r'
        self.pump.write(command.encode())

    def set_path(self, reagent):
        port = self.dictionary[reagent]
        print(f"move the pump port to {port}")
        command = '/1I' + str(port) + 'R\r'
        self.pump.write(command.encode())
        time.sleep(2)

    def fillSyringe(self, vol, speed_code):
        self.set_speed(speed_code)
        time.sleep(2)
        print(self.syringe_vol)
        print(vol)
        increments = str(int(math.ceil((vol / self.syringe_vol) * 181490))) #vol is in ul
        print(increments)
        command = '/1A' + increments + 'R\r'
        self.pump.write(command.encode())
        time.sleep(2)
        self.check_pump_status()
        return 

    def dispense_pump(self, vol, speed_code):
        self.set_speed(speed_code)
        time.sleep(2)
        print(self.syringe_vol)
        print(vol)
        increments = str(int(math.floor((vol / self.syringe_vol) * 181490)))
        print(increments)
        command = '/1D' + increments + 'R\r'
        self.pump.write(command.encode())
        time.sleep(2)
        self.check_pump_status()
        return 

    def stop_pump(self):
        command = '/1T\r'
        self.pump.write(command.encode())




    def calculate_time(self, vol, speed_code):
        increment_per_seconds = self.speed_dict[str(speed_code)]
        increments = int(math.ceil((vol / self.syringe_vol) * 181490))
        time_use = increments / increment_per_seconds
        return time_use


