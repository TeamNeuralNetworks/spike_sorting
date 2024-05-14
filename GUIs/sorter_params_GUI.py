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
                           sg.Combo(values=('True', 'False'), default_value=str(current_param_value), k=current_param_name, tooltip=tooltip, size=(len_input,2))])
        elif current_param_value is None:
            layout.append([sg.T(current_param_name, tooltip=tooltip), 
                           sg.Input('None', k=current_param_name, tooltip=tooltip, size=(len_input,2))])
        elif isinstance(current_param_value, list) or isinstance(current_param_value, tuple):
            current_row = [sg.T(current_param_name, tooltip=tooltip)]
            for indx, current_param_item in enumerate(current_param_value):
                current_row.append(sg.Input(current_param_item, size=(len_input,2), k=(indx, current_param_name), tooltip=tooltip))
            layout.append(current_row)
        else:
            layout.append([sg.T(current_param_name, tooltip=tooltip), 
                           sg.Input(current_param_value, size=(len_input,2), k=current_param_name, tooltip=tooltip)])
    
    layout = [[sg.B('Save', k='save_param'), sg.B('Reset', k='reset_param')]
                [sg.Frame(layout=layout,title=f'{sorter_name} parmeters', relief=sg.RELIEF_SUNKEN)]]
    return sg.Window('Sorter parameters', layout, finalize=True)


def save_sorting_param():
    sorting_param = {}
    for current_param_name in current_sorter_param[0]['sorting_param'].keys():
    
        if values[current_param_name] == 'None' or '':
            param_value = None
        elif values[current_param_name] == 'True':
            param_value = True
        elif values[current_param_name] == 'False':
            param_value = False
        else:
            param_value = values[current_param_name]
        
        if isinstance(current_param_name, tuple):
            try:
                if '.' or ',' in values[current_param_name]:
                    param_to_convert = values[current_param_name].replace(',', '.')
                    param_value = float(param_to_convert)
                else:
                    param_value = int(values[current_param_name])
            except ValueError:
                pass
                
            current_sorter_param[0]['sorting_param'][current_param_name[1]] = list(current_sorter_param[0]['sorting_param'][current_param_name[1]])
            current_sorter_param[0]['sorting_param'][current_param_name[1]][current_param_name[0]] = param_value
            current_sorter_param[0]['sorting_param'][current_param_name[1]] = tuple(current_sorter_param[0]['sorting_param'][current_param_name[1]])
        else:
            try:
                if '.' or ',' in values[current_param_name]:
                    param_to_convert = values[current_param_name].replace(',', '.')
                    param_value = float(param_to_convert)
                else:
                    param_value = int(values[current_param_name])
            except ValueError:
                pass
            
            current_sorter_param[0]['sorting_param'][current_param_name] = param_value

def make_sorter_param_dict(sorter_name=None):
    sorter_param_dict =  {}
    sorter_list = sorterlist.available_sorters()
    for current_sorter_name in sorter_list:
        if sorter_name is not None and current_sorter_name != sorter_name:
            continue
        sorter_param_dict[sorter_name] = {'param': sorterlist.get_default_sorter_params(sorter_name),
                                          'param_description': sorterlist.get_sorter_params_description(sorter_name)}

    return sorter_param_dict

def sorting_param_event_handler(window, values, event, current_sorter_param):
    
    if event == sg.WIN_CLOSED:
        current_param = save_custom_cleaning_parameters(window)
        if current_param != current_sorter_param[0]['sorting_param']:
            save_changes_answer = sg.popup_yes_no('Save changes?')
            if save_changes_answer:
                current_sorter_param[0]['custom_cleaning_param'] = current_param
            else:
                window.close()
        else:
            window.close()
    
    if event == 'save_param':
       
                
    if event == 'reset_param':
        default_param = make_sorter_param_dict(sorter_name=current_sorter_param[0]['name'])
        for current_param_name, current_param_value in default_param.items():
            if isinstance(current_param_value, bool):
                window[current_param_name].update(current_param_value)
            elif current_param_value is None:
                window[current_param_name].update(str(current_param_value))
            elif isinstance(current_param_value, list) or isinstance(current_param_value, tuple):
                for indx, current_param_item in enumerate(current_param_value):
                    window[(indx, current_param_name)].update(current_param_value)
