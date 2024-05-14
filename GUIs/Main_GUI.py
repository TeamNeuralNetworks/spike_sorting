# -*- coding: utf-8 -*-
"""
Created on Mon May 13 15:24:47 2024

@author: _LMT
"""
import spikeinterface as si  # import core only
import spikeinterface.extractors as se

from GUIs.sorter_params_GUI import make_sorter_param_dict, sorting_param_event_handler, configure_sorter_param
from GUIs.custom_cleaning_GUI import make_config_custom_cleaning_param_window, custom_cleaning_event_handler, default_custom_cleaning_parameters_dict
import PySimpleGUI as sg
import time
import tkinter as tk
from tkinter import filedialog
import os

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

def load_analysis(window, recording, sorter, analyser, current_sorter_param):
    path = select_folder()
    if path is not None:
        folder_list = os.listdir(path)
        if 'base sorting' in folder_list:
           SetLED(window, 'led_bandpass', 'green')
           SetLED(window, 'led_comon_ref', 'green')
           SetLED(window, 'led_sorting', 'green')
           
           sorter[0] = se.NpzSortingExtractor.load_from_folder(fr'{path}\base sorting\in_container_sorting')
           recording[0] = analyser[0].recording()
           sorter_name = analyser[0].get_sorting_property()
           current_sorter_param[0]['probe_assign'] = False
           current_sorter_param[0]['sorting'] = False
           current_sorter_param[0]['bandpass'][0] = False
           current_sorter_param[0]['comon_ref'] = False
        # if 'custom cleaning' in folder_list:
        #     SetLED(window, 'led_bandpass', 'green')
        #     SetLED(window, 'led_comon_ref', 'green')
        #     SetLED(window, 'led_Custom', 'green')
        # if 'manual curation' in folder_list:
        #     SetLED(window, 'led_bandpass', 'green')
        #     SetLED(window, 'led_comon_ref', 'green')
        #     SetLED(window, 'led_Manual', 'green')
        
        
        
def make_window():
    
    sorter_param_dict =  make_sorter_param_dict()
    
    main_menu_layout = [['File', ['Load analysis']]]
    
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
   
def main_gui_maker(main_window, state, current_sorter_param, ephy_extension_dict, recording, sorter, analyser):
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
                load_analysis(window, recording, sorter, analyser, current_sorter_param)

            if event == 'ephy_file_input':
                if values['ephy_file_input'].split('.')[-1] not in ephy_extension_dict.keys():
                    sg.popup_error(f"Unsuported ephy file format: {values['ephy_file_input'].split('.')[-1]}")
                    main_window[0]['Load_ephy_file'].update(button_color='red')
                else:
                    current_sorter_param[0]['ephy_file_reading_function'] = ephy_extension_dict[values['ephy_file_input'].split('.')[-1]]
                    current_sorter_param[0]['ephy_file_path'] = values['ephy_file_input'] 
                    main_window[0]['Load_ephy_file'].update(button_color='green')
                    
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
                SetLED(main_window, 'led_bandpass', 'red')
                SetLED(main_window, 'led_comon_ref', 'red')
                SetLED(main_window, 'led_sorting', 'red')
                SetLED(main_window, 'led_Custom', 'red')
                SetLED(main_window, 'led_Manual', 'red')
                if 'name' not in current_sorter_param[0].keys():
                    sg.popup_error('Please select a sorter')
                elif 'ephy_file_path' not in current_sorter_param[0].keys():
                    sg.popup_error('Please select a ephy file')
                elif 'probe_file_path' not in current_sorter_param[0].keys():
                    sg.popup_error('Please select a probe file')
                elif 'output_folder_path' not in current_sorter_param[0].keys():
                    sg.popup_error('Please select a output folder')
                else:
                    current_sorter_param[0]['bandpass'] = [values['bandpass_checkbox'], values['low_bandpass_input'], values['high_bandpass_input']]
                    current_sorter_param[0]['comon_ref'] = values['comon_ref_checkbox']
                    current_sorter_param[0]['custom_cleaning'] = values['custom_cleaning_checkbox']
                    current_sorter_param[0]['manual_curation'] = values['manual_curation_checkbox']
                    state[0] = 'launch'
            
            if event == 'debug_button':
                print('\n')
                print(sorter[0], analyser[0], recording[0])