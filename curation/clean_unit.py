# -*- coding: utf-8 -*-
"""
Created on Mon Oct 16 17:09:48 2023

@author: Pierre.LE-CABEC
"""
from spikeinterface.core import create_sorting_analyzer
from spikeinterface.curation import CurationSorting, SplitUnitSorting
from spikeinterface.postprocessing import align_sorting
from spikeinterface import get_template_extremum_channel_peak_shift
import spikeinterface.qualitymetrics as sqm

import multiprocessing as mp
import matplotlib.pyplot as plt
import numpy as np
import os
# import phate
import pandas as pd
from tqdm import tqdm
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA
from scipy.cluster.hierarchy import linkage, fcluster
# from scipy.cluster import HDBSCAN
import pickle
import shutil
from time import sleep
from skimage.filters import threshold_otsu

from additional.toolbox import load_or_compute_extension

big_artefact_methods = ['mad', 
                        'abs_value']

splitting_method_list = ['pca', 
                         'phate',
                         'template_as_ref']

channel_method_list = ['highest',
                       'concatenate']

def get_highest_amplitude_channel(waveforms):
    
    new_current_selected_waveforms = []
    for i in range(len(waveforms)):
        current_spike_waveform = waveforms[i,:,:]
        current_spike_waveform_channel_indx = np.argmax(abs(current_spike_waveform).max(axis=0))
        new_current_selected_waveforms.append(current_spike_waveform[:,current_spike_waveform_channel_indx])
        
    return np.array(new_current_selected_waveforms)

def perform_split(cs, unit_id, mask, remove_first_index_unit=True):
    """
    mask should beA list of index arrays selecting the spikes to split in each segment. 
    Each array can contain more than 2 indices (e.g. for splitting in 3 or more units) 
    and it should be the same length as the spike train (for each segment).
    Indices can be either True or False (when splited into 2, False will become the first new unit and True the second)
    or integers corresponding to each new units (when splited into 2 or more, have to start from 0, 0 will become the first new unit, 1 the second ...)
    """
    if len(set(mask)) > 1:
        sorting = cs.sorting
        before_split_id = sorting.get_unit_ids()
        
        nb_of_new_unit_ids = len(set(mask))
        new_unit_ids = cs._get_unused_id(nb_of_new_unit_ids)
        new_sorting = SplitUnitSorting(
                                      sorting,
                                      split_unit_id=unit_id,
                                      indices_list=mask,
                                      new_unit_ids=new_unit_ids,
                                      properties_policy=cs._properties_policy,
                                    )
        after_split_id = new_sorting.get_unit_ids()
        new_unit_id_list = [new_unit_id for new_unit_id in after_split_id if new_unit_id not in before_split_id]
        
        new_cs = CurationSorting(sorting=new_sorting)
        if remove_first_index_unit:
            bad_unit = min(new_unit_id_list)
            new_cs.remove_units([bad_unit])
            new_unit_id_list.remove(bad_unit)
            
        return new_cs, new_unit_id_list
    else:
        return cs, [unit_id, ]

def remove_big_artefact(analyzer, cs, df_cleaning_summary, threshold, method='mad', save_folder=None, **kwargs):
    
    load_or_compute_extension(analyzer, ['random_spikes', 'waveforms'], extension_params={"random_spikes":{"method": "all"}})
    
    new_df_row_list = []
    for unit_id in tqdm(analyzer.unit_ids, desc='Remove big artefact', bar_format='{l_bar}{bar}\n'):
        current_waveforms = analyzer.get_extension('waveforms').get_waveforms_one_unit(unit_id=unit_id, force_dense=True)
        #select the highs channel for each spike
        
        new_current_selected_waveforms = get_highest_amplitude_channel(current_waveforms)
        before_cleaning_waveforms = new_current_selected_waveforms.T
        
        if method == 'mad':
            median_absolute_deviation = np.median(np.abs(before_cleaning_waveforms - np.median(before_cleaning_waveforms)))
            threshold = median_absolute_deviation*threshold
        elif method == 'abs_value':
            threshold = threshold
            
        mask = np.all(abs(before_cleaning_waveforms) < threshold, axis=0)
        
        cs, new_unit_id_list = perform_split(cs, unit_id, mask, remove_first_index_unit=True) #artefact are label False and will be the first unit formed
        
        for new_unit_id in new_unit_id_list:
            current_unit_df_cleaning_summary = df_cleaning_summary[df_cleaning_summary[df_cleaning_summary.columns[-1]] == unit_id]
            assert len(current_unit_df_cleaning_summary) == 1, "there cannot be two unit with the same id"
            new_df = current_unit_df_cleaning_summary.copy()
            new_df['Remove big artefact'] = [new_unit_id, ]
            new_df_row_list.append(new_df)
    
    df_cleaning_summary = pd.concat(new_df_row_list)
    clean_sorting = cs.sorting
    if save_folder is not None:
        clean_analyzer = create_sorting_analyzer(sorting=clean_sorting,
                                               recording=analyzer.recording,
                                               format="binary_folder",
                                               return_scaled=True, # this is the default to attempt to return scaled
                                               folder=f"{save_folder}/SortingAnalyzer", 
                                               overwrite=True,
                                               sparse=False
                                               )
    else:
        clean_analyzer = create_sorting_analyzer(sorting=clean_sorting,
                                               recording=analyzer.recording, 
                                               format="memory",
                                               sparse=False
                                               )
        
    return clean_analyzer, df_cleaning_summary

