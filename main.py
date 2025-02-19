# -*- coding: utf-8 -*-
"""
Created on Tue May  7 10:26:45 2024

@author: Pierre.LE-CABEC
"""

from spikeinterface.sorters import run_sorter
from spikeinterface.core import create_sorting_analyzer
from probeinterface.io import read_probeinterface
from spikeinterface.core import load_sorting_analyzer
from spikeinterface.exporters import export_to_phy

import threading
import time
import traceback
import json
import datetime
from docker.errors import DockerException
import shutil
import warnings
import os
import pandas as pd 
import numpy as np

from plotting.plot_unit_summary import plot_sorting_summary
from curation.clean_unit import clean_unit
from curation.manual_curation import manual_curation_module
from curation.preprocessing import apply_preprocessing
from GUIs.Main_GUI import Main_GUI
from additional.toolbox import get_default_param, load_or_compute_extension, ephy_extractor_dict, select_folder_file, led_loading_animation, SetLED

warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=RuntimeWarning)
warnings.filterwarnings('ignore', category=UserWarning)

default_param = {}


class Spike_sorting_MAIN:
    
    def __init__(self):
        
        self.state = None
        self.pipeline_parameters = get_default_param()
        self.analyzer = None
        self.recording = None
        self.probe = None
        
        self.Main_GUI_instance = Main_GUI()
        self.Main_GUI_thread = threading.Thread(target=self.Main_GUI_instance.launch_GUI, args=[self])
        self.Main_GUI_thread.start()
        
        self.sorting_main()
        
    def sorting_main(self):

        while True:
            if self.state == 'stop':
                break
            elif self.state == 'Load analysis':
                self.load_analysis()
                self.state = None
                
            elif self.state == 'load_recording':
                self.load_recording()
                self.state = None
            
            elif self.state == 'load_multi_recording':
                self.load_multiple_recording()
                self.state = None
                
            elif self.state == 'load_probe':
                self.load_probe()
                self.state = None
                
            elif self.state == 'launch': 
                self.Main_GUI_instance.window['launch_sorting_button'].update(disabled=True)
                self.Main_GUI_instance.window['reset_analysis_button'].update(disabled=True)
                
                if isinstance(self.recording, list):
                    self.window.write_event_value('popup_error', 'Work in progress, multi recording pipeline not yet implemented.') #TODO
                    # for indx, (recording_path, probe_file_path, output_folder_path) in enumerate(self.recording):
                    #     self.Main_GUI_instance.window['progress_text'].update('Recording {indx+1} out of {len(recording)}')
                        
                    #     SetLED(self.Main_GUI_instance.window, 'led_preprocessing', 'red')
                    #     SetLED(self.Main_GUI_instance.window, 'led_sorting', 'red')
                    #     SetLED(self.Main_GUI_instance.window, 'led_unit_auto_cleaning', 'red')
                    #     SetLED(self.Main_GUI_instance.window, 'led_Manual', 'red')
                        
                    #     base_pipeline_parameters = [copy.deepcopy(self.pipeline_parameters)]
                    #     base_pipeline_parameters[0]['load_ephy']['ephy_file_path'] = recording_path
                    #     base_pipeline_parameters[0]['output_folder_path'] = output_folder_path
                    #     base_pipeline_parameters[0]['probe_file_path'] = probe_file_path
                    #     current_recording, _ = load_recording(self.Main_GUI_instance.window, base_pipeline_parameters)
                    #     current_probe = load_probe(self.Main_GUI_instance.window, probe_file_path)
                    #     state[0] = 'launch'
                    #     launch_analysis(base_pipeline_parameters, self.Main_GUI_instance.window, self.state, self.analyzer, current_recording, current_probe)
                else:
                    self.launch_analysis()
                
                self.Main_GUI_instance.window['launch_sorting_button'].update(disabled=False)
                self.Main_GUI_instance.window['reset_analysis_button'].update(disabled=False)
                
            elif self.state == 'export_spike_time':
                self.export_to_excel(mode='spike_time')
                del self.pipeline_parameters['export_spike_time_path']
                self.state = None
                
            elif self.state == 'export_template':
                self.export_to_excel(mode='template')
                del self.pipeline_parameters['export_template_path']
                self.state = None
            
            elif self.state == 'export_to_phy':
                load_or_compute_extension(self.analyzer, ['random_spikes', 'waveforms', 'templates'])
                export_to_phy(sorting_analyzer=self.analyzer, 
                              output_folder=self.pipeline_parameters['export_template_path'])
                del self.pipeline_parameters['export_template_path']
                self.state = None
                
            else:
                time.sleep(0.1)
                
            
    def export_to_excel(self, mode):
        
        tab_unit_df_list = []
        
        if mode == 'template':
            load_or_compute_extension(self.analyzer, ['random_spikes', 'waveforms', 'templates'])
        
        for  unit_id in self.analyzer.sorting.unit_ids:
            if mode == 'spike_time':
                path = self.pipeline_parameters['export_spike_time_path']
                curent_spike_train_indx = self.analyzer.sorting.get_unit_spike_train(unit_id=unit_id)
                curent_spike_train_time = curent_spike_train_indx / self.analyzer.sampling_frequency
                tab_unit_df = pd.DataFrame(np.column_stack((curent_spike_train_indx, curent_spike_train_time)), 
                                           columns=['spike_index', 'spike_time'])
                tab_unit_df_list.append((unit_id, tab_unit_df))
                
            elif mode == 'template':
                path = self.pipeline_parameters['export_template_path']
                curent_template = self.analyzer.get_extension('templates').get_unit_template(unit_id)
                channel_ids = self.analyzer.channel_ids
                tab_unit_df = pd.DataFrame(curent_template, columns=channel_ids)
                tab_unit_df_list.append((unit_id, tab_unit_df))
        
        with pd.ExcelWriter(path, engine='openpyxl') as writer:
            for unit_id, tab_unit_df in tab_unit_df_list:
                tab_unit_df.to_excel(writer, sheet_name=f'unit_{unit_id}', index=False, )

    def load_analysis(self): #TODO probably better to have a file listing the historic of analysis done and automaticly choising the last one instead of this arbitrary ranking
        path = select_folder_file(mode='folder')
        if path is not None:
            folder_list = os.listdir(path)
            if 'manual curation' in folder_list or os.path.basename(path) == 'manual curation':
                mode = 'manual curation'
                if 'manual curation' in folder_list:
                    path = fr'{path}\{mode}'
            elif 'unit auto cleaning' in folder_list or os.path.basename(path) == 'unit_auto_cleaning':
                mode = 'unit_auto_cleaning'
                if 'unit_auto_cleaning' in folder_list:
                    path = fr'{path}\{mode}'
    
            elif 'base_sorting' in folder_list or os.path.basename(path) == 'base_sorting':
                mode = 'base_sorting'
                if 'base_sorting' in folder_list:
                    path = fr'{path}\{mode}'
            else:
                self.Main_GUI_instance.window.write_event_value('popup_error', 'No anlysis pipeline find')
                return
            
            try:
                self.analyzer = load_sorting_analyzer(folder=fr'{path}\SortingAnalyzer')
                with open(fr'{path}/pipeline_param.json', 'r') as file:
                     self.pipeline_parameters = json.load(file)
                     
                if mode == 'base_sorting': 
                    self.pipeline_parameters["manual_curation_param"]['from_loading'] = True
                else:
                    self.pipeline_parameters["manual_curation_param"]['from_loading'] = False
                
                self.recording = self.analyzer.recording
                self.probe = self.analyzer.get_probe()
                self.Main_GUI_instance.window['sorter_combo'].update(self.pipeline_parameters['name'])
                    
            except:
                self.Main_GUI_instance.window.write_event_value('popup_error', 'Unable to load analysis')
                self.analyzer, self.recording, self.probe = None, None, None
            else:
                if self.pipeline_parameters['preprocessing'] == 'Done':
                    SetLED(self.Main_GUI_instance.window, 'led_preprocessing', 'green')
                    
                if self.pipeline_parameters['sorting'] == 'Done':
                    SetLED(self.Main_GUI_instance.window, 'led_sorting', 'green')

                if self.pipeline_parameters['unit_auto_cleaning'] == 'Done':
                    SetLED(self.Main_GUI_instance.window, 'led_unit_auto_cleaning', 'green')
                    
                if self.pipeline_parameters['manual_curation'] == 'Done':
                    SetLED(self.Main_GUI_instance.window, 'led_Manual', 'green')
                
                if self.recording is not None:
                    self.Main_GUI_instance.window['Load_recording'].update(button_color='green')
                    
                if self.probe is not None:
                    self.Main_GUI_instance.window['Load_probe_file'].update(button_color='green')
                
                if self.pipeline_parameters['output_folder_path']:
                    self.Main_GUI_instance.window['Select_output_folder'].update(button_color='green')
                
                for analysis_to_be_done in ['preprocessing', 'unit_auto_cleaning', 'manual_curation']:
                    self.Main_GUI_instance.window[f'{analysis_to_be_done}_checkbox'].update(value=self.pipeline_parameters[analysis_to_be_done])
                self.Main_GUI_instance.window['sorter_combo'].update(self.pipeline_parameters['name'])

    # def load_multiple_recording(self):#TODO
    #     try:
    #         ephy_path_df = pd.read_excel(self.pipeline_parameters['load_ephy']['ephy_file_path'])
            
    #         self.recording = []
    #         for ephy_row_indx, ephy_row in ephy_path_df.iterrows():
    #             self.recording.append((ephy_row['ephy_recording_path'], ephy_row['probe_file_path'], ephy_row['output_folder_path']))
    #     except:
    #         self.Main_GUI_instance.window.write_event_value('popup_error', "Unable to load multi recording excel file (the excel file must contain 3 column 'ephy_recording_path', 'probe_file_path' and 'output_folder_path')")
        
    #     self.Main_GUI_instance.window['Load_recording'].update(button_color='green')
    #     self.Main_GUI_instance.window['Load_probe_file'].update(button_color='green')
    #     self.Main_GUI_instance.window['Load_probe_file'].update(disabled=True)
    #     self.Main_GUI_instance.window['Select_output_folder'].update(button_color='green')
    #     self.Main_GUI_instance.window['Select_output_folder'].update(disabled=True)
        
        
    #     self.pipeline_parameters['probe_file_path'] = 'to be loaded'
    #     self.pipeline_parameters['output_folder_path'] = 'to be loaded'
    #     self.Main_GUI_instance.reset_analysis_pipeline(self)

    def load_recording(self):

        try:
            self.recording = ephy_extractor_dict[self.pipeline_parameters['load_ephy']['mode']][self.pipeline_parameters['load_ephy']['extractor']]['function'](self.pipeline_parameters['load_ephy']['extractor_parameters'])
        except Exception:
            print('\n') 
            traceback.print_exc()
            self.Main_GUI_instance.window.write_event_value('popup_error', "unable to load ephy data")
            return 
        
        if self.pipeline_parameters['load_ephy']['trigger_from'] == 'Recording_tool_GUI':
            self.Main_GUI_instance.additional_GUI_instance_dict['Recording_tool_instance'].window['main_window'].write_event_value('recording_loaded', "trigger from main")
        
        else:
            path_syntax = ephy_extractor_dict[self.pipeline_parameters['load_ephy']['mode']][self.pipeline_parameters['load_ephy']['extractor']]['path_syntax']
            if os.path.isfile(f"{self.pipeline_parameters['load_ephy']['extractor_parameters'][path_syntax]}/probe.json"):
                self.pipeline_parameters['probe_file_path'] = f"{self.pipeline_parameters['load_ephy']['extractor_parameters'][path_syntax]}/probe.json"
                self.load_probe()
                self.recording = self.recording.set_probe(self.probe)
                    
            self.Main_GUI_instance.window['Load_recording'].update(button_color='green')
            
            if self.pipeline_parameters['preprocessing'] == 'Done' or self.pipeline_parameters['sorting'] == 'Done':
                self.Main_GUI_instance.reset_analysis_pipeline(self)
                self.analyzer = None

    def load_probe(self):
        self.probe = read_probeinterface(self.pipeline_parameters['probe_file_path'])
        self.probe = self.probe.probes[0]
        self.Main_GUI_instance.window['Load_probe_file'].update(button_color='green')
        
        if self.recording is not None:
            self.recording = self.recording.set_probe(self.probe)
            
    def launch_analysis(self):
        
        try:
            led_loading_animation_thread = threading.Thread(target=led_loading_animation, args=(self.Main_GUI_instance.window, self))
            led_loading_animation_thread.start()
            
            current_time = datetime.datetime.now()
    
            self.pipeline_parameters['time of analysis'] = current_time.strftime("%Y-%m-%d %H:%M:%S")
            #############################################
            if self.pipeline_parameters['preprocessing'] is True:
                print('\n########### Preprocess recording #############')
                self.state = 'preprocessing'
                self.recording = apply_preprocessing(self.recording, self.pipeline_parameters['preprocessing_param'], self.Main_GUI_instance.window)
                self.pipeline_parameters['preprocessing'] = 'Done'
                SetLED(self.Main_GUI_instance.window, 'led_preprocessing', 'green')
                print('Done')
                print('###########################################')
    
            #############################################
            if self.pipeline_parameters['sorting'] is True:
                print('\n############# Running sorter #################')
                self.state = 'sorting'
                if 'verbose' in self.pipeline_parameters['sorting_param'].keys():
                    sorter = run_sorter(sorter_name=self.pipeline_parameters['name'], recording=self.recording, docker_image=True, 
                                                  folder=f"{self.pipeline_parameters['output_folder_path']}/{self.pipeline_parameters['name']}/base_sorting/SorterOutput", 
                                                  **self.pipeline_parameters['sorting_param'])
                else:
                    sorter = run_sorter(sorter_name=self.pipeline_parameters['name'], recording=self.recording, docker_image=True, 
                                                  folder=f"{self.pipeline_parameters['output_folder_path']}/{self.pipeline_parameters['name']}/base_sorting/SorterOutput", 
                                                  verbose=True, 
                                                  **self.pipeline_parameters['sorting_param'])
                    
                if len(sorter.get_unit_ids()) == 0:
                    self.Main_GUI_instance.window.write_event_value('popup_error', f"{self.pipeline_parameters['name']} has finished sorting but no units has been found")
                    raise ValueError('No unit found during sorting')
                
                
                if not self.recording.has_scaleable_traces():
                    self.recording.set_channel_gains(1)
                    self.recording.set_channel_offsets(0)
                    
                self.analyzer = create_sorting_analyzer(sorting=sorter,
                                                    recording=self.recording,
                                                    format="binary_folder",
                                                    return_scaled=True, # this is the default to attempt to return scaled
                                                    folder=f"{self.pipeline_parameters['output_folder_path']}/{self.pipeline_parameters['name']}/base_sorting/SortingAnalyzer", 
                                                    sparse=True,
                                                    ms_before=2, ms_after=5,
                                                    )
                self.pipeline_parameters['sorting'] = 'Done'
                self.Main_GUI_instance.window['unit_found'].update(f'{len(self.analyzer.unit_ids)} Units found.')
                
                with open(f"{self.pipeline_parameters['output_folder_path']}/{self.pipeline_parameters['name']}/base_sorting/pipeline_param.json", "w") as outfile: 
                    json.dump(self.pipeline_parameters, outfile)
                
                if self.pipeline_parameters['summary_plot_param']['auto_save']['activate']:
                    plot_sorting_summary(self.analyzer, 
                                         self.pipeline_parameters['name'], 
                                         save_path=f"{self.pipeline_parameters['output_folder_path']}/{self.pipeline_parameters['name']}/base_sorting", 
                                         summary_plot_param=self.pipeline_parameters['summary_plot_param'],
                                         )
                    
                SetLED(self.Main_GUI_instance.window, 'led_sorting', 'green')
                print('Done')
                print('##########################################')
            
            
            #############################################
            if self.pipeline_parameters['unit_auto_cleaning'] is True:
                print('\n############# Unit auto leaning #############')
                self.state = 'unit_auto_cleaning'
                self.analyzer = clean_unit(self,
                                        save_folder=f"{self.pipeline_parameters['output_folder_path']}/{self.pipeline_parameters['name']}/unit_auto_cleaning",
                                        save_plot_path=f"{self.pipeline_parameters['output_folder_path']}/{self.pipeline_parameters['name']}/unit_auto_cleaning",
                                        ) 
                
                self.pipeline_parameters['unit_auto_cleaning'] = 'Done'            
                with open(f"{self.pipeline_parameters['output_folder_path']}/{self.pipeline_parameters['name']}/unit_auto_cleaning/pipeline_param.json", "w") as outfile: 
                    json.dump(self.pipeline_parameters, outfile)
                
                if self.pipeline_parameters['summary_plot_param']['auto_save']['activate']:
                    plot_sorting_summary(self.analyzer, 
                                         self.pipeline_parameters['name'], 
                                         save_path=f"{self.pipeline_parameters['output_folder_path']}/{self.pipeline_parameters['name']}/unit_auto_cleaning", 
                                         summary_plot_param=self.pipeline_parameters['summary_plot_param'],
                                         )
                
                
                self.Main_GUI_instance.window['unit_found'].update(f'{len(self.analyzer.unit_ids)} Units after cleaning.')
                SetLED(self.Main_GUI_instance.window, 'led_unit_auto_cleaning', 'green')
                print('Done')
                print('##########################################')
            
            
            #############################################
            if self.pipeline_parameters['manual_curation'] is True or self.pipeline_parameters['manual_curation'] == 'Done':
                print('\n############## Manual curation ##############')
                self.state = 'Manual'
                manual_curation_module(self,
                                       save_path=f"{self.pipeline_parameters['output_folder_path']}/{self.pipeline_parameters['name']}/manual_curation", 
                                       )
                self.pipeline_parameters['manual_curation'] = 'Done'
                with open(f"{self.pipeline_parameters['output_folder_path']}/{self.pipeline_parameters['name']}/manual_curation/pipeline_param.json", "w") as outfile: 
                    json.dump(self.pipeline_parameters, outfile)
                
                SetLED(self.Main_GUI_instance.window, 'led_Manual', 'green')
                self.Main_GUI_instance.window['unit_found'].update(f'{len(self.analyzer.unit_ids)} Units after curation.')
                print('Done')
                print('##########################################')
            self.state = None
            
            if self.analyzer is not None:
                print(f'Analysis pipeline is done: {len(self.analyzer.unit_ids)} unit has been found')
        
        except Exception as e:
            print('\n')
            traceback.print_exc()
            if self.state is not None:
                error_stage = self.state
                SetLED(self.Main_GUI_instance.window, f'led_{self.state}', 'orange')
                self.state = None
                
                if error_stage == 'preprocessing':
                    self.pipeline_parameters['preprocessing'] = True
                    
                elif error_stage == 'sorting':
                    self.pipeline_parameters['sorting'] = True
                    
                elif error_stage == 'unit_auto_cleaning': #TODO new nomenclature
                    self.pipeline_parameters['unit_auto_cleaning'] = True
                    shutil.rmtree(f"{self.pipeline_parameters['output_folder_path']}/{self.pipeline_parameters['name']}/unit_auto_cleaning")
                    
                elif error_stage == 'Manual':
                    self.pipeline_parameters['manual_curation'] = True
                    shutil.rmtree(f"{self.pipeline_parameters['output_folder_path']}/{self.pipeline_parameters['name']}/manual_curation")
                    
            if isinstance(e, DockerException):
                self.Main_GUI_instance.window.write_event_value('popup_error', "Docker Desktop need to be open for sorting")
            
            self.analyzer
                


if __name__ == "__main__":
    sorting_main = Spike_sorting_MAIN()
