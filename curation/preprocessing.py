# -*- coding: utf-8 -*-
"""
Created on Thu May 16 17:22:25 2024

@author: _LMT
"""
from spikeinterface.preprocessing import bandpass_filter, common_reference

def apply_preprocessing(recording, preprocessing_param, window):
    
    if preprocessing_param['bandpass']['activate']:
        print('applying bandpass')
        recording = bandpass_filter(recording, freq_min=int(preprocessing_param['bandpass']['low_freq']), freq_max=int(preprocessing_param['bandpass']['high_freq']))
        window[0]['progress_text'].update('')
    
    #############################################
    if preprocessing_param['comon_ref']['activate']:
        print('Removing comon ref')
        window[0]['progress_text'].update('Removing comon ref')
        recording = common_reference(recording, reference='global', operator='median')
        window[0]['progress_text'].update('')
        
    recording.annotate(is_filtered=True)
        
    return recording