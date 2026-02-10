###############################################################################
#
#                       OLD UNREFACTORED CODE
#
###############################################################################


class ZZZOldCode:
    # was WindowWidgets.py
    def __init__(self, mainwindow, tkapp, path):
        pass

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
        self.server = self.controller.account_field.get() + "@" + self.server_field_manual.get()
        if self.controller.work_path_field.get() == "":
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
        
        with open(os.path.join( get_resource_dir() , "tissue_scanner", "slide1_chamber_coor.pos")) as f:
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
    def __init__(self, window, stitched_image, stitched_image_rt, path, width, tilesdf, z):
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