def remove_edge_artefact(analyzer, cs, df_cleaning_summary, save_folder=None, lenght_to_remove=7, **kwargs):
    
    new_df_row_list = []
    sampling_frequency = analyzer.sampling_frequency
    
    len_recording = analyzer.get_total_samples()
        
    for unit_id in tqdm(analyzer.unit_ids, desc='Remove edge artefact', bar_format='{l_bar}{bar}\n'):
        spikes = analyzer.sorting.get_unit_spike_train(unit_id=unit_id)
        spikes_indx = np.arange(0, len(spikes), 1)
        spikes_indx = spikes_indx[(spikes > (lenght_to_remove*(sampling_frequency/1000))) & (spikes < (len_recording-(lenght_to_remove*(sampling_frequency/1000))))]
        mask = np.zeros(len(spikes), dtype=bool)
        mask[spikes_indx] = True
        cs, new_unit_id_list = perform_split(cs, unit_id, mask, remove_first_index_unit=True) #artefact are label False and will be the first unit formed
        for new_unit_id in new_unit_id_list:
            current_unit_df_cleaning_summary = df_cleaning_summary[df_cleaning_summary[df_cleaning_summary.columns[-1]] == unit_id]
            assert len(current_unit_df_cleaning_summary) == 1, "there cannot be two unit with the same id"
            new_df = current_unit_df_cleaning_summary.copy()
            new_df['Remove edge artefact'] = [new_unit_id]
            new_df_row_list.append(new_df)
   
    df_cleaning_summary = pd.concat(new_df_row_list)
    clean_sorting = cs.sorting
    if save_folder is not None:
        clean_analyzer = create_sorting_analyzer(sorting=clean_sorting,
                                               recording=analyzer.recording,
                                               format="binary_folder",
                                               return_scaled=True, # this is the default to attempt to return scaled
                                               folder=f"{save_folder}/SortingAnalyzer", 
                                               overwrite=True, 
                                               sparse=False
                                               )
    else:
        clean_analyzer = create_sorting_analyzer(sorting=clean_sorting,
                                               recording=analyzer.recording, 
                                               format="memory",
                                               sparse=False
                                               )

    return clean_analyzer, df_cleaning_summary

def compute_best_split_using_silhouette(splitting_results_dict, result_message, waveforms, method, n_components, max_split, threshold, unit_id, unit_idx, verbose=False, total_numbder_of_unit=None):
    
    # if method == 'phate':
    #     phate_operator = phate.PHATE(n_jobs=-2)
    #     phate_operator.set_params(knn=5, n_components=n_components, verbose=verbose)
    #     principal_components = phate_operator.fit_transform(waveforms)
    if method == 'pca':
        pca = PCA(n_components=n_components)
        principal_components = pca.fit_transform(waveforms)

    linkage_matrix = linkage(principal_components, method='ward')
    
    best_silhouette_score = -1
    for num_clusters in range(2, max_split+1):
        clusters = fcluster(linkage_matrix, t=num_clusters, criterion='maxclust')
        silhouette = silhouette_score(waveforms, clusters)
        if silhouette > best_silhouette_score:
            best_silhouette_score = silhouette
            group_array = clusters
        del clusters, silhouette
    
    group_array = group_array - 1 #spikeinterface need to start from 0 not 1
    if best_silhouette_score < threshold:
        group_array = np.zeros(len(group_array))
    
    if verbose:
        if len(set(group_array)) > 1:
            result_message.append([unit_id, f'Unit {unit_idx+1}/{total_numbder_of_unit}--> {len(set(group_array))} split'])
        else:
            result_message.append([unit_id, f'Unit {unit_idx+1}/{total_numbder_of_unit}--> No split performed'])
    
    splitting_results_dict[unit_id] = {'unit_idx': unit_idx, 'principal_components': principal_components, 'group_array': group_array, 'best_silhouette_score': best_silhouette_score}

