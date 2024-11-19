# -*- coding: utf-8 -*-
"""
Created on Mon Oct 23 13:55:43 2023

@author: Pierre.LE-CABEC
"""

from viziphant.statistics import plot_time_histogram
from viziphant.rasterplot import rasterplot_rates
from elephant import statistics, kernels
from elephant.statistics import time_histogram
from neo.core import SpikeTrain
import spikeinterface.widgets as sw
from spikeinterface.core import get_template_amplitudes


from quantities import s, ms
import numpy as np
import math 
from scipy import stats
import os
import multiprocessing as mp
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import quantities as pq
from tqdm import tqdm

from curation.clean_unit import get_highest_amplitude_channel
from additional.toolbox import load_or_compute_extension

def add_event(ax, event_dict):
    if event_dict is not None:
        for event_name in event_dict.keys():
            if 'alpha' in event_dict[event_name].keys():
                alpha = event_dict[event_name]['alpha']
            else:
                alpha = None
                
            if isinstance(event_dict[event_name]['event_time'], (list, tuple)):
                assert len(event_dict[event_name]['event_time']) == 2
                ax.axvspan(event_dict[event_name]['event_time'][0], event_dict[event_name]['event_time'][1], color=event_dict[event_name]['color'], alpha=alpha)
            else:
                ax.axvline(event_dict[event_name]['event_time'], color=event_dict[event_name]['color'], alpha=alpha)
                
def plot_summary_for_unit(unit_id, analyzer, sorter_name, ylim=None, unit_for_plot_name=None, save_path=None, trial_len=9, event_dict=None):
        
    unit_for_plot_name = unit_id if unit_for_plot_name is None else unit_for_plot_name
    
    fig = plt.figure(figsize=(30, 13))
    gs = GridSpec(nrows=3, ncols=7)
    fig.suptitle(f'{sorter_name}\nunits {unit_for_plot_name} (Total spike {analyzer.sorting.get_total_num_spikes()[unit_id]})',)
    ax0 = fig.add_subplot(gs[0, 0:2])
    ax1 = fig.add_subplot(gs[0, 2:4])
    ax1.set_title('Mean firing rate during a trial')
    add_event(ax1, event_dict)
    ax8 = fig.add_subplot(gs[0, 4:6])
    ax8.set_title('zscore firing rate during a trial')
    add_event(ax8, event_dict)
    ax7 = fig.add_subplot(gs[1:3, 0:3])
    ax2 = fig.add_subplot(gs[1, 3:6])
    ax2.set_title('Waveform of the unit')
    ax3 = fig.add_subplot(gs[0, 6])
    ax4 = fig.add_subplot(gs[1, 6], sharey = ax3)
    ax5 = fig.add_subplot(gs[2, 6])
    ax6 = fig.add_subplot(gs[2, 3:6])
    add_event(ax6, event_dict)
    
    window_ms_autocorr = 200
    sw.plot_autocorrelograms(analyzer.sorting, unit_ids=[unit_id], axes=ax0, bin_ms=1, window_ms=window_ms_autocorr, )
    ax0.set_xlim(-(window_ms_autocorr/2), (window_ms_autocorr/2))
    ax0.set_title('Autocorrelogram')
    
    current_spike_train = analyzer.sorting.get_unit_spike_train(unit_id)/analyzer.sampling_frequency
    current_spike_train_list = []
    while len(current_spike_train) > 0: #this loop is to split the spike train into trials with correct duration in seconds
        # Find indices of elements under 9 (9 sec being the duration of the trial)
        indices = np.where(current_spike_train < trial_len)[0]
        if len(indices)>0:
            # Append elements to the result list
            current_spike_train_list.append(SpikeTrain(current_spike_train[indices]*s, t_stop=trial_len))
            # Remove the appended elements from the array
            current_spike_train = np.delete(current_spike_train, indices)
            # Subtract 9 from all remaining elements
        current_spike_train -= trial_len
    
    kernel = kernels.GaussianKernel(sigma=100 * pq.ms)
    rates = statistics.instantaneous_rate(current_spike_train_list,
                                        sampling_period=50 * pq.ms,
                                        kernel=kernel)
    
    edge_effect_bin = math.ceil(100/50)
    time_map = np.arange(0, trial_len, 0.05)
    rates = np.array(rates)
    if trial_len == 9:
        rates = rates[edge_effect_bin:-edge_effect_bin]
        time_map = time_map[edge_effect_bin:-edge_effect_bin]
    rate_zscored = stats.zscore(rates)
    
    mean_rate = np.mean(rate_zscored, axis=1)
    sem_rate = stats.sem(rate_zscored, axis=1)
    time_map = time_map[:len(mean_rate)]
    ax8.plot(time_map, mean_rate)
    ax8.fill_between(time_map, mean_rate+sem_rate, mean_rate-sem_rate, alpha=0.5)
    
    bin_size = 100
    histogram = time_histogram(current_spike_train_list, bin_size=bin_size*ms, output='mean')
    histogram = histogram*(1000/bin_size)
    ax1.set_ylabel('Freqeuncy (Hz)')

    plot_time_histogram(histogram, units='s', axes=ax1)
    ax1.set_xlim(0, trial_len)
    sw.plot_spike_locations(analyzer, unit_ids=[unit_id], ax=ax7, with_channel_ids=True)
    ax7.set_title('Unit localisation')
    sw.plot_unit_waveforms_density_map(analyzer, unit_ids=[unit_id], ax=ax2)
    if ylim is not None:
        ax2.set_ylim(ylim)
        
    template = get_template_amplitudes(analyzer)[unit_id]
    for curent_ax in [
                      ax3, 
                      ax4, 
                      ]:
        max_channel = np.argmax(template)
        template[max_channel] = 0
        current_channel_waveform = analyzer.get_extension('waveforms').get_waveforms_one_unit(unit_id=unit_id, force_dense=True)[:,:,max_channel]
        mean_residual = np.mean(np.abs((current_channel_waveform - current_channel_waveform.mean(axis=0))), axis=0)

        curent_ax.plot(mean_residual)
        curent_ax.set_title('Mean residual of the waveform for channel '+str(analyzer.channel_ids[max_channel]))
        if ylim is not None:
            curent_ax.set_ylim(ylim)
    
    waveform = analyzer.get_extension('waveforms').get_waveforms_one_unit(unit_id=unit_id, force_dense=True)
    waveform = get_highest_amplitude_channel(waveform).T
    ax5.plot(waveform, alpha=0.1, color='b')
    ax5.plot(np.median(waveform, axis=1), color='r', alpha=1)
    ax5.set_title('Waveform of all spike (at max channel)')
    plt.tight_layout()

    rasterplot_rates(current_spike_train_list, ax=ax6, histscale=0.1)
    if save_path is not None:
        os.makedirs(fr'{save_path}\Unit_summary_plot', exist_ok=True)
        plt.savefig(fr'{save_path}\Unit_summary_plot\Unit_{int(unit_for_plot_name)}.pdf')
        
        os.makedirs(fr'{save_path}\Unit_summary_plot\png_version', exist_ok=True)
        plt.savefig(fr'{save_path}\Unit_summary_plot\png_version\Unit_{int(unit_for_plot_name)}.png')
        plt.close()

def parallel_plot_summary(args):
    return plot_summary_for_unit(*args)

def plot_sorting_summary(analyzer, sorter_name, save_extention=False, save_path=None, trial_len=9, acelerate=False, event_dict=None):
    load_or_compute_extension(analyzer, ['random_spikes', 'waveforms', 'templates', 'spike_locations'], save_extention)
    
    max_unit_amplitude = 0
    min_unit_amplitude = 0
    
    for unit_id, template in get_template_amplitudes(analyzer, peak_sign='pos').items():
        current_max_amplitude = template.max()
        if current_max_amplitude > max_unit_amplitude:
            max_unit_amplitude = current_max_amplitude
            
    for unit_id, template in get_template_amplitudes(analyzer, peak_sign='neg').items():
        current_min_amplitude = -1*template.max()
        if current_min_amplitude < min_unit_amplitude:
            min_unit_amplitude = current_min_amplitude
            
    ylim_margin = (max_unit_amplitude-min_unit_amplitude)*0.01
    ylim = (min_unit_amplitude-ylim_margin, max_unit_amplitude+ylim_margin)
    
    if acelerate:
         args = [(unit_id, analyzer.copy(), sorter_name, ylim, None, save_path, trial_len) for unit_id in analyzer.unit_ids]
         with mp.Pool(mp.cpu_count()) as pool:
             pool.map(parallel_plot_summary, args)
    else:
        for unit_id in tqdm(analyzer.unit_ids, desc='Plot sorting summary', bar_format='{l_bar}{bar}\n'):
            plot_summary_for_unit(unit_id, analyzer, sorter_name, ylim, None, save_path, trial_len, event_dict=event_dict)
            