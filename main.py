# -*- coding: utf-8 -*-
"""
Created on Tue May  7 10:26:45 2024

@author: Pierre.LE-CABEC
"""
from spikeinterface.extractors import read_intan
from spikeinterface.sorters import run_sorter
from spikeinterface.preprocessing import bandpass_filter, common_reference
from spikeinterface.core import create_sorting_analyzer
from probeinterface.io import read_probeinterface

import threading
import time
import traceback
import json
import datetime
from docker.errors import DockerException
import shutil
import warnings

from plotting.plot_unit_summary import plot_sorting_summary
from curation.clean_unit import clean_unit
from curation.manual_curation import manual_curation_module
from GUIs.Main_GUI import main_gui_maker, led_loading_animation, SetLED, trigger_popup_error, unlock_analysis
from additional.toolbox import get_default_param

warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=RuntimeWarning)
warnings.filterwarnings('ignore', category=UserWarning)

ephy_extension_dict = {'rhd': lambda x:read_intan(x, stream_id='0'),
                       }

default_param = {}


def launch_sorting(current_sorter_param, main_window, state, recording, sorter, analyser):
    
    try:
               
        led_loading_animation_thread = threading.Thread(target=led_loading_animation, args=(state, main_window))
        led_loading_animation_thread.start()
        
        current_time = datetime.datetime.now()

        current_sorter_param[0]['time of analysis'] = current_time.strftime("%Y-%m-%d %H:%M:%S")
        
        #############################################
        if current_sorter_param[0]['bandpass'][0] is True:
            print('\n############## BandPass filter ##############')
            state[0] = 'bandpass'
            recording[0] = bandpass_filter(recording[0], freq_min=int(current_sorter_param[0]['bandpass'][1]), freq_max=int(current_sorter_param[0]['bandpass'][2]))
            SetLED(main_window, 'led_bandpass', 'green')
            current_sorter_param[0]['bandpass'][0] = 'Done'
            print('Done')
            print('#############################################')
        
        #############################################
        if current_sorter_param[0]['comon_ref'] is True:
            print('\n############# Comon ref removal #############')
            state[0] = 'comon_ref'
            recording[0] = common_reference(recording[0], reference='global', operator='median')
            SetLED(main_window, 'led_comon_ref', 'green')
            current_sorter_param[0]['comon_ref'] = 'Done'
            print('Done')
            print('#############################################')
        recording[0].annotate(is_filtered=True)
            
        
        #############################################
        if current_sorter_param[0]['probe_assign'] is True:
            print('\n############# Probe assignement #############')
            probe = read_probeinterface(current_sorter_param[0]['probe_file_path'])
            probe = probe.probes[0]
            recording[0] = recording[0].set_probe(probe)
            current_sorter_param[0]['probe_assign'] = 'Done'
            print('Done')
            print('############################################n')
        
        #############################################
        if current_sorter_param[0]['sorting'] is True:
            print('\n############## Running sorter ###############')
            state[0] = 'sorting'
            sorter[0] = run_sorter(sorter_name=current_sorter_param[0]['name'], recording=recording[0], docker_image=True, 
                                          output_folder=f"{current_sorter_param[0]['output_folder_path']}/{current_sorter_param[0]['name']}/base sorting/SorterOutput", 
                                          verbose=True, 
                                          **current_sorter_param[0]['sorting_param'])
            if len(sorter[0].get_unit_ids()) == 0:
                trigger_popup_error(f"{current_sorter_param[0]['name']} has finished sorting but no units has been found")
                raise ValueError
            analyser[0] = create_sorting_analyzer(sorting=sorter[0],
                                                   recording=recording[0],
                                                   format="binary_folder",
                                                   return_scaled=True, # this is the default to attempt to return scaled
                                                   folder=f"{current_sorter_param[0]['output_folder_path']}/{current_sorter_param[0]['name']}/base sorting/SortingAnalyzer", 
                                                   )
            plot_sorting_summary(analyser[0], 
                                 current_sorter_param[0]['name'], 
                                 save_path=f"{current_sorter_param[0]['output_folder_path']}/{current_sorter_param[0]['name']}/base sorting", 
                                 trial_len=recording[0].get_duration(), 
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
            state[0] = 'Custom'
            analyser[0] = clean_unit(analyser[0], current_sorter_param[0]['custom_cleaning_param'],
                                    save_folder=f"{current_sorter_param[0]['output_folder_path']}/{current_sorter_param[0]['name']}/custom cleaning",
                                    sorter_name=current_sorter_param[0]['name'], 
                                    save_plot=f"{current_sorter_param[0]['output_folder_path']}/{current_sorter_param[0]['name']}/custom cleaning") 
            
            plot_sorting_summary(analyser[0], 
                                 current_sorter_param[0]['name'], 
                                 save_path=f"{current_sorter_param[0]['output_folder_path']}/{current_sorter_param[0]['name']}/custom cleaning", 
                                 trial_len=recording[0].get_duration(), 
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
            analyser[0], sorter[0], analyser_path = manual_curation_module(analyser[0], 
                                                                             sorter[0], 
                                                                             recording[0], 
                                                                             f"{current_sorter_param[0]['output_folder_path']}/{current_sorter_param[0]['name']}/manual curation", 
                                                                             current_sorter_param[0]['name'], 
                                                                             delay=None, 
                                                                             mouse='', 
                                                                             trial_len=recording[0].get_duration()
                                                                             )
            current_sorter_param[0]['manual_curation'] = 'Done'
            with open(f"{current_sorter_param[0]['output_folder_path']}/{current_sorter_param[0]['name']}/manual curation/pipeline_param.json", "w") as outfile: 
                json.dump(current_sorter_param[0], outfile)
            
            SetLED(main_window, 'led_Manual', 'green')
            print('Done')
            print('#############################################')
        state[0] = None
        
    except Exception as e:
        print('\n')
        traceback.print_exc()
        if state[0] is not None:
            SetLED(main_window, f'led_{state[0]}', 'orange')

        if state[0] == 'sorting':
            shutil.rmtree(f"{current_sorter_param[0]['output_folder_path']}/{current_sorter_param[0]['name']}/base sorting")
            
        elif state[0] == 'Custom':
            current_sorter_param[0]['custom_cleaning'] = False
            with open(f"{current_sorter_param[0]['output_folder_path']}/{current_sorter_param[0]['name']}/base sorting/pipeline_param.json", "w") as outfile: 
                json.dump(current_sorter_param[0], outfile)
            shutil.rmtree(f"{current_sorter_param[0]['output_folder_path']}/{current_sorter_param[0]['name']}/custom cleaning")
        
        elif state[0] == 'Manual':
            current_sorter_param[0]['manual_curation'] = False
            with open(f"{current_sorter_param[0]['output_folder_path']}/{current_sorter_param[0]['name']}/custom cleaning/pipeline_param.json", "w") as outfile: 
                json.dump(current_sorter_param[0], outfile)
            shutil.rmtree(f"{current_sorter_param[0]['output_folder_path']}/{current_sorter_param[0]['name']}/manual curation")
            
        unlock_analysis(main_window, current_sorter_param)
        
        state[0] = None
        if isinstance(e, DockerException):
            trigger_popup_error('Docker Desktop need to be open first')
            
def sorting_main():
    
    state = [None]
    main_window = [None]
    current_sorter_param = [get_default_param()]
    recording = [None]
    sorter = [None]
    analyser = [None]
    
    gui_thread = threading.Thread(target=main_gui_maker, args=(main_window, state, current_sorter_param, ephy_extension_dict, recording, sorter, analyser))
    gui_thread.start()
    # main_gui_maker(main_window, state, current_sorter_param, ephy_extension_dict, recording, sorter, analyser)
    
    while True:
        while state[0] is None:
            time.sleep(0.1)
        
        if state[0] == 'stop':
            break
        
        main_window[0]['launch_sorting_button'].update('Sorting in porgress')
        main_window[0]['launch_sorting_button'].update(disabled=True)
        
        recording[0] = ephy_extension_dict[current_sorter_param[0]['ephy_file_extension']](current_sorter_param[0]['ephy_file_path'])
        
        launch_sorting(current_sorter_param, main_window, state, recording, sorter, analyser)
        
        main_window[0]['launch_sorting_button'].update('Launch Sorting')
        main_window[0]['launch_sorting_button'].update(disabled=False)
        

if __name__ == "__main__":
    sorting_main()