def compute_best_split_using_template_as_ref(splitting_results_dict, result_message, template, waveforms, n_components, max_split, unit_id, unit_idx, verbose=False, total_numbder_of_unit=None):
    correlation = np.array([np.corrcoef(template, trace)[0, 1] for trace in waveforms])
    threshold = threshold_otsu(correlation)
    group_array = np.array([0 if np.corrcoef(template, trace)[0, 1] >= threshold else 1 for trace in waveforms])
    
    if verbose:
        if len(set(group_array)) > 1:
            result_message.append([unit_id, f'Unit {unit_idx+1}/{total_numbder_of_unit}--> {len(set(group_array))} split'])
        else:
            result_message.append([unit_id, f'Unit {unit_idx+1}/{total_numbder_of_unit}--> No split performed'])

    splitting_results_dict[unit_id] = {'unit_idx': unit_idx, 'group_array': group_array}


def split_noise_from_unit(analyzer, cs, window, df_cleaning_summary, min_spike_per_unit=50, 
                          threshold=0.2, max_split=10, 
                          save_folder=None, save_plot=None, 
                          method='phate', n_components=10,
                          channel_mode='concatenate',
                          verbose=True,
                          **kwargs):
        
    load_or_compute_extension(analyzer, ['random_spikes', 'templates', 'waveforms'], extension_params={"random_spikes":{"method": "all"}})
    
    new_df_row_list = []
    
    
    with mp.Manager() as manager:
        splitting_results_dict = manager.dict()
        if verbose:
            result_message = manager.list()
        else:
            result_message = None
            
        print('Initializing splitting processes, please wait...')
        processes = []
        for unit_idx, unit_id in enumerate(analyzer.unit_ids):
            waveforms = analyzer.get_extension('waveforms').get_waveforms_one_unit(unit_id=unit_id, force_dense=True)
            if channel_mode == 'concatenate':
                waveforms = waveforms.transpose(0, 2, 1).reshape(waveforms.shape[0], -1)
            elif channel_mode == 'highest':
                waveforms = get_highest_amplitude_channel(waveforms)
            
            if waveforms.shape[0] > min_spike_per_unit:
                if method in ['phate', 'pca']:
                    processes.append(mp.Process(target=compute_best_split_using_silhouette, args=(splitting_results_dict, result_message, waveforms, method, n_components, max_split, threshold, unit_id, unit_idx, verbose, len(analyzer.unit_ids))))
                elif method == 'template_as_ref':
                    template = analyzer.get_extension('templates').get_unit_template(unit_id=unit_id)
                    if channel_mode == 'concatenate':
                        template = template.T.ravel()
                    elif channel_mode == 'highest':
                        template = get_highest_amplitude_channel(np.array([template]))
                    processes.append(mp.Process(target=compute_best_split_using_template_as_ref, args=(template, result_message, waveforms, n_components, max_split, unit_id, unit_idx, verbose, len(analyzer.unit_ids))))
                    save_plot = None
            
    
        for process in processes:
            process.start()
        
        if verbose:
            unit_done_splitting = []
            while len(result_message) != len(processes):
                for message_indx, message_tuple in enumerate(result_message):
                    if message_tuple[0] not in unit_done_splitting:
                        print(message_tuple[1])
                        unit_done_splitting.append(message_tuple[0])
                sleep(0.1)
        else:
            for porcess in processes:
                process.join()

        for unit_id, results_dict in splitting_results_dict.items():
            
                if len(set(results_dict['group_array'])) > 1:
                   
                    cs, new_unit_id_list = perform_split(cs, unit_id, results_dict['group_array'], remove_first_index_unit=False)
    
                    
                    for new_unit_id in new_unit_id_list:
                        current_unit_df_cleaning_summary = df_cleaning_summary[df_cleaning_summary[df_cleaning_summary.columns[-1]] == unit_id]
                        assert len(current_unit_df_cleaning_summary) == 1, "there cannot be two unit with the same id"
                        new_df = current_unit_df_cleaning_summary.copy()
                        new_df['Remove noise by splitting'] = [new_unit_id]
                        new_df_row_list.append(new_df)
                else:                
                    current_unit_df_cleaning_summary = df_cleaning_summary[df_cleaning_summary[df_cleaning_summary.columns[-1]] == unit_id]
                    assert len(current_unit_df_cleaning_summary) == 1, "there cannot be two unit with the same id"
                    new_df = current_unit_df_cleaning_summary.copy()
                    new_df['Remove noise by splitting'] = [unit_id]
                    new_df_row_list.append(new_df)
                    
                
                if save_plot is not None:
                    number_ofcluster = len(np.unique(results_dict['group_array']))
                    fig= plt.figure(figsize=(12,8))
                    ax = fig.add_subplot(111, projection='3d')
                    ax.set_title(f'Unit {unit_id}, {round(results_dict["best_silhouette_score"], 3)}')
                    # Set labels for the axes
                    ax.set_xlabel('Principal Component 1')
                    ax.set_ylabel('Principal Component 2')
                    ax.set_zlabel('Principal Component 3')
                    
                    fig_cluster = plt.figure(figsize=(12,8))
                    fig_cluster.suptitle(f'Unit {unit_id}')
                    ax_indx = 0
                    for group in np.unique(results_dict['group_array']):
                        mask = results_dict['group_array'] == group
                        ax.scatter(results_dict['principal_components'][mask, 0],
                                    results_dict['principal_components'][mask, 1], 
                                    results_dict['principal_components'][mask, 2], 
                                    label=f'Group {group}')
                        waveforms = analyzer.get_extension('waveforms').get_waveforms_one_unit(unit_id=unit_id, force_dense=True)
                        waveforms = get_highest_amplitude_channel(waveforms)
                        ax_indx += 1
                        current_ax_regular = fig_cluster.add_subplot(number_ofcluster, 1, ax_indx)
                        current_ax_regular.set_title(f'{group}, number of spikes: {len(waveforms[mask])}')
                        current_ax_regular.plot(waveforms[mask].T, color='k', alpha=0.1)
                        current_ax_regular.plot(np.median(waveforms[mask].T, axis=1), color='r', alpha=1)
    
                    ax.legend()
                    if not os.path.isdir(f'{save_plot}/cleaning_summary/splitting_summary'):
                        os.makedirs(f'{save_plot}/cleaning_summary/splitting_summary')
                    fig.savefig(f'{save_plot}/cleaning_summary/splitting_summary/Unit{unit_id}_3d')
                    fig_cluster.savefig(f'{save_plot}/cleaning_summary/splitting_summary/Unit{unit_id}_ind_cluster')
                    plt.close('all')
                    
    df_cleaning_summary = pd.concat(new_df_row_list)            
    clean_sorting = cs.sorting
    if save_folder is not None:
        clean_analyzer = create_sorting_analyzer(sorting=clean_sorting,
                                                recording=analyzer.recording,
                                                format="binary_folder",
                                                return_scaled=True, # this is the default to attempt to return scaled
                                                folder=f"{save_folder}/SortingAnalyzer", 
                                                overwrite=True,
                                                sparse=False
                                                )
    else:
        clean_analyzer = create_sorting_analyzer(sorting=clean_sorting,
                                                recording=analyzer.recording, 
                                                format="memory",
                                                sparse=False
                                                )
    return clean_analyzer, df_cleaning_summary

