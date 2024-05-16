# -*- coding: utf-8 -*-
"""
Created on Mon May 13 15:24:47 2024

@author: _LMT
"""
from GUIs.sorter_params_GUI import make_sorter_param_dict, sorting_param_event_handler, configure_sorter_param
from GUIs.custom_cleaning_GUI import make_config_custom_cleaning_param_window, custom_cleaning_event_handler
from GUIs.preprocessing_GUI import make_config_preprocessing_param_window, preprocessing_event_handler
from curation.manual_curation import manual_curation_event_handler

import PySimpleGUI as sg
import time
import tkinter as tk
from tkinter import filedialog

def led_loading_animation(state, main_window):
    while state[0] is not None:
        if state[0] is not None and state[0] != 'launch':
            SetLED(main_window, f'led_{state[0]}', 'green')
        time.sleep(0.25)
        if state[0] is not None and state[0] != 'launch':
            SetLED(main_window, f'led_{state[0]}', 'red')
        time.sleep(0.25)
  
def LEDIndicator(key=None, radius=30):
    return sg.Graph(canvas_size=(radius, radius),
             graph_bottom_left=(-radius, -radius),
             graph_top_right=(radius, radius),
             pad=(0, 0), key=key)

def SetLED(window, key, color):
    graph = window[0][key]
    graph.erase()
    graph.draw_circle((0, 0), 12, fill_color=color, line_color=color)

def select_folder_file(mode='folder'):
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    if mode == 'folder':
        path = filedialog.askdirectory()
    elif mode == 'file':
        path = filedialog.askopenfilename()
    if mode == 'both':
        raise ValueError('not yet implemented')
        
    if path:
        return path
    else:
        return None


def lock_analysis(window, current_sorter_param):
    current_sorter_param[0]['from_loading'] = True
    
    window[0]['preprocessing_checkbox'].update(disabled=True)
    window[0]['Load_probe_file'].update(disabled=True)
    

    window[0]['Load_ephy_file'].update(button_color='green')
    window[0]['Load_probe_file'].update(button_color='green')
    window[0]['Select_output_folder'].update(button_color='green')
    
    if current_sorter_param[0]['preprocessing']:
        window[0]['preprocessing_checkbox'].update(True)
        if current_sorter_param[0]['preprocessing'] == 'Done':
            SetLED(window, 'led_preprocessing', 'green')
    else:
        window[0]['preprocessing_checkbox'].update(False)
        SetLED(window, 'led_preprocessing', 'red')
    
    if current_sorter_param[0]['preprocessing'] == 'Done':
        SetLED(window, 'led_sorting', 'green')
        window[0]['sorter_combo'].update(value=current_sorter_param[0]['name'])
        
    if current_sorter_param[0]['custom_cleaning'] or current_sorter_param[0]['manual_curation']:
        window[0]['sorter_combo'].update(disabled=True)
        if current_sorter_param[0]['custom_cleaning'] == 'Done':
            SetLED(window, 'led_Custom', 'green')
        
        window[0]['custom_cleaning_checkbox'].update(True)
        window[0]['custom_cleaning_checkbox'].update(disabled=True)
        if current_sorter_param[0]['manual_curation']:
            if current_sorter_param[0]['manual_curation'] == 'Done':
                SetLED(window, 'led_Manual', 'green')
            window[0]['manual_curation_checkbox'].update(True)
            window[0]['manual_curation_checkbox'].update(disabled=True)
        else:
            window[0]['manual_curation_checkbox'].update(False)
            window[0]['manual_curation_checkbox'].update(disabled=False)
    else:
        window[0]['custom_cleaning_checkbox'].update(False)
        window[0]['manual_curation_checkbox'].update(False)

