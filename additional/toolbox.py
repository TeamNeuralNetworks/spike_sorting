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
import numpy as np

from spikeinterface.extractors import read_intan
from spikeinterface.core import BinaryFolderRecording, BinaryRecordingExtractor, ZarrRecordingExtractor
import spikeinterface.sorters.sorterlist as sorterlist
from spikeinterface.core.job_tools import get_best_job_kwargs

ephy_extractor_dict = {'file': {
                                'Binary': {'function': lambda x:BinaryRecordingExtractor(**x), 'path_syntax': 'file_paths', 'args': ['sampling_frequency',
                                                                                                                                    'dtype',
                                                                                                                                    'num_channels',
                                                                                                                                    ]},
                                'Intan': {'function': lambda x:read_intan(**x, stream_id='0'), 'path_syntax': 'file_path', 'args': [], 'extension': 'rhd'},
                                },
                       'folder': {'Binary': {'function': lambda x:BinaryFolderRecording(**x), 'path_syntax': 'folder_path', 'args': []},                  
                                  'Zarr': {'function': lambda x:ZarrRecordingExtractor(**x), 'path_syntax': 'folder_path', 'args': []},
                                  }
                       }

ephy_extractor_dict['multi_file'] = ephy_extractor_dict['file']

availabled_dtype = {'float16': np.float16, 
                    'float32': np.float32, 
                    'float64': np.float64,                     
                    'int16': np.int16, 
                    'int32': np.int32,
                    'int64': np.int64,
                    'uint16': np.uint16, 
                    'uint32': np.uint32, 
                    'uint64': np.uint64, 
                    }
        
def count_decimals(num):
    num_str = str(num)
    if '.' in num_str:
        return len(num_str.split('.')[1])
    return 0  # No decimals if there's no dot

def get_availabled_extension_extractor_converter_dict(mode):
    extension_extractor_converter_dict = {}
    for extractor_name, extractor_dict in ephy_extractor_dict[mode].items():
        if 'extension' in extractor_dict.keys():
            extension_extractor_converter_dict[extractor_dict['extension']] = extractor_name
    return extension_extractor_converter_dict

def get_availabled_extractor(mode):
    return list(ephy_extractor_dict[mode].keys())
    
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

def load_or_compute_extension(analyzer, extension_list, extension_params=None):
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
            analyzer.compute(extention_to_be_computes, verbose=True, **get_best_job_kwargs())
        else:
            analyzer.compute(extention_to_be_computes, verbose=True, extension_params=extension_params, **get_best_job_kwargs())

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