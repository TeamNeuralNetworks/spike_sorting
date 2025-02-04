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
import matplotlib.pyplot as plt


ephy_folder_path = r'C:/local_data/new task/Results/TEST_250128_114549/TEST_250128_114549.rhd'
recording = se.read_intan(ephy_folder_path, stream_id='0')
recording = spre.bandpass_filter(recording, freq_min=300, freq_max=6000)
recording = spre.common_reference(recording, reference='global', operator='median')
recording.annotate(is_filtered=True)


plt.plot(recording.get_traces()[:,0])

# fig, axes = plt.subplots(recording.get_traces().shape[1], 1, sharex=True, sharey=True)
# for channel_nb, ax in enumerate(axes):
#     ax.plot(recording.get_traces()[:,channel_nb])



# probe = pi.io.read_probeinterface('C:/local_data/new task/Results/TEST_250128_114549/CM16_Buz_Sparse.json')
# probe = probe.probes[0]
# recording = recording.set_probe(probe)

# sorter = ss.run_sorter(sorter_name='spykingcircus2', recording=recording, 
#                               folder=f'C:/local_data/new task/Results/TEST_250128_114549/result/spykingcircus2', verbose=True, 
#                               # **sorter[sorter_name]
#                               )



