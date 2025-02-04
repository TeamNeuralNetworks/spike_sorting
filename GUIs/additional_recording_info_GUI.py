# -*- coding: utf-8 -*-
"""
Created on Thu May 23 10:59:34 2024

@author: Pierre.LE-CABEC
"""


import PySimpleGUI as sg

from additional.toolbox import availabled_extention


class additional_recording_info_GUI:
    
    def __init__(self):
        
        self.window = None

    def create_window(self, default_input_size=(5,2), multi_recording_loading=False):
    
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
        
        self.window = sg.Window('Additional recording info needed', layout, finalize=True)


    def save_parameters(self, current_load_ephy_param):
        
        for window_key in self.window.AllKeysDict:
            if not isinstance(window_key, tuple):
                continue
            else:
                    
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
                
                if current_load_ephy_param[window_key[1]] is not None:
                    current_load_ephy_param[window_key[1]] = f'{current_load_ephy_param[window_key[1]]}_{current_param_value}'
                else:
                    current_load_ephy_param[window_key[1]] = current_param_value
                
        return current_load_ephy_param
    
    def event_handler(self, values, event, base_instance):
        if event == sg.WIN_CLOSED:
            save_changes_answer = sg.popup_yes_no('Save changes?')
            if save_changes_answer == 'Yes':
                base_instance.pipeline_parameters['load_ephy'] = self.save_parameters(base_instance.pipeline_parameters['load_ephy'])
                if values['multi_recording_loading']:
                    base_instance.state = "load_multi_recording"
                else:
                    base_instance.state = "load_recording"
            else:
                base_instance.pipeline_parameters['load_ephy']['ephy_file_extension'] = None
                base_instance.pipeline_parameters['ephy_file_path'] = None
            self.window.close()
            self.window = None
    
        if event == 'save_ephy_param':
            base_instance.pipeline_parameters['load_ephy'] = self.save_parameters(base_instance.pipeline_parameters['load_ephy'])
            if values['multi_recording_loading']:
                base_instance.state = "load_multi_recording"
            else:
                base_instance.state = "load_recording"
            self.window.close()
            self.window = None
            
        if event == 'cancel_ephy_param':
            base_instance.pipeline_parameters['load_ephy']['ephy_file_extension'] = None
            base_instance.pipeline_parameters['load_ephy']['ephy_file_path'] = None
            self.window.close()
            self.window = None
