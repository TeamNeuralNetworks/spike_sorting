# -*- coding: utf-8 -*-
"""
Created on Tue May  7 10:26:45 2024

@author: Pierre.LE-CABEC
"""
import spikeinterface.extractors as se
import spikeinterface.sorters as ss
import spikeinterface.preprocessing as spre
import spikeinterface as si  # import core only
import probeinterface as pi

import threading
import time

from plotting.plot_unit_summary import plot_sorting_summary
from curation.clean_unit import clean_unit
from curation.manual_curation import manual_curation_module
from GUIs.Main_GUI import main_gui_maker, led_loading_animation, SetLED, trigger_popup_error

ephy_extension_dict = {'rhd': lambda x:se.read_intan(x, stream_id='0'),
                       }


def launch_sorting(current_sorter_param, main_window, state):
    try:
        recording = current_sorter_param[0]['ephy_file_reading_function'](current_sorter_param[0]['ephy_file_path'])
        
        
        #############################################
        ############## BandPass filter ##############
        if current_sorter_param[0]['bandpass'][0]:
            state[0] = 'bandpass'
            recording = spre.bandpass_filter(recording, freq_min=int(current_sorter_param[0]['bandpass'][1]), freq_max=int(current_sorter_param[0]['bandpass'][2]))
            SetLED(main_window, 'led_bandpass', 'green')
            state[0] = None
        #############################################
        
        #############################################
        ############# Comon ref removal #############
        if current_sorter_param[0]['comon_ref']:
            state[0] = 'comon_ref'
            recording = spre.common_reference(recording, reference='global', operator='median')
            SetLED(main_window, 'led_comon_ref', 'green')
            state[0] = None
        recording.annotate(is_filtered=True)
        #############################################
        
        #############################################
        ############# Probe assignement #############
        probe = pi.io.read_probeinterface(current_sorter_param[0]['probe_file_path'])
        probe = probe.probes[0]
        recording = recording.set_probe(probe)
        #############################################
        
        #############################################
        ############## Running sorter ###############
        state[0] = 'sorting'
        sorter = ss.run_sorter(sorter_name=current_sorter_param[0]['name'], recording=recording, docker_image=True, 
                                      output_folder=f"{current_sorter_param[0]['output_folder_path']}/{current_sorter_param[0]['name']}/base sorting", verbose=True, **current_sorter_param[0]['param'])
        if len(sorter.get_unit_ids()) == 0:
            trigger_popup_error(f"{current_sorter_param[0]['name']} has finished sorting but no units has been found")
            raise ValueError
        we = si.extract_waveforms(recording, sorter, max_spikes_per_unit=None, folder=f"{current_sorter_param[0]['output_folder_path']}/{current_sorter_param[0]['name']}/base sorting/we")
        plot_sorting_summary(we, 
                             current_sorter_param[0]['name'], None, '', 
                             save_path=f"{current_sorter_param[0]['output_folder_path']}/{current_sorter_param[0]['name']}/base sorting", 
                              trial_len=recording.get_duration(), 
                             acelerate=False)
        SetLED(main_window, 'led_sorting', 'green')
        state[0] = None
        #############################################
        
        
        #############################################
        ############## Custom cleaning ##############
        if current_sorter_param[0]['custom_cleaning']:
            state[0] = 'Custom'
            we = clean_unit(sorter, recording, df_real_time=None,
                            save_folder=f"{current_sorter_param[0]['output_folder_path']}/{current_sorter_param[0]['name']}/custom cleaning", delay=None, mouse='', 
                            sorter_name=current_sorter_param[0]['name'], 
                            plot=True, save_plot=f"{current_sorter_param[0]['output_folder_path']}/{current_sorter_param[0]['name']}/custom cleaning")   
            plot_sorting_summary(we, current_sorter_param[0]['name'], 
                                 None, '', 
                                 save_path=f"{current_sorter_param[0]['output_folder_path']}/{current_sorter_param[0]['name']}/custom cleaning", 
                                 trial_len=recording.get_duration(), acelerate=False)
            SetLED(main_window, 'led_Custom', 'green')
            state[0] = None
        #############################################
        
        
        #############################################
        ############## Manual curation ##############
        if current_sorter_param[0]['manual_curation']:
            state[0] = 'Manual'
            we, sorter, we_path = manual_curation_module(we, 
                                                         sorter, 
                                                         recording, 
                                                         f"{current_sorter_param[0]['output_folder_path']}/{current_sorter_param[0]['name']}/manual curation", 
                                                         current_sorter_param[0]['name'], 
                                                         delay=None, 
                                                         mouse='', 
                                                         trial_len=recording.get_duration()
                                                         )
            SetLED(main_window, 'led_Manual', 'green')
            state[0] = None
        #############################################
        
    except Exception as e:
        print('\n')
        print(e)
        if state[0] is not None:
            SetLED(main_window, f'led_{state[0]}', 'orange')
        state[0] = None

def sorting_main():
    
    state = [None]
    main_window = [None]
    current_sorter_param = [{}]
    gui_thread = threading.Thread(target=main_gui_maker, args=(main_window, state, current_sorter_param, ephy_extension_dict))
    gui_thread.start()
        
    while True:
        while state[0] is None:
            time.sleep(0.1)
        
        if state[0] == 'stop':
            break
        
        main_window[0]['launch_sorting_button'].update('Sorting in porgress')
        main_window[0]['launch_sorting_button'].update(disabled=True)
        
        led_loading_animation_thread = threading.Thread(target=led_loading_animation, args=(state, main_window))
        led_loading_animation_thread.start()
        
        launch_sorting(current_sorter_param, main_window, state)
        
        main_window[0]['launch_sorting_button'].update('Launch Sorting')
        main_window[0]['launch_sorting_button'].update(disabled=False)
        state[0] = None

if __name__ == "__main__":
    sorting_main()