def unlock_analysis(window, current_sorter_param):

    current_sorter_param[0]['sorting'] = True
    current_sorter_param[0]['custom_cleaning'] = window[0]['custom_cleaning_checkbox'].get()
    current_sorter_param[0]['manual_curation'] = window[0]['manual_curation_checkbox'].get()
    
    if not current_sorter_param[0]['preprocessing']:
        SetLED(window, 'led_preprocessing', 'preprocessing')
    if not current_sorter_param[0]['sorting']:
        SetLED(window, 'led_sorting', 'red')

    window[0]['Load_probe_file'].update(disabled=False)
    
    if not current_sorter_param[0]['custom_cleaning']:
        SetLED(window, 'led_Custom', 'red')
        window[0]['sorter_combo'].update(disabled=False)
        window[0]['custom_cleaning_checkbox'].update(disabled=False)
    if not current_sorter_param[0]['manual_curation']:
        SetLED(window, 'led_Manual', 'red')  
        window[0]['sorter_combo'].update(disabled=False)
        window[0]['custom_cleaning_checkbox'].update(disabled=False)
        window[0]['manual_curation_checkbox'].update(disabled=False)
    
def make_window(current_sorter_param):
    
    sorter_param_dict =  make_sorter_param_dict()
    
    main_menu_layout = [['File', ['Load analysis', 'Export spike time', 'Export Template']], 
                        ['Edit',['Import metadata', 'Ephy file tool', 'Probe tool']],
                        ['Parameters',['Preprocessing parameter', 'Sorter parameter', 'Custom cleaning parameter']],
                        ]
    
    if current_sorter_param[0]['ephy_file_path'] is None:
        ephy_file_button = sg.B("Load ephy file", k="Load_ephy_file", button_color='red', enable_events=True)
    else:
        ephy_file_button = sg.B("Load ephy file", k="Load_ephy_file", button_color='green', enable_events=True)
    
    if current_sorter_param[0]['probe_file_path'] is None:
        probe_file_button = sg.B("Load probe file", k="Load_probe_file", button_color='red', enable_events=True)
    else:
        probe_file_button = sg.B("Load probe file", k="Load_probe_file", button_color='green', enable_events=True)
    
    if current_sorter_param[0]['output_folder_path'] is None:
        output_folder_button = sg.B("Select output folder", k='Select_output_folder', button_color='red', enable_events=True)
    else:
        output_folder_button = sg.B("Select output folder", k='Select_output_folder', button_color='green', enable_events=True)
    
    if current_sorter_param[0]['name'] is None:
        sorter_row = [LEDIndicator('led_sorting'), sg.T('Select Sorter'), sg.Combo(list(sorter_param_dict.keys()), k='sorter_combo', enable_events=True)]
    else:
        sorter_row = [LEDIndicator('led_sorting'), sg.T('Select Sorter'), sg.Combo(list(sorter_param_dict.keys()), default_value=current_sorter_param[0]['name'], k='sorter_combo', enable_events=True)]
    
    layout = [[sg.Menu(main_menu_layout, key='main_menu')],
              [ephy_file_button, probe_file_button, output_folder_button],
              [LEDIndicator('led_preprocessing'), sg.T('Preprocess recoding'), sg.Checkbox('', k='preprocessing_checkbox', enable_events=True, default=current_sorter_param[0]["preprocessing"])],
              sorter_row,
              [LEDIndicator('led_Custom'), sg.T('Perform custom cleaning'), sg.Checkbox('', k='custom_cleaning_checkbox', enable_events=True, default=current_sorter_param[0]["custom_cleaning"])],
              [LEDIndicator('led_Manual'), sg.T('Perform manual curation'), sg.Checkbox('', k='manual_curation_checkbox', enable_events=True, default=current_sorter_param[0]["manual_curation"])],
              [sg.pin(sg.Column(
                                [[sg.I('', readonly=True, k='manual_curation_outputlink_input', size=(27,2)),
                                  sg.B('Open to browser', k='open_manual_curation_outputlink_button', disabled=True), ],
                                 [sg.I('', k='manual_curation_inputlink_input', size=(27,2)), 
                                  sg.B('Continue', k='continue_manual_curation_inputlink_button', disabled=True, tooltip='Generate a new curation link to continue manual curation'), 
                                  sg.B('Accept', k='accept_manual_curation_inputlink_button', disabled=True, tooltip='Accept the current link has final and stop manual curation')]]
                                , k='manual_cleaning_input_column', visible=current_sorter_param[0]["manual_curation"]))],
              [sg.B('Launch Sorting', k='launch_sorting_button', ), 
               # sg.B('Debug', k='debug_button'), 
               sg.T('', k='progress_text'), sg.ProgressBar(100, key='progress_bar', visible=False, size=(5, 2))]
             ]
    
    return sg.Window('Spike sorting GUI', layout, finalize=True), sorter_param_dict
   
