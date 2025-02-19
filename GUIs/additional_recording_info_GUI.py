# -*- coding: utf-8 -*-
"""
Created on Thu May 23 10:59:34 2024

@author: Pierre.LE-CABEC
"""

import numpy as np
import PySimpleGUI as sg

from additional.toolbox import get_availabled_extractor, ephy_extractor_dict, availabled_dtype


class additional_recording_info_GUI:
    
    def __init__(self):
        
        self.window = None
        self.mode = None
        self.path = None
        self.extractor = None
        
    def get_extractor_args_element(self, default_input_size=(5,2)):
        
        
        all_available_args_element_dict = {
            'gain_to_uV': lambda x: [sg.T('Gain to µV', tooltip='In what unit the recording is set to (if µV set to 1)'), sg.I('1', k=(x,'gain_to_uV'), tooltip='In what unit the recording is set to (if µV set to 1)', size=default_input_size)],
            'offset_to_uV': lambda x: [sg.T('Channel offset', tooltip='How much (in µV) does the signal is offset to 0'), sg.I('0', k=(x,'offset_to_uV'), tooltip='How much (in µV) does the signal is offset to 0', size=default_input_size)],
            'sampling_frequency': lambda x: [sg.T('Sampling frequency'), sg.I('20000', k=(x,'sampling_frequency'), size=default_input_size), sg.T('Hz')],
            'dtype': lambda x: [sg.T('dtype'), sg.Combo(list(availabled_dtype.keys()), default_value=list(availabled_dtype.keys())[0], k=(x, 'dtype'))],
            'num_channels': lambda x: [sg.T('Number of channels'), sg.I('16', k=(x,'num_channels'), size=default_input_size)],
            }
        
        extractor_args_element_list = []
        for extractor_name in get_availabled_extractor(mode=self.mode):
            current_colum_layout = []
            for args in ephy_extractor_dict[self.mode][extractor_name]['args']:
                current_colum_layout.append(all_available_args_element_dict[args](extractor_name))
            
            visible = True if extractor_name == self.extractor else False
            extractor_args_element_list.append([sg.pin(sg.Column(current_colum_layout, key=f'{extractor_name}_param_container', visible=visible))])
        
        return extractor_args_element_list
    
    def create_window(self, mode, multi_recording_loading=False):
        self.mode = mode
        available_extractor = get_availabled_extractor(mode=self.mode)
        self.extractor = available_extractor[0]
        
        additional_recording_info_layout = self.get_extractor_args_element()
        additional_recording_info_layout.insert(0, [sg.T('Recording format'), 
         sg.Combo(available_extractor, default_value=self.extractor, k='extractor', enable_events=True)])
        
        layout = [
            [sg.Frame('Additional recording info needed', additional_recording_info_layout, tooltip='Additional information about the recording is needed to properly load the recording')],
            [sg.B('Save', k='save_ephy_param'), sg.B('Cancel', k='cancel_ephy_param')],
            [sg.Checkbox('', k='multi_recording_loading', default=multi_recording_loading, visible=False)]
            ]
        
        self.window = sg.Window('Additional recording info needed', layout, finalize=True, modal=True)


    def save_parameters(self):
        
        new_load_ephy_param = {}
        for window_key in self.window.AllKeysDict:
            if not isinstance(window_key, tuple):
                continue
            else:
                if window_key[0] == self.extractor:
                    current_param_value = self.window[window_key].get()
                    
                    if current_param_value == 'None' or current_param_value == '':
                        current_param_value = None
                    elif current_param_value == 'True':
                        current_param_value = True
                    elif current_param_value == 'False':
                        current_param_value = False
                    
                    if window_key[1] == 'dtype':
                        current_param_value = availabled_dtype[current_param_value]
                    else:
                        if not isinstance(current_param_value, bool) and current_param_value is not None:
                            try:
                                if isinstance(current_param_value, type):
                                    current_param_value = current_param_value
                                elif '.' in current_param_value or ',' in current_param_value:
                                    param_to_convert = current_param_value.replace(',', '.')
                                    current_param_value = float(param_to_convert)
                                else:
                                    current_param_value = int(current_param_value)
                            except ValueError:
                                pass
                    
                    new_load_ephy_param[window_key[1]] = current_param_value
                    
        return new_load_ephy_param
    
    def event_handler(self, values, event, base_instance):
        if event == sg.WIN_CLOSED:
            save_changes_answer = sg.popup_yes_no('Save changes?')
            if save_changes_answer == 'Yes':
                base_instance.pipeline_parameters['load_ephy']['extractor_parameters'] = self.save_parameters()
                base_instance.pipeline_parameters['load_ephy']['extractor'] = self.extractor
                if values['multi_recording_loading']:
                    base_instance.state = "load_multi_recording"
                else:
                    base_instance.state = "load_recording"
                    path_syntax = ephy_extractor_dict[base_instance.pipeline_parameters['load_ephy']['mode']][base_instance.pipeline_parameters['load_ephy']['extractor']]['path_syntax']
                    base_instance.pipeline_parameters['load_ephy']['extractor_parameters'][path_syntax] = self.path
            else:
                base_instance.pipeline_parameters['load_ephy']['extractor'] = None
                path_syntax = ephy_extractor_dict[base_instance.pipeline_parameters['load_ephy']['mode']][base_instance.pipeline_parameters['load_ephy']['extractor']]['path_syntax']
                base_instance.pipeline_parameters['load_ephy']['extractor_parameters'][path_syntax] = None

            self.window.close()
            self.window = None
    
        if event == 'save_ephy_param':
            base_instance.pipeline_parameters['load_ephy']['extractor_parameters'] = self.save_parameters()
            base_instance.pipeline_parameters['load_ephy']['extractor'] = self.extractor
            if values['multi_recording_loading']:
                base_instance.state = "load_multi_recording"
            else:
                base_instance.state = "load_recording"
                path_syntax = ephy_extractor_dict[base_instance.pipeline_parameters['load_ephy']['mode']][base_instance.pipeline_parameters['load_ephy']['extractor']]['path_syntax']
                base_instance.pipeline_parameters['load_ephy']['extractor_parameters'][path_syntax] = self.path
            self.window.close()
            self.window = None
            
        elif event == 'cancel_ephy_param':
            self.window.close()
            self.window = None
        
        elif event == 'extractor':
            self.extractor = values['extractor']
            for extractor_name in get_availabled_extractor(mode=self.mode):
                visible = True if extractor_name == self.extractor else False
                self.window[f'{extractor_name}_param_container'].update(visible=visible)

