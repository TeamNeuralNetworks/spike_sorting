# -*- coding: utf-8 -*-
"""
Created on Mon May  6 10:56:27 2024

@author: Pierre.LE-CABEC
"""
import spikeinterface as si  # import core only
import spikeinterface.extractors as se
import spikeinterface.sorters as ss
import probeinterface as pi
import spikeinterface.preprocessing as spre
import os

from plot_unit_summary import plot_sorting_summary
from clean_unit import clean_unit
from manual_curation import manual_curation_module

ephy_folder_path = r'C:/local_data/Gilles/raw intan/0032_01_10/0032_01_240110_165516/0032_01_240110_165516.rhd'
recording = se.read_intan(ephy_folder_path, stream_id='0')
recording = spre.bandpass_filter(recording, freq_min=300, freq_max=6000)
recording = spre.common_reference(recording, reference='global', operator='median')
recording.annotate(is_filtered=True)

probe = pi.io.read_probeinterface('C:/local_data/Gilles/A1x16-Poly2-5mm-50s-177.json')
probe = probe.probes[0]
recording = recording.set_probe(probe)

sorter_result_folder = r'C:\local_data\Gilles\spike'

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

for sorter_name, sorter_params in sorter.items():
    if not os.path.isdir(fr'{sorter_result_folder}\{sorter_name}'):
        sorter = ss.run_sorter(sorter_name=sorter_name, recording=recording, docker_image=True, 
                                      output_folder=f'{sorter_result_folder}/{sorter_name}', verbose=True, **sorter_params)
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