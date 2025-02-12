# -*- coding: utf-8 -*-
"""
Created on Thu May 16 17:22:25 2024

@author: _LMT
"""
from spikeinterface.preprocessing import bandpass_filter, common_reference

def apply_preprocessing(recording, preprocessing_param, window):
    
    #TODO
    # spikeinterface.preprocessing.astype(recording, dtype=None, round: bool | None = None) Converts a recording to another dtype on the fly.
    # spikeinterface.preprocessing.blank_staturation(recording, abs_threshold=None, quantile_threshold=None, direction='upper', fill_value=None, num_chunks_per_segment=50, chunk_size=500, seed=0)  Find and remove parts of the signal with extereme values. Some arrays may produce these when amplifiers enter saturation, typically for short periods of time. To remove these artefacts, values below or above a threshold are set to the median signal value. The threshold is either be estimated automatically, using the lower and upper 0.1 signal percentile with the largest deviation from the median, or specificed. Use this function with caution, as it may clip uncontaminated signals. A warning is printed if the data range suggests no artefacts.
    # spikeinterface.preprocessing.correct_motion(recording, preset='dredge_fast', folder=None, output_motion=False, output_motion_info=False, overwrite=False, detect_kwargs={}, select_kwargs={}, localize_peaks_kwargs={}, estimate_motion_kwargs={}, interpolate_motion_kwargs={}, **job_kwargs) High-level function that estimates the motion and interpolates the recording
    # see https://spikeinterface.readthedocs.io/en/stable/api.html#api-preprocessing for more
    
    if preprocessing_param['bandpass']['activate']:
        print('applying bandpass')
        recording = bandpass_filter(recording, freq_min=int(preprocessing_param['bandpass']['low_freq']), freq_max=int(preprocessing_param['bandpass']['high_freq']))
    
    #############################################
    if preprocessing_param['comon_ref']['activate']:
        print('Removing comon ref')
        recording = common_reference(recording, reference='global', operator='median')
    
    if preprocessing_param['gain_to_uV']['activate']:
        print('Setting gain')
        recording.set_channel_gains(preprocessing_param['gain_to_uV']['value'])
    
    if preprocessing_param['offset_to_uV']['activate']:
        print('Setting offset')
        recording.set_channel_offsets(preprocessing_param['offset_to_uV']['value'])
    
    if preprocessing_param['astype']['activate']:
        print('Setting recording dtype')
        recording.set_channel_offsets(preprocessing_param['astype']['dtype'])
    
    #TODO add the script from coline to remove noise
        
    recording.annotate(is_filtered=True)
        
    return recording