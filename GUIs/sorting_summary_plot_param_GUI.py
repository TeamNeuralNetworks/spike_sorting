# -*- coding: utf-8 -*-
"""
Created on Thu May 16 16:52:38 2024

@author: _LMT
"""

import PySimpleGUI as sg
from additional.toolbox import get_default_param


class sorting_summary_plot_param_GUI:

    def __init__(self):
        
        self.window = None

    def create_window(self, summary_plot_param, recording=None, default_input_size=(5,2)):
        
        auto_save_row = [sg.T('Auto save plot after analysis', tooltip='A summery plot will be save after each analysis step of every units'), 
                         sg.Checkbox('', default=summary_plot_param['auto_save']['activate'], k=('auto_save', 'activate'), tooltip='A summery plot will be save after each analysis step of every units')]
        
        if summary_plot_param['trial_info']['lenght'] is not None:
            trial_len = summary_plot_param['trial_info']['lenght']
        elif recording is not None:
            trial_len = recording.get_duration()
        else:
            trial_len = None
            
        trial_info_row = [sg.T('Trial lenght', tooltip='Adjust '),
                          sg.I(trial_len, size=(8, 2), k=('trial_info', 'lenght'), tooltip='Display the mean frequency, zscored, ect... during trials'),
                          sg.T('s')],
                
        layout = [
                auto_save_row,
                trial_info_row,
                [sg.B('Save', k='save_button'), sg.B('Reset', k='reset_button')],
                ]
        
        if self.window is not None:
            location = self.window.current_location()
            self.window.close()
        else:
            location = None
            
        self.window = sg.Window('Summary plot parameters', layout, finalize=True, location=location)
    
    def save_parameters(self):
        
        summary_plot_param = {}
        for window_key in self.window.AllKeysDict:
            if not isinstance(window_key, tuple):
                continue
            else:
                if window_key[0] not in summary_plot_param.keys():
                    summary_plot_param[window_key[0]] = {}
                    
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
                    
                summary_plot_param[window_key[0]][window_key[1]] = current_param_value
                
        return summary_plot_param
    
    def event_handler(self, values, event, base_instance):
        if event == sg.WIN_CLOSED:
            current_param = self.save_parameters()
            if current_param != base_instance.pipeline_parameters['summary_plot_param']:
                
                save_changes_answer = sg.popup_yes_no('Save changes?')
                if save_changes_answer == 'Yes':
                    base_instance.pipeline_parameters['summary_plot_param'] = current_param
                self.window.close()
                self.window = None
            else:
                self.window.close()
                self.window = None
    
        if event == 'save_button':
            base_instance.pipeline_parameters['summary_plot_param'] = self.save_parameters()
            self.window.close()
            self.window = None
            
        if event == 'reset_button':
            default_param = get_default_param()
            
            for main_param_name, main_param_dict in default_param['summary_plot_param'].items():
                for param_name, param_value in main_param_dict.items():
                    self.window[(main_param_name, param_name)].update(str(param_value))