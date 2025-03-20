# -*- coding: utf-8 -*-
"""
Created on Wed Mar 19 19:13:24 2025

@author: Pierre.LE-CABEC
"""

from spikeinterface.extractors import read_intan
from probeinterface.io import read_probeinterface
from spikeinterface.sorters import run_sorter
from spikeinterface.core import create_sorting_analyzer

from plotting.plot_unit_summary import plot_sorting_summary


recording_path = r'C:/local_data/new task/Data/Groupe 5/etape 5 (variation)/jour +30/session 1/05133 Session 1, 18-03-2025/05133 Session 1, 18-03-2025_250318_095113/05133 Session 1, 18-03-2025_250318_095113.rhd'
probe_path = r'C:/local_data/new task/Data/Groupe 5/cerebellum_probe.json'
output_path = r'C:\local_data\new task\Results\groupe 5\test'

sorter_name = 'kilosort2_5'

recording = read_intan(recording_path, stream_id='0')

selected_channels = ['A-040', 'A-041', 'A-042',
'A-043', 'A-044', 'A-045', 'A-046', 'A-047', 'A-048', 'A-049',
'A-050', 'A-051', 'A-052', 'A-053', 'A-054', 'A-055']

recording = recording.select_channels(selected_channels)

probe = read_probeinterface(probe_path)
probe = probe.probes[0]

recording = recording.set_probe(probe)

sorter = run_sorter(sorter_name=sorter_name, recording=recording, docker_image=True, 
                              folder=f"{output_path}/{sorter_name}/base_sorting/SorterOutput")

analyzer = create_sorting_analyzer(sorting=sorter,
                                    recording=recording,
                                    format="binary_folder",
                                    return_scaled=True, # this is the default to attempt to return scaled
                                    folder=f"{output_path}/{sorter_name}/base_sorting/SortingAnalyzer", 
                                    sparse=True,
                                    ms_before=2, ms_after=5,
                                    )

plot_sorting_summary(analyzer, 
                     sorter_name, 
                     save_path=f"{output_path}/{sorter_name}/base_sorting", 
                     # summary_plot_param=self.pipeline_parameters['summary_plot_param'],
                     )