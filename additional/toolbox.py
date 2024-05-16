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

def load_or_compute_extension(analyzer, extension_list, save_extention=False, extension_params=None):
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