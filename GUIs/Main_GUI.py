# -*- coding: utf-8 -*-
"""
Created on Mon May 13 15:24:47 2024

@author: _LMT
"""
import PySimpleGUI as sg
import traceback
import os 
import copy
import json
from time import sleep

from GUIs.preprocessing_GUI import preprocessing_GUI
from GUIs.sorter_params_GUI import sorter_param_GUI
from GUIs.unit_auto_cleaning_GUI import unit_auto_cleaning_GUI
from GUIs.additional_recording_info_GUI import additional_recording_info_GUI
from GUIs.trace_visualization_GUI import trace_visualization_GUI
from GUIs.probe_visualization_GUI import probe_visualization_GUI
from GUIs.sorting_summary_plot_GUI import sorting_summary_plot_GUI
from GUIs.sorting_summary_plot_param_GUI import sorting_summary_plot_param_GUI
from GUIs.probe_tool_GUI import probe_tool_GUI
from GUIs.Recording_tool_GUI import Recording_tool_GUI
from GUIs.Custom_popup_GUI import Custom_popup_GUI
from curation.manual_curation import manual_curation_event_handler
from additional.toolbox import make_sorter_param_dict, ephy_extractor_dict, select_folder_file, LEDIndicator, SetLED, get_availabled_extension_extractor_converter_dict, get_default_param

