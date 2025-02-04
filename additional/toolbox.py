# -*- coding: utf-8 -*-
"""
Created on Wed May 15 09:42:55 2024

@author: _LMT
"""
import os
import json
import math
import tkinter as tk
from PySimpleGUI import Graph
import time

from spikeinterface.extractors import read_intan
from spikeinterface.core import BinaryFolderRecording, BinaryRecordingExtractor, ZarrRecordingExtractor
import spikeinterface.sorters.sorterlist as sorterlist

ephy_extension_dict = {'rhd': lambda x:read_intan(x, stream_id='0'),
                           'intan': lambda x:read_intan(x, stream_id='0'),
                           'folder_binary': lambda x:BinaryFolderRecording(x),
                           'binary': lambda x:BinaryRecordingExtractor(x),
                           'zarr': lambda x:ZarrRecordingExtractor(x),
                           }

availabled_extention = ['intan', 'binary', 'zarr']


def led_loading_animation(window, base_instance):
    while base_instance.state is not None:
        if base_instance.state is not None and base_instance.state != 'launch':
            SetLED(window, f'led_{base_instance.state}', 'green')
        time.sleep(0.25)
        if base_instance.state is not None and base_instance.state != 'launch':
            SetLED(window, f'led_{base_instance.state}', 'red')
        time.sleep(0.25)
  
def LEDIndicator(key=None, radius=30):
    return Graph(canvas_size=(radius, radius),
             graph_bottom_left=(-radius, -radius),
             graph_top_right=(radius, radius),
             pad=(0, 0), key=key)

def SetLED(window, key, color):
    window[key].erase()
    window[key].draw_circle((0, 0), 12, fill_color=color, line_color=color)

def select_folder_file(mode='folder'):
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    if mode == 'folder':
        path = tk.filedialog.askdirectory()
    elif mode == 'file':
        path = tk.filedialog.askopenfilename()
    if mode == 'both':
        raise ValueError('not yet implemented')
        
    if path:
        return path
    else:
        return None
    
def get_default_param():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    with open(fr'{script_dir}/default_param.json', 'r') as file:
         default_param = json.load(file)
    return default_param

def load_or_compute_extension(analyzer, extension_list, save_extention=True, extension_params=None):
    if not isinstance(extension_list, list) or isinstance(extension_list, tuple):
        extension_list = [extension_list]
        
    extention_to_be_computes = []
    for extension_name in extension_list:
        extension_statues = analyzer.get_extension(extension_name)
        if extension_statues is None:
            extention_to_be_computes.append(extension_name)
            
    if extention_to_be_computes:
        
        if extension_params is not None:
            use_extension_params = False 
            for extention_name in extention_to_be_computes:
                if extention_name in extension_params.keys():
                    use_extension_params = True
                    break
            
        if extension_params is None or not use_extension_params:
            analyzer.compute(extention_to_be_computes, save=save_extention)
        else:
            analyzer.compute(extention_to_be_computes, save=save_extention, extension_params=extension_params)

def largest_power_of_ten(num):
    if num == 0:
        return 0  # No meaningful power of ten for zero
    exponent = math.floor(math.log10(num))
    return 10 ** exponent

def make_sorter_param_dict(sorter_name=None):
    
    if sorter_name is not None:
        sorter_param_dict = {'param': sorterlist.get_default_sorter_params(sorter_name),
                             'param_description': sorterlist.get_sorter_params_description(sorter_name)}
    else:
        sorter_param_dict =  {}
        sorter_list = sorterlist.available_sorters()
        for current_sorter_name in sorter_list:
            sorter_param_dict[current_sorter_name] = {'param': sorterlist.get_default_sorter_params(current_sorter_name),
                                                      'param_description': sorterlist.get_sorter_params_description(current_sorter_name)}

    return sorter_param_dict