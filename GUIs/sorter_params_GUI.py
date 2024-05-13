# -*- coding: utf-8 -*-
"""
Created on Mon May 13 14:38:07 2024

@author: _LMT
"""
import PySimpleGUI as sg
import spikeinterface.sorters.sorterlist as sorterlist
import math 

def configure_sorter_param(sorter_name, sorter_param_dict):
    layout = []
    
    for current_param_name, current_param_value in sorter_param_dict[sorter_name]['param'].items():
        
        if current_param_name in sorter_param_dict[sorter_name]['param_description']:
            tooltip = sorter_param_dict[sorter_name]['param_description'][current_param_name]
        else:
            tooltip = None
        
        if len(str(current_param_value)) > 7:
            len_input = math.ceil(len(str(current_param_value))*0.75)
        else:
            len_input = 7
        
        if isinstance(current_param_value, bool):
            layout.append([sg.T(current_param_name, tooltip=tooltip), 
                           sg.Combo(values=('True', 'False'), default_value=str(current_param_value), k=current_param_name, tooltip=tooltip, size=(len_input,2), enable_events=True)])
        elif current_param_value is None:
            layout.append([sg.T(current_param_name, tooltip=tooltip), 
                           sg.Input('None', k=current_param_name, tooltip=tooltip, size=(len_input,2), enable_events=True)])
        elif isinstance(current_param_value, list) or isinstance(current_param_value, tuple):
            current_row = [sg.T(current_param_name, tooltip=tooltip)]
            for indx, current_param_item in enumerate(current_param_value):
                current_row.append(sg.Input(current_param_item, size=(len_input,2), k=(indx, current_param_name), tooltip=tooltip, enable_events=True))
            layout.append(current_row)
        else:
            layout.append([sg.T(current_param_name, tooltip=tooltip), 
                           sg.Input(current_param_value, size=(len_input,2), k=current_param_name, tooltip=tooltip, enable_events=True)])
    
    layout = [[sg.Frame(layout=layout,title=f'{sorter_name} parmeters', relief=sg.RELIEF_SUNKEN)]]
    return sg.Window('Sorter parameters', layout, finalize=True)


def make_sorter_param_dict():
    sorter_param_dict =  {}
    sorter_list = sorterlist.available_sorters()
    for sorter_name in sorter_list:
        sorter_param_dict[sorter_name] = {'param': sorterlist.get_default_sorter_params(sorter_name),
                                          'param_description': sorterlist.get_sorter_params_description(sorter_name)}

    return sorter_param_dict

def sorting_param_event_handler(window, values, event, current_sorter_param):
    
    print(event, values[event], type(values[event]))
    try:
        if values[event] == 'None' or '':
            param_value = None
        elif values[event] == 'True':
            param_value = True
        elif values[event] == 'False':
            param_value = False
        else:
            param_value = values[event]
        
        if isinstance(event, tuple):
            try:
                if '.' or ',' in values[event]:
                    param_to_convert = values[event].replace(',', '.')
                    param_value = float(param_to_convert)
                else:
                    param_value = int(values[event])
            except ValueError:
                pass
                
            current_sorter_param[0]['sorting_param'][event[1]] = list(current_sorter_param[0]['sorting_param'][event[1]])
            current_sorter_param[0]['sorting_param'][event[1]][event[0]] = param_value
            current_sorter_param[0]['sorting_param'][event[1]] = tuple(current_sorter_param[0]['sorting_param'][event[1]])
        else:
            try:
                if '.' or ',' in values[event]:
                    param_to_convert = values[event].replace(',', '.')
                    param_value = float(param_to_convert)
                else:
                    param_value = int(values[event])
            except ValueError:
                pass
            
            current_sorter_param[0]['sorting_param'][event] = param_value
        print(param_value, type(param_value))
    except:
        print(current_sorter_param[0]['sorting_param'])