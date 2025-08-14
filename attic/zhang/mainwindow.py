#!/usr/bin/env python 

"""
Author: Aixin Zhang
Description: Mainwindow widgets Layouts and GUI entrance

"""
import os
import sys

#this_file = os.path.abspath(__file__)
#(base, exe) = os.path.split(this_file)
#(libdir, script_dir) = os.path.split(base)
#gitpath=os.path.expanduser(libdir)
#sys.path.append(gitpath)

from front_end.Widgets import *
from front_end.logwindow import *

mainwindow = Log_window.mainwindow
my_widgets = window_widgets( mainwindow=mainwindow, path=os.getcwd())

##automation tab area
my_widgets.work_path_lb_auto.grid(row=3, column=0, padx=15,sticky="w")
my_widgets.work_path_field_auto.grid(row=3, column=3, padx=15, sticky="w")
my_widgets.browse_btn_auto.grid(row=3, column=4, padx=15, sticky="w")
my_widgets.exp_btn_auto.grid(row=3, column=7, padx=15, sticky="w")

my_widgets.slice_per_slide_lb_auto.grid(row=0, column=0, padx=5,sticky="w")
my_widgets.slice_number_field_auto.grid(row=0, column=1, padx=1,sticky="w")
my_widgets.slice_per_slide_lb_manual.grid(row=0, column=0, padx=5,sticky="w")
my_widgets.slice_number_field_manual.grid(row=0, column=1, padx=1,sticky="w")

my_widgets.mock_alignment_cbox.grid(row=0, column=2, padx=5, sticky="w")
my_widgets.mock_alignment_cbox_manual.grid(row=0, column=2, padx=5, sticky="w")
my_widgets.current_cycle_lb.grid(row=0, column=3, padx=5, sticky="w")
my_widgets.current_cbox.grid(row=0, column=4, padx=5, sticky="w")
my_widgets.sb1_cycle_number.grid(row=0, column=5, padx=5, sticky="w")

my_widgets.build_own_cycle_sequence.grid(row=0, column=3, padx=5, sticky="w")
my_widgets.OR_lb.grid(row=0, column=4, padx=5, sticky="w")
my_widgets.recipe_btn.grid(row=0, column=5, padx=5, sticky="w")
my_widgets.assign_heater_btn.grid(row=0, column=6, padx=5, sticky="w")


my_widgets.change_pixel_auto.grid(row=1, column=0, padx=5, sticky="w")
my_widgets.change_pixel_manual.grid(row=1, column=0, padx=5, sticky="w")
my_widgets.pixel_size_field_auto.grid(row=1, column=1, padx=5, sticky="w")
my_widgets.pixel_size_field_manual.grid(row=1, column=1, padx=5, sticky="w")
my_widgets.change_server_auto_cb.grid(row=1, column=2, padx=5, sticky="w")
my_widgets.change_server_manual_cb.grid(row=1, column=2, padx=5, sticky="w")
my_widgets.server_account_lb_auto.grid(row=1, column=3, padx=5, sticky="w")
my_widgets.account_field_auto.grid(row=1, column=4, padx=5, sticky="w")
my_widgets.server_lb_auto.grid(row=1, column=5, padx=5, sticky="w")
my_widgets.server_field_auto.grid(row=1, column=6, padx=5, sticky="w")
my_widgets.server_account_lb_manual.grid(row=1, column=3, padx=5, sticky="w")
my_widgets.account_field_manual.grid(row=1, column=4, padx=5, sticky="w")
my_widgets.server_lb_manual.grid(row=1, column=5, padx=5, sticky="w")
my_widgets.server_field_manual.grid(row=1, column=6, padx=5, sticky="w")



