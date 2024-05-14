# -*- coding: utf-8 -*-
"""
Created on Mon May 13 14:35:57 2024

@author: _LMT
"""
import PySimpleGUI as sg
from curation.clean_unit import big_artefact_methods, dimensionality_reduction_method_list


default_custom_cleaning_parameters_dict = {'remove_edge_artefact': {'activate': True,
                                                            'lenght_to_remove': 7,
                                                            'trial_length': None},
                                   'remove_big_artefact': {'activate': True,
                                                           'method': big_artefact_methods[0],
                                                           'threshold': 15},
                                   'split_multi_unit': {'activate': True,
                                                        'method': dimensionality_reduction_method_list[0],
                                                        'threshold': 0.2,
                                                        'max_split': 10,
                                                        'min_spike_per_unit': 50},
                                   'rename_unit': {'activate': True},
                                   'plot_cleaning_summary': {'activate': True}
                                   }

def make_config_custom_cleaning_param_window(custom_cleaning_param, default_input_size=(5,2)):
    
    remove_edge_artefact_layout = [[sg.T('Activate', tooltip='If selected will remove spikes at the edge of the recording'), sg.Checkbox('', default=custom_cleaning_param['remove_edge_artefact']['activate'], k=('remove_edge_artefact', 'activate'), tooltip='If selected will remove spikes at the edge of the recording')],
                                   [sg.T('Lenght to remove', tooltip='In ms, all spike at the begining and end of the recoding that are in this window are removed'), sg.I(custom_cleaning_param['remove_edge_artefact']['lenght_to_remove'], size=default_input_size, k=('remove_edge_artefact', 'lenght_to_remove'), tooltip='In ms, all spike at the begining and end of the recoding that are in this window are removed'), sg.T('ms')],
                                   [sg.T('Trial lenght', tooltip='In s, will assume that all trial have separate recoding on wich edge artifeact need to be removed, set to None to ignore'), sg.I(str(custom_cleaning_param['remove_edge_artefact']['trial_length']), size=default_input_size, k=('remove_edge_artefact', 'trial_length'), tooltip='In s, will assume that all trial have separate recoding on wich edge artifeact need to be removed, set to None to ignore'), sg.T('s')],
                                   # [sg.B('load custom excel', k=('remove_edge_artefact', 'load_custom_excel_button'), tooltip='An excel file can be loaded with contain the index of the transition from one file to the other')], #TODO
                                   ]
    
    remove_big_artefact_layout = [[sg.T('Activate', tooltip='If selected will remove spikes wich amplitude is too high'), sg.Checkbox('', default=custom_cleaning_param['remove_big_artefact']['activate'], k=('remove_big_artefact', 'activate'), tooltip='If selected will remove spikes wich amplitude is too high')],
                                   [sg.T('Method', tooltip='Method used for the thresholding of spikes'), sg.Combo(big_artefact_methods, default_value=custom_cleaning_param['remove_big_artefact']['method'], k=('remove_big_artefact', 'method'), tooltip='Method used for the thresholding of spikes')],
                                   [sg.T('Threshold', tooltip='Threshold above wich the amplitud of the spike has to be to be removed (relative to other spike from the same unit)'), sg.I(custom_cleaning_param['remove_big_artefact']['threshold'], size=default_input_size, k=('remove_big_artefact', 'threshold'), tooltip='Threshold above wich the amplitud of the spike has to be to be removed (relative to other spike from the same unit)')],
                                   ]
    
    split_multi_unit_layout = [[sg.T('Activate', tooltip='If selected will split units containing 2 or more population of spikes waveform profil'), sg.Checkbox('', default=custom_cleaning_param['split_multi_unit']['activate'], k=('split_multi_unit', 'activate'), tooltip='If selected will split units containing 2 or more population of spikes waveform profil')],
                               [sg.T('Method', tooltip='Method used for reduction of dimention'), sg.Combo(dimensionality_reduction_method_list, default_value=custom_cleaning_param['split_multi_unit']['method'], k=('split_multi_unit', 'method'), tooltip='Method used for reduction of dimention')],
                               [sg.T('Silhouette threshold', tooltip='Threshold above wich the unit will be split'), sg.I(custom_cleaning_param['split_multi_unit']['threshold'], size=default_input_size, k=('split_multi_unit', 'threshold'), tooltip='Threshold above wich the unit will be split')],
                               [sg.T('Maximum number of split', tooltip='Maximum number of split per unit'), sg.I(custom_cleaning_param['split_multi_unit']['max_split'], size=default_input_size, k=('split_multi_unit', 'max_split'), tooltip='Maximum number of split per unit')],
                               [sg.T('Minimum spike per unit', tooltip='Minimum number of spikes per unit (if inferior the unit will be removed)'), sg.I(custom_cleaning_param['split_multi_unit']['min_spike_per_unit'], size=default_input_size, k=('split_multi_unit', 'min_spike_per_unit'), tooltip='Minimum number of spikes per unit (if inferior the unit will be removed)')],#TODO probably better to put that in addictional filter or something
                               ]
    
    additional_param_layout = [[sg.T('Rename units', tooltip='If selected will rename units (if 10 units remain at the end of the pipeline the units number will go from 0 to 10)'), sg.Checkbox('', default=custom_cleaning_param['rename_unit']['activate'], k=('rename_unit', 'activate'), tooltip='If selected will rename units (if 10 units remain at the end of the pipeline the units number will go from 0 to 10)')],
                               [sg.T('Plot cleaning summary', tooltip='If selected will plot a summary of the cleaning done for each remaining unit'), sg.Checkbox('', default=custom_cleaning_param['plot_cleaning_summary']['activate'], k=('plot_cleaning_summary', 'activate'), tooltip='If selected will plot a summary of the cleaning done for each remaining unit')],
                                ]
    
    layout = [
            [sg.Frame('Remove edge artefact', remove_edge_artefact_layout, tooltip='If activated, will remove spikes at the edge of the recording')],
            [sg.Frame('Remove big artefact', remove_big_artefact_layout, tooltip='If activated, will remove spikes which amplitude is too big to be a real spike')],
            [sg.Frame('Split multi unit', split_multi_unit_layout, tooltip='If activated, will split units containing 2 or more population of spikes waveform profil')],
            [sg.Frame('Additional parameters', additional_param_layout, tooltip='Additional parmaters used at the end of the pipeline')],
            [sg.B('Save', k='save_custom_cleaning_param_button'), sg.B('Reset', k='reset_custom_cleaning_param_button')],
            ]
    
    return sg.Window('Custom cleaning parameters', layout, finalize=True)