def rename_unit(recording, cs, window, df_cleaning_summary, save_folder=None):
    
    before_empty_unti_remouval = cs.sorting.get_unit_ids()
    remove_empty_unit_sorting = cs.sorting.remove_empty_units()
    after_empty_unti_remouval = cs.sorting.get_unit_ids()
    removed_unit_id_list = [removed_unit_id for removed_unit_id in before_empty_unti_remouval if removed_unit_id not in after_empty_unti_remouval]
    for removed_unit_id in removed_unit_id_list:
        print(f'Unit {removed_unit_id} removed for empty: spikes number {len(cs.sorting.get_unit_spike_train(unit_id=removed_unit_id))}')
    cs = CurationSorting(sorting=remove_empty_unit_sorting)
    print(f'{len(before_empty_unti_remouval)-len(after_empty_unti_remouval)} units have been remouve for being empty')
    
    number_of_unit = len(cs.sorting.get_unit_ids())
    new_unit_id_list = [unit_id for unit_id in range(number_of_unit)]
    
    new_df_row_list = []
    for old_unit_id, new_unit_id in zip(cs.sorting.get_unit_ids(), new_unit_id_list):
        current_unit_df_cleaning_summary = df_cleaning_summary[df_cleaning_summary[df_cleaning_summary.columns[-1]] == old_unit_id]
        assert len(current_unit_df_cleaning_summary) == 1, "there cannot be two unit with the same id"
        new_df = current_unit_df_cleaning_summary.copy()
        new_df['Rename units'] = [new_unit_id]
        new_df_row_list.append(new_df)
    
    df_cleaning_summary = pd.concat(new_df_row_list) 
    
    cs.rename(new_unit_id_list)
    
    clean_sorting = cs.sorting
    if save_folder is not None:
        clean_analyzer = create_sorting_analyzer(sorting=clean_sorting,
                                               recording=recording,
                                               format="binary_folder",
                                               return_scaled=True, # this is the default to attempt to return scaled
                                               folder=f"{save_folder}/SortingAnalyzer", 
                                               overwrite=True,
                                               sparse=False
                                               )
    else:
        clean_analyzer = create_sorting_analyzer(sorting=clean_sorting,
                                               recording=recording, 
                                               format="memory",
                                               sparse=False
                                               )
    return clean_analyzer, df_cleaning_summary
    