my_widgets.upload_aws_auto.grid(row=0, column=0, padx=5, sticky="w")
my_widgets.aws_account_lb_auto.grid(row=0, column=1, padx=5, sticky="w")
my_widgets.aws_account_field_auto.grid(row=0, column=2, padx=5,sticky="w")
my_widgets.aws_password_lb_auto.grid(row=0, column=3, padx=5, sticky="w")
my_widgets.aws_pwd_field_auto.grid(row=0, column=4, padx=5, sticky="w")

my_widgets.upload_aws_manual.grid(row=0, column=0, padx=5, sticky="w")
my_widgets.aws_account_lb_manual.grid(row=0, column=1, padx=5, sticky="w")
my_widgets.aws_account_field_manual.grid(row=0, column=2, padx=5,sticky="w")
my_widgets.aws_password_lb_manual.grid(row=0, column=3, padx=5, sticky="w")
my_widgets.aws_pwd_field_manual.grid(row=0, column=4, padx=5, sticky="w")

my_widgets.info_btn_auto.grid(row=2, column=0, padx=10, pady=5)
my_widgets.info_btn_manual.grid(row=2, column=0, padx=10, pady=5)


my_widgets.device_btn.grid(row=0, column=0, padx=10,sticky="w")
my_widgets.brain_btn.grid(row=0, column=1, padx=10, sticky="w")
my_widgets.prime_btn.grid(row=0, column=2, padx=10,sticky="w")
my_widgets.fill_lb.grid(row=0, column=3, padx=10, sticky="w")
my_widgets.reagent_list_cbox.grid(row=0, column=4, padx=10, sticky="w")
my_widgets.reagent_amount.grid(row=0, column=5, padx=10, sticky="w")
my_widgets.inchamber_path_cbox.grid(row=0, column=6, padx=10,sticky="w")
my_widgets.fill_single_btn.grid(row=0, column=7, padx=10, sticky="w")

my_widgets.start_sequence_btn.grid(row=0, column=1, padx=10, sticky="w")
my_widgets.cancel_sequence_btn.grid(row=0, column=2, padx=10, sticky="w")
my_widgets.wash_btn.grid(row=0, column=3, padx=10, sticky="w")
my_widgets.avoid_wash_cbox.grid(row=0, column=4, padx=10, sticky="w")
my_widgets.check_sequence_btn.grid(row=0, column=0, padx=10, sticky="w")

my_widgets.canvas_focus.get_tk_widget().grid(row=1, column=0,padx=10,sticky="w")
my_widgets.canvas_align.get_tk_widget().grid(row=1, column=1,padx=10,sticky="w")
my_widgets.canvas_tile.get_tk_widget().grid(row=1, column=2,padx=10,sticky="w")

my_widgets.focus_lb.grid(row=0, column=0,padx=5,pady=3)
my_widgets.align_lb.grid(row=0, column=1,padx=5,pady=3)
my_widgets.tile_lb.grid(row=0, column=2,padx=5,pady=3)

my_widgets.note_lb.grid(row=0, column=0,padx=5,pady=3)
my_widgets.note_stw.grid(row=0, column=1,padx=5,pady=3)
my_widgets.note_btn.grid(row=0, column=2,padx=5,pady=3)
## manual tab area
my_widgets.work_path_lb_manual.grid(row=0, column=0, padx=10,sticky="w")
my_widgets.work_path_field_manual.grid(row=0, column=10, padx=10, sticky="w")

my_widgets.browse_btn_manual.grid(row=0, column=15, padx=10, sticky="w")
my_widgets.exp_btn_manual.grid(row=0, column=25, padx=10, sticky="w")

my_widgets.focus_btn.grid(row=0, column=0, padx=10, pady=10)
my_widgets.align_btn.grid(row=0, column=1, padx=10, pady=10)
my_widgets.tile_btn.grid(row=0, column=2, padx=10, pady=10)
my_widgets.max_btn.grid(row=0, column=3, padx=10, pady=10)
my_widgets.cancel_image_btn.grid(row=0, column=4, padx=10, pady=10)

if __name__ == '__main__':
    mainwindow.mainloop()
