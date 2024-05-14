# -*- coding: utf-8 -*-
"""
Created on Tue May  7 10:26:45 2024

@author: Pierre.LE-CABEC
"""
import spikeinterface.extractors as se
import spikeinterface.sorters as ss
import spikeinterface.preprocessing as spre
from spikeinterface.core import create_sorting_analyzer, load_sorting_analyzer
import probeinterface as pi

import threading
import time

from plotting.plot_unit_summary import plot_sorting_summary
from curation.clean_unit import clean_unit
from curation.manual_curation import manual_curation_module
from GUIs.Main_GUI import main_gui_maker, led_loading_animation, SetLED, trigger_popup_error

ephy_extension_dict = {'rhd': lambda x:se.read_intan(x, stream_id='0'),
                       }


def launch_sorting(current_sorter_param, main_window, state, recording, sorter, analyser):
    try:
                
        led_loading_animation_thread = threading.Thread(target=led_loading_animation, args=(state, main_window))
        led_loading_animation_thread.start()
        
        #############################################
        ############## BandPass filter ##############
        if current_sorter_param[0]['bandpass'][0]:
            state[0] = 'bandpass'
            recording[0] = spre.bandpass_filter(recording[0], freq_min=int(current_sorter_param[0]['bandpass'][1]), freq_max=int(current_sorter_param[0]['bandpass'][2]))
            SetLED(main_window, 'led_bandpass', 'green')
        #############################################
        
        #############################################
        ############# Comon ref removal #############
        if current_sorter_param[0]['comon_ref']:
            state[0] = 'comon_ref'
            recording[0] = spre.common_reference(recording[0], reference='global', operator='median')
            SetLED(main_window, 'led_comon_ref', 'green')
        recording[0].annotate(is_filtered=True)
        #############################################
        
        #############################################
        ############# Probe assignement #############
        if current_sorter_param[0]['probe_assign']:
            probe = pi.io.read_probeinterface(current_sorter_param[0]['probe_file_path'])
            probe = probe.probes[0]
            recording[0] = recording[0].set_probe(probe)
        #############################################
        
        #############################################
        ############## Running sorter ###############
        if current_sorter_param[0]['sorting']:
            state[0] = 'sorting'
            sorter[0] = ss.run_sorter(sorter_name=current_sorter_param[0]['name'], recording=recording[0], docker_image=True, 
                                          output_folder=None, verbose=True, **current_sorter_param[0]['sorting_param'])
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
                                 current_sorter_param[0]['name'], None, '', 
                                 save_path=f"{current_sorter_param[0]['output_folder_path']}/{current_sorter_param[0]['name']}/base sorting", 
                                 trial_len=recording[0].get_duration(), 
                                 acelerate=False,)
            SetLED(main_window, 'led_sorting', 'green')
        #############################################
        
        
        #############################################
        ############## Custom cleaning ##############
        if current_sorter_param[0]['custom_cleaning']:
            state[0] = 'Custom'
            analyser[0] = clean_unit(sorter[0], recording[0], current_sorter_param[0]['custom_cleaning_param'],
                            save_folder=f"{current_sorter_param[0]['output_folder_path']}/{current_sorter_param[0]['name']}/custom cleaning",
                            sorter_name=current_sorter_param[0]['name'], 
                            save_plot=f"{current_sorter_param[0]['output_folder_path']}/{current_sorter_param[0]['name']}/custom cleaning") 
            
            plot_sorting_summary(analyser[0], current_sorter_param[0]['name'], 
                                 None, '', 
                                 save_path=f"{current_sorter_param[0]['output_folder_path']}/{current_sorter_param[0]['name']}/custom cleaning", 
                                 trial_len=recording[0].get_duration(), acelerate=False)
            SetLED(main_window, 'led_Custom', 'green')
        #############################################
        
        
        #############################################
        ############## Manual curation ##############
        if current_sorter_param[0]['manual_curation']:
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
            SetLED(main_window, 'led_Manual', 'green')
        #############################################
        
        state[0] = None
    except Exception as e:
        print('\n')
        print(e)
        if state[0] is not None:
            SetLED(main_window, f'led_{state[0]}', 'orange')
        state[0] = None

def sorting_main():
    
    state = [None]
    main_window = [None]
    current_sorter_param = [{'probe_assign': True,
                             'sorting': True}]
    recording = [None]
    sorter = [None]
    analyser = [None]
    
    gui_thread = threading.Thread(target=main_gui_maker, args=(main_window, state, current_sorter_param, ephy_extension_dict, recording, sorter, analyser))
    gui_thread.start()
        
    while True:
        while state[0] is None:
            time.sleep(0.1)
        
        if state[0] == 'stop':
            break
        
        main_window[0]['launch_sorting_button'].update('Sorting in porgress')
        main_window[0]['launch_sorting_button'].update(disabled=True)
        
        recording[0] = current_sorter_param[0]['ephy_file_reading_function'](current_sorter_param[0]['ephy_file_path'])
        
        launch_sorting(current_sorter_param, main_window, state, recording, sorter, analyser)
        
        main_window[0]['launch_sorting_button'].update('Launch Sorting')
        main_window[0]['launch_sorting_button'].update(disabled=False)

if __name__ == "__main__":
    sorting_main()