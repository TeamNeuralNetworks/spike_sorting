# -*- coding: utf-8 -*-
"""
Created on Mon May 13 15:24:47 2024

@author: _LMT
"""
import PySimpleGUI as sg

from GUIs.preprocessing_GUI import preprocessing_GUI
from GUIs.sorter_params_GUI import sorter_param_GUI
from GUIs.unit_auto_cleaning_GUI import unit_auto_cleaning_GUI
from GUIs.additional_recording_info_GUI import additional_recording_info_GUI
from GUIs.trace_visualization_GUI import trace_visualization_GUI
from GUIs.probe_visualization_GUI import probe_visualization_GUI
from curation.manual_curation import manual_curation_event_handler
from additional.toolbox import make_sorter_param_dict, ephy_extension_dict, select_folder_file, LEDIndicator, SetLED

#TODO
# def lock_analysis(base_instance):
#     base_instance.pipeline_parameters['from_loading'] = True
    
#     base_instance.main_window['preprocessing_checkbox'].update(disabled=True)
#     base_instance.main_window['Load_probe_file'].update(disabled=True)
    

#     base_instance.main_window['Load_ephy_file'].update(button_color='green')
#     base_instance.main_window['Load_probe_file'].update(button_color='green')
#     base_instance.main_window['Select_output_folder'].update(button_color='green')
    
#     if base_instance.pipeline_parameters['preprocessing']:
#         base_instance.main_window['preprocessing_checkbox'].update(True)
#         if base_instance.pipeline_parameters['preprocessing'] == 'Done':
#             SetLED(base_instance.main_window['led_preprocessing'], 'green')
#     else:
#         base_instance.main_window['preprocessing_checkbox'].update(False)
#         SetLED(base_instance.main_window['led_preprocessing'], 'red')
    
#     if base_instance.pipeline_parameters['preprocessing'] == 'Done':
#         SetLED(base_instance.main_window['led_sorting'], 'green')
#         base_instance.main_window['sorter_combo'].update(value=base_instance.pipeline_parameters['name'])
        
#     if base_instance.pipeline_parameters['unit_auto_cleaning'] or base_instance.pipeline_parameters['manual_curation']:
#         base_instance.main_window['sorter_combo'].update(disabled=True)
#         if base_instance.pipeline_parameters['unit_auto_cleaning'] == 'Done':
#             SetLED(base_instance.main_window['led_unit_auto_cleaning'], 'green')
        
#         base_instance.main_window['unit_auto_cleaning_checkbox'].update(True)
#         if not base_instance.pipeline_parameters['from_loading'] and (base_instance.pipeline_parameters['unit_auto_cleaning'] != 'Done' or base_instance.pipeline_parameters['manual_curation'] !='Done'):
#             base_instance.main_window['unit_auto_cleaning_checkbox'].update(disabled=True)
            
#         if base_instance.pipeline_parameters['manual_curation']:
#             if base_instance.pipeline_parameters['manual_curation'] == 'Done':
#                 SetLED(base_instance.main_window['led_Manual'], 'green')
#             base_instance.main_window['manual_curation_checkbox'].update(True)
#             if not base_instance.pipeline_parameters['from_loading'] and base_instance.pipeline_parameters['manual_curation'] !='Done':
#                 base_instance.main_window['manual_curation_checkbox'].update(disabled=True)
#         else:
#             base_instance.main_window['manual_curation_checkbox'].update(False)
#             base_instance.main_window['manual_curation_checkbox'].update(disabled=False)
#     else:
#         base_instance.main_window['unit_auto_cleaning_checkbox'].update(False)
#         base_instance.main_window['manual_curation_checkbox'].update(False)

# def unlock_analysis(base_instance, trigger_by_error=False):

#     base_instance.pipeline_parameters['sorting'] = True
    
#     if base_instance.pipeline_parameters['preprocessing'] != "Done":
#         base_instance.main_window['preprocessing_checkbox'].update(disabled=False)
#         if not trigger_by_error:
#             SetLED(base_instance.main_window['led_preprocessing'], 'red')
#     if base_instance.pipeline_parameters['sorting'] != "Done":
#         if not trigger_by_error:
#             SetLED(base_instance.main_window['led_sorting'], 'red')

