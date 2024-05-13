# -*- coding: utf-8 -*-
"""
Created on Tue May  7 13:57:19 2024

@author: Pierre.LE-CABEC
"""
import spikeinterface as si  # import core only
from spikeinterface.curation import apply_sortingview_curation, get_potential_auto_merge
from spikeinterface.postprocessing import (compute_spike_amplitudes, compute_unit_locations,
                                           compute_template_metrics, 
                                           compute_template_similarity, compute_correlograms)
import spikeinterface.widgets as ww
import spikeinterface.sorters as ss

from plotting.plot_unit_summary import plot_sorting_summary

import os 
import shutil

def manual_curation_module(we, sorter, multirecording, sorter_folder, sorter_name, delay, mouse, save_plot=True, temp_file_indx=0, trial_len=9):
    
    temp_file_indx += 1
    while True:
        print(f'\n######### Curent curation version: {temp_file_indx} #########')
        _ = compute_spike_amplitudes(waveform_extractor=we, load_if_exists=True)
        _ = compute_unit_locations(waveform_extractor=we, load_if_exists=True)
        _ = compute_template_similarity(waveform_extractor=we, load_if_exists=True)
        _ = compute_correlograms(we, load_if_exists=True)
        _ = compute_template_metrics(we, load_if_exists=True)
        # _ = compute_principal_components(we, load_if_exists=True)
        # _ = compute_isi_histograms(we, load_if_exists=True)
        # _ = compute_noise_levels(we, load_if_exists=True)                        
        
        merges = get_potential_auto_merge(waveform_extractor=we, minimum_spikes=0,  maximum_distance_um=150.,
                                          peak_sign="neg", bin_ms=0.25, window_ms=100.,
                                          corr_diff_thresh=0.16, template_diff_thresh=0.25,
                                          censored_period_ms=0., refractory_period_ms=1.0,
                                          contamination_threshold=0.2, num_channels=5, num_shift=5,
                                          firing_contamination_balance=1.5)
        
        print( f'\nRecomanded merge: {merges}')
        print('\nManual curation link:')
        
        ww.plot_sorting_summary(we, curation=True, backend='sortingview')
        
        print('\nEnter manualy curated path or url (or "end" to make no modification)')
        manualy_curated_json_file_path = input()
        print('')
        
        if manualy_curated_json_file_path == 'end':
            end_loop = 'end'
        else:
            sorter_manualy_curated = apply_sortingview_curation(sorting=sorter, 
                                                    uri_or_json=manualy_curated_json_file_path,
                                                    exclude_labels=["reject", "noise", "artifact"])
            
            if os.path.isdir(f'{sorter_folder}/sorter_manualy_curated_temp_{temp_file_indx}_'):
                shutil.rmtree(f'{sorter_folder}/sorter_manualy_curated_temp_{temp_file_indx}_')
                
            sorter_manualy_curated.save(folder=f'{sorter_folder}/sorter_manualy_curated_temp_{temp_file_indx}_', )
            we_path = f'{sorter_folder}/we_manualy_curated_temp_{temp_file_indx}_'
            we_manualy_curated = si.extract_waveforms(multirecording, sorter_manualy_curated, max_spikes_per_unit=None, folder=we_path, overwrite=True)
            
            
            print('\nPlot sorting summary in progress')
            if save_plot:
                save_path = we_path
                plot_sorting_summary(we_manualy_curated, sorter_name, delay, mouse, save_path=save_path, trial_len=trial_len)          
            
            print(f'\nAccept current manual curation?\nCheck current version at {we_path}/Unit summary plot\nPress: -"y" to accept and generate a new url\n       -"n" to go back to previous curration\n       -"end" to accept and exit manual curration module')
            end_loop = input()
            print('##############################################')
        if end_loop == 'n':
            shutil.rmtree(f'{sorter_folder}/sorter_manualy_curated_temp_{temp_file_indx}_')
            shutil.rmtree(f'{sorter_folder}/we_manualy_curated_temp_{temp_file_indx}_')
            continue
        
        elif end_loop == 'end':
            temporary_manualy_curated_sorter_folder = os.listdir(sorter_folder)
            temporary_manualy_curated_sorter_folder = [folder for folder in temporary_manualy_curated_sorter_folder if 'sorter_manualy_curated_temp_' in folder]
            if not temporary_manualy_curated_sorter_folder:
                print('\nNo manualy curated file found, do you want to save without making mdofication?\nPress "y" to save, "n" to continue manual curation')
                while True:    
                    manualy_curated_json_file_path = input()
                    if manualy_curated_json_file_path == 'n':
                        break
                    elif manualy_curated_json_file_path == 'y':
                        break
                    else:
                        print(f'\nUnrocognize input: {manualy_curated_json_file_path}')
                        
                if manualy_curated_json_file_path == 'n':
                    continue
                elif manualy_curated_json_file_path == 'y':
                    break
            else:
                temporary_manualy_curated_sorter_indx_list = [folder.split('_')[-2] for folder in temporary_manualy_curated_sorter_folder]
                print(f'\nwich of the following curation version is final: {temporary_manualy_curated_sorter_indx_list}')
                manualy_curated_json_file_path = input()
                del we, sorter
                final_manualy_curated_sorter = temporary_manualy_curated_sorter_folder[temporary_manualy_curated_sorter_indx_list.index(manualy_curated_json_file_path)]
                sorter = ss.NpzSortingExtractor.load_from_folder(f'{sorter_folder}/{final_manualy_curated_sorter}')
            
            if os.path.isdir(f'{sorter_folder}/sorter_manualy_curated'):
                shutil.rmtree(f'{sorter_folder}/sorter_manualy_curated')
                
            sorter.save(folder=f'{sorter_folder}/sorter_manualy_curated')
            we_path = f'{sorter_folder}/we_manualy_curated'
            we = si.extract_waveforms(multirecording, sorter, max_spikes_per_unit=None, folder=we_path, overwrite=True)
        
            #Move plot file so it doesn't need to be computed again
            shutil.move(f'{sorter_folder}/we_manualy_curated_temp_{manualy_curated_json_file_path}_/Unit summary plot', f'{sorter_folder}/we_manualy_curated/Unit summary plot')

            for current_temp_file_indx in temporary_manualy_curated_sorter_folder:
                try:
                    shutil.rmtree(f'{sorter_folder}/{current_temp_file_indx}')
                except:
                    print(f"{sorter_folder}/{current_temp_file_indx}, couldn't be deleted")
                try:
                    shutil.rmtree(f'{sorter_folder}/{current_temp_file_indx.replace("sorter", "we")}')
                except:
                    print(f"{sorter_folder}/{current_temp_file_indx.replace('sorter', 'we')}, couldn't be deleted")
            break
        
        elif end_loop == 'y':
            temp_file_indx += 1
            sorter = sorter_manualy_curated
            we = we_manualy_curated
            continue
        
    return we, sorter, we_path