def align_spike(analyzer, df_cleaning_summary, ms_before=1, ms_after=2.5, save_folder=None):
    
    load_or_compute_extension(analyzer,  ['random_spikes', 'waveforms', 'templates'], extension_params={"random_spikes":{"method": "all"}})
    unit_peak_shifts = get_template_extremum_channel_peak_shift(analyzer, peak_sign='neg')
    clean_sorting = align_sorting(analyzer.sorting, unit_peak_shifts) 
    
    new_df_row_list = []
    for unit_id in clean_sorting.get_unit_ids():
        current_unit_df_cleaning_summary = df_cleaning_summary[df_cleaning_summary[df_cleaning_summary.columns[-1]] == unit_id]
        assert len(current_unit_df_cleaning_summary) == 1, "there cannot be two unit with the same id"
        new_df = current_unit_df_cleaning_summary.copy()
        new_df['Align spikes'] = [unit_id]
        new_df_row_list.append(new_df)
    df_cleaning_summary = pd.concat(new_df_row_list) 
    
    if save_folder is not None:
        clean_analyzer = create_sorting_analyzer(sorting=clean_sorting,
                                               recording=analyzer.recording,
                                               format="binary_folder",
                                               return_scaled=True, # this is the default to attempt to return scaled
                                               folder=f"{save_folder}/SortingAnalyzer", 
                                               overwrite=True,
                                               sparse=False, 
                                               )
    else:
        clean_analyzer = create_sorting_analyzer(sorting=clean_sorting,
                                               recording=analyzer.recording, 
                                               format="memory",
                                               sparse=False
                                               )

    return clean_analyzer, df_cleaning_summary

def remove_by_metric(analyzer, cs, window, df_cleaning_summary, 
                     isi_violation_activate=True, isi_threshold_ms=1, isi_violatio_thr=0.2, 
                     min_freq_activate=True, min_freq_threshold_hz_low=0.1, min_freq_threshold_hz_high=50, 
                     presence_ratio_activate=True, presence_ratio_threshold_low=0.9, presence_ratio_threshold_high=1,
                     L_ratio_activate=True, L_ratio_threshold=10, 
                     save_folder=None, **kwargs):
    
    bad_units = []
    if isi_violation_activate:
        isi_violations_ratio, _ = sqm.compute_isi_violations(sorting_analyzer=analyzer, isi_threshold_ms=isi_threshold_ms)
        isi_bad_units = []
        for unit, unit_violatio_ratio in isi_violations_ratio.items():
            if unit_violatio_ratio >= isi_violatio_thr:
                isi_bad_units.append(unit)
        print(f'Units {isi_bad_units} removed for isi violation')
        bad_units = list(set(bad_units + isi_bad_units))
    
    if min_freq_activate:
        units_firing_rate = sqm.compute_firing_rates(sorting_analyzer=analyzer)
        min_freq_bad_units = []
        for unit, unit_firing_rate in units_firing_rate.items():
            if unit_firing_rate <= min_freq_threshold_hz_low or unit_firing_rate >= min_freq_threshold_hz_high:
                min_freq_bad_units.append(unit)

                
        print(f'Units {min_freq_bad_units} removed because of low rate frequency')
        bad_units = list(set(bad_units + min_freq_bad_units))
    
    if presence_ratio_activate:
        units_presence_ratio = sqm.compute_presence_ratios(sorting_analyzer=analyzer)
        presence_ratio_bad_units = []
        for unit, unit_presence_ratio in units_presence_ratio.items():
            if unit_presence_ratio <= presence_ratio_threshold_low or unit_presence_ratio >= presence_ratio_threshold_high:
                presence_ratio_bad_units.append(unit)
        print(f'Units {presence_ratio_bad_units} removed because of low presence ratio')
        bad_units = list(set(bad_units + presence_ratio_bad_units))
    
    if L_ratio_activate:
        load_or_compute_extension(analyzer, ['random_spikes', 'waveforms', 'principal_components'], extension_params={"random_spikes":{"method": "all"},
                                                                                                                      "principal_components":{"n_components":3, "mode":"by_channel_local"}
                                                                                                                      })
        all_pcs, all_labels = analyzer.get_extension("principal_components").get_some_projections()
        all_pcs = analyzer.compute("principal_components", n_components=3, mode="concatenated").get_data()
        
        l_ratio_bad_units = []
        for unit in analyzer.unit_ids:
            _, unit_l_ratio = sqm.pca_metrics.mahalanobis_metrics(all_pcs=all_pcs, all_labels=all_labels, this_unit_id=unit)
            if unit_l_ratio >= L_ratio_threshold:
                l_ratio_bad_units.append(unit)
        print(f'Units {l_ratio_bad_units} removed because of high L-ratio')
        bad_units = list(set(bad_units + l_ratio_bad_units))
        
    cs.remove_units(bad_units)
    clean_sorting = cs.sorting
    
    if len(clean_sorting.get_unit_ids()) == 0:
        raise ValueError('No units ramaining after unit auto cleaning')
    
    new_df_row_list = []
    for unit_id in clean_sorting.get_unit_ids():
        current_unit_df_cleaning_summary = df_cleaning_summary[df_cleaning_summary[df_cleaning_summary.columns[-1]] == unit_id]
        assert len(current_unit_df_cleaning_summary) == 1, "there cannot be two unit with the same id"
        new_df = current_unit_df_cleaning_summary.copy()
        new_df['Remove bad units with metric'] = [unit_id]
        new_df_row_list.append(new_df)
    df_cleaning_summary = pd.concat(new_df_row_list) 
    
    if save_folder is not None:
        clean_analyzer = create_sorting_analyzer(sorting=clean_sorting,
                                               recording=analyzer.recording,
                                               format="binary_folder",
                                               return_scaled=True, # this is the default to attempt to return scaled
                                               folder=f"{save_folder}/SortingAnalyzer", 
                                               overwrite=True,
                                               sparse=False, 
                                               )
    else:
        clean_analyzer = create_sorting_analyzer(sorting=clean_sorting,
                                               recording=analyzer.recording, 
                                               format="memory",
                                               sparse=False
                                               )

    return clean_analyzer, df_cleaning_summary

