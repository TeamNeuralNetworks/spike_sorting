# -*- coding: utf-8 -*-
"""
Created on Wed May 15 09:42:55 2024

@author: _LMT
"""
import os
import json

def get_default_param():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    with open(fr'{script_dir}/default_param.json', 'r') as file:
         default_param = json.load(file)
    return default_param

def load_or_compute_extension(analyzer, extension_list, save_extention=False):
    if not isinstance(extension_list, list) or isinstance(extension_list, tuple):
        extension_list = [extension_list]
        
    for extension_name in extension_list:
        extension_statues = analyzer.get_extension(extension_name)
        if extension_statues is None:
            analyzer.compute([extension_name], save=save_extention)