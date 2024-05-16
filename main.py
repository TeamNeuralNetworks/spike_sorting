# -*- coding: utf-8 -*-
"""
Created on Tue May  7 10:26:45 2024

@author: Pierre.LE-CABEC
"""
from spikeinterface.extractors import read_intan
from spikeinterface.sorters import run_sorter
from spikeinterface.core import create_sorting_analyzer
from probeinterface.io import read_probeinterface
from spikeinterface.core import load_sorting_analyzer

import threading
import time
import traceback
import json
import datetime
from docker.errors import DockerException
import shutil
import warnings
import os 

from plotting.plot_unit_summary import plot_sorting_summary
from curation.clean_unit import clean_unit
from curation.manual_curation import manual_curation_module
from curation.preprocessing import apply_preprocessing
from GUIs.Main_GUI import main_gui_maker, led_loading_animation, SetLED, unlock_analysis, lock_analysis, select_folder_file
from additional.toolbox import get_default_param

warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=RuntimeWarning)
warnings.filterwarnings('ignore', category=UserWarning)

ephy_extension_dict = {'rhd': lambda x:read_intan(x, stream_id='0'),
                       }

default_param = {}


def load_analysis(window, current_sorter_param):
    path = select_folder_file(mode='folder')
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
            window[0].write_event_value('popup_error', 'No anlysis pipeline find')
            return None
        
        try:
            analyzer = load_sorting_analyzer(folder=fr'{path}\SortingAnalyzer')
            with open(fr'{path}/pipeline_param.json', 'r') as file:
                 current_sorter_param[0] = json.load(file)
                 
            if mode == 'base sorting': 
                current_sorter_param[0]["manual_curation_param"]['from_loading'] = True
            else:
                current_sorter_param[0]["manual_curation_param"]['from_loading'] = False
                
        except:
            window[0].write_event_value('popup_error', 'Unable to load analysis')
            return  None
        else:
            lock_analysis(window, current_sorter_param) 
            return analyzer

