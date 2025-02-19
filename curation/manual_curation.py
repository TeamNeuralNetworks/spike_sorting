# -*- coding: utf-8 -*-
"""
Created on Tue May  7 13:57:19 2024

@author: Pierre.LE-CABEC
"""
from spikeinterface.curation import apply_sortingview_curation, compute_merge_unit_groups
import spikeinterface.widgets as ww

from plotting.plot_unit_summary import plot_sorting_summary
from additional.toolbox import load_or_compute_extension

from PySimpleGUI import popup_yes_no
import os 
import shutil
import webbrowser
import time
import kachery_cloud as kcl
import json
import traceback

def manual_curation_event_handler(base_instance, values, event): 
    if event == 'open_manual_curation_outputlink_button':
        webbrowser.open( base_instance.pipeline_parameters['manual_curation_param']['outputlink'])
        
    if event in ['continue_manual_curation_inputlink_button', 'accept_manual_curation_inputlink_button']:
        base_instance.pipeline_parameters['manual_curation_param']['mode'] = event.split('_')[0]
        base_instance.pipeline_parameters['manual_curation_param']['inputlink'] = values['manual_curation_inputlink_input']

        
def manual_curation_module(base_instance, save_path):
     
    base_instance.Main_GUI_instance.window['manual_cleaning_input_column'].update(visible=True)
        
    version = 1
    while True:
        print(f'\n######### Curation version: {version} #########')
        load_or_compute_extension(base_instance.analyzer, ['spike_amplitudes', 'random_spikes', 'waveforms', 'templates', 'template_similarity', 'unit_locations', 'correlograms', 'template_metrics'])

        merges = compute_merge_unit_groups(base_instance.analyzer)

        print('Generating link, please wait...')
        sorting_view = ww.plot_sorting_summary(base_instance.analyzer, curation=True, backend='sortingview')
        base_instance.pipeline_parameters['manual_curation_param']['outputlink'] = sorting_view.url
        base_instance.pipeline_parameters['manual_curation_param']['inputlink'] = None
        print(f'Recomanded merge: {merges}')
        
        base_instance.Main_GUI_instance.window['manual_curation_outputlink_input'].update(sorting_view.url)
        base_instance.Main_GUI_instance.window['manual_curation_outputlink_input'].update(text_color='black')
        base_instance.Main_GUI_instance.window['manual_curation_inputlink_input'].update('')
        base_instance.Main_GUI_instance.window['open_manual_curation_outputlink_button'].update(disabled=False)
        base_instance.Main_GUI_instance.window['continue_manual_curation_inputlink_button'].update(disabled=False)
        base_instance.Main_GUI_instance.window['accept_manual_curation_inputlink_button'].update(disabled=False)
        
        while True:
            time.sleep(0.1)
            if base_instance.pipeline_parameters['manual_curation_param']['inputlink'] is not None:
                try:
                    print('Converting link into sorting analyzer')
                    sortingview_curation_dict = kcl.load_json(uri=base_instance.pipeline_parameters['manual_curation_param']['inputlink'])
                    
                    if 'labelsByUnit' not in sortingview_curation_dict.keys():
                        sortingview_curation_dict['labelsByUnit'] = {}
                        for unit in base_instance.analyzer.unit_ids:
                            sortingview_curation_dict['labelsByUnit'][int(unit)] = ['accept']
                            
                        if not os.path.isdir(save_path):
                            os.makedirs(save_path)
                            save_path_existed = False
                        else:
                            save_path_existed = True
                            
                        with open(f"{save_path}/sortingview_curation_dict_temp_.json", "w") as outfile: 
                            json.dump(sortingview_curation_dict, outfile)
                        
                        analyzer_manualy_curated = apply_sortingview_curation(base_instance.analyzer, #TODO this is not working for some reason
                                                                            uri_or_json=f"{save_path}/sortingview_curation_dict_temp_.json",
                                                                            include_labels=['accept'])
                        
                        os.remove(f"{save_path}/sortingview_curation_dict_temp_.json")
                        if not save_path_existed: #this is done so that if it crash before saving SorterAnalyzer there will not be a empty manual curation folder
                            shutil.rmtree(save_path)
                            
                    else:
                        excluded_list = []
                        for unit, label in sortingview_curation_dict['labelsByUnit'].items():
                            if label in ["reject", "noise", "artifact"]:
                                excluded_list.append(label)
                        excluded_list = list(set(excluded_list))
                        
                        print(excluded_list,sortingview_curation_dict)
                        base_instance.analyzer = apply_sortingview_curation(base_instance.analyzer, 
                                                                            uri_or_json=base_instance.pipeline_parameters['manual_curation_param']['inputlink'],
                                                                            exclude_labels=excluded_list)                
                except Exception:
                    print('')
                    traceback.print_exc()
                    base_instance.Main_GUI_instance.window.write_event_value('popup_error', "Unable to convert link into SortingAnalyzer")
                    base_instance.Main_GUI_instance.window['manual_curation_inputlink_input'].update('')
                    base_instance.pipeline_parameters['manual_curation_param']['inputlink'] = None
                    continue
                else:
                    break
                print('')

        base_instance.Main_GUI_instance.window['manual_curation_outputlink_input'].update('')
        base_instance.Main_GUI_instance.window['manual_curation_inputlink_input'].update('')
        base_instance.Main_GUI_instance.window['open_manual_curation_outputlink_button'].update(disabled=True)
        base_instance.Main_GUI_instance.window['continue_manual_curation_inputlink_button'].update(disabled=True)
        base_instance.Main_GUI_instance.window['accept_manual_curation_inputlink_button'].update(disabled=True)
        base_instance.pipeline_parameters['manual_curation_param']['outputlink'] = None
        base_instance.pipeline_parameters['manual_curation_param']['inputlink'] = None
        
        os.makedirs(save_path, exist_ok=True)
        if base_instance.pipeline_parameters['manual_curation_param']['mode'] == 'continue':
            continue
            
        elif base_instance.pipeline_parameters['manual_curation_param']['mode'] == 'accept':
            base_instance.Main_GUI_instance.window['manual_cleaning_input_column'].update(visible=False)
            if os.path.isdir(f"{save_path}/SortingAnalyzer"):
                save_analyzer = None
                while save_analyzer is None:
                    try:
                        shutil.rmtree(f"{save_path}/SortingAnalyzer" )
                    except PermissionError:
                        base_instance.Main_GUI_instance.window.write_event_value('popup_error', "")
                        response = popup_yes_no("Unable top save curated sorting analyzer.\nWould you like to try again or continue with sorting analyzer in memory only?")
                        if response == 'Yes':
                            continue
                        else:
                           save_analyzer = False
                    else:
                        save_analyzer = True
            else:
                save_analyzer = True
            
            if save_analyzer:
                base_instance.analyzer.create(sorting=base_instance.analyzer.sorting,
                                                recording=base_instance.analyzer.recording,
                                                format="binary_folder",
                                                return_scaled=True, # this is the default to attempt to return scaled
                                                folder=f"{save_path}/SortingAnalyzer" , 
                                                )
        print('')
        
        if os.path.isdir(fr'{save_path}\Unit_summary_plot'):
            while True:
                try:
                    shutil.rmtree(fr'{save_path}\Unit_summary_plot')
                except PermissionError:
                    base_instance.Main_GUI_instance.window.write_event_value('popup_error', "Please close previous version summary plot")
                else:
                    break
        
        if base_instance.pipeline_parameters['summary_plot_param']['auto_save']['activate']:
            print('Sorting Summary plot in progress')
            plot_sorting_summary(base_instance.analyzer, 
                                  base_instance.pipeline_parameters['nale'], 
                                  save_path=save_path, 
                                  summary_plot_param=base_instance.pipeline_parameters['summary_plot_param'],)
        print('')
        
        if base_instance.pipeline_parameters['manual_curation_param']['mode'] == 'continue':
            version += 1
            continue
        elif base_instance.pipeline_parameters['manual_curation_param']['mode'] == 'accept':
            break
        else:
            raise ValueError('Not implemented')
            