def plot_cleaning_summary(temp_file_path, sorter_name, save_plot=None):
    
    *_, df_cleaning_summary, plot_data_dict = load_temp_file(temp_file_path, load_df_cleaning_summary=True, load_plot_data_dict=True)
    
    last_cleaning_performed = df_cleaning_summary.columns[-1]
    for unit_id in tqdm(df_cleaning_summary[last_cleaning_performed], desc='Plot cleaning summary', bar_format='{l_bar}{bar}\n'):

        title = f'Unit: {unit_id}, {sorter_name}\n'
        for sup_title, df_cleaning_summary_column_name, data_dict, color in plot_data_dict['figure_data']:
            
            #this need to be done because one base unit can be split into multiple unit 
            current_unit_id = df_cleaning_summary[df_cleaning_summary[last_cleaning_performed] == unit_id][df_cleaning_summary_column_name]
            assert len(current_unit_id) == 1, "there cannot be two unit with the same id"
            current_unit_id = int(current_unit_id)
            
            title = f'{title}Spike {sup_title}: {data_dict[current_unit_id].shape[1]} '
            
        fig = plt.figure(figsize=(15, 12))
        fig.suptitle(title)
        
        ax_indx = 1
        for sup_title, df_cleaning_summary_column_name, data_dict, color in plot_data_dict['figure_data']:
            #this need to be done because one base unit can be split into multiple unit 
            current_unit_id = df_cleaning_summary[df_cleaning_summary[last_cleaning_performed] == unit_id][df_cleaning_summary_column_name]
            assert len(current_unit_id) == 1, "there cannot be two unit with the same id"
            current_unit_id = int(current_unit_id)
            
            current_ax_regular = fig.add_subplot(int(f'{len(plot_data_dict["figure_data"])}1{ax_indx}'))
            current_ax_regular.set_title(sup_title)
            current_ax_regular.plot(data_dict[current_unit_id], alpha=0.1, color=color)
            ax_indx += 1
            
        plt.tight_layout()    
        if save_plot is not None:
            if not os.path.isdir(f'{save_plot}/cleaning_summary'):
                os.makedirs(f'{save_plot}/cleaning_summary')
            plt.savefig(f'{save_plot}/cleaning_summary/Unit{unit_id}')
            plt.close()