def launch_sorting(current_sorter_param, main_window, state, analyzer):
    
    try:
               
        led_loading_animation_thread = threading.Thread(target=led_loading_animation, args=(state, main_window))
        led_loading_animation_thread.start()
        
        current_time = datetime.datetime.now()

        current_sorter_param[0]['time of analysis'] = current_time.strftime("%Y-%m-%d %H:%M:%S")
        
        #############################################
        recording = ephy_extension_dict[current_sorter_param[0]['ephy_file_extension']](current_sorter_param[0]['ephy_file_path'])
        main_window[0]['progress_text'].update('Assigning probe')
        probe = read_probeinterface(current_sorter_param[0]['probe_file_path'])
        probe = probe.probes[0]
        recording = recording.set_probe(probe)
        #############################################
        
        #############################################
        if current_sorter_param[0]['preprocessing'] is True:
            print('\n############## Preprocess recording ##############')
            main_window[0]['progress_text'].update('Preprocess recording')
            state[0] = 'preprocessing'
            apply_preprocessing(recording, current_sorter_param[0]['preprocessing_param'], main_window)
            current_sorter_param[0]['preprocessing'] = 'Done'
            SetLED(main_window, 'led_preprocessing', 'green')
            print('Done')
            print('#############################################')

        #############################################
        if current_sorter_param[0]['sorting'] is True:
            print('\n############## Running sorter ###############')
            main_window[0]['progress_text'].update('Sorting in progress')
            state[0] = 'sorting'
            sorter = run_sorter(sorter_name=current_sorter_param[0]['name'], recording=recording, docker_image=True, 
                                          output_folder=f"{current_sorter_param[0]['output_folder_path']}/{current_sorter_param[0]['name']}/base sorting/SorterOutput", 
                                          verbose=True, 
                                          **current_sorter_param[0]['sorting_param'])
            if len(sorter.get_unit_ids()) == 0:
                main_window[0].write_event_value('popup_error', f"{current_sorter_param[0]['name']} has finished sorting but no units has been found")
                raise ValueError
            analyzer = create_sorting_analyzer(sorting=sorter,
                                                   recording=recording,
                                                   format="binary_folder",
                                                   return_scaled=True, # this is the default to attempt to return scaled
                                                   folder=f"{current_sorter_param[0]['output_folder_path']}/{current_sorter_param[0]['name']}/base sorting/SortingAnalyzer", 
                                                   sparse=False
                                                   )
            main_window[0]['progress_text'].update('Sorting Summary plot in progress')
            plot_sorting_summary(analyzer, 
                                 current_sorter_param[0]['name'], 
                                 save_path=f"{current_sorter_param[0]['output_folder_path']}/{current_sorter_param[0]['name']}/base sorting", 
                                 trial_len=recording.get_duration(), 
                                 acelerate=False,)
            current_sorter_param[0]['sorting'] = 'Done'
            
            with open(f"{current_sorter_param[0]['output_folder_path']}/{current_sorter_param[0]['name']}/base sorting/pipeline_param.json", "w") as outfile: 
                json.dump(current_sorter_param[0], outfile)
                
            SetLED(main_window, 'led_sorting', 'green')
            print('Done')
            print('#############################################')
        
        
        #############################################
        if current_sorter_param[0]['custom_cleaning'] is True:
            print('\n############## Custom cleaning ##############')
            main_window[0]['progress_text'].update('Custom cleaning in progress')
            state[0] = 'Custom'
            analyzer = clean_unit(analyzer, current_sorter_param[0]['custom_cleaning_param'], main_window[0],
                                    save_folder=f"{current_sorter_param[0]['output_folder_path']}/{current_sorter_param[0]['name']}/custom cleaning",
                                    sorter_name=current_sorter_param[0]['name'], 
                                    save_plot=f"{current_sorter_param[0]['output_folder_path']}/{current_sorter_param[0]['name']}/custom cleaning") 
            
            main_window[0]['progress_text'].update('Sorting Summary plot in progress')
            plot_sorting_summary(analyzer, 
                                 current_sorter_param[0]['name'], 
                                 save_path=f"{current_sorter_param[0]['output_folder_path']}/{current_sorter_param[0]['name']}/custom cleaning", 
                                 trial_len=recording.get_duration(), 
                                 acelerate=False,)
            
            current_sorter_param[0]['custom_cleaning'] = 'Done'            
            with open(f"{current_sorter_param[0]['output_folder_path']}/{current_sorter_param[0]['name']}/custom cleaning/pipeline_param.json", "w") as outfile: 
                json.dump(current_sorter_param[0], outfile)
            
            SetLED(main_window, 'led_Custom', 'green')
            print('Done')
            print('#############################################')
        
        
        #############################################
        if current_sorter_param[0]['manual_curation'] is True or current_sorter_param[0]['manual_curation'] == 'Done':
            print('\n############## Manual curation ##############')
            state[0] = 'Manual'
            analyzer = manual_curation_module(analyzer, 
                                                f"{current_sorter_param[0]['output_folder_path']}/{current_sorter_param[0]['name']}/manual curation", 
                                                current_sorter_param, 
                                                trial_len=recording.get_duration(),
                                                window = main_window[0]
                                                )
            current_sorter_param[0]['manual_curation'] = 'Done'
            with open(f"{current_sorter_param[0]['output_folder_path']}/{current_sorter_param[0]['name']}/manual curation/pipeline_param.json", "w") as outfile: 
                json.dump(current_sorter_param[0], outfile)
            
            SetLED(main_window, 'led_Manual', 'green')
            print('Done')
            print('#############################################')
        state[0] = None
        
        main_window[0]['progress_text'].update(f'Analysis pipeline is done: {len(analyzer.unit_ids)} unit has been found')
        
    except Exception as e:
        print('\n')
        traceback.print_exc()
        if state[0] is not None:
            error_stage = state[0]
            SetLED(main_window, f'led_{state[0]}', 'orange')
            state[0] = None
            
            if error_stage == 'preprocessing':
                current_sorter_param[0]['preprocessing'] = False
                current_sorter_param[0]['sorting'] = False
                current_sorter_param[0]['custom_cleaning'] = False
                current_sorter_param[0]['manual_curation'] = False
            elif error_stage == 'sorting':
                current_sorter_param[0]['sorting'] = False
                current_sorter_param[0]['custom_cleaning'] = False
                current_sorter_param[0]['manual_curation'] = False
                shutil.rmtree(f"{current_sorter_param[0]['output_folder_path']}/{current_sorter_param[0]['name']}/base sorting")
            elif error_stage == 'Custom':
                current_sorter_param[0]['custom_cleaning'] = False
                current_sorter_param[0]['manual_curation'] = False
                with open(f"{current_sorter_param[0]['output_folder_path']}/{current_sorter_param[0]['name']}/base sorting/pipeline_param.json", "w") as outfile: 
                    json.dump(current_sorter_param[0], outfile)
                shutil.rmtree(f"{current_sorter_param[0]['output_folder_path']}/{current_sorter_param[0]['name']}/custom cleaning")
            elif error_stage == 'Manual':
                current_sorter_param[0]['manual_curation'] = False
                with open(f"{current_sorter_param[0]['output_folder_path']}/{current_sorter_param[0]['name']}/custom cleaning/pipeline_param.json", "w") as outfile: 
                    json.dump(current_sorter_param[0], outfile)
                if not current_sorter_param[0]["manual_curation_param"]['from_loading']:
                    shutil.rmtree(f"{current_sorter_param[0]['output_folder_path']}/{current_sorter_param[0]['name']}/manual curation")
                
            unlock_analysis(main_window, current_sorter_param)
        
        
        
        if isinstance(e, DockerException):
            main_window[0].write_event_value('popup_error', "Docker Desktop need to be open for sorting")
            
def sorting_main():
    
    state = [None]
    main_window = [None]
    current_sorter_param = [get_default_param()]
    analyzer = None
    
    gui_thread = threading.Thread(target=main_gui_maker, args=(main_window, state, current_sorter_param, ephy_extension_dict))
    gui_thread.start()
    
    while True:
        if state[0] == 'stop':
            break
        elif state[0] == 'Load analysis':
            analyzer = load_analysis(main_window, current_sorter_param)
            state[0] = None
        
        elif state[0] == 'launch': 
            main_window[0]['launch_sorting_button'].update('Sorting in porgress')
            main_window[0]['launch_sorting_button'].update(disabled=True)

            launch_sorting(current_sorter_param, main_window, state, analyzer)
            
            main_window[0]['launch_sorting_button'].update('Launch Sorting')
            main_window[0]['launch_sorting_button'].update(disabled=False)
            
        else:
            time.sleep(0.1)
        

if __name__ == "__main__":
    sorting_main()