class Main_GUI:
    
    def __init__(self):
        
        self.additional_GUI_instance_dict = {
                                            'preprocessing_instance': preprocessing_GUI(), 
                                            'sorter_param_instance': sorter_param_GUI(),
                                            'unit_auto_cleaning_instance': unit_auto_cleaning_GUI(),
                                            'additional_recording_info_instance': additional_recording_info_GUI(),
                                            'trace_visualization_instance': trace_visualization_GUI(),
                                            'probe_visualization_instance': probe_visualization_GUI(),
                                            'probe_tool_instance': probe_tool_GUI(),
                                            'sorting_summary_plot_instance': sorting_summary_plot_GUI(),
                                            'sorting_summary_plot_param_instance': sorting_summary_plot_param_GUI(),
                                            'Recording_tool_instance': Recording_tool_GUI(),
                                            'Custom_popup_instance': Custom_popup_GUI(),
                                            }
        
        self.sorter_param_dict = make_sorter_param_dict()
        self.window = None

    def launch_GUI(self, base_instance):
        
        self.create_window(base_instance.pipeline_parameters)
        
        SetLED(self.window, 'led_preprocessing', 'red')
        SetLED(self.window, 'led_sorting', 'red')
        SetLED(self.window, 'led_unit_auto_cleaning', 'red')
        SetLED(self.window, 'led_Manual', 'red')
        
        self.event_handler(base_instance)
    
    def create_window(self, pipeline_parameters):
        
        sg.theme('DarkBlue')
        
        main_menu_layout = [['File', ['Load analysis', 
                                      'Export spike time', 
                                      'Export Template',
                                      'Export to phy', 
                                      'Save settings', 
                                      'Load settings']], 
                            
                             ['Edit',['Create probe', 
                                      'Edit recording'
                                      ]],
                             
                            ['Parameters',['Preprocessing parameter', 
                                           'Sorter parameter', 
                                           'Unit auto cleaning parameter', 
                                           'Plotting parameter'
                                           ]],
                            
                            ['Visualize',['Traces', 
                                          'Probe', 
                                          'Unit summary'
                                          ]],
                            ]
        
        if pipeline_parameters['load_ephy']['mode'] is None:
            ephy_file_button = sg.B("Load recording", k="Load_recording", button_color='red', enable_events=True)
        else:
            ephy_file_button = sg.B("Load recording", k="Load_recording", button_color='green', enable_events=True)
        
        if pipeline_parameters['probe_file_path'] is None:
            probe_file_button = sg.B("Load probe file", k="Load_probe_file", button_color='red', enable_events=True)
        else:
            probe_file_button = sg.B("Load probe file", k="Load_probe_file", button_color='green', enable_events=True)
        
        if pipeline_parameters['output_folder_path'] is None:
            output_folder_button = sg.B("Select output folder", k='Select_output_folder', button_color='red', enable_events=True)
        else:
            output_folder_button = sg.B("Select output folder", k='Select_output_folder', button_color='green', enable_events=True)
        
        
        if pipeline_parameters['name'] is None:
            sorter_row = [LEDIndicator('led_sorting'), sg.T('Select Sorter'), sg.Combo(['']+list(self.sorter_param_dict.keys()), k='sorter_combo', enable_events=True)]
        else:
            sorter_row = [LEDIndicator('led_sorting'), sg.T('Select Sorter'), sg.Combo(['']+list(self.sorter_param_dict.keys()), default_value=pipeline_parameters['name'], k='sorter_combo', enable_events=True)]
        
        layout = [[sg.Menu(main_menu_layout, key='main_menu')],
                  [ephy_file_button, probe_file_button, output_folder_button],
                  [LEDIndicator('led_preprocessing'), sg.T('Preprocess recoding'), sg.Checkbox('', k='preprocessing_checkbox', enable_events=True, default=pipeline_parameters["preprocessing"])],
                  sorter_row,
                  [LEDIndicator('led_unit_auto_cleaning'), sg.T('Perform unit auto cleaning'), sg.Checkbox('', k='unit_auto_cleaning_checkbox', enable_events=True, default=pipeline_parameters["unit_auto_cleaning"])],
                  [LEDIndicator('led_Manual'), sg.T('Perform manual curation'), sg.Checkbox('', k='manual_curation_checkbox', enable_events=True, default=pipeline_parameters["manual_curation"])],
                  [sg.pin(sg.Column(
                                    [[sg.I('', readonly=True, k='manual_curation_outputlink_input', size=(27,2)),
                                      sg.B('Open to browser', k='open_manual_curation_outputlink_button', disabled=True), ],
                                     [sg.I('', k='manual_curation_inputlink_input', size=(27,2)), 
                                      sg.B('Continue', k='continue_manual_curation_inputlink_button', disabled=True, tooltip='Generate a new curation link to continue manual curation'), 
                                      sg.B('Accept', k='accept_manual_curation_inputlink_button', disabled=True, tooltip='Accept the current link has final and stop manual curation')]]
                                    , k='manual_cleaning_input_column', visible=pipeline_parameters["manual_curation"]))],
                  [sg.B('Start analysis', k='launch_sorting_button'), sg.B('Reset analysis', k='reset_analysis_button'), sg.T('', k='unit_found')],
                  [sg.Multiline(size=(10,7), expand_x=True, expand_y=False, write_only=True, k='progress_output', 
                                reroute_stdout=True, reroute_stderr=True, echo_stdout_stderr=True, autoscroll=True, auto_refresh=True, )]
                 ]
        
        self.window = sg.Window('Spike sorting GUI', layout, finalize=True)
        
    def reset_analysis_pipeline(self, base_instance):
        
        SetLED(self.window, 'led_preprocessing', 'red')
        base_instance.pipeline_parameters['preprocessing'] =  self.window['preprocessing_checkbox'].get()
        
        SetLED(self.window, 'led_sorting', 'red')
        if self.window['sorter_combo'].get() == '':
            base_instance.pipeline_parameters['sorting'] = False
        else:
            base_instance.pipeline_parameters['sorting'] = True
            
        SetLED(self.window, 'led_unit_auto_cleaning', 'red')
        base_instance.pipeline_parameters['unit_auto_cleaning'] =  self.window['unit_auto_cleaning_checkbox'].get()
        
        SetLED(self.window, 'led_Manual', 'red')
        base_instance.pipeline_parameters['manual_curation'] =  self.window['manual_curation_checkbox'].get()
        
        base_instance.pipeline_parameters['output_folder_path'] = None
        self.window['Select_output_folder'].update(button_color='red')
        
        self.window['unit_found'].update('')
   
    def event_handler(self, base_instance):

       while True:
            
            try:
                window, event, values = sg.read_all_windows()
                 
                for additional_GUI_key, additional_GUI_instance in self.additional_GUI_instance_dict.items():
                    if isinstance(additional_GUI_instance.window, dict) and window in additional_GUI_instance.window.values(): #Some GUI have multiple window
                        additional_GUI_instance.event_handler(window, values, event, base_instance)
                        break
                
                    elif window == additional_GUI_instance.window:
                        additional_GUI_instance.event_handler(values, event, base_instance)
                        break
                
                if event in ['manual_curation_outputlink_input', 'open_manual_curation_outputlink_button', 'continue_manual_curation_inputlink_button', 'accept_manual_curation_inputlink_button', 'manual_cleaning_input_column']:
                    manual_curation_event_handler(base_instance, values, event)
                
                elif window == self.window:
                    
                    if event == sg.WIN_CLOSED:
                        
                        for additional_GUI_key, additional_GUI_instance in self.additional_GUI_instance_dict.items():
                            if isinstance(additional_GUI_instance.window, dict):
                                for current_additional_GUI_instance_window in additional_GUI_instance.window.values():
                                    if current_additional_GUI_instance_window is not None:
                                        current_additional_GUI_instance_window.close()
                                        current_additional_GUI_instance_window = None
                                        
                            elif additional_GUI_instance.window is not None:
                                additional_GUI_instance.window.close()
                                additional_GUI_instance.window = None
                            
                        base_instance.state = 'stop'
                        window.close()
                        break
                    
                    if base_instance.state is not None and event in ['Load analysis', 'Load_recording', 'Load multiple recording', 'Load_probe_file', 'Select_output_folder']:
                        sg.popup_error('Parameters can not be changed while a analysis is in progress')
                        
                    elif event == 'preprocessing_checkbox' and (base_instance.state == 'preprocessing' or base_instance.pipeline_parameters['preprocessing'] == 'Done'):
                        self.window['preprocessing_checkbox'].update(True)
                        if base_instance.state == 'preprocessing':
                            sg.popup_error('Parameters can not be changed while a analysis is in progress')
                        else:
                            sg.popup_error('Preprocessing has already been applyed, reset the analysis to repreprocess ephy data')
                    
                    elif event == 'sorter_combo' and (base_instance.state == 'sorting' or base_instance.pipeline_parameters['sorting'] == 'Done'):
                        self.window['sorter_combo'].update(base_instance.pipeline_parameters['name'])
                        if base_instance.state == 'sorting':
                            sg.popup_error('Parameters can not be changed while a analysis is in progress')
                        else:
                            sg.popup_error('The data has already been sorted, reset the analysis to resort data')
                    
                    elif event == 'unit_auto_cleaning_checkbox' and (base_instance.state == 'unit_auto_cleaning' or base_instance.pipeline_parameters['unit_auto_cleaning'] == 'Done'):
                        self.window['unit_auto_cleaning_checkbox'].update(True)
                        if base_instance.state == 'unit_auto_cleaning':
                            sg.popup_error('Parameters can not be changed while a analysis is in progress')
                        else:
                            sg.popup_error('Units has already been cleaned, reset the analysis or load sbase sorting folder to reclean units')
                    
                    else:
                        if event == 'Load analysis':
                            base_instance.state = 'Load analysis'
                        
                        elif event == 'Load_probe_file':
                            path = select_folder_file(mode='file')
                            if path is not None:
                                if path.split('.')[-1] != 'json':
                                    sg.popup_error(f"Unsuported probe file format: {path.split('.')[-1]}")
                                    self.window['Load_probe_file'].update(button_color='red')
                                else:
                                    base_instance.pipeline_parameters['probe_file_path'] = path
                                    self.window['Load_probe_file'].update(button_color='green')
                                    base_instance.state = 'load_probe'
                        
                        elif event == 'Load_recording':
                            self.additional_GUI_instance_dict['Custom_popup_instance'].create_window(text='Select loading method', 
                                                                                                            buttons=['Load ephy file', 
                                                                                                                     'Load ephy folder', 
                                                                                                                     #'Load all file in a folder'#TODO not implemented yet 'Load all file in a folder'
                                                                                                                     ], 
                                                                                                            event='load_recordings_answer',
                                                                                                            window_to_call=self.window,
                                                                                                            title='Load recording')
                        
                        elif event == 'load_recordings_answer':
                            if values[event] == 'Load ephy file':
                                self.window.write_event_value('Load_ephy_file', "Main_GUI")
                            elif values[event] == 'Load ephy folder':
                                self.window.write_event_value('Load_ephy_folder', "Main_GUI")
                            elif values[event] == 'Load all file in a folder':
                                sg.popup_error('Not yet implemented')
                                
                        elif event == 'Load_ephy_file'  or event == 'Load_ephy_folder' or event == 'Load_multi_ephy_file':
                            default_param = get_default_param()
                            base_instance.pipeline_parameters['load_ephy']['extractor_parameters'] = default_param['load_ephy']['extractor_parameters']
                            
                            if 'Load_ephy_file' in event:
                                path = select_folder_file(mode='file')
                            elif 'Load_ephy_folder' in event:
                                path = select_folder_file(mode='folder')
                            elif event == 'Load_multi_ephy_file':
                                path = select_folder_file(mode='folder')
                                
                            if path is not None:
                                base_instance.pipeline_parameters['load_ephy']['trigger_from'] = values[event]
                                
                                if event == 'Load_ephy_folder':
                                    base_instance.pipeline_parameters['load_ephy']['mode'] = 'folder'
                                    base_instance.pipeline_parameters['load_ephy']['extension'] = 'folder'
                                    self.window.write_event_value('launch_recording_loading', "")
                                elif event == 'Load_ephy_file':
                                    base_instance.pipeline_parameters['load_ephy']['mode'] = 'file'
                                    base_instance.pipeline_parameters['load_ephy']['extension'] = path.split('.')[-1]
                                    self.window.write_event_value('launch_recording_loading', "")
                                elif event == 'Load_multi_ephy_file':
                                    base_instance.pipeline_parameters['load_ephy']['mode'] = 'multi_file'
                                    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]

                                    extention_list = []
                                    for file in files:
                                        extension = file.split('.')[-1]
                                        extention_list.append(extension)
                                    extention_list = sorted(list(set(extention_list)))
                                    
                                    if len(extention_list) > 1:
                                        self.additional_GUI_instance_dict['Custom_popup_instance'].create_window(text='Multiple file type detected, which one to load?', 
                                                                                                                 buttons=extention_list, 
                                                                                                                 event='Multi_file_loading_chose_extention',
                                                                                                                 window_to_call=self.window,
                                                                                                                 title='Multi file loading, chose extention')
                                    else:
                                        base_instance.pipeline_parameters['load_ephy']['extension'] = extention_list[0]
                                        path = [f'{path}/{file}' for file in files]
                                        self.window.write_event_value('launch_recording_loading', "")
                        
                        elif event == 'launch_recording_loading':

                                extension_extractor_converter_dict = get_availabled_extension_extractor_converter_dict(mode=base_instance.pipeline_parameters['load_ephy']['mode'])
                                if base_instance.pipeline_parameters['load_ephy']['extension'] in extension_extractor_converter_dict.keys() and len(ephy_extractor_dict[base_instance.pipeline_parameters['load_ephy']['mode']][extension_extractor_converter_dict[base_instance.pipeline_parameters['load_ephy']['extension']]]['args']) == 0:
                                    base_instance.pipeline_parameters['load_ephy']['extractor'] = extension_extractor_converter_dict[base_instance.pipeline_parameters['load_ephy']['extension']]
                                    path_syntax = ephy_extractor_dict[base_instance.pipeline_parameters['load_ephy']['mode']][base_instance.pipeline_parameters['load_ephy']['extractor']]['path_syntax']
                                    
                                    if base_instance.pipeline_parameters['load_ephy']['mode'] == 'multi_file':
                                        extractor_parameters_list = []
                                        for current_path in path:
                                            current_extractor_parameters = copy.deepcopy(base_instance.pipeline_parameters['load_ephy']['extractor_parameters'])
                                            current_extractor_parameters[path_syntax] = current_path
                                            extractor_parameters_list.append(current_extractor_parameters)
                                        base_instance.pipeline_parameters['load_ephy']['extractor_parameters'] = extractor_parameters_list
                                    else:
                                        base_instance.pipeline_parameters['load_ephy']['extractor_parameters'][path_syntax] = path
                                    base_instance.state = "load_recording"
                                else:
                                    self.additional_GUI_instance_dict['additional_recording_info_instance'].path = path
                                    self.additional_GUI_instance_dict['additional_recording_info_instance'].create_window(mode=base_instance.pipeline_parameters['load_ephy']['mode'],)

                            
                        elif event == 'Multi_file_loading_chose_extention':
                            
                            extension = values[event]
                            file_to_keep = [file for file in files if file.split('.')[-1] == extension]
                            base_instance.pipeline_parameters['load_ephy']['extension'] = extension
                            path = [f'{path}/{file}' for file in file_to_keep]
                            self.window.write_event_value('launch_recording_loading', "")
                                
                        elif event == 'Select_output_folder':
                            path = select_folder_file(mode='folder')
                            if path is not None:
                                base_instance.pipeline_parameters['output_folder_path'] = path
                                self.window['Select_output_folder'].update(button_color='green')
                            else:
                                self.window['Select_output_folder'].update(button_color='red')
                        
                        elif event == 'sorter_combo':
                            if values['sorter_combo'] == '':
                                base_instance.pipeline_parameters['sorting'] = False
                                base_instance.pipeline_parameters['name'] = None
                            else:
                                base_instance.pipeline_parameters['sorting'] = True
                                base_instance.pipeline_parameters['name'] = values['sorter_combo']
                                base_instance.pipeline_parameters['sorting_param'] = self.sorter_param_dict[values['sorter_combo']]['param'] 
                        
                        elif event == 'Sorter parameter':
                            if values['sorter_combo'] == '':
                                sg.popup_error('Please select a sorter')
                            else:
                                self.additional_GUI_instance_dict['sorter_param_instance'].sorter_name = base_instance.pipeline_parameters['name']
                                self.additional_GUI_instance_dict['sorter_param_instance'].create_window(self.sorter_param_dict[base_instance.pipeline_parameters['name']]['param_description'], 
                                                                                                    base_instance.pipeline_parameters['sorting_param'])
                        
                        elif event == 'preprocessing_checkbox':
                            base_instance.pipeline_parameters['preprocessing'] = values['preprocessing_checkbox']
                        
                        elif event == 'Preprocessing parameter':
                            self.additional_GUI_instance_dict['preprocessing_instance'].create_window(base_instance.pipeline_parameters['preprocessing_param'], base_instance.recording)
                        
                        elif event == 'unit_auto_cleaning_checkbox':
                            base_instance.pipeline_parameters['unit_auto_cleaning'] = values['unit_auto_cleaning_checkbox']
                        
                        elif event == 'Unit auto cleaning parameter':
                            self.additional_GUI_instance_dict['unit_auto_cleaning_instance'].create_window(base_instance.pipeline_parameters['unit_auto_cleaning_param'])
                            
                        elif event == 'manual_curation_checkbox':
                            base_instance.pipeline_parameters['manual_curation'] = values['manual_curation_checkbox']
        
                        elif event == 'launch_sorting_button':
                            if base_instance.pipeline_parameters['load_ephy']['mode'] is None:
                                sg.popup_error('Please select a ephy file')
                            elif base_instance.pipeline_parameters['sorting'] is False and (base_instance.pipeline_parameters['unit_auto_cleaning'] or base_instance.pipeline_parameters['manual_curation']):
                                sg.popup_error('Please select a sorter')
                            elif base_instance.pipeline_parameters['probe_file_path'] is None and base_instance.pipeline_parameters['sorting']: 
                                sg.popup_error('Please select a probe file')
                            elif base_instance.pipeline_parameters['output_folder_path'] is None and base_instance.pipeline_parameters['sorting']:
                                sg.popup_error('Please select a output folder')
                            else:
                                base_instance.state = 'launch'
                                
                        elif event == 'reset_analysis_button':
                            
                            if base_instance.pipeline_parameters['preprocessing'] == 'Done': 
                                base_instance.load_recording()
                            else:
                                self.reset_analysis_pipeline(base_instance)
                            
                    if event == 'Export spike time':
                        if base_instance.analyzer is None:   
                            sg.popup_error('No analysis found to export spike time from')
                        else:
                            base_instance.pipeline_parameters['export_spike_time_path'] = sg.popup_get_file('Export spike time', save_as=True, no_window=True, file_types=(("Excel", "*.xlsx"),))
                            base_instance.state = 'export_spike_time'
                    elif event == 'Export Template':
                        if base_instance.analyzer is None:     
                            sg.popup_error('No analysis found to export spike time from')
                        else:
                            base_instance.pipeline_parameters['export_template_path'] = sg.popup_get_file('Export spike time', save_as=True, no_window=True, file_types=(("Excel", "*.xlsx"),))
                            base_instance.state = 'export_template'
                            
                    elif event == 'Export to phy':
                        if base_instance.analyzer is None:   
                            sg.popup_error('No analysis found to export to phy')
                        else:
                            base_instance.pipeline_parameters['export_template_path'] = sg.popup_get_file('Export to phy', save_as=True, no_window=True)
                            base_instance.state = 'export_to_phy'
                            
                    elif event == 'Traces':
                        if base_instance.recording is None:
                            sg.popup_error('Please load a recording')
                        else:
                            self.additional_GUI_instance_dict['trace_visualization_instance'].create_window(recording=base_instance.recording)
                    
                    elif event == 'Create probe': #TODO buged
                            
                        if base_instance.probe is not None:
                            self.additional_GUI_instance_dict['Custom_popup_instance'].create_window(text='A probe has already been loaded.\nEdit current probe or create a new one?', 
                                                                                                     buttons=['Edit', 'Create', 'Cancel'], 
                                                                                                     event='launch probe creation',
                                                                                                     window_to_call=self.window,
                                                                                                     title='launch probe creation')
                        else:
                            self.window.write_event_value('launch probe creation', "Create")
                    
                    elif event == 'launch probe creation':
                        if base_instance.recording is not None:
                            self.additional_GUI_instance_dict['probe_tool_instance'].recording_channel_ids = base_instance.recording.channel_ids
                            
                        if values[event] == 'Create':
                            self.additional_GUI_instance_dict['probe_tool_instance'].create_window(mode='create_base_probe')
                        elif values[event] == 'Edit':
                            self.additional_GUI_instance_dict['probe_tool_instance'].probe = base_instance.probe
                            self.additional_GUI_instance_dict['probe_tool_instance'].create_window(mode='edit_table_window')
                    
                    elif event == 'Probe':
                        if base_instance.probe is None:
                            sg.popup_error('Please load a probe')
                        else:
                            if base_instance.recording is not None:
                                self.additional_GUI_instance_dict['probe_tool_instance'].recording_channel_ids = base_instance.recording.channel_ids
                                
                            self.additional_GUI_instance_dict['probe_tool_instance'].probe = base_instance.probe
                            self.additional_GUI_instance_dict['probe_tool_instance'].create_window(mode='edit_table_window')
                            
                    
                    elif event == 'Edit recording':
                        self.additional_GUI_instance_dict['Recording_tool_instance'].create_window(base_instance=base_instance)
                        
                    elif event == 'Unit summary':
                        if base_instance.analyzer is None:
                            sg.popup_error('Sorting has not been done yet')
                        else:
                            self.additional_GUI_instance_dict['sorting_summary_plot_instance'].create_window(base_instance=base_instance)
                    
                    elif event == 'Plotting parameter':
                            self.additional_GUI_instance_dict['sorting_summary_plot_param_instance'].create_window(summary_plot_param=base_instance.pipeline_parameters['summary_plot_param'], 
                                                                                                                   recording=base_instance.recording)
                    
                    elif event == 'Save settings':
                        path = sg.popup_get_file('Save sorting GUI settings', save_as=True, no_window=True)
                        if path is not None:
                            if path[-5:] != '.json':
                                base_instance.pipeline_parameters['default_sorting_gui_settings_path'] = f'{path}.json'
                            else:
                                base_instance.pipeline_parameters['default_sorting_gui_settings_path'] = path
                                
                            pipeline_parameters_to_save = copy.deepcopy(base_instance.pipeline_parameters)                                                                         
                            for analysis_to_be_done in ['preprocessing', 'sorting', 'unit_auto_cleaning', 'manual_curation']:
                                pipeline_parameters_to_save[analysis_to_be_done]
                                if pipeline_parameters_to_save[analysis_to_be_done] in [True, 'Done']:
                                    pipeline_parameters_to_save[analysis_to_be_done] = True
                                else:
                                    pipeline_parameters_to_save[analysis_to_be_done] = False

                            with open(base_instance.pipeline_parameters['default_sorting_gui_settings_path'], "w") as outfile: 
                                json.dump(pipeline_parameters_to_save, outfile)
                    
                    elif event == 'Load settings':
                        path = select_folder_file(mode='file')
                        if path is not None:
                            with open(path, 'r') as file:
                                 base_instance.pipeline_parameters = json.load(file)
                            base_instance.pipeline_parameters['default_sorting_gui_settings_path'] = path
                            for analysis_to_be_done in ['preprocessing', 'unit_auto_cleaning', 'manual_curation']:
                                self.window[f'{analysis_to_be_done}_checkbox'].update(value=base_instance.pipeline_parameters[analysis_to_be_done])
                            self.window['sorter_combo'].update(base_instance.pipeline_parameters['name'])
                    
                    elif event == 'popup_error':
                        sg.popup_error(values[event])
                        
            except Exception:
                print('\n')
                traceback.print_exc()