def plot_data_dict_maker(title, df_cleaning_summary_column_name, analyzer, color, temp_file_path, unit_id_conversion_dict=None):
    
    *_, plot_data_dict = load_temp_file(temp_file_path, load_plot_data_dict=True)
    load_or_compute_extension(analyzer, ['random_spikes', 'waveforms'], extension_params={"random_spikes":{"method": "all"}})
    data_dict = {}
    for unit_id in analyzer.unit_ids:
        if unit_id_conversion_dict is not None:
            data_dict[unit_id_conversion_dict[unit_id]] = get_highest_amplitude_channel(analyzer.get_extension('waveforms').get_waveforms_one_unit(unit_id=unit_id, force_dense=True)).T
        else:
            data_dict[unit_id] = get_highest_amplitude_channel(analyzer.get_extension('waveforms').get_waveforms_one_unit(unit_id=unit_id, force_dense=True)).T
    
    plot_data_dict['figure_data'].append((title, df_cleaning_summary_column_name, data_dict, color))
    save_temp_file(temp_file_path, plot_data_dict=plot_data_dict)

def erase_temp_file(temp_file_path):
    try:
        # Use shutil.rmtree() to delete the folder and its contents
        shutil.rmtree(temp_file_path)
    except Exception as e:
        print(f"Temp files couldn't be erase': {e}")
        
def load_temp_file(temp_file_path, load_we=False, load_df_cleaning_summary=False, load_plot_data_dict=False): 
    
    we, cs, df_cleaning_summary, plot_data_dict = None, None, None, None
    if load_we:
        if os.path.exists(f'{temp_file_path}/temp_we.pkl'): 
           with open(f'{temp_file_path}/temp_we.pkl', 'rb') as file:
               we = pickle.load(file)
           cs = CurationSorting(sorting=we.sorting)

    if load_df_cleaning_summary is not None:
        if os.path.exists(f'{temp_file_path}/temp_df_cleaning_summary.pkl'): 
            with open(f'{temp_file_path}/temp_df_cleaning_summary.pkl', 'rb') as file:
                df_cleaning_summary = pickle.load(file)

             
    if load_plot_data_dict is not None:
        if os.path.exists(f'{temp_file_path}/temp_plot_data_dict.pkl'): 
            with open(f'{temp_file_path}/temp_plot_data_dict.pkl', 'rb') as file:
                plot_data_dict = pickle.load(file)

    return we, cs, df_cleaning_summary, plot_data_dict

def save_temp_file(temp_file_path, df_cleaning_summary=None, plot_data_dict=None):
    temp_file_to_save_list = []
    if df_cleaning_summary is not None:
        temp_file_to_save_list.append((df_cleaning_summary, 'temp_df_cleaning_summary'))
    if plot_data_dict is not None:
        temp_file_to_save_list.append((plot_data_dict, 'temp_plot_data_dict'))
    
    for file_to_save, file_name_to_save in temp_file_to_save_list:
        with open(f'{temp_file_path}\{file_name_to_save}.pkl', 'wb') as file:
            pickle.dump(file_to_save, file)
            
