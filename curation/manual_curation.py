# -*- coding: utf-8 -*-
"""
Created on Tue May  7 13:57:19 2024

@author: Pierre.LE-CABEC
"""
from spikeinterface.curation import apply_sortingview_curation, get_potential_auto_merge
import spikeinterface.widgets as ww
from spikeinterface.core import create_sorting_analyzer

from plotting.plot_unit_summary import plot_sorting_summary
from additional.toolbox import load_or_compute_extension

import os 
import shutil
import webbrowser
import time
import kachery_cloud as kcl
import json

def manual_curation_event_handler(window, values, event, current_sorter_param, state): 
    if event == 'open_manual_curation_outputlink_button':
        webbrowser.open(current_sorter_param[0]['manual_curation_param']['outputlink'])
        
    if event in ['continue_manual_curation_inputlink_button', 'accept_manual_curation_inputlink_button']:
        current_sorter_param[0]['manual_curation_param']['mode'] = event.split('_')[0]
        current_sorter_param[0]['manual_curation_param']['inputlink'] = values['manual_curation_inputlink_input']

        
def manual_curation_module(analyzer, save_path, current_sorter_param, window, trial_len=9, save_plot=True):
    
    window['manual_cleaning_input_column'].update(visible=True)
        
    version = 1
    while True:
        print(f'\n######### Curation version: {version} #########')
        load_or_compute_extension(analyzer, ['spike_amplitudes', 'random_spikes', 'waveforms', 'templates', 'template_similarity', 'unit_locations', 'correlograms', 'template_metrics'])

        
        merges = get_potential_auto_merge(analyzer, minimum_spikes=0,  maximum_distance_um=150.,
                                          peak_sign="neg", bin_ms=0.25, window_ms=100.,
                                          corr_diff_thresh=0.16, template_diff_thresh=0.25,
                                          censored_period_ms=0., refractory_period_ms=1.0,
                                          contamination_threshold=0.2, num_channels=5, num_shift=5,
                                          firing_contamination_balance=1.5)

        
        window['progress_text'].update('Generating link')
        sorting_view = ww.plot_sorting_summary(analyzer, curation=True, backend='sortingview')
        current_sorter_param[0]['manual_curation_param']['outputlink'] = sorting_view.url
        current_sorter_param[0]['manual_curation_param']['inputlink'] = None
        window['progress_text'].update(f'Recomanded merge: {merges}')
        
        window['manual_curation_outputlink_input'].update(sorting_view.url)
        window['manual_curation_outputlink_input'].update(text_color='black')
        window['manual_curation_inputlink_input'].update('')
        window['open_manual_curation_outputlink_button'].update(disabled=False)
        window['continue_manual_curation_inputlink_button'].update(disabled=False)
        window['accept_manual_curation_inputlink_button'].update(disabled=False)
        
        while True:
            time.sleep(0.1)
            if current_sorter_param[0]['manual_curation_param']['inputlink'] is not None:
                try:
                    window['progress_text'].update('Converting link into SortingAnalyzer')
                    sortingview_curation_dict = kcl.load_json(uri=current_sorter_param[0]['manual_curation_param']['inputlink'])
                    if 'labelsByUnit' not in sortingview_curation_dict.keys():
                        sortingview_curation_dict['labelsByUnit'] = {}
                        for unit in analyzer.unit_ids:
                            sortingview_curation_dict['labelsByUnit'][int(unit)] = ['accept']
                            
                        if not os.path.isdir(save_path):
                            os.makedirs(save_path)
                            save_path_existed = False
                        else:
                            save_path_existed = True
                            
                        with open(f"{save_path}/sortingview_curation_dict_temp_.json", "w") as outfile: 
                            json.dump(sortingview_curation_dict, outfile)
                        
                        sorter_manualy_curated = apply_sortingview_curation(sorting=analyzer.sorting, 
                                                                            uri_or_json=f"{save_path}/sortingview_curation_dict_temp_.json",
                                                                            exclude_labels=["reject", "noise", "artifact"])
                        os.remove(f"{save_path}/sortingview_curation_dict_temp_.json")
                        if not save_path_existed: #this is done so that if it crash before saving SorterAnalyzer there will not be a empty manual curation folder
                            shutil.rmtree(save_path)
                            
                    else:
                        sorter_manualy_curated = apply_sortingview_curation(sorting=analyzer.sorting, 
                                                                            uri_or_json=current_sorter_param[0]['manual_curation_param']['inputlink'],
                                                                            exclude_labels=["reject", "noise", "artifact"])                
                except:
                    window['progress_text'].update('')
                    window.write_event_value('popup_error', "Unable to convert link into SortingAnalyzer")
                    window['manual_curation_inputlink_input'].update('')
                    current_sorter_param[0]['manual_curation_param']['inputlink'] = None
                    continue
                else:
                    break
                window['progress_text'].update('')

        window['manual_curation_outputlink_input'].update('')
        window['manual_curation_inputlink_input'].update('')
        window['open_manual_curation_outputlink_button'].update(disabled=True)
        window['continue_manual_curation_inputlink_button'].update(disabled=True)
        window['accept_manual_curation_inputlink_button'].update(disabled=True)
        current_sorter_param[0]['manual_curation_param']['outputlink'] = None
        current_sorter_param[0]['manual_curation_param']['inputlink'] = None
        
        os.makedirs(save_path, exist_ok=True)
        if current_sorter_param[0]['manual_curation_param']['mode'] == 'continue':
            analyzer = create_sorting_analyzer(sorting=sorter_manualy_curated,
                                                recording=analyzer.recording, 
                                                format="memory"
                                                )
        elif current_sorter_param[0]['manual_curation_param']['mode'] == 'accept':
            window['manual_cleaning_input_column'].update(visible=False)
            create_sorting_analyzer(sorting=sorter_manualy_curated,
                                                recording=analyzer.recording,
                                                format="binary_folder",
                                                return_scaled=True, # this is the default to attempt to return scaled
                                                folder=f"{save_path}/SortingAnalyzer" , 
                                                overwrite=True, 
                                                )
        window['progress_text'].update('')
        
        if os.path.isdir(fr'{save_path}\Unit_summary_plot'):
            while True:
                try:
                    shutil.rmtree(fr'{save_path}\Unit_summary_plot')
                except PermissionError:
                    window.write_event_value('popup_error', "Please close previous version summary plot")
                else:
                    break
        
        window['progress_text'].update('Sorting Summary plot in progress')
        plot_sorting_summary(analyzer, 
                              current_sorter_param[0]['name'], 
                              save_path=save_path, 
                              trial_len=analyzer.get_total_duration())
        window['progress_text'].update('')
        
        if current_sorter_param[0]['manual_curation_param']['mode'] == 'continue':
            version += 1
            continue
        elif current_sorter_param[0]['manual_curation_param']['mode'] == 'accept':
            break
        else:
            raise ValueError('Not implemented')
        
    return analyzer