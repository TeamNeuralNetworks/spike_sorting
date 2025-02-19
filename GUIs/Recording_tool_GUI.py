# -*- coding: utf-8 -*-
"""
Created on Thu May 16 16:52:38 2024

@author: _LMT
"""
import PySimpleGUI as sg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path

from spikeinterface.widgets import plot_traces
from spikeinterface import concatenate_recordings

from additional.toolbox import get_default_param, availabled_dtype, largest_power_of_ten, ephy_extractor_dict, select_folder_file, get_availabled_extension_extractor_converter_dict
from curation.preprocessing import apply_preprocessing

class Recording_tool_GUI:

    def __init__(self):
        
        self.window = {'main_window': None,
                        'window_trace': None,
                        }
        
        self.set_default_param()
    
    def set_default_param(self):
        
        self.selected_recording_index = None
        self.recording_list = []
        
        
        self.base_instance_pipeline_parameters_load_ephy = {}
        
        self.time_slider_resolution = None
        self.time_slider_range = (None, None)
        self.time_window_size = None
        
        self.recording_file_df = pd.DataFrame({'Name': [],
                                                'Recording lenght': [],
                                                'Number of channel': [],
                                                'dtype': [],
                                                'sampling frequency': [],
                                                'File format': []})
    
    def generate_trace_visualization_window(self):
        
        self.time_window_size = 1 if self.recording_list[self.selected_recording_index].get_times()[-1] >= 1 else self.recording_list[self.selected_recording_index].get_times()[-1]
        self.time_slider_resolution = largest_power_of_ten(self.time_window_size)*0.1
        if self.recording_list[self.selected_recording_index].get_times()[-1] > (self.time_slider_resolution*100):
            self.time_slider_range = (self.recording_list[self.selected_recording_index].get_times()[0], self.time_slider_resolution*100)
        else:
            self.time_slider_range = (self.recording_list[self.selected_recording_index].get_times()[0], self.recording_list[self.selected_recording_index].get_times()[-1]-self.time_window_size)
        
        checkbox_channel = [[sg.pin(sg.Checkbox(channel_id, key=f'channel_checkbox_{channel_id}', enable_events=True, default=True))] for channel_id in self.recording_list[self.selected_recording_index].get_channel_ids()]
        checkbox_channel.insert(0, [sg.T('Channels:')])
        checkbox_column = sg.Column(checkbox_channel, size=(200, 300), scrollable=True, vertical_scroll_only=True, expand_y=True)

            
        
        checkbox_channel_column = sg.Column(
            [[checkbox_column], 
             [sg.Button('Select All', key='select_all_channels'), 
             sg.Button('Deselect All', key='deselect_all_channels')],
             [sg.Button('Remove unselected channel', key='removed_unselected_channels')],
             ], expand_y=True
        )
        
        trace_vizualization_layout = [[sg.Canvas(key='-TOOLBAR-'), sg.T(self.recording_file_df.iloc[self.selected_recording_index]['Name'])],
                                         [sg.Canvas(key='-CANVAS-'), checkbox_channel_column],
                                        [
                                            sg.Slider(
                                                orientation='h', key='time_slider', resolution=self.time_slider_resolution, 
                                                expand_x=True, enable_events=True, range=self.time_slider_range, disable_number_display=True,
                                            ), 
                                            sg.Text('Window size'), 
                                            sg.Input(self.time_window_size, key='time_window_size', enable_events=True, size=(7, 1)), 
                                            sg.Text('s')
                                        ],
                                        [
                                            sg.Text(f'Recording length: {self.recording_list[self.selected_recording_index].get_total_duration()}s', key='recording_info_text'), 
                                            sg.Button('preprocess data', k='preprocess', tooltip='The parameters are accessible in the main window param tab'), #TODO cut recording
                                        ],
                                        ]
        
        if self.window['window_trace'] is not None:
            location = self.window['window_trace'].current_location()
            self.window['window_trace'].close()
        else:
            location = None
            
        self.window['window_trace'] = sg.Window('Recording tool visualization', trace_vizualization_layout, finalize=True, location=location)
        
        self.fig, self.ax = plt.subplots(figsize=(9, 7))
        self.create_figure(self.recording_list[self.selected_recording_index].channel_ids, self.recording_list[self.selected_recording_index])
            
    def add_recording(self, load_ephy_param, recording, recording_path):
        self.recording_list.append(recording)
        self.selected_recording_index = len(self.recording_list)-1
        self.recording_file_df  = pd.concat([self.recording_file_df ,
                                        pd.DataFrame({'Name': [Path(recording_path).name],
                                                     'Recording lenght': [self.recording_list[self.selected_recording_index].get_total_duration()],
                                                     'Number of channel': [self.recording_list[self.selected_recording_index].get_num_channels()],
                                                     'dtype': [self.recording_list[self.selected_recording_index].dtype],
                                                     'sampling frequency': [self.recording_list[self.selected_recording_index].get_sampling_frequency()],
                                                     'File format': [load_ephy_param['extractor']],
                                                     })
                                        ])
        
        self.recording_file_df.reset_index(drop=True, inplace=True)
        
        self.window['main_window']['recording_file_table'].update(values=self.recording_file_df.values.tolist())
        self.window['main_window']['recording_file_table'].update(select_rows=[self.selected_recording_index])
    
    def create_window(self, base_instance=None, default_input_size=(5,2)):
    
        # Layout
        layout = [
            [sg.Column([[sg.Table(values=self.recording_file_df.values.tolist(), headings=list(self.recording_file_df.columns), 
                      auto_size_columns=True, justification='center', num_rows=44, display_row_numbers=True, 
                      key='recording_file_table', enable_cell_editing=True, enable_click_events=True,
                      tooltip='contact_ids refere to the name of this channel in your recording (probably set by the amplifier)\ndevice_channel_indices refere the indice of this electrode on the recording (indice 0 is the first trace of the recording)')],
                     [sg.Button("load recording", k= 'load_recording'),
                      sg.Button("Delete recording", k='delete_recording'),
                      sg.Button("Concatenate all recordings", k='concatenate_all_recordings')
                      ],
                     [sg.Button("Save recording", k= 'save_recording'),
                      sg.Button("Use recording for current anlasysis", k='use_recording'),
                         ]
                     ]), 
             sg.Column([[sg.Button("⬆", k='move_up')],
                         [sg.Button("⬇", k='move_down')]]),
            ],
        ]
        
        if self.window['main_window'] is not None:
            location = self.window['main_window'].current_location()
            self.window['main_window'].close()
        else:
            location = None
            
        self.window['main_window'] = sg.Window('Recording tool', layout, finalize=True, location=location)
        
        if base_instance is not None:
            self.base_instance_pipeline_parameters_load_ephy = base_instance.pipeline_parameters['load_ephy']
            if base_instance.recording is not None:
                path_syntax = ephy_extractor_dict[base_instance.pipeline_parameters['load_ephy']['mode']][base_instance.pipeline_parameters['load_ephy']['extractor']]['path_syntax']
                recording_path = f"{base_instance.pipeline_parameters['load_ephy']['extractor_parameters'][path_syntax]}"
                self.add_recording(base_instance.pipeline_parameters['load_ephy'], base_instance.recording, recording_path)
        
        if self.recording_list:
            self.generate_trace_visualization_window()
    
    def draw_figure(self, canvas):
        figure_canvas_agg = FigureCanvasTkAgg(self.fig, canvas)
        figure_canvas_agg.draw()
        figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
        return figure_canvas_agg
    
    def add_toolbar(self, canvas, figure_canvas_agg):
        # Remove previous toolbar if it exists
        if hasattr(self, 'toolbar'):
            self.toolbar.destroy()  # Destroy the previous toolbar widget
    
        # Create a new toolbar
        self.toolbar = NavigationToolbar2Tk(figure_canvas_agg, canvas)
        self.toolbar.update()
        self.toolbar.pack(side='top', fill='both', expand=1)
    
    def create_figure(self, selected_channels, recording, time_range=None):
        plt.ioff()  # Disable interactive mode
    
        # Clear the previous figure from the Tkinter canvas if it exists
        if hasattr(self, 'figure_canvas_agg'):
            self.figure_canvas_agg.get_tk_widget().destroy()  # Remove the old canvas
            
    
        # Clear the existing axes to prevent over-plotting
        self.ax.clear()
        # Replot the traces on the cleared axes
        plot_traces(recording=self.recording_list[self.selected_recording_index], 
                    backend="matplotlib", 
                    ax=self.ax, 
                    channel_ids=selected_channels, 
                    time_range=time_range,
                    show_channel_ids=True)
        
        self.fig.tight_layout()
        plt.ion()
    
        # Redraw the figure on the existing canvas
        canvas_elem = self.window['window_trace']['-CANVAS-'].TKCanvas  
        self.figure_canvas_agg = FigureCanvasTkAgg(self.fig, canvas_elem)  # Store it as an instance variable
        self.figure_canvas_agg.draw()
        self.figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
        
        toolbar_elem = self.window['window_trace']['-TOOLBAR-'].TKCanvas  # Get the Tkinter canvas element from PySimpleGUI for the toolbar
        self.add_toolbar(toolbar_elem, self.figure_canvas_agg)
    
    
    def get_selected_channel(self, values):
        selected_channels = [key.split('channel_checkbox_')[-1] for key, value in values.items() if 'channel_checkbox_' in key and value is True]
        
        if len(selected_channels) == 0:
            sg.popup_error('At least one channel need to be selected')
            return
        
        for indx, channel in enumerate(selected_channels): #this is to prevent crashing when the id are not string in the recording
            if channel not in self.recording_list[self.selected_recording_index].get_channel_ids():
                if int(channel) in self.recording_list[self.selected_recording_index].get_channel_ids():
                    selected_channels[indx] = int(channel)
                elif float(channel) in self.recording_list[self.selected_recording_index].get_channel_ids():
                    selected_channels[indx] = float(channel)
        
        return selected_channels
    
    def redraw_fig(self, values, event):
        try:
            if float(values['time_window_size']) == 0:
                return
        except ValueError:
            return
       
        if event == 'time_window_size':
            self.time_window_size = float(values['time_window_size'])
            
            self.time_slider_resolution = largest_power_of_ten(self.time_window_size)*0.1
            self.window['window_trace']['time_slider'].widget['resolution'] = self.time_slider_resolution
            
            slider_current_postion = float(values['time_slider'])/(self.time_slider_range[0]+self.time_slider_range[1])
            
            time_slider_range_min = float(values['time_slider'])-(self.time_slider_resolution*100*slider_current_postion)
            
            if time_slider_range_min < self.recording_list[self.selected_recording_index].get_times()[0]:
                time_slider_range_min = self.recording_list[self.selected_recording_index].get_times()[0]       
            
            time_slider_range_max = float(values['time_slider'])+self.time_slider_resolution*100*(1-slider_current_postion)
            if time_slider_range_max >= self.recording_list[self.selected_recording_index].get_times()[-1]:
                time_slider_range_max = self.recording_list[self.selected_recording_index].get_times()[-1] - self.time_window_size
            
            self.time_slider_range = (time_slider_range_min, time_slider_range_max)
            self.window['window_trace']['time_slider'].update(range=self.time_slider_range)
        
        if event == 'time_slider': #dynamicly update the range of the slider as it become very hard to control small increamant when recording is long 
            if values['time_slider'] > self.time_slider_range[0]+(self.time_slider_resolution*75) and self.time_slider_range[1] != self.recording_list[self.selected_recording_index].get_times()[-1]:
                time_slider_new_range_min = values['time_slider'] - (self.time_slider_resolution*75)
                time_slider_new_range_max = values['time_slider'] + (self.time_slider_resolution*25)
                if time_slider_new_range_max >= self.recording_list[self.selected_recording_index].get_times()[-1]:
                    time_slider_new_range_max = self.recording_list[self.selected_recording_index].get_times()[-1] - self.time_window_size
                slider_change = True
                    
            elif values['time_slider'] < self.time_slider_range[0]+(self.time_slider_resolution*25) and self.time_slider_range[0] != self.recording_list[self.selected_recording_index].get_times()[0]:
                time_slider_new_range_min = values['time_slider'] - (self.time_slider_resolution*25)
                time_slider_new_range_max = values['time_slider'] + (self.time_slider_resolution*75)
                if time_slider_new_range_min < self.recording_list[self.selected_recording_index].get_times()[0]:
                    time_slider_new_range_min = self.recording_list[self.selected_recording_index].get_times()[0]
                slider_change = True
            
            else:
                slider_change = False
            
            if slider_change:
                self.time_slider_range = (time_slider_new_range_min, time_slider_new_range_max)
                self.window['window_trace']['time_slider'].update(range=self.time_slider_range)
        
        selected_channels = self.get_selected_channel(values)
            
        time_range = (values['time_slider'], values['time_slider']+self.time_window_size)
        self.create_figure(selected_channels, self.recording_list[self.selected_recording_index], time_range=time_range)
        
    def event_handler(self, window, values, event, base_instance):
        if event == sg.WIN_CLOSED :
            if window == self.window['main_window']:
                save_changes_answer = sg.popup_yes_no('Save changes?')
                if save_changes_answer == 'Yes':
                    default_ephy_param = get_default_param()["load_ephy"]
                    default_ephy_param['mode'] = 'from_recording_edition'
                    base_instance.pipeline_parameters['load_ephy'] = default_ephy_param
                    base_instance.recording = self.recording_list[self.selected_recording_index]
                    base_instance.Main_GUI_instance.window['Load_recording'].update(button_color='green')
                else:
                    default_ephy_param = get_default_param()["load_ephy"]
                    default_ephy_param['mode'] = None
                    base_instance.pipeline_parameters['load_ephy'] = default_ephy_param
                    base_instance.recording = None
                    base_instance.Main_GUI_instance.window['Load_recording'].update(button_color='red')
                
                self.window['main_window'].close()
                self.window['main_window'] = None
                if self.window['window_trace'] is not None:
                    self.window['window_trace'].close()
                    self.window['window_trace'] = None
                    
            elif window == self.window['window_trace']:
                self.window['window_trace'].close()
                self.window['window_trace'] = None

        
        elif event == 'time_slider' or event == 'time_window_size' or 'channel_checkbox' in event:
            self.redraw_fig(values, event)
        
        elif event in ['select_all_channels', 'deselect_all_channels']:
            selected_channels = [key for key, value in values.items() if 'channel_checkbox_' in key]
            for selected_channel in selected_channels:
                if event == 'select_all_channels':
                    self.window['window_trace'][selected_channel].update(True)
                else:
                    self.window['window_trace'][selected_channel].update(False)
        
        elif event == 'load_recording':
            base_instance.Main_GUI_instance.additional_GUI_instance_dict['Custom_popup_instance'].create_window(text='Select loading method', 
                                                                                                                buttons=['Load ephy file', 'Load ephy folder', 'Load all file in a folder'], 
                                                                                                                event='load_recordings_answer',
                                                                                                                window_to_call=self.window['main_window'],
                                                                                                                title='Load recording')
        elif event == 'concatenate_all_recordings':
            self.recording_list = [concatenate_recordings(self.recording_list)]
            self.selected_recording_index = 0
            recording_path = 'Concatenated recording'
            self.recording_file_df  = pd.DataFrame({'Name': [Path(recording_path).name],
                                                    'Recording lenght': [self.recording_list[self.selected_recording_index].get_total_duration()],
                                                    'Number of channel': [self.recording_list[self.selected_recording_index].get_num_channels()],
                                                    'dtype': [self.recording_list[self.selected_recording_index].dtype],
                                                    'sampling frequency': [self.recording_list[self.selected_recording_index].get_sampling_frequency()],
                                                    'File format': [base_instance.pipeline_parameters['load_ephy']['extractor']],
                                                    })
            
            self.window['main_window']['recording_file_table'].update(values=self.recording_file_df.values.tolist())
            self.window['main_window']['recording_file_table'].update(select_rows=[self.selected_recording_index])
            self.generate_trace_visualization_window()
            
        elif event == 'load_recordings_answer':
            if values[event] == 'Load ephy file':
                base_instance.Main_GUI_instance.window.write_event_value('Load_ephy_file', "Recording_tool_GUI")
            elif values[event] == 'Load ephy folder':
                base_instance.Main_GUI_instance.window.write_event_value('Load_ephy_folder', "Recording_tool_GUI")
            elif values[event] == 'Load all file in a folder':
                base_instance.Main_GUI_instance.window.write_event_value('Load_multi_ephy_file', "Recording_tool_GUI")
        
        elif event == 'recording_loaded':
            path_syntax = ephy_extractor_dict[base_instance.pipeline_parameters['load_ephy']['mode']][base_instance.pipeline_parameters['load_ephy']['extractor']]['path_syntax']
            if isinstance(base_instance.recording, list):
                for recording_indx, recording in enumerate(base_instance.recording):
                    recording_path = f"{base_instance.pipeline_parameters['load_ephy']['extractor_parameters'][recording_indx][path_syntax]}"
                    self.add_recording(base_instance.pipeline_parameters['load_ephy'], recording, recording_path)
            else:
                recording_path = f"{base_instance.pipeline_parameters['load_ephy']['extractor_parameters'][path_syntax]}"
                self.add_recording(base_instance.pipeline_parameters['load_ephy'], base_instance.recording, recording_path)
            self.generate_trace_visualization_window()
            base_instance.recording = None
        
        elif event == 'delete_recording':
            del self.recording_list[self.selected_recording_index]
            self.recording_file_df.drop(index=self.selected_recording_index, inplace=True)
            self.recording_file_df.reset_index(drop=True, inplace=True)
            
            self.window['main_window']['recording_file_table'].update(values=self.recording_file_df.values.tolist())
            
            if len(self.recording_list) == 0:
                self.window['window_trace'].close()
                self.window['window_trace'] = None
            else:
                if self.selected_recording_index == len(self.recording_list):
                    self.selected_recording_index -= 1
                self.generate_trace_visualization_window()
                self.window['main_window']['recording_file_table'].update(select_rows=[self.selected_recording_index])
                
        elif event == 'preprocess':
            self.recording_list[self.selected_recording_index] = apply_preprocessing(self.recording_list[self.selected_recording_index], base_instance.pipeline_parameters['preprocessing_param'], base_instance.Main_GUI_instance.window)
            self.redraw_fig(values, event)
            self.recording_file_df.at[self.selected_recording_index,'dtype'] = self.recording_list[self.selected_recording_index].dtype
            self.window['main_window']['recording_file_table'].update(values=self.recording_file_df.values.tolist())
            self.window['main_window']['recording_file_table'].update(select_rows=[self.selected_recording_index])
        
        elif event == 'removed_unselected_channels':
            selected_channels = self.get_selected_channel(values)
            self.recording_list[self.selected_recording_index] = self.recording_list[self.selected_recording_index].select_channels(selected_channels)
            self.redraw_fig(values, event)
            [self.window['window_trace'][key].update(visible=False) for key, value in values.items() if 'channel_checkbox_' in key and value is False]
            self.recording_file_df.at[self.selected_recording_index, 'Number of channel'] = self.recording_list[self.selected_recording_index].get_num_channels()
            self.window['main_window']['recording_file_table'].update(values=self.recording_file_df.values.tolist())
            self.window['main_window']['recording_file_table'].update(select_rows=[self.selected_recording_index])
            
        elif event == 'move_up' or event == 'move_down':
            if event == 'move_up' and self.selected_recording_index > 0:
                new_index = self.selected_recording_index - 1
                move = True
            elif event == 'move_down' and self.selected_recording_index < len(self.recording_list)-1:
                new_index = self.selected_recording_index + 1
                move = True
            else:
                move = False
            
            if move:
                index_list = list(range(len(self.recording_list)))
                index_list[self.selected_recording_index] = index_list[new_index]
                index_list[new_index] = self.selected_recording_index
                
                self.recording_list = list(np.array(self.recording_list)[index_list])
                self.recording_file_df = self.recording_file_df.loc[index_list].reset_index(drop=True)
                
                self.selected_recording_index = new_index
                
                self.window['main_window']['recording_file_table'].update(values=self.recording_file_df.values.tolist())
                self.window['main_window']['recording_file_table'].update(select_rows=[self.selected_recording_index])
        
        elif event == 'save_recording':
            path = sg.popup_get_file('Save selected recording', save_as=True, no_window=True)
            if path is not None:
                self.recording_list[self.selected_recording_index].save_to_folder(path)
            
        elif event == 'use_recording':
            if len(self.recording_list) == 0:
                sg.popup_error('At least one recording must be selected to continue.')
            else:
                response = 'Yes'
                if len(self.recording_list) > 1:
                    response = sg.popup_yes_no('Only the selected recording will be use.\nContinue and quit recording edition?')
                if response == 'Yes':
                    default_ephy_param = get_default_param()["load_ephy"]
                    default_ephy_param['mode'] = 'from_recording_edition'
                    base_instance.pipeline_parameters['load_ephy'] = default_ephy_param
                    base_instance.recording = self.recording_list[self.selected_recording_index]
                    base_instance.Main_GUI_instance.window['Load_recording'].update(button_color='green')
                    self.window['main_window'].close()
                    self.window['main_window'] = None
                    if self.window['window_trace'] is not None:
                        self.window['window_trace'].close()
                        self.window['window_trace'] = None
                        
            
        elif '+CLICKED+' in event:
            if event[2][0] is not None:
                self.row_index_clicked_on = event[2][0]
                self.column_index_clicked_on = event[2][1]
                self.selected_recording_index = self.row_index_clicked_on
                self.generate_trace_visualization_window()
                
