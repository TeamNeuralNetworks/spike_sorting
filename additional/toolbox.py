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