def main_gui_maker(main_window, state, current_sorter_param, ephy_extension_dict):
   sg.theme('DarkBlue')
   main_window[0], sorter_param_dict = make_window(current_sorter_param)
   SetLED(main_window, 'led_preprocessing', 'red')
   SetLED(main_window, 'led_sorting', 'red')
   SetLED(main_window, 'led_Custom', 'red')
   SetLED(main_window, 'led_Manual', 'red')
   
   config_preprocessing_param_window = None
   config_sorter_param_window = None
   config_custom_cleaning_param_window = None
   while True:
        window, event, values = sg.read_all_windows()
        
        if state[0] == 'stop':
            main_window[0].close()
            try:
                config_sorter_param_window.close()
            except AttributeError:
                pass
            try:
                config_custom_cleaning_param_window.close()
            except AttributeError:
                pass
            break
        
        if window == config_preprocessing_param_window:
            preprocessing_event_handler(window, values, event, current_sorter_param, state)
        
        if window == config_custom_cleaning_param_window:
            custom_cleaning_event_handler(window, values, event, current_sorter_param, state)
        
        elif window == config_sorter_param_window:
            sorting_param_event_handler(window, values, event, current_sorter_param, state)
        
        elif event in ['manual_curation_outputlink_input', 'open_manual_curation_outputlink_button', 'continue_manual_curation_inputlink_button', 'accept_manual_curation_inputlink_button', 'manual_cleaning_input_column']:
            manual_curation_event_handler(window, values, event, current_sorter_param, state)
        
        elif window == main_window[0]:
            
            if event == sg.WIN_CLOSED:
                if window == config_sorter_param_window:
                    config_sorter_param_window = None
                elif window == config_custom_cleaning_param_window:
                    config_custom_cleaning_param_window = None
                if window == main_window[0]:
                    try:
                        config_sorter_param_window.close()
                    except AttributeError:
                        pass
                    try:
                        config_custom_cleaning_param_window.close()
                    except AttributeError:
                        pass
                    state[0] = 'stop'
                    window.close()
                    break
            
            if state[0] is not None and event in ['Load analysis', 'Load_ephy_file', 'Load_probe_file', 'Select_output_folder', 'sorter_combo', 'launch_sorting_button']:
                if event == 'sorter_combo':
                    main_window[0]['sorter_combo'].update(current_sorter_param[0]['name'])
                sg.popup_error('Parameters can not while a analysis is in progress')
            
            else:
                if event == 'Load analysis':
                    state[0] = 'Load analysis'
                    
                if event == 'Load_ephy_file':
                    path = select_folder_file(mode='file')
                    if path is not None:
                        if path.split('.')[-1] not in ephy_extension_dict.keys():
                            sg.popup_error(f"Unsuported ephy file format: {path.split('.')[-1]}")
                            if current_sorter_param[0]['from_loading'] is None:
                                main_window[0]['Load_ephy_file'].update(button_color='red')
                        else:
                            current_sorter_param[0]['ephy_file_extension'] = path.split('.')[-1]
                            current_sorter_param[0]['ephy_file_path'] = path
                            main_window[0]['Load_ephy_file'].update(button_color='green')
                            if current_sorter_param[0]['from_loading'] is not None:
                                current_sorter_param[0]['from_loading'] = None
                                unlock_analysis(main_window, current_sorter_param)
                                main_window[0]['Load_probe_file'].update(button_color='red')
                                main_window[0]['Select_output_folder'].update(button_color='red')
                                del current_sorter_param[0]['probe_file_path'], current_sorter_param[0]['output_folder_path']
                                
                        
                if event == 'Load_probe_file':
                    path = select_folder_file(mode='file')
                    if path is not None:
                        if path.split('.')[-1] != 'json':
                            sg.popup_error(f"Unsuported probe file format: {path.split('.')[-1]}")
                            main_window[0]['Load_probe_file'].update(button_color='red')
                        else:
                            current_sorter_param[0]['probe_file_path'] = path
                            main_window[0]['Load_probe_file'].update(button_color='green')
                
                if event == 'Select_output_folder':
                    path = select_folder_file(mode='folder')
                    if path is not None:
                        current_sorter_param[0]['output_folder_path'] = path
                        main_window[0]['Select_output_folder'].update(button_color='green')
                    else:
                        main_window[0]['Select_output_folder'].update(button_color='red')
                
                if event == 'sorter_combo':
                    if current_sorter_param[0]['name'] != values['sorter_combo'] and current_sorter_param[0]['from_loading'] is not None:
                        unlock_analysis(main_window, current_sorter_param)
                    current_sorter_param[0]['name'] = values['sorter_combo']
                    current_sorter_param[0]['sorting_param'] = sorter_param_dict[values['sorter_combo']]['param'] 
                
                if event == 'Sorter parameter':
                    if values['sorter_combo'] == '':
                        sg.popup_error('Please select a sorter')
                    else:
                        config_sorter_param_window = configure_sorter_param(current_sorter_param[0]['name'], sorter_param_dict[current_sorter_param[0]['name']]['param_description'] , current_sorter_param[0]['sorting_param'])
                
                if event == 'preprocessing_checkbox':
                    current_sorter_param[0]['preprocessing'] = values['preprocessing_checkbox']
                
                if event == 'Preprocessing parameter':
                    config_preprocessing_param_window = make_config_preprocessing_param_window(current_sorter_param[0]['preprocessing_param'])
                
                if event == 'custom_cleaning_checkbox':
                    current_sorter_param[0]['custom_cleaning'] = values['custom_cleaning_checkbox']
                
                if event == 'Custom cleaning parameter':
                    config_custom_cleaning_param_window = make_config_custom_cleaning_param_window(current_sorter_param[0]['custom_cleaning_param'])
                    
                if event == 'manual_curation_checkbox':
                    current_sorter_param[0]['manual_curation'] = values['manual_curation_checkbox']

                if event == 'launch_sorting_button':
                    if current_sorter_param[0]['name'] is None:
                        sg.popup_error('Please select a sorter')
                    elif current_sorter_param[0]['ephy_file_path'] is None:
                        sg.popup_error('Please select a ephy file')
                    elif current_sorter_param[0]['probe_file_path'] is None:
                        sg.popup_error('Please select a probe file')
                    elif current_sorter_param[0]['output_folder_path'] is None:
                        sg.popup_error('Please select a output folder')
                    else:
                        if current_sorter_param[0]['from_loading'] is None:
                            SetLED(main_window, 'led_preprocessing', 'red')
                            SetLED(main_window, 'led_sorting', 'red')
                            SetLED(main_window, 'led_Custom', 'red')
                            SetLED(main_window, 'led_Manual', 'red')
                        lock_analysis(main_window, current_sorter_param)
                        state[0] = 'launch'
            
            if event == 'popup_error':
                sg.popup_error(values['popup_error'])
            if event == 'debug_button':
                lock_analysis(main_window, 'sorting', current_sorter_param)
                # print('\n')
                # print(current_sorter_param[0])
                # print(sorter[0], analyzer[0], recording[0])
                # current_sorter_param[0]['from_loading'] = False
                # current_sorter_param[0]['bandpass'] = [True, 300, 600]
                # current_sorter_param[0]['comon_ref'] = True
                # current_sorter_param[0]['custom_cleaning'] = False
                # current_sorter_param[0]['manual_curation'] = False
                # with open(r"C:\code\spike_sorting\additional/default_param.json", "w") as outfile: 
                #     json.dump(current_sorter_param[0], outfile)