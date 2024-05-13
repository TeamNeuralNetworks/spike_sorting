# -*- coding: utf-8 -*-
"""
Created on Mon May 13 14:35:57 2024

@author: _LMT
"""
import PySimpleGUI as sg
import math

custom_cleaning_param_dict = {'remove_edge_artefact': True,
                                'remove_edge_artefact_param_dict': {'len to remove': {'tooltip': 'In ms, all spike at the begining and end of the recoding that are in this window are removed',
                                                                                      'value': 7},
                                                                    'trial len': {'tooltip': 'In s, if not set to None, will assume that all trial have separate recoding on wich edge artifeact need to be removed',
                                                                                  'value': None},
                                                                    'load custom excel': {'tooltip': 'In s, if not set to None, will assume that all trial have separate recoding on wich edge artifeact need to be removed',
                                                                                          'value': None},
                                                                    },
                                'remove_big_artefact': True,
                                'remove_big_artefact_param_dict': {},
                                'remove_noise_by_splitting': True,
                                'remove_noise_by_splitting_param_dict': {},
                                'additional_param_dict' : {'rename_units': True,
                                                           'plot_cleaning_summary': True,
                                                           },
                                }

def make_parameters_categori_layout():
    layout = []
    
    for main_parameters_name, main_parameters_dict in custom_cleaning_param_dict.items():
        current_parameters_frame_layout = []
        for current_param_name, parameters_dict in main_parameters_dict.items():
            tooltip = parameters_dict['tooltip']
            current_param_value = parameters_dict['value']
            
            if len(str(current_param_value)) > 7:
                len_input = math.ceil(len(str(current_param_value))*0.75)
            else:
                len_input = 7
            
            if isinstance(current_param_value, bool):
                current_parameters_frame_layout.append([sg.T(current_param_name, tooltip=tooltip), 
                               sg.Combo(values=('True', 'False'), default_value=str(current_param_value), k=current_param_name, tooltip=tooltip, size=(len_input,2), enable_events=True)])
            elif current_param_value is None:
                current_parameters_frame_layout.append([sg.T(current_param_name, tooltip=tooltip), 
                               sg.Input('None', k=current_param_name, tooltip=tooltip, size=(len_input,2), enable_events=True)])
            elif isinstance(current_param_value, list) or isinstance(current_param_value, tuple):
                current_row = [sg.T(current_param_name, tooltip=tooltip)]
                for indx, current_param_item in enumerate(current_param_value):
                    current_row.append(sg.Input(current_param_item, size=(len_input,2), k=(indx, current_param_name), tooltip=tooltip, enable_events=True))
                current_parameters_frame_layout.append(current_row)
            else:
                current_parameters_frame_layout.append([sg.T(current_param_name, tooltip=tooltip), 
                                                        sg.Input(current_param_value, size=(len_input,2), k=current_param_name, tooltip=tooltip, enable_events=True)])
        
        
        layout.append(sg.Frame('main_parameters_name', current_parameters_frame_layout))   
            
        return layout
    
def make_config_custom_cleaning_param_window():
    
    layout = make_parameters_categori_layout()
            
    
    layout.append([sg.B('Save', k='save_custom_cleaning_param_button'), sg.B('Reset', k='reset_custom_cleaning_param_button')])
    return sg.Window('Custom cleaning parameters', layout, finalize=True)

def custom_cleaning_event_handler(window, values, event):
    pass