def clean_unit(base_instance, save_folder=None, save_plot_path=None, *args): 
    
    if not base_instance.pipeline_parameters['unit_auto_cleaning_param']['plot_cleaning_summary']['activate']:
        save_plot=None
    else:
        base_instance.pipeline_parameters['unit_auto_cleaning_param']['plot_cleaning_summary']['cleaning_summary_plot_path'] = save_plot_path
        save_plot = save_plot_path
    
    temp_file_path = f'{save_folder}/splitting_temp_file'
    if not os.path.isdir(temp_file_path):
        os.makedirs(temp_file_path)
        
    save_temp_file(temp_file_path, plot_data_dict={'figure_data': []})

    cs = CurationSorting(sorting=base_instance.analyzer.sorting)
    df_cleaning_summary = pd.DataFrame({'unfilter': base_instance.analyzer.unit_ids})
    if base_instance.pipeline_parameters['unit_auto_cleaning_param']['plot_cleaning_summary']['activate']:
        #plot_data_dict is used to store the waveform of each step of cleaning for the different units
        #df_cleaning_summary will be used to keep track of the change of id each unit had at every step of the cleaning
        if save_plot is not None:
            plot_data_dict_maker('Before cleaning', 'unfilter', base_instance.analyzer, 'r', temp_file_path)
    save_temp_file(temp_file_path, df_cleaning_summary=df_cleaning_summary)
    
    if base_instance.pipeline_parameters['unit_auto_cleaning_param']['remove_edge_artefact']['activate']:
        print('\n##### Remove edge artefact #######')
        if df_cleaning_summary is None or 'Remove edge artefact' not in df_cleaning_summary.columns:
            base_instance.analyzer, df_cleaning_summary = remove_edge_artefact(base_instance.analyzer, cs, df_cleaning_summary, **base_instance.pipeline_parameters['unit_auto_cleaning_param']['remove_edge_artefact'])
            cs = CurationSorting(sorting=base_instance.analyzer.sorting)
            save_temp_file(temp_file_path, df_cleaning_summary=df_cleaning_summary)
        else:
            print('Loading from files')
        print('##################################')
    
    
    if base_instance.pipeline_parameters['unit_auto_cleaning_param']['remove_big_artefact']['activate']:
        print('\n###### Remove big artefact #######')
        if df_cleaning_summary is None or 'Remove big artefact' not in df_cleaning_summary.columns:
            base_instance.analyzer, df_cleaning_summary = remove_big_artefact(base_instance.analyzer, cs, df_cleaning_summary, **base_instance.pipeline_parameters['unit_auto_cleaning_param']['remove_big_artefact'])
            cs = CurationSorting(sorting=base_instance.analyzer.sorting)
            if save_plot is not None:
                plot_data_dict_maker('After cleaning', 'Remove big artefact', base_instance.analyzer, 'g', temp_file_path)
            save_temp_file(temp_file_path, df_cleaning_summary=df_cleaning_summary)
        else:
            print('Loading from files')
        print('##################################')
    
    
    print('\n########## Align spikes ###########')
    if df_cleaning_summary is None or 'Align spikes' not in df_cleaning_summary.columns:
        base_instance.analyzer, df_cleaning_summary = align_spike(base_instance.analyzer, df_cleaning_summary, save_folder=None)
        cs = CurationSorting(sorting=base_instance.analyzer.sorting)
        save_temp_file(temp_file_path, df_cleaning_summary=df_cleaning_summary)
    else:
        print('Loading from files')
    print('##################################')
    
    if base_instance.pipeline_parameters['unit_auto_cleaning_param']['split_multi_unit']['activate']:
        print('\n#### Remove noise by splitting ###')
        if df_cleaning_summary is None or 'Remove noise by splitting' not in df_cleaning_summary.columns:
            base_instance.analyzer, df_cleaning_summary = split_noise_from_unit(base_instance.analyzer, cs, base_instance.Main_GUI_instance.window, df_cleaning_summary, save_plot=save_plot, **base_instance.pipeline_parameters['unit_auto_cleaning_param']['split_multi_unit'])
            cs = CurationSorting(sorting=base_instance.analyzer.sorting)
            save_temp_file(temp_file_path, df_cleaning_summary=df_cleaning_summary)
        else:
            print('Loading from files')
        print('##################################')
    
    if base_instance.pipeline_parameters['unit_auto_cleaning_param']['remove_by_metric']['activate']:
        print('\n## Remove bad units with metric ##')
        if df_cleaning_summary is None or 'Remove bad units with metric' not in df_cleaning_summary.columns:
            base_instance.analyzer, df_cleaning_summary = remove_by_metric(base_instance.analyzer, cs, base_instance.Main_GUI_instance.window, df_cleaning_summary, **base_instance.pipeline_parameters['unit_auto_cleaning_param']['remove_by_metric'])
            save_temp_file(temp_file_path, df_cleaning_summary=df_cleaning_summary)
        else:
            print('Loading from files')
        print('##################################')

    if base_instance.pipeline_parameters['unit_auto_cleaning_param']['rename_unit']['activate']:
        print('\n######### Rename units ##########')
        if df_cleaning_summary is None or 'Rename units' not in df_cleaning_summary.columns:
            cs = CurationSorting(sorting=base_instance.analyzer.sorting) 
            base_instance.analyzer, df_cleaning_summary = rename_unit(base_instance.analyzer.recording, cs, base_instance.Main_GUI_instance.window, df_cleaning_summary, save_folder=save_folder)
            save_temp_file(temp_file_path, df_cleaning_summary=df_cleaning_summary)
            if save_plot is not None:
                plot_data_dict_maker('After splitting', 'Rename units', base_instance.analyzer, 'k', temp_file_path)
        else:
            print('Loading from files')
        print('##################################')
    
    #TODO buged, it seem that units are not properly tracked at each step and il will also be nice to also plot unit that has been remeved to allow manual confirmation that the removing was proper
    # if save_plot is not None:
    #     print('\n###### Plot cleaning summary #####')
    #     plot_cleaning_summary(temp_file_path, sorter_name, save_plot=save_plot)
    #     print('##################################')
    
    erase_temp_file(temp_file_path)
    return base_instance.analyzer   
    