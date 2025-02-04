# -*- coding: utf-8 -*-
"""
Created on Thu May 16 16:52:38 2024

@author: _LMT
"""

import PySimpleGUI as sg
from additional.toolbox import get_default_param


class preprocessing_GUI:

    def __init__(self):
        
        self.window = None

    def make_config_preprocessing_param_window(self, preprocessing_param, default_input_size=(5,2)):
        
        bandpass_row = [sg.T('Bandpass', tooltip='Frequency at witch to aplly a bandpass filter on the recording'), 
                         sg.I(preprocessing_param['bandpass']['low_freq'], size=default_input_size, k=('bandpass', 'low_freq'), tooltip='Frequency at witch to aplly a bandpass filter on the recording'), 
                         sg.T("-"), sg.I(preprocessing_param['bandpass']['high_freq'], size=default_input_size, k=('bandpass', 'high_freq'), tooltip='Frequency at witch to aplly a bandpass filter on the recording'), 
                         sg.Checkbox('', default=preprocessing_param['bandpass']['activate'], k=('bandpass', 'activate'), tooltip='Frequency at witch to aplly a bandpass filter on the recording')]
        
        common_ref_row = [sg.T('Comon ref removal', tooltip='Remove the median signal comon to all electrodes to the signal'),
                          sg.Checkbox('', default=preprocessing_param['comon_ref']['activate'], k=('comon_ref', 'activate'), tooltip='Remove the median signal comon to all electrodes to the signal')],
        
        layout = [
                bandpass_row,
                common_ref_row,
                [sg.B('Save', k='save_preprocessing_param_button'), sg.B('Reset', k='reset_preprocessing_param_button')],
                ]
        
        self.window = sg.Window('Preprocessing parameters', layout, finalize=True)
    
    def save_parameters(self):
        
        preprocessing_dict = {}
        for window_key in self.window.AllKeysDict:
            if not isinstance(window_key, tuple):
                continue
            else:
                if window_key[0] not in preprocessing_dict.keys():
                    preprocessing_dict[window_key[0]] = {}
                    
                current_param_value = self.window[window_key].get()
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
                    
                preprocessing_dict[window_key[0]][window_key[1]] = current_param_value
                
        return preprocessing_dict
    
    def event_handler(self, values, event, base_instance):
        if event == sg.WIN_CLOSED:
            current_param = self.save_parameters()
            if current_param != base_instance.pipeline_parameters['preprocessing_param']:
                if base_instance.state is not None:
                    sg.popup_error('Parameters can not be saved while a analysis is in progress')
                else:
                    save_changes_answer = sg.popup_yes_no('Save changes?')
                    if save_changes_answer == 'Yes':
                        base_instance.pipeline_parameters['preprocessing_param'] = current_param
                    self.window.close()
                    self.window = None
            else:
                self.window.close()
                self.window = None
    
        if event == 'save_preprocessing_param_button':
            if base_instance.state is not None:
                sg.popup_error('Parameters can not while a analysis is in progress')
            else:
                base_instance.pipeline_parameters['preprocessing_param'] = self.save_parameters()
                self.window.close()
                self.window = None
            
        if event == 'reset_preprocessing_param_button':
            default_param = get_default_param()
            
            for main_param_name, main_param_dict in default_param['preprocessing_param'].items():
                for param_name, param_value in main_param_dict.items():
                    self.window[(main_param_name, param_name)].update(str(param_value))