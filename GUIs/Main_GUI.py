# -*- coding: utf-8 -*-
"""
Created on Mon May 13 15:24:47 2024

@author: _LMT
"""
from spikeinterface.core import load_sorting_analyzer

from GUIs.sorter_params_GUI import make_sorter_param_dict, sorting_param_event_handler, configure_sorter_param
from GUIs.custom_cleaning_GUI import make_config_custom_cleaning_param_window, custom_cleaning_event_handler, default_custom_cleaning_parameters_dict
import PySimpleGUI as sg
import time
import tkinter as tk
from tkinter import filedialog
import os
import json

def trigger_popup_error(message):
    sg.popup_error(message)

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

def select_folder():
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    folder_path = filedialog.askdirectory()
    if folder_path:
        return folder_path
    else:
        return None


def lock_analysis(window, mode, current_sorter_param):
    current_sorter_param[0]['from_loading'] = True
    
    window[0]['Load_ephy_file'].update(button_color='green')
    window[0]['Load_probe_file'].update(button_color='green')
    window[0]['Load_probe_file'].update(disabled=True)
    window[0]['Select_output_folder'].update(button_color='green')
    window[0]['sorter_param_button'].update(button_color='green')
    window[0]['sorter_param_button'].update(disabled=True)
    
    
    
    window[0]['bandpass_checkbox'].update(disabled=True)
    window[0]['high_bandpass_input'].update(disabled=True)
    window[0]['low_bandpass_input'].update(disabled=True)
    if current_sorter_param[0]['bandpass'][0]:
        SetLED(window, 'led_bandpass', 'green')
        window[0]['low_bandpass_input'].update(current_sorter_param[0]['bandpass'][1])
        window[0]['high_bandpass_input'].update(current_sorter_param[0]['bandpass'][2])
        window[0]['bandpass_checkbox'].update(True)
    else:
        SetLED(window, 'led_bandpass', 'red')
        window[0]['bandpass_checkbox'].update(False)
    current_sorter_param[0]['bandpass'][0] = False
    
    
    window[0]['comon_ref_checkbox'].update(disabled=True)
    if current_sorter_param[0]['comon_ref']:
        window[0]['comon_ref_checkbox'].update(True)
        SetLED(window, 'led_comon_ref', 'green')
    else:
        window[0]['comon_ref_checkbox'].update(False)
        SetLED(window, 'led_comon_ref', 'red')
    current_sorter_param[0]['comon_ref'] = False

    current_sorter_param[0]['probe_assign'] = False
    
    SetLED(window, 'led_sorting', 'green')
    current_sorter_param[0]['sorting'] = False
    window[0]['sorter_combo'].update(value=current_sorter_param[0]['name'])
    window[0]['sorter_combo'].update(disabled=True)
    
    if mode == 'custom cleaning' or mode == 'manual curation':
        SetLED(window, 'led_Custom', 'green')
        current_sorter_param[0]['custom_cleaning'] = False
        window[0]['custom_cleaning_button'].update(disabled=True)
        window[0]['custom_cleaning_checkbox'].update(True)
        window[0]['custom_cleaning_checkbox'].update(disabled=True)
        if mode == 'manual curation':
            SetLED(window, 'led_Manual', 'green')
            current_sorter_param[0]['manual_curation'] = False
            window[0]['manual_curation_checkbox'].update(True)
            window[0]['manual_curation_checkbox'].update(disabled=True)
        else:
            window[0]['manual_curation_checkbox'].update(False)
            window[0]['manual_curation_checkbox'].update(disabled=True)
    else:
        window[0]['custom_cleaning_checkbox'].update(False)
        window[0]['manual_curation_checkbox'].update(False)

def unlock_analysis(window, current_sorter_param):
    
    window[0]['comon_ref_checkbox'].update(disabled=False)
    window[0]['bandpass_checkbox'].update(disabled=False)
    window[0]['bandpass_checkbox'].update(disabled=False)
    window[0]['high_bandpass_input'].update(disabled=False)
    window[0]['low_bandpass_input'].update(disabled=False)
    window[0]['sorter_param_button'].update(disabled=False)
    window[0]['Load_probe_file'].update(disabled=False)
    window[0]['custom_cleaning_checkbox'].update(False)
    window[0]['custom_cleaning_checkbox'].update(disabled=False)
    window[0]['manual_curation_checkbox'].update(False)
    window[0]['manual_curation_checkbox'].update(disabled=False)

    window[0]['sorter_combo'].update(disabled=False)
    window[0]['sorter_combo'].update('')
    
    window[0]['Load_probe_file'].update(button_color='red')
    window[0]['Select_output_folder'].update(button_color='red')
    window[0]['sorter_param_button'].update(button_color='red')

    
    window[0]['custom_cleaning_checkbox'].update(False)
    window[0]['manual_curation_checkbox'].update(False)
    
    SetLED(window, 'led_bandpass', 'red')
    SetLED(window, 'led_comon_ref', 'red')
    SetLED(window, 'led_sorting', 'red')
    SetLED(window, 'led_Custom', 'red')
    SetLED(window, 'led_Manual', 'red')
    del current_sorter_param[0]['probe_file_path'], current_sorter_param[0]['output_folder_path'], current_sorter_param[0]['name']
    
    
def load_analysis(window, recording, sorter, analyzer, current_sorter_param):
    path = select_folder()
    if path is not None:
        folder_list = os.listdir(path)
        if 'manual curation' in folder_list or os.path.basename(path) == 'manual curation':
            mode = 'manual curation'
            if 'manual curation' in folder_list:
                path = fr'{path}\{mode}'
        elif 'custom cleaning' in folder_list or os.path.basename(path) == 'custom cleaning':
            mode = 'custom cleaning'
            if 'custom cleaning' in folder_list:
                path = fr'{path}\{mode}'

        elif 'base sorting' in folder_list or os.path.basename(path) == 'base sorting':
            mode = 'base sorting'
            if 'base sorting' in folder_list:
                path = fr'{path}\{mode}'
        else:
            sg.popup_error('No anlysis pipeline find')
            return 
        
        analyzer[0] = load_sorting_analyzer(folder=fr'{path}\SortingAnalyzer')
        sorter[0] = analyzer[0].sorting
        recording[0] = analyzer[0].recording
        with open(fr'{path}/pipeline_param.json', 'r') as file:
             current_sorter_param[0] = json.load(file)
     
    lock_analysis(window, mode, current_sorter_param)
        
        
  
def make_window():
    
    sorter_param_dict =  make_sorter_param_dict()
    
    main_menu_layout = [['File', ['Load analysis', 'Export spike time', 'Export Template']], 
                        ['Edit',['Import metadata', 'Ephy file tool', 'Probe tool']]]
    
    layout = [[sg.Menu(main_menu_layout, key='main_menu')],
              [sg.Input('', key='ephy_file_input', size=(30,2), visible=False, enable_events=True), sg.FileBrowse("Load ephy file", k="Load_ephy_file", button_color='red', enable_events=True),
               sg.Input('', key='probe_file_input', size=(30,2), visible=False, enable_events=True), sg.FileBrowse("Load probe file", k="Load_probe_file", button_color='red', enable_events=True),
              sg.Input('', key='output_folder_input', size=(30,2), visible=False, enable_events=True), sg.FolderBrowse("Select output folder", k='Select_output_folder', button_color='red', enable_events=True)],
              [LEDIndicator('led_bandpass'), sg.T('Bandpass'), sg.Input('300', k='low_bandpass_input', size=(5, 2)),sg.T('-'), sg.Input('6000', k='high_bandpass_input', size=(5, 2)), sg.Checkbox('', k='bandpass_checkbox', default=True)],
              [LEDIndicator('led_comon_ref'), sg.T('Comon ref removal'), sg.Checkbox('', k='comon_ref_checkbox', default=True)],
              [LEDIndicator('led_sorting'), sg.T('Select Sorter'), sg.Combo(list(sorter_param_dict.keys()), k='sorter_combo', enable_events=True), sg.B('Sorter Param', k='sorter_param_button', button_color='red')],
              [LEDIndicator('led_Custom'), sg.T('Perform custom cleaning'), sg.Checkbox('', k='custom_cleaning_checkbox', enable_events=True), sg.pin(sg.B('Custom cleaning Param', k='custom_cleaning_button', visible=False))],
              [LEDIndicator('led_Manual'), sg.T('Perform manual curation'), sg.Checkbox('', k='manual_curation_checkbox', enable_events=True)],
              [sg.pin(sg.Column(
                                [[sg.I('', readonly=True, k='manual_curation_outputlink_input', size=(27,2))],
                                 [sg.I('', k='manual_curation_intputlink_input', size=(27,2)), 
                                  sg.B('Continue', k='continue_manual_curation_inputlink_button', disabled=True), 
                                   sg.B('Revert', k='revert_manual_curation_inputlink_button', disabled=True), 
                                  sg.B('Accept', k='accept_manual_curation_inputlink_button', disabled=True)]]
                                , k='manual_cleaning_input_column', visible=False))],
              [sg.B('Launch Sorting', k='launch_sorting_button', ), sg.B('Debug', k='debug_button')]
             ]
    
    return sg.Window('Spike sorting GUI', layout, finalize=True), sorter_param_dict
   
def main_gui_maker(main_window, state, current_sorter_param, ephy_extension_dict, recording, sorter, analyzer):
   sg.theme('DarkBlue')
   main_window[0], sorter_param_dict = make_window()
   SetLED(main_window, 'led_bandpass', 'red')
   SetLED(main_window, 'led_comon_ref', 'red')
   SetLED(main_window, 'led_sorting', 'red')
   SetLED(main_window, 'led_Custom', 'red')
   SetLED(main_window, 'led_Manual', 'red')
   
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
        
        if window == config_custom_cleaning_param_window:
            custom_cleaning_event_handler(window, values, event, current_sorter_param)
        
        elif window == config_sorter_param_window:
            sorting_param_event_handler(window, values, event, current_sorter_param)
        
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
            
            if event == 'Load analysis':
                load_analysis(main_window, recording, sorter, analyzer, current_sorter_param)

            if event == 'ephy_file_input':
                if values['ephy_file_input'].split('.')[-1] not in ephy_extension_dict.keys():
                    sg.popup_error(f"Unsuported ephy file format: {values['ephy_file_input'].split('.')[-1]}")
                    if not current_sorter_param[0]['from_loading']:
                        main_window[0]['Load_ephy_file'].update(button_color='red')
                else:
                    current_sorter_param[0]['ephy_file_extension'] = values['ephy_file_input'].split('.')[-1]
                    current_sorter_param[0]['ephy_file_path'] = values['ephy_file_input'] 
                    main_window[0]['Load_ephy_file'].update(button_color='green')
                    if current_sorter_param[0]['from_loading']:
                       unlock_analysis(main_window, current_sorter_param)
                    
                    current_sorter_param[0]['from_loading'] = False
                    
                    
                    
            if event == 'probe_file_input':
                if values['probe_file_input'].split('.')[-1] != 'json':
                    sg.popup_error(f"Unsuported probe file format: {values['ephy_file_input'].split('.')[-1]}")
                    main_window[0]['Load_probe_file'].update(button_color='red')
                else:
                    current_sorter_param[0]['probe_file_path'] = values['probe_file_input'] 
                    main_window[0]['Load_probe_file'].update(button_color='green')
            
            if event == 'output_folder_input':
                if values['output_folder_input'] != '':
                    current_sorter_param[0]['output_folder_path'] = values['output_folder_input'] 
                    main_window[0]['Select_output_folder'].update(button_color='green')
                else:
                    main_window[0]['Select_output_folder'].update(button_color='red')
            
            if event == 'sorter_combo':
                current_sorter_param[0]['name'] = values['sorter_combo']
                current_sorter_param[0]['sorting_param'] = sorter_param_dict[values['sorter_combo']]['param'] 
                main_window[0]['sorter_param_button'].update(button_color='green')
            
            if event == 'sorter_param_button':
                if values['sorter_combo'] == '':
                    sg.popup_error('Please select a sorter')
                else:
                    config_sorter_param_window = configure_sorter_param(current_sorter_param[0]['name'], sorter_param_dict[current_sorter_param[0]['name']]['param_description'] , current_sorter_param[0]['sorting_param'])
            
            if event == 'custom_cleaning_checkbox':
                if values['custom_cleaning_checkbox']:
                    main_window[0]['custom_cleaning_button'].update(visible=True)
                    current_sorter_param[0]['custom_cleaning_param'] = default_custom_cleaning_parameters_dict
                else:
                    main_window[0]['custom_cleaning_button'].update(visible=False)
                    del current_sorter_param[0]['custom_cleaning_param']
            
            if event == 'custom_cleaning_button':
                config_custom_cleaning_param_window = make_config_custom_cleaning_param_window(current_sorter_param[0]['custom_cleaning_param'])
                
            if event == 'manual_curation_checkbox':
                if values['manual_curation_checkbox']:
                    main_window[0]['manual_cleaning_input_column'].update(visible=True)
                else:
                    main_window[0]['manual_cleaning_input_column'].update(visible=False)

            if event == 'launch_sorting_button':
                
                if 'name' not in current_sorter_param[0].keys():
                    sg.popup_error('Please select a sorter')
                elif 'ephy_file_path' not in current_sorter_param[0].keys():
                    sg.popup_error('Please select a ephy file')
                elif 'probe_file_path' not in current_sorter_param[0].keys():
                    sg.popup_error('Please select a probe file')
                elif 'output_folder_path' not in current_sorter_param[0].keys():
                    sg.popup_error('Please select a output folder')
                else:
                    if not current_sorter_param[0]['from_loading']:
                        SetLED(main_window, 'led_bandpass', 'red')
                        SetLED(main_window, 'led_comon_ref', 'red')
                        SetLED(main_window, 'led_sorting', 'red')
                        SetLED(main_window, 'led_Custom', 'red')
                        SetLED(main_window, 'led_Manual', 'red')
                        current_sorter_param[0]['bandpass'] = [values['bandpass_checkbox'], values['low_bandpass_input'], values['high_bandpass_input']]
                        current_sorter_param[0]['comon_ref'] = values['comon_ref_checkbox']
                    current_sorter_param[0]['custom_cleaning'] = values['custom_cleaning_checkbox']
                    current_sorter_param[0]['manual_curation'] = values['manual_curation_checkbox']
                    state[0] = 'launch'
            
            if event == 'debug_button':
                print('\n')
                print(sorter[0], analyzer[0], recording[0])
                current_sorter_param[0]['from_loading'] = False
                with open(r"C:\Pierre.LE-CABEC\Code Pierre\spike_sorting\aditional/default_param.json", "w") as outfile: 
                    json.dump(current_sorter_param[0], outfile)