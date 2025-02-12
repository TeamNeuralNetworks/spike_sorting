# -*- coding: utf-8 -*-
"""
Created on Mon May 13 14:35:57 2024

@author: _LMT
"""
import PySimpleGUI as sg
from curation.clean_unit import big_artefact_methods, splitting_method_list, channel_method_list
from additional.toolbox import get_default_param

class unit_auto_cleaning_GUI:
    
    def __init__(self):
        
        self.window = None
    
    def create_window(self, unit_auto_cleaning_param, default_input_size=(5,2)):
        
        
        remove_edge_artefact_layout = [[sg.T('Activate', tooltip='If selected will remove spikes at the edge of the recording'), sg.Checkbox('', default=unit_auto_cleaning_param['remove_edge_artefact']['activate'], k=('remove_edge_artefact', 'activate'), tooltip='If selected will remove spikes at the edge of the recording')],
                                       [sg.T('Lenght to remove', tooltip='In ms, all spike at the begining and end of the recoding that are in this window are removed'), sg.I(unit_auto_cleaning_param['remove_edge_artefact']['lenght_to_remove'], size=default_input_size, k=('remove_edge_artefact', 'lenght_to_remove'), tooltip='In ms, all spike at the begining and end of the recoding that are in this window are removed'), sg.T('ms')],
                                       # [sg.B('load custom excel', k=('remove_edge_artefact', 'load_custom_excel_button'), tooltip='An excel file can be loaded with contain the index of the transition from one file to the other')], #TODO
                                       ]
        
        remove_big_artefact_layout = [[sg.T('Activate', tooltip='If selected will remove spikes wich amplitude is too high'), sg.Checkbox('', default=unit_auto_cleaning_param['remove_big_artefact']['activate'], k=('remove_big_artefact', 'activate'), tooltip='If selected will remove spikes wich amplitude is too high')],
                                       [sg.T('Method', tooltip='Method used for the thresholding of spikes'), sg.Combo(big_artefact_methods, default_value=unit_auto_cleaning_param['remove_big_artefact']['method'], k=('remove_big_artefact', 'method'), tooltip='Method used for the thresholding of spikes')],
                                       [sg.T('Threshold', tooltip='Threshold above wich the amplitud of the spike has to be to be removed (relative to other spike from the same unit)'), sg.I(unit_auto_cleaning_param['remove_big_artefact']['threshold'], size=default_input_size, k=('remove_big_artefact', 'threshold'), tooltip='Threshold above wich the amplitud of the spike has to be to be removed (relative to other spike from the same unit)')],
                                       ]
        
        split_multi_unit_layout = [[sg.T('Activate', tooltip='If selected will split units containing 2 or more population of spikes waveform profil'), sg.Checkbox('', default=unit_auto_cleaning_param['split_multi_unit']['activate'], k=('split_multi_unit', 'activate'), tooltip='If selected will split units containing 2 or more population of spikes waveform profil')],
                                   [sg.T('Method', tooltip='Method used for reduction of dimention'), sg.Combo(splitting_method_list, default_value=unit_auto_cleaning_param['split_multi_unit']['method'], k=('split_multi_unit', 'method'), tooltip='Method used for reduction of dimention', enable_events=True)], 
                                   [sg.pin(sg.Column(
                                                     [[sg.T('number of Component', tooltip='Number of component used to compare cluster'), sg.I(unit_auto_cleaning_param['split_multi_unit']['n_component'], k=('split_multi_unit', 'n_component'), size=default_input_size, tooltip='Number of component used to compare cluster')],
                                                      [sg.T('Channel method', tooltip='what channel to use'), sg.Combo(channel_method_list, default_value=unit_auto_cleaning_param['split_multi_unit']['channel_method'], k=('split_multi_unit', 'channel_method'), tooltip='what channel to use')], 
                                                      [sg.T('Silhouette threshold', tooltip='Threshold above wich the unit will be split'), sg.I(unit_auto_cleaning_param['split_multi_unit']['threshold'], size=default_input_size, k=('split_multi_unit', 'threshold'), tooltip='Threshold above wich the unit will be split')],
                                                     [sg.T('Maximum number of split', tooltip='Maximum number of split per unit'), sg.I(unit_auto_cleaning_param['split_multi_unit']['max_split'], size=default_input_size, k=('split_multi_unit', 'max_split'), tooltip='Maximum number of split per unit')],
                                                     [sg.T('Minimum spike per unit', tooltip='Minimum number of spikes per unit (if inferior the unit will be removed)'), sg.I(unit_auto_cleaning_param['split_multi_unit']['min_spike_per_unit'], size=default_input_size, k=('split_multi_unit', 'min_spike_per_unit'), tooltip='Minimum number of spikes per unit (if inferior the unit will be removed)')]],#TODO probably better to put that in addictional filter or something
                                                     k=('split_multi_unit', 'silhouette_column'), visible=True if unit_auto_cleaning_param['split_multi_unit']['method'] in ['pca', 'phate'] else False))],
                                   
                                   [sg.pin(sg.Column(
                                                     [[sg.T('Channel method', tooltip='what channel to use'), sg.Combo(channel_method_list, default_value=unit_auto_cleaning_param['split_multi_unit']['channel_method'], k=('split_multi_unit', 'channel_method'), tooltip='what channel to use')], 
                                                     ], k=('split_multi_unit', 'template_as_ref_column'), visible=True if unit_auto_cleaning_param['split_multi_unit']['method'] == 'template_as_ref' else False))],
                                   
                                   ]
        remove_by_metric_layout = [[sg.T('Activate', tooltip='Remove bad unit using metrics'), sg.Checkbox('', default=unit_auto_cleaning_param['remove_by_metric']['activate'], k=('remove_by_metric', 'activate'), tooltip='Remove bad unit using metrics')],
                                   
                                   [sg.T('Isi violation', tooltip='Isi violation conrespond to spikes that occur during the refractoryperiod of the neuron and is a indication of contamiation of the unit'), sg.Checkbox('', default=unit_auto_cleaning_param['remove_by_metric']['isi_violation_activate'], k=('remove_by_metric', 'isi_violation_activate'), tooltip='Isi violation conrespond to spikes that occur during the refractoryperiod of the neuron and is a indication of contamiation of the unit'),
                                   sg.T('Refractory period', tooltip='interval in ms where two spikes are concidered to be in the isi violation'), sg.I(unit_auto_cleaning_param['remove_by_metric']['isi_threshold_ms'], k=('remove_by_metric', 'isi_threshold_ms'), tooltip='interval in ms where two spikes are concidered to be in the isi violation', size=default_input_size), sg.T('ms'),
                                   sg.T('Violation ratio', tooltip='Inter sike interval violation ratio'), sg.I(unit_auto_cleaning_param['remove_by_metric']['isi_violation_ratio'], k=('remove_by_metric', 'isi_violation_ratio'), tooltip='Initer sike interval violation ratio', size=default_input_size)],
                                   
                                   [sg.T('Minimum frequency', tooltip='Minimum frequency that a unit must have to be selected'), sg.Checkbox('', default=unit_auto_cleaning_param['remove_by_metric']['min_freq_activate'], k=('remove_by_metric', 'min_freq_activate'), tooltip='Minimum frequency that a unit must have to be selected'),
                                    sg.I(unit_auto_cleaning_param['remove_by_metric']['min_freq_threshold_hz_low'], k=('remove_by_metric', 'min_freq_threshold_hz_low'), tooltip='Minimum frequency that a unit must have to be selected', size=default_input_size),
                                    sg.T('-'), sg.I(unit_auto_cleaning_param['remove_by_metric']['min_freq_threshold_hz_high'], k=('remove_by_metric', 'min_freq_threshold_hz_high'), tooltip='Minimum frequency that a unit must have to be selected', size=default_input_size), sg.T('Hz')],
                                   
                                   [sg.T('Presence ratio', tooltip='Presence ratio is the proportion of discrete time bins in which at least one spike occurred. Each unit must be above the treshold to be selected.'), sg.Checkbox('', default=unit_auto_cleaning_param['remove_by_metric']['presence_ratio_activate'], k=('remove_by_metric', 'presence_ratio_activate'), tooltip='Presence ratio is the proportion of discrete time bins in which at least one spike occurred. Each unit must be above the treshold to be selected.'),
                                    sg.I(unit_auto_cleaning_param['remove_by_metric']['presence_ratio_threshold_low'], k=('remove_by_metric', 'presence_ratio_threshold_low'), tooltip='Presence ratio is the proportion of discrete time bins in which at least one spike occurred. Each unit must be above the treshold to be selected.', size=default_input_size),
                                    sg.T('-'), sg.I(unit_auto_cleaning_param['remove_by_metric']['presence_ratio_threshold_high'], k=('remove_by_metric', 'presence_ratio_threshold_high'), tooltip='Presence ratio is the proportion of discrete time bins in which at least one spike occurred. Each unit must be above the treshold to be selected.', size=default_input_size),],
                                   
                                   [sg.T('L-ratio', tooltip='This metric identifies unit separation, a high value indicates a highly contaminated unit. Each unit must be below the treshold to be selected.'), sg.Checkbox('', default=unit_auto_cleaning_param['remove_by_metric']['L_ratio_activate'], k=('remove_by_metric', 'L_ratio_activate'), tooltip='This metric identifies unit separation, a high value indicates a highly contaminated unit. Each unit must be below the treshold to be selected.'),
                                   sg.I(unit_auto_cleaning_param['remove_by_metric']['L_ratio_threshold'], k=('remove_by_metric', 'L_ratio_threshold'), tooltip='This metric identifies unit separation, a high value indicates a highly contaminated unit. Each unit must be below the treshold to be selected.', size=default_input_size)],
                                   
                                   ]
        additional_param_layout = [[sg.T('Rename units', tooltip='If selected will rename units (if 10 units remain at the end of the pipeline the units number will go from 0 to 10)'), sg.Checkbox('', default=unit_auto_cleaning_param['rename_unit']['activate'], k=('rename_unit', 'activate'), tooltip='If selected will rename units (if 10 units remain at the end of the pipeline the units number will go from 0 to 10)')],
                                   [sg.T('Plot cleaning summary', tooltip='If selected will plot a summary of the cleaning done for each remaining unit'), sg.Checkbox('', default=unit_auto_cleaning_param['plot_cleaning_summary']['activate'], k=('plot_cleaning_summary', 'activate'), tooltip='If selected will plot a summary of the cleaning done for each remaining unit')],
                                    ]
        
        layout = [
                [sg.Frame('Remove edge artefact', remove_edge_artefact_layout, tooltip='If activated, will remove spikes at the edge of the recording')],
                [sg.Frame('Remove big artefact', remove_big_artefact_layout, tooltip='If activated, will remove spikes which amplitude is too big to be a real spike')],
                [sg.Frame('Split multi unit', split_multi_unit_layout, tooltip='If activated, will split units containing 2 or more population of spikes waveform profil')],
                [sg.Frame('Remove bad unit with metrics', remove_by_metric_layout, tooltip='If activated, will remove unit witch metrics exced a certain threshold')],
                [sg.Frame('Additional parameters', additional_param_layout, tooltip='Additional parmaters used at the end of the pipeline')],
                [sg.B('Save', k='save_unit_auto_cleaning_param_button'), sg.B('Reset', k='reset_unit_auto_cleaning_param_button')],
                ]
        
        if self.window is not None:
            location = self.window.current_location()
            self.window.close()
        else:
            location = None
            
        self.window = sg.Window('Custom cleaning parameters', layout, finalize=True, location=location)
    
    def save_parameters(self):
        
        unit_auto_cleaning_parameters_dict = {}
        for window_key in self.window.AllKeysDict:
            if not isinstance(window_key, tuple) or 'column' in window_key[1]:
                continue
            else:
                if window_key[0] not in unit_auto_cleaning_parameters_dict.keys():
                    unit_auto_cleaning_parameters_dict[window_key[0]] = {}
                    
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
                    
                unit_auto_cleaning_parameters_dict[window_key[0]][window_key[1]] = current_param_value
                
        return unit_auto_cleaning_parameters_dict
    
    def event_handler(self, values, event, base_instance):
        if event == sg.WIN_CLOSED:
            current_param = self.save_parameters()
            if current_param != base_instance.pipeline_parameters['unit_auto_cleaning_param']:
                if base_instance.state == 'unit_auto_cleaning':
                    save_changes_answer = sg.popup_yes_no('Parameters can not be saved while a analysis is in progress. Close anyway?')
                    if save_changes_answer == 'Yes':
                        self.window.close()
                        self.window = None
                else:
                    save_changes_answer = sg.popup_yes_no('Save changes?')
                    if save_changes_answer == 'Yes':
                        base_instance.pipeline_parameters['unit_auto_cleaning_param'] = current_param
                    self.window.close()
                    self.window = None
            else:
                self.window.close()
                self.window = None
    
        if event == 'save_unit_auto_cleaning_param_button':
            if base_instance.state is not None:
                sg.popup_error('Parameters can not while a analysis is in progress')
            else:
                base_instance.pipeline_parameters['unit_auto_cleaning_param'] = self.save_parameters()
                self.window.close()
                self.window = None
            
        if event == 'reset_unit_auto_cleaning_param_button':
            default_param = get_default_param()
            
            for main_param_name, main_param_dict in default_param['unit_auto_cleaning_param'].items():
                for param_name, param_value in main_param_dict.items():
                    self.window[(main_param_name, param_name)].update(str(param_value))
        
        if event == ('split_multi_unit', 'method'):
            if values[('split_multi_unit', 'method')] in ['pca', 'phate']:
                self.window[('split_multi_unit', 'silhouette_column')].update(visible=True)
                self.window[('split_multi_unit', 'template_as_ref_column')].update(visible=False)
            elif values[('split_multi_unit', 'method')] == 'template_as_ref':
                self.window[('split_multi_unit', 'silhouette_column')].update(visible=False)
                self.window[('split_multi_unit', 'template_as_ref_column')].update(visible=True)