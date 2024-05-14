# -*- coding: utf-8 -*-
"""
Created on Mon Oct 16 17:09:48 2023

@author: Pierre.LE-CABEC
"""
import spikeinterface as si  # import core only
import matplotlib.pyplot as plt
import numpy as np
import os
import phate
import pandas as pd
from spikeinterface.curation import CurationSorting, SplitUnitSorting
from spikeinterface.postprocessing import align_sorting
from tqdm import tqdm
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA
from scipy.cluster.hierarchy import linkage, fcluster
import warnings
import pickle
import shutil
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=RuntimeWarning)


big_artefact_methods = ['mad', 
                        'abs_value']

dimensionality_reduction_method_list = ['pca', 
                                        'phate']

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
        
        new_cs = CurationSorting(parent_sorting=new_sorting)
        if remove_first_index_unit:
            bad_unit = min(new_unit_id_list)
            new_cs.remove_units([bad_unit])
            new_unit_id_list.remove(bad_unit)
            
        return new_cs, new_unit_id_list
    else:
        return cs, [unit_id, ]

def remove_big_artefact(recording, we, cs, df_cleaning_summary, thr, method='mad', save_folder=None):
    
    new_df_row_list = []
    for unit_id in tqdm(we.sorting.get_unit_ids(), desc='Remove big artefact'):
        current_waveforms = we.get_waveforms(unit_id=unit_id)
        #select the highs channel for each spike
        
        new_current_selected_waveforms = get_highest_amplitude_channel(current_waveforms)
        before_cleaning_waveforms = new_current_selected_waveforms.T
        
        if method == 'mad':
            median_absolute_deviation = np.median(np.abs(before_cleaning_waveforms - np.median(before_cleaning_waveforms)))
            threshold = median_absolute_deviation*thr
        elif method == 'abs_value':
            threshold = thr
            
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
        clean_we = si.extract_waveforms(recording, clean_sorting, max_spikes_per_unit=None, folder=f'{save_folder}/we', overwrite=True)
        clean_sorting.save(folder=f'{save_folder}/sorter')
    else:
        clean_we = si.extract_waveforms(recording, clean_sorting, max_spikes_per_unit=None, mode='memory')
        
    return clean_we, df_cleaning_summary

def remove_edge_artefact(recording, we, cs, df_cleaning_summary, df_real_time, save_folder=None, lenght_to_remove=7, trial_length=None):
    
    new_df_row_list = []
    for unit_id in tqdm(we.sorting.get_unit_ids(), desc='Remove edge artefact'):
        spikes = we.sorting.get_unit_spike_train(unit_id=unit_id)
        
        if trial_length is None:
            len_recording = recording.get_duration()
            
        
        # spikes_indx = spikes_edge_filter['spike_indx'].tolist()
        
        mask = np.zeros(len(spikes), dtype=bool)
    #     mask[spikes_indx] = True
    #     cs, new_unit_id_list = perform_split(cs, unit_id, mask, remove_first_index_unit=True) #artefact are label False and will be the first unit formed
    #     for new_unit_id in new_unit_id_list:
    #         current_unit_df_cleaning_summary = df_cleaning_summary[df_cleaning_summary[df_cleaning_summary.columns[-1]] == unit_id]
    #         assert len(current_unit_df_cleaning_summary) == 1, "there cannot be two unit with the same id"
    #         new_df = current_unit_df_cleaning_summary.copy()
    #         new_df['Remove edge artefact'] = [new_unit_id]
    #         new_df_row_list.append(new_df)
   
    # df_cleaning_summary = pd.concat(new_df_row_list)
    # clean_sorting = cs.sorting
    # if save_folder is not None:
    #     clean_we = si.extract_waveforms(recording, clean_sorting, max_spikes_per_unit=None, folder=f'{save_folder}/we', overwrite=True)
    #     clean_sorting.save(folder=f'{save_folder}/sorter')
    # else:
    #     clean_we = si.extract_waveforms(recording, clean_sorting, max_spikes_per_unit=None, mode='memory')

    # return clean_we, df_cleaning_summary

def split_noise_from_unit(recording, we, cs, df_cleaning_summary, min_spike_per_unit=50, 
                          min_silhouette_score_for_splitting=0.2, max_number_of_split=10, 
                          save_folder=None, save_plot=None, mouse=None, delay=None,
                          dimensionality_reduction_method='phate'):
    
    new_df_row_list = []
    unit_id_list = list(we.sorting.get_unit_ids())
    unit_id_list.sort()
    for unit_idx, unit_id in enumerate(unit_id_list):
        waveforms = we.get_waveforms(unit_id=unit_id)
        waveforms = get_highest_amplitude_channel(waveforms)
        
        if waveforms.shape[0] > min_spike_per_unit:
            n_components = 10  # Number of principal components
            if dimensionality_reduction_method == 'phate':
                phate_operator = phate.PHATE(n_jobs=-2)
                phate_operator.set_params(knn=5, n_components=n_components, verbose=False)
                principal_components = phate_operator.fit_transform(waveforms)
            elif dimensionality_reduction_method == 'pca':
                pca = PCA(n_components=n_components)
                principal_components = pca.fit_transform(waveforms)

            linkage_matrix = linkage(principal_components, method='ward')
            
            best_silhouette_score = -1
            for num_clusters in range(2, max_number_of_split+1):
                clusters = fcluster(linkage_matrix, t=num_clusters, criterion='maxclust')
                silhouette = silhouette_score(waveforms, clusters)
                if silhouette > best_silhouette_score:
                    best_silhouette_score = silhouette
                    group_array = clusters
            
            group_array = group_array - 1 #spikeinterface need to start from 0 not 1
            if best_silhouette_score < min_silhouette_score_for_splitting:
                group_array = np.zeros(len(group_array))
            
                    
            if len(set(group_array)) > 1:
                print(f'Unit {unit_idx}/{len(we.sorting.get_unit_ids())}--> {len(set(group_array))} split')

                cs, new_unit_id_list = perform_split(cs, unit_id, group_array, remove_first_index_unit=False)
                
                for new_unit_id in new_unit_id_list:
                    current_unit_df_cleaning_summary = df_cleaning_summary[df_cleaning_summary[df_cleaning_summary.columns[-1]] == unit_id]
                    assert len(current_unit_df_cleaning_summary) == 1, "there cannot be two unit with the same id"
                    new_df = current_unit_df_cleaning_summary.copy()
                    new_df['Remove noise by splitting'] = [new_unit_id]
                    new_df_row_list.append(new_df)
            else:
                print(f'Unit {unit_idx}/{len(we.sorting.get_unit_ids())}--> No split performed')
                
                current_unit_df_cleaning_summary = df_cleaning_summary[df_cleaning_summary[df_cleaning_summary.columns[-1]] == unit_id]
                assert len(current_unit_df_cleaning_summary) == 1, "there cannot be two unit with the same id"
                new_df = current_unit_df_cleaning_summary.copy()
                new_df['Remove noise by splitting'] = [unit_id]
                new_df_row_list.append(new_df)
                
            
            if save_plot is not None:
                number_ofcluster = len(np.unique(group_array))
                fig= plt.figure(figsize=(12,8))
                ax = fig.add_subplot(111, projection='3d')
                ax.set_title(f'Unit {unit_id}, {round(best_silhouette_score, 3)}')
                # Set labels for the axes
                ax.set_xlabel('Principal Component 1')
                ax.set_ylabel('Principal Component 2')
                ax.set_zlabel('Principal Component 3')
                
                fig_cluster = plt.figure(figsize=(12,8))
                fig_cluster.suptitle(f'Unit {unit_id}')
                ax_indx = 0
                for group in np.unique(group_array):
                    mask = group_array == group
                    ax.scatter(principal_components[mask, 0],
                               principal_components[mask, 1], 
                               principal_components[mask, 2], 
                               label=f'Group {group}')
                    ax_indx += 1
                    current_ax_regular = fig_cluster.add_subplot(int(f'{number_ofcluster}1{ax_indx}'))
                    current_ax_regular.set_title(f'{group}, number of spikes: {len(waveforms[mask])}')
                    current_ax_regular.plot(waveforms[mask].T, color='k', alpha=0.1)
                    current_ax_regular.plot(np.median(waveforms[mask].T, axis=1), color='r', alpha=1)

                ax.legend()
                if not os.path.isdir(f'{save_plot}/cleaning_summary/splitting_summary'):
                    os.makedirs(f'{save_plot}/cleaning_summary/splitting_summary')
                fig.savefig(f'{save_plot}/cleaning_summary/splitting_summary/{mouse}_{delay}_Unit{unit_id}_3d')
                fig_cluster.savefig(f'{save_plot}/cleaning_summary/splitting_summary/{mouse}_{delay}_Unit{unit_id}_ind_cluster')
                plt.close('all')
                
        else:
            cs.remove_unit(unit_id=unit_id)
            print(f'Unit {unit_idx}/{len(we.sorting.get_unit_ids())}--> Unit removed for not enought spike')
    
    df_cleaning_summary = pd.concat(new_df_row_list)            
    clean_sorting = cs.sorting
    if save_folder is not None:
        clean_we = si.extract_waveforms(recording, clean_sorting, max_spikes_per_unit=None, folder=f'{save_folder}/we', overwrite=True)
        clean_sorting.save(folder=f'{save_folder}/sorter')
    else:
        clean_we = si.extract_waveforms(recording, clean_sorting, max_spikes_per_unit=None, mode='memory')

    return clean_we, df_cleaning_summary

def rename_unit(recording, cs, df_cleaning_summary, save_folder=None):
    
    before_empty_unti_remouval = cs.sorting.get_unit_ids()
    remove_empty_unit_sorting = cs.sorting.remove_empty_units()
    after_empty_unti_remouval = cs.sorting.get_unit_ids()
    removed_unit_id_list = [removed_unit_id for removed_unit_id in before_empty_unti_remouval if removed_unit_id not in after_empty_unti_remouval]
    for removed_unit_id in removed_unit_id_list:
        print(f'Unit {removed_unit_id} removed for empty: spikes number {len(cs.sorting.get_unit_spike_train(unit_id=removed_unit_id))}')
    cs = CurationSorting(parent_sorting=remove_empty_unit_sorting)
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
        clean_we = si.extract_waveforms(recording, clean_sorting, max_spikes_per_unit=None, folder=f'{save_folder}/we', overwrite=True)
        clean_sorting.save(folder=f'{save_folder}/sorter')
    else:
        clean_we = si.extract_waveforms(recording, clean_sorting, max_spikes_per_unit=None, mode='memory')
    
    return clean_we, df_cleaning_summary
    
def align_spike(we, recording, df_cleaning_summary, save_folder=None):

    unit_peak_shifts = si.get_template_extremum_channel_peak_shift(we, peak_sign='neg')
    clean_sorting = align_sorting(we.sorting, unit_peak_shifts) 
    
    new_df_row_list = []
    for unit_id in clean_sorting.get_unit_ids():
        current_unit_df_cleaning_summary = df_cleaning_summary[df_cleaning_summary[df_cleaning_summary.columns[-1]] == unit_id]
        assert len(current_unit_df_cleaning_summary) == 1, "there cannot be two unit with the same id"
        new_df = current_unit_df_cleaning_summary.copy()
        new_df['Align spikes'] = [unit_id]
        new_df_row_list.append(new_df)
    df_cleaning_summary = pd.concat(new_df_row_list) 
    
    if save_folder is not None:
        clean_we = si.extract_waveforms(recording, clean_sorting, max_spikes_per_unit=None, folder=f'{save_folder}/we', overwrite=True)
        clean_sorting.save(folder=f'{save_folder}/sorter')
    else:
        clean_we = si.extract_waveforms(recording, clean_sorting, max_spikes_per_unit=None, mode='memory')

    return clean_we, df_cleaning_summary

def plot_cleaning_summary(temp_file_path, mouse, delay, sorter_name, save_plot=None):
    
    *_, df_cleaning_summary, plot_data_dict = load_temp_file(temp_file_path, load_df_cleaning_summary=True, load_plot_data_dict=True)
    
    last_cleaning_performed = df_cleaning_summary.columns[-1]
    for unit_id in tqdm(df_cleaning_summary[last_cleaning_performed], desc='Plot cleaning summary'):

        title = f'{mouse}, {delay}, Unit: {unit_id}, {sorter_name}\n'
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
            plt.savefig(f'{save_plot}/cleaning_summary/{mouse}_{delay}_Unit{unit_id}')
            plt.close()

def plot_data_dict_maker(title, df_cleaning_summary_column_name, we, color, temp_file_path, unit_id_conversion_dict=None):
    
    *_, plot_data_dict = load_temp_file(temp_file_path, load_plot_data_dict=True)
    
    data_dict = {}
    for unit_id in we.sorting.get_unit_ids():
        if unit_id_conversion_dict is not None:
            data_dict[unit_id_conversion_dict[unit_id]] = get_highest_amplitude_channel(we.get_waveforms(unit_id=unit_id)).T
        else:
            data_dict[unit_id] = get_highest_amplitude_channel(we.get_waveforms(unit_id=unit_id)).T
    
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
           cs = CurationSorting(parent_sorting=we.sorting)

    if load_df_cleaning_summary is not None:
        if os.path.exists(f'{temp_file_path}/temp_df_cleaning_summary.pkl'): 
            with open(f'{temp_file_path}/temp_df_cleaning_summary.pkl', 'rb') as file:
                df_cleaning_summary = pickle.load(file)

             
    if load_plot_data_dict is not None:
        if os.path.exists(f'{temp_file_path}/temp_plot_data_dict.pkl'): 
            with open(f'{temp_file_path}/temp_plot_data_dict.pkl', 'rb') as file:
                plot_data_dict = pickle.load(file)

    return we, cs, df_cleaning_summary, plot_data_dict

def save_temp_file(temp_file_path, we=None, df_cleaning_summary=None, plot_data_dict=None):
    temp_file_to_save_list = []
    if we is not None:
        temp_file_to_save_list.append((we, 'temp_we'))
    if df_cleaning_summary is not None:
        temp_file_to_save_list.append((df_cleaning_summary, 'temp_df_cleaning_summary'))
    if plot_data_dict is not None:
        temp_file_to_save_list.append((plot_data_dict, 'temp_plot_data_dict'))
    
    for file_to_save, file_name_to_save in temp_file_to_save_list:
        with open(f'{temp_file_path}\{file_name_to_save}.pkl', 'wb') as file:
            pickle.dump(file_to_save, file)
            
def clean_unit(sorter, recording, cleaning_param, save_folder=None, sorter_name=None, save_plot=None, *args): 
    
    temp_file_path = f'{save_folder}/splitting_temp_file'
    if not os.path.isdir(temp_file_path):
        os.makedirs(temp_file_path)
        we, cs, df_cleaning_summary = None, None, None
        save_temp_file(temp_file_path, plot_data_dict={'figure_data': []})
    else:
        we, cs, df_cleaning_summary, _ = load_temp_file(temp_file_path, load_we=True, load_df_cleaning_summary=True, load_plot_data_dict=True)
        
        
    print('\n######### Extract unfilter waveforms #########')
    if we is None:
        we = si.extract_waveforms(recording, sorter, max_spikes_per_unit=None, mode='memory')
        cs = CurationSorting(parent_sorting=we.sorting)
        df_cleaning_summary = pd.DataFrame({'unfilter': we.sorting.get_unit_ids()})
        if cleaning_param['plot_cleaning_summary']['activate']:
            #plot_data_dict is used to store the waveform of each step of cleaning for the different units
            #df_cleaning_summary will be used to keep track of the change of id each unit had at every step of the cleaning
            plot_data_dict_maker('Before cleaning', 'unfilter', we, 'r', temp_file_path)
        save_temp_file(temp_file_path, we=we, df_cleaning_summary=df_cleaning_summary)
    else:
        print('Loading from files')
    print('##############################################')
    
    if cleaning_param['remove_edge_artefact']['activate']:
        print('\n########### Remove edge artefact #############')
        if df_cleaning_summary is None or 'Remove edge artefact' not in df_cleaning_summary.columns:
            we, df_cleaning_summary = remove_edge_artefact(recording, we, cs, df_cleaning_summary, 
                                                           **cleaning_param['remove_edge_artefact'])
            cs = CurationSorting(parent_sorting=we.sorting)
            save_temp_file(temp_file_path, we=we, df_cleaning_summary=df_cleaning_summary)
        else:
            print('Loading from files')
        print('##############################################')
    
    
    # print('\n############ Remove big artefact #############')
    # if df_cleaning_summary is None or 'Remove big artefact' not in df_cleaning_summary.columns:
    #     we, df_cleaning_summary = remove_big_artefact(recording, we, cs, df_cleaning_summary, thr=15, method='mad')
    #     cs = CurationSorting(parent_sorting=we.sorting)
    #     if plot:
    #         plot_data_dict_maker('After cleaning', 'Remove big artefact', we, 'g', temp_file_path)
    #     save_temp_file(temp_file_path, we=we, df_cleaning_summary=df_cleaning_summary)
    # else:
    #     print('Loading from files')
    # print('##############################################')
    
    
    # print('\n############# Align spikes ###################')
    # if df_cleaning_summary is None or 'Align spikes' not in df_cleaning_summary.columns:
    #     we, df_cleaning_summary = align_spike(we, recording, df_cleaning_summary, save_folder=None)
    #     cs = CurationSorting(parent_sorting=we.sorting)
    #     save_temp_file(temp_file_path, we=we, df_cleaning_summary=df_cleaning_summary)
    # else:
    #     print('Loading from files')
    # print('##############################################')
    

    # print('\n########## Remove noise by splitting #########')
    # if df_cleaning_summary is None or 'Remove noise by splitting' not in df_cleaning_summary.columns:
    #     we, df_cleaning_summary = split_noise_from_unit(recording, we, cs, df_cleaning_summary,
    #                                                         min_silhouette_score_for_splitting=0.2, max_number_of_split=5, 
    #                                                         save_plot=save_plot, 
    #                                                         mouse=mouse, delay=delay)
    #     save_temp_file(temp_file_path, we=we, df_cleaning_summary=df_cleaning_summary)
    # else:
    #     print('Loading from files')
    # print('##############################################')


    # print('\n########## Rename units #########')
    # if df_cleaning_summary is None or 'Rename units' not in df_cleaning_summary.columns:
    #     cs = CurationSorting(parent_sorting=we.sorting) 
    #     we, df_cleaning_summary = rename_unit(recording, cs, df_cleaning_summary, save_folder=save_folder)
    #     save_temp_file(temp_file_path, we=we, df_cleaning_summary=df_cleaning_summary)
    #     if plot:
    #         plot_data_dict_maker('After splitting', 'Rename units', we, 'k', temp_file_path)
    # else:
    #     print('Loading from files')
    # print('##############################################')
    
    # if plot:
    #     print('\n############ Plot cleaning summary ###########')
    #     plot_cleaning_summary(temp_file_path, mouse, delay, sorter_name, save_plot=save_plot)
    #     print('##############################################')
    
    # # erase_temp_file(temp_file_path)
    # return we

if __name__ == "__main__":
    summary = pd.read_excel('C:/local_data/Paper/Data/metadata/metadata_summary.xlsx')
    unit_id_list = summary['unit_id']
    summary_simple = summary.dropna()[['peak_to_valley', 'peak_trough_ratio', 'half_width' ,'recovery_slope']]
    phate_operator = phate.PHATE(n_jobs=-2)
    phate_operator.set_params(knn=5, n_components=10, verbose=True)
    principal_components = phate_operator.fit_transform(summary_simple)
    
    linkage_matrix = linkage(principal_components, method='ward')
    
    best_silhouette_score = -1
    for num_clusters in range(2, 10+1):
        clusters = fcluster(linkage_matrix, t=num_clusters, criterion='maxclust')
        silhouette = silhouette_score(principal_components, clusters)
        if silhouette > best_silhouette_score:
            best_silhouette_score = silhouette
            group_array = clusters
    
    number_ofcluster = len(np.unique(group_array))
    fig= plt.figure(figsize=(12,8))
    ax = fig.add_subplot(111, projection='3d')
    ax.set_title(f'{round(best_silhouette_score, 3)}')
    # Set labels for the axes
    ax.set_xlabel('Principal Component 1')
    ax.set_ylabel('Principal Component 2')
    ax.set_zlabel('Principal Component 3')
    
    for group in np.unique(group_array):
        mask = group_array == group
        ax.scatter(principal_components[mask, 0],
                   principal_components[mask, 1], 
                   principal_components[mask, 2], 
                   label=f'Group {group}')
    
    summary['template_metrics_cluster'] = group_array
    
    
    