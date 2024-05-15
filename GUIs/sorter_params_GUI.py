# -*- coding: utf-8 -*-
"""
Created on Mon May 13 14:38:07 2024

@author: _LMT
"""
import PySimpleGUI as sg
import spikeinterface.sorters.sorterlist as sorterlist
import math 
import copy

def configure_sorter_param(sorter_name, sorter_param_description, sorter_values):
    layout = []
    
    for current_param_name, current_param_value in sorter_values.items():
        
        if current_param_name in sorter_param_description:
            tooltip = sorter_param_description[current_param_name]
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
    
    layout = [[sg.Frame(layout=layout,title=f'{sorter_name} parmeters', relief=sg.RELIEF_SUNKEN)],
              [sg.B('Save', k='save_param'), sg.B('Reset', k='reset_param')]]
    return sg.Window('Sorter parameters', layout, finalize=True)


def convert_str_to_param(str_value):
        if str_value == 'None' or '':
            param_value = None
        elif str_value == 'True':
            param_value = True
        elif str_value == 'False':
            param_value = False
        else:
            param_value = str_value
            try:
                if '.' in param_value or ',' in param_value:
                    param_to_convert = param_value.replace(',', '.')
                    param_value = float(param_to_convert)
                else:
                    param_value = int(param_value)
            except ValueError:
                pass
        
        return param_value

def save_sorting_param(sorting_param, window):
    
    for current_param_name in sorting_param.keys():
        
        if isinstance(sorting_param[current_param_name], tuple) or isinstance(sorting_param[current_param_name], list):
            for indx in range(len(sorting_param[current_param_name])):
                param_value = convert_str_to_param(window[(indx, current_param_name)].get())
                
                if isinstance(sorting_param[current_param_name], tuple):
                    sorting_param[current_param_name] = list(sorting_param[current_param_name])
                    sorting_param[current_param_name][indx] = param_value
                    sorting_param[current_param_name] = tuple(sorting_param[current_param_name])
                else:
                    sorting_param[current_param_name][indx] = param_value
        else:
            param_value = convert_str_to_param(window[current_param_name].get())
            sorting_param[current_param_name] = param_value 
            
    return sorting_param
    
def make_sorter_param_dict(sorter_name=None):
    
    if sorter_name is not None:
        sorter_param_dict = {'param': sorterlist.get_default_sorter_params(sorter_name),
                             'param_description': sorterlist.get_sorter_params_description(sorter_name)}
    else:
        sorter_param_dict =  {}
        sorter_list = sorterlist.available_sorters()
        for current_sorter_name in sorter_list:
            sorter_param_dict[current_sorter_name] = {'param': sorterlist.get_default_sorter_params(current_sorter_name),
                                                      'param_description': sorterlist.get_sorter_params_description(current_sorter_name)}

    return sorter_param_dict

def sorting_param_event_handler(window, values, event, current_sorter_param, state):
    
    if event == sg.WIN_CLOSED:
        sorting_param = save_sorting_param(copy.deepcopy(current_sorter_param[0]['sorting_param']), window)
        if sorting_param != current_sorter_param[0]['sorting_param']:
            if state[0] is not None:
                sg.popup_error('You can not change parameters while a analysis is in progress')
            else:
                save_changes_answer = sg.popup_yes_no('Save changes?')
                if save_changes_answer == 'Yes':
                    current_sorter_param[0]['sorting_param'] = sorting_param
                window.close()
        else:
            window.close()
    
    if event == 'save_param':
        if state[0] is not None:
            sg.popup_error('You can not change parameters while a analysis is in progress')
        else:
            save_sorting_param(current_sorter_param[0]['sorting_param'], window)
            window.close()
                
    if event == 'reset_param':
        default_param = make_sorter_param_dict(sorter_name=current_sorter_param[0]['name'])
        for current_param_name, current_param_value in default_param['param'].items():
            if isinstance(current_param_value, list) or isinstance(current_param_value, tuple):
                for indx, current_param_item in enumerate(current_param_value):
                    window[(indx, current_param_name)].update(current_param_value[indx])
            else:
                window[current_param_name].update(str(current_param_value))