#     base_instance.main_window['Load_probe_file'].update(disabled=False)
    
#     if  base_instance.pipeline_parameters['unit_auto_cleaning'] != "Done":
#         if not trigger_by_error:
#             SetLED(base_instance.main_window['led_unit_auto_cleaning'], 'red')
#         base_instance.main_window['sorter_combo'].update(disabled=False)
#         base_instance.main_window['unit_auto_cleaning_checkbox'].update(disabled=False)
#     if base_instance.pipeline_parameters['manual_curation'] != "Done":
#         if not trigger_by_error:
#             SetLED(base_instance.main_window['led_Manual'], 'red')  
#         base_instance.main_window['sorter_combo'].update(disabled=False)
#         base_instance.main_window['unit_auto_cleaning_checkbox'].update(disabled=False)
#         base_instance.main_window['manual_curation_checkbox'].update(disabled=False)

class Main_GUI:
    
    def __init__(self):
        
        self.additional_GUI_instance_dict = {
                                            'preprocessing_instance': preprocessing_GUI(), 
                                            'sorter_param_instance': sorter_param_GUI(),
                                            'unit_auto_cleaning_instance': unit_auto_cleaning_GUI(),
                                            'additional_recording_info_instance': additional_recording_info_GUI(),
                                            'trace_visualization_instance': trace_visualization_GUI(),
                                            'probe_visualization_instance': probe_visualization_GUI(),
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
        
        main_menu_layout = [['File', ['Load ephy folder', 'Load multiple recording', 'Load analysis', 'Export spike time', 'Export Template']], 
                            ['Edit',['Probe tool', 
                                     # 'Import metadata', 'Ephy file tool'
                                     ]],
                            ['Parameters',['Preprocessing parameter', 'Sorter parameter', 'Custom cleaning parameter', 'Plotting parameter']],
                            ['Visualize',['Traces', 'Probe']],
                            ]
        
        if pipeline_parameters['load_ephy']['ephy_file_path'] is None:
            ephy_file_button = sg.B("Load ephy file", k="Load_ephy_file", button_color='red', enable_events=True)
        else:
            ephy_file_button = sg.B("Load ephy file", k="Load_ephy_file", button_color='green', enable_events=True)
        
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
                  [sg.B('Start analysis', k='launch_sorting_button'), sg.B('Reset analysis', k='reset_analysis_button'),
                   # sg.B('Debug', k='debug_button'), 
                   sg.T('', k='progress_text'), sg.ProgressBar(100, key='progress_bar', visible=False, size=(5, 2))],
                  [sg.Multiline(size=(10,7), expand_x=True, expand_y=False, write_only=True, k='progress_output', 
                                reroute_stdout=True, reroute_stderr=True, echo_stdout_stderr=True, autoscroll=True, auto_refresh=True, )]
                 ]
        
        self.window = sg.Window('Spike sorting GUI', layout, finalize=True)
        
    def reset_analysis_pipeline(self, base_instance):
        if base_instance.pipeline_parameters['preprocessing'] == 'Done':
            SetLED(self.window, 'led_preprocessing', 'red')
            base_instance.pipeline_parameters['preprocessing'] =  self.window['preprocessing_checkbox'].get()
            
        if base_instance.pipeline_parameters['sorting'] == 'Done':
            SetLED(self.window, 'led_sorting', 'red')
            if self.window['sorter_combo'].get() == '':
                base_instance.pipeline_parameters['sorting'] = False
            else:
                base_instance.pipeline_parameters['sorting'] = True
                
        if base_instance.pipeline_parameters['unit_auto_cleaning'] == 'Done':
            SetLED(self.window, 'led_unit_auto_cleaning', 'red')
            base_instance.pipeline_parameters['unit_auto_cleaning'] =  self.window['unit_auto_cleaning_checkbox'].get()
            
        if base_instance.pipeline_parameters['manual_curation'] == 'Done':
            SetLED(self.window, 'led_Manual', 'red')
            base_instance.pipeline_parameters['manual_curation'] =  self.window['manual_curation_checkbox'].get()
   
    def event_handler(self, base_instance):

       while True:
            window, event, values = sg.read_all_windows()
             
            for additional_GUI_key, additional_GUI_instance in self.additional_GUI_instance_dict.items():
                
                if window == additional_GUI_instance.window:
                    additional_GUI_instance.event_handler(values, event, base_instance)
                    break
            
            if event in ['manual_curation_outputlink_input', 'open_manual_curation_outputlink_button', 'continue_manual_curation_inputlink_button', 'accept_manual_curation_inputlink_button', 'manual_cleaning_input_column']:
                manual_curation_event_handler(window, values, event, base_instance.pipeline_parameters, base_instance.state)
            
            elif window == self.window:
                
                if event == sg.WIN_CLOSED:
                    
                    for additional_GUI_key, additional_GUI_instance in self.additional_GUI_instance_dict.items():
                        if additional_GUI_instance.window is not None:
                            additional_GUI_instance.window.close()
                            additional_GUI_instance.window = None
                        
                    base_instance.state = 'stop'
                    window.close()
                    break
                
                if base_instance.state is not None and event in ['Load analysis', 'Load_ephy_file', 'Load multiple recording', 'Load_probe_file', 'Select_output_folder', 'sorter_combo', 'launch_sorting_button']:
                    if event == 'sorter_combo':
                        self.window['sorter_combo'].update(base_instance.pipeline_parameters['name'])
                    sg.popup_error('Parameters can not while a analysis is in progress')
                
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
                    
                    elif event == 'Load_ephy_file' or event == 'Load ephy folder':
                        if event == 'Load_ephy_file':
                            path = select_folder_file(mode='file')
                        else:
                            path = select_folder_file(mode='folder')
                        if path is not None:
                            extention = path.split('.')[-1] if event == 'Load_ephy_file' else 'folder'
                            base_instance.pipeline_parameters['load_ephy']['ephy_file_extension'] = extention
                            base_instance.pipeline_parameters['load_ephy']['ephy_file_path'] = path
                            if base_instance.pipeline_parameters['from_loading']:
                                base_instance.pipeline_parameters['from_loading'] = False
                                base_instance.pipeline_parameters['preprocessing'] = False
                                base_instance.pipeline_parameters['sorting'] = False
                                base_instance.pipeline_parameters['unit_auto_cleaning'] = False
                                base_instance.pipeline_parameters['manual_curation'] = False
                                # unlock_analysis(self.window, base_instance.pipeline_parameters) #TODO
                                self.window['Load_probe_file'].update(button_color='red')
                                self.window['Select_output_folder'].update(button_color='red')
                                
                            if extention not in ephy_extension_dict.keys() or extention in ['folder']:
                                self.additional_GUI_instance_dict['additional_recording_info_instance'].create_window()
                            else:
                                base_instance.state = "load_recording"
                            
                    elif event == 'Load multiple recording':
                        multi_file_path = sg.popup_get_file('Select excel file containing ephy_file_path, probe_file_path, output_folder_path (each row is a different recording)')   
                        if multi_file_path is not None:
                            base_instance.pipeline_parameters['load_ephy']['ephy_file_path'] = multi_file_path
                            self.additional_GUI_instance_dict['additional_recording_info_instance'].create_window(multi_recording_loading=True)
                            base_instance.pipeline_parameters['from_loading'] = True
                            base_instance.state = "load_multi_recording"
                            
                    elif event == 'Select_output_folder':
                        path = select_folder_file(mode='folder')
                        if path is not None:
                            base_instance.pipeline_parameters['output_folder_path'] = path
                            self.window['Select_output_folder'].update(button_color='green')
                        else:
                            self.window['Select_output_folder'].update(button_color='red')
                    
                    elif event == 'sorter_combo':
                        # if base_instance.pipeline_parameters['name'] != values['sorter_combo'] and not base_instance.pipeline_parameters['from_loading']:
                        #     unlock_analysis(self.window, base_instance.pipeline_parameters) #TODO
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
                        self.additional_GUI_instance_dict['preprocessing_instance'].create_window(base_instance.pipeline_parameters['preprocessing_param'])
                    
                    elif event == 'unit_auto_cleaning_checkbox':
                        base_instance.pipeline_parameters['unit_auto_cleaning'] = values['unit_auto_cleaning_checkbox']
                    
                    elif event == 'Unit auto cleaning parameter':
                        self.additional_GUI_instance_dict['unit_auto_cleaning_instance'].create_window(base_instance.pipeline_parameters['unit_auto_cleaning_param'])
                        
                    elif event == 'manual_curation_checkbox':
                        base_instance.pipeline_parameters['manual_curation'] = values['manual_curation_checkbox']
    
                    elif event == 'launch_sorting_button':
                        if base_instance.pipeline_parameters['load_ephy']['ephy_file_path'] is None:
                            sg.popup_error('Please select a ephy file')
                        elif base_instance.pipeline_parameters['name'] is None and base_instance.pipeline_parameters['name'] is not None:
                            sg.popup_error('Please select a sorter')
                        elif base_instance.pipeline_parameters['probe_file_path'] is None and base_instance.pipeline_parameters['name'] is not None: 
                            sg.popup_error('Please select a probe file')
                        elif base_instance.pipeline_parameters['output_folder_path'] is None and base_instance.pipeline_parameters['name'] is not None:
                            sg.popup_error('Please select a output folder')
                        else:

                            # lock_analysis(base_instance) #TODO
                            base_instance.state = 'launch'
                            
                    elif event == 'reset_analysis_button':
                        
                        if base_instance.pipeline_parameters['preprocessing'] == 'Done': 
                            base_instance.load_recording()
                        else:
                            self.reset_analysis_pipeline(base_instance)
                        
                if event == 'Export spike time':
                    if base_instance.base_instance.pipeline_parameters['sorting'] == 'Done' or base_instance.base_instance.pipeline_parameters['unit_auto_cleaning'] == 'Done' or base_instance.base_instance.pipeline_parameters['manual_curation'] == 'Done':
                        export_spike_time_path = sg.popup_get_file('Export spike time', save_as=True, no_window=True, file_types=(("Excel", "*.xlsx"),))
                        base_instance.base_instance.pipeline_parameters['export_spike_time_path'] = export_spike_time_path
                        base_instance.state = 'export_spike_time'
                    else:
                        sg.popup_error('No analysis found to export spike time from')
                elif event == 'Export Template':
                    if base_instance.base_instance.pipeline_parameters['sorting'] == 'Done' or base_instance.base_instance.pipeline_parameters['unit_auto_cleaning'] == 'Done' or base_instance.base_instance.pipeline_parameters['manual_curation'] == 'Done':
                        base_instance.base_instance.pipeline_parameters['export_template_path'] = sg.popup_get_file('Export spike time', save_as=True, no_window=True, file_types=(("Excel", "*.xlsx"),))
                        base_instance.state = 'export_template'
                    else:
                        sg.popup_error('No analysis found to export spike time from')
                
                elif event == 'Traces':
                    if base_instance.recording is None:
                        sg.popup_error('Please load a recording')
                    else:
                        self.additional_GUI_instance_dict['trace_visualization_instance'].create_window(base_instance=base_instance)
            
                elif event == 'Probe':
                    if base_instance.probe is None:
                        sg.popup_error('Please load a probe')
                    else:
                        self.additional_GUI_instance_dict['probe_visualization_instance'].create_window(probe=base_instance.probe)
                
                
                elif event == 'popup_error':
                    sg.popup_error(values['popup_error'])
                # if event == 'debug_button':
                #     lock_analysis(base_instance)
                    # print('\n')
                    # print(base_instance.base_instance.pipeline_parameters)
                    # print(sorter[0], analyzer[0], recording[0])
                    # base_instance.base_instance.pipeline_parameters['from_loading'] = False
                    # base_instance.base_instance.pipeline_parameters['bandpass'] = [True, 300, 600]
                    # base_instance.base_instance.pipeline_parameters['comon_ref'] = True
                    # base_instance.base_instance.pipeline_parameters['unit_auto_cleaning'] = False
                    # base_instance.base_instance.pipeline_parameters['manual_curation'] = False
                    # with open(r"C:\code\spike_sorting\additional/default_param.json", "w") as outfile: 
                    #     json.dump(pipeline_parameters[0], outfile)
