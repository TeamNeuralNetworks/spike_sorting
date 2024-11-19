# -*- coding: utf-8 -*-
"""
Created on Tue Jul  2 16:54:20 2024

@author: Pierre.LE-CABEC
"""
import os

import spikeinterface as si  
import spikeinterface.extractors as se
import probeinterface as pi
import spikeinterface.preprocessing as spre
import spikeinterface.sorters as ss

sorter_name = 'kilosort2'

list_recording = [r'D:/0041_240415_172710/0041_240415_172710.rhd', 
                  r'D:/0041_240415_172710/0041_240415_173710.rhd', 
                  r'D:/0041_240415_172710/0041_240415_174710.rhd']

list_open_recording = []
for recording in list_recording:
    list_open_recording.append(se.read_intan(recording, stream_name='RHD2000 amplifier channel'))

multirecording = si.concatenate_recordings(list_open_recording)

# multirecording.save(folder=fr"D:\0041_240415_172710\concatenated")


probe = pi.io.read_probeinterface(r'C:/local_data/Gilles/concatenated_recordings/0022_31_07/probe.jsonn')
probe = probe.probes[0]
multirecording = multirecording.set_probe(probe)

multirecording = spre.bandpass_filter(multirecording, freq_min=300, freq_max=6000)
multirecording = spre.common_reference(multirecording, reference='global', operator='median')
multirecording.annotate(is_filtered=True)

sorter_result_folder = r'D:\0041_240415_172710\result'

sorter = {
            'kilosort2': {
                        "detect_threshold": -6,
                        "projection_threshold": [10, 6],
                        "preclust_threshold": 8,
                        "car": False,
                        "minFR": 0.1,
                        "minfr_goodchannels": 0.1,
                        "freq_min": 150,
                        "sigmaMask": 30,
                        "nPCs": 3,
                        "ntbuff": 64,
                        "nfilt_factor": 6,
                        "NT": None,
                        "AUCsplit": 0.9,
                        "wave_length": 61,
                        "keep_good_only": False,
                        "skip_kilosort_preprocessing": False,
                        "scaleproc": 200,
                        "save_rez_to_mat": False,
                        "delete_tmp_files": False,
                        "delete_recording_dat": True,
                        },
    }

if not os.path.isdir(fr'{sorter_result_folder}\{sorter_name}'):
    sorter = ss.run_sorter(sorter_name=sorter_name, recording=recording, docker_image=True, 
                                  output_folder=f'{sorter_result_folder}/{sorter_name}', verbose=True, **sorter[sorter_name])
else:
    print('Unfilter_sorter folder not found, load from folder')
    sorter = ss.NpzSortingExtractor.load_from_folder(fr'{sorter_result_folder}\{sorter_name}\in_container_sorting')


we = clean_unit(sorter, recording, df_real_time=None,
                save_folder=fr'{sorter_result_folder}\{sorter_name}', delay=None, mouse='0032', 
                sorter_name=sorter_name, plot=True, save_plot=fr'{sorter_result_folder}')   

plot_sorting_summary(we, sorter_name, None, '0032', save_path=f'{sorter_result_folder}/we', trial_len=30, acelerate=False)

we, sorter, we_path = manual_curation_module(we, 
                                              sorter, 
                                              recording, 
                                              fr'{sorter_result_folder}\{sorter_name}', 
                                              sorter_name, 
                                              delay=None, 
                                              mouse='', 
                                              trial_len=30)