# -*- coding: utf-8 -*-
"""
Created on Thu May 23 10:59:34 2024

@author: Pierre.LE-CABEC
"""
from spikeinterface.extractors import read_intan
from spikeinterface.core import BinaryFolderRecording, BinaryRecordingExtractor, ZarrRecordingExtractor

import PySimpleGUI as sg


ephy_extension_dict = {'rhd': lambda x:read_intan(x, stream_id='0'),
                       'intan': lambda x:read_intan(x, stream_id='0'),
                       'folder_binary': lambda x:BinaryFolderRecording(x),
                       'binary': lambda x:BinaryRecordingExtractor(x),
                       'zarr': lambda x:ZarrRecordingExtractor(x),
                       }

availabled_extention = ['intan', 'binary', 'zarr']

def make_additional_recording_info_window(default_input_size=(5,2), multi_recording_loading=False):
    
    additional_recording_info_layout = [
                                        [sg.T('Recording format'), 
                                         sg.Combo(availabled_extention, default_value=availabled_extention[0], k=('load_ephy', 'ephy_file_extension'))],
                                        [sg.T('Gain to µV', tooltip='In what unit the recording is set to (if µV set to 1)'), 
                                         sg.I('1', k=('load_ephy','gain_to_uV'), tooltip='In what unit the recording is set to (if µV set to 1)', size=default_input_size)],
                                        [sg.T('Channel offset', tooltip='How much (in µV) does the signal is offset to 0'), 
                                         sg.I('0', k=('load_ephy','offset_to_uV'), tooltip='How much (in µV) does the signal is offset to 0', size=default_input_size)],
                                        ]
    
    layout = [
        [sg.Frame('Additional recording info needed', additional_recording_info_layout, tooltip='Additional information about the recording is needed to properly load the recording')],
        [sg.B('Save', k='save_ephy_param'), sg.B('Cancel', k='cancel_ephy_param')],
        [sg.Checkbox('', k='multi_recording_loading', default=multi_recording_loading, visible=False)]
        ]
    
    return sg.Window('Additional recording info needed', layout, finalize=True)


def save_additional_recording_info_parameters(window, current_load_ephy_param):
    
    for window_key in window.AllKeysDict:
        if not isinstance(window_key, tuple):
            continue
        else:
                
            current_param_value = window[window_key].get()
            if current_param_value == 'None' or current_param_value == '':
                current_param_value = None
            elif current_param_value == 'True':
                current_param_value = True
            elif current_param_value == 'False':
                current_param_value = False
            
            if not isinstance(current_param_value, bool) and current_param_value is not None:
                try:
                    if '.' in current_param_value or ',' in current_param_value:
                        param_to_convert = current_param_value.replace(',', '.')
                        current_param_value = float(param_to_convert)
                    else:
                        current_param_value = int(current_param_value)
                except ValueError:
                    pass
            
            if current_load_ephy_param[window_key[1]] is not None:
                current_load_ephy_param[window_key[1]] = f'{current_load_ephy_param[window_key[1]]}_{current_param_value}'
            else:
                current_load_ephy_param[window_key[1]] = current_param_value
            
    return current_load_ephy_param

def additional_recording_info_event_handler(window, values, event, current_sorter_param, state):
    if event == sg.WIN_CLOSED:
        save_changes_answer = sg.popup_yes_no('Save changes?')
        if save_changes_answer == 'Yes':
            current_sorter_param[0]['load_ephy'] = save_additional_recording_info_parameters(window, current_sorter_param['load_ephy'])
            if values['multi_recording_loading']:
                state[0] = "load_multi_recording"
            else:
                state[0] = "load_recording"
        else:
            current_sorter_param[0]['load_ephy']['ephy_file_extension'] = None
            current_sorter_param[0]['ephy_file_path'] = None
        window.close()

    if event == 'save_ephy_param':
        current_sorter_param[0]['load_ephy'] = save_additional_recording_info_parameters(window, current_sorter_param[0]['load_ephy'])
        if values['multi_recording_loading']:
            state[0] = "load_multi_recording"
        else:
            state[0] = "load_recording"
        window.close()
        
    if event == 'cancel_ephy_param':
        current_sorter_param[0]['load_ephy']['ephy_file_extension'] = None
        current_sorter_param[0]['load_ephy']['ephy_file_path'] = None
        window.close()