def save_custom_cleaning_parameters(window):
    
    custom_cleaning_parameters_dict = {}
    for window_key in window.AllKeysDict:
        if not isinstance(window_key, tuple):
            continue
        else:
            if window_key[0] not in custom_cleaning_parameters_dict.keys():
                custom_cleaning_parameters_dict[window_key[0]] = {}
                
            current_param_value = window[window_key].get()
            if current_param_value == 'None' or current_param_value == '':
                current_param_value = None
            elif current_param_value == 'True':
                current_param_value = True
            elif current_param_value == 'False':
                current_param_value = False
            else:
                try:
                    if '.' or ',' in current_param_value:
                        param_to_convert = current_param_value.replace(',', '.')
                        current_param_value = float(param_to_convert)
                    else:
                        current_param_value = int(current_param_value)
                except ValueError:
                    pass
                
            custom_cleaning_parameters_dict[window_key[0]][window_key[1]] = current_param_value
            
    return custom_cleaning_parameters_dict

def custom_cleaning_event_handler(window, values, event, current_sorter_param):
    if event == sg.WIN_CLOSED:
        current_param = save_custom_cleaning_parameters(window)
        if current_param != current_sorter_param[0]['custom_cleaning_param']:
            save_changes_answer = sg.popup_yes_no('Save changes?')
            if save_changes_answer:
                current_sorter_param[0]['custom_cleaning_param'] = current_param
            else:
                window.close()
        else:
            window.close()
        
    if event == 'save_custom_cleaning_param_button':
        current_sorter_param[0]['custom_cleaning_param'] = save_custom_cleaning_parameters(window)
        window.close()
        
    if event == 'reset_custom_cleaning_param_button':
        for main_param_name, main_param_dict in default_custom_cleaning_parameters_dict.items():
            for param_name, param_value in main_param_dict.items():
                window[(main_param_name, param_name)].update(param_value)