# -*- coding: utf-8 -*-
"""
Created on Tue Jan 28 15:56:56 2025

@author: Pierre.LE-CABEC
"""
import PySimpleGUI as sg
import matplotlib.pyplot as plt
from spikeinterface.widgets import plot_traces
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from additional.toolbox import largest_power_of_ten

class trace_visualization_GUI:
    
    def __init__(self):
        self.window = None
        self.time_slider_resolution = None
        self.time_slider_range = (None, None)
        self.time_window_size = None
        
    def create_window(self, base_instance):
        # PySimpleGUI layout
        self.time_window_size = 1 if base_instance.recording.get_times()[-1] >= 1 else base_instance.recording.get_times()[-1]
        self.time_slider_resolution = largest_power_of_ten(self.time_window_size)*0.1
        if base_instance.recording.get_times()[-1] > (self.time_slider_resolution*100):
            self.time_slider_range = (base_instance.recording.get_times()[0], self.time_slider_resolution*100)
        else:
            self.time_slider_range = (base_instance.recording.get_times()[0], base_instance.recording.get_times()[-1]-self.time_window_size)
        
        checkbox_channel = [[sg.Checkbox(channel_id, key=f'channel_checkbox_{channel_id}', enable_events=True, default=True)] for channel_id in base_instance.recording.get_channel_ids()]
        checkbox_channel.insert(0, [sg.T('Channels:')])
        checkbox_column = sg.Column(checkbox_channel, size=(200, 300), scrollable=True, vertical_scroll_only=True, expand_y=True)
        
        # Buttons for select/deselect all
        checkbox_controls = [
            sg.Button('Select All', key='select_all_channels'), 
            sg.Button('Deselect All', key='deselect_all_channels')
        ]
        
        checkbox_channel_column = sg.Column(
            [[checkbox_column], checkbox_controls], expand_y=True
        )
        
        layout = [
            [sg.Canvas(key='-TOOLBAR-')],
            [sg.Canvas(key='-CANVAS-'), checkbox_channel_column],  # <-- Now side by side
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
                sg.Text(f'Recording length: {base_instance.recording.get_total_duration()}s', key='recording_info_text'), 
                sg.Button('Refresh', key='refresh_button')
            ],
        ]

        # Create the window
        if self.window is not None:
            location = self.window.current_location()
            self.window.close()
        else:
            location = None
            
        self.window = sg.Window('Trace visualisation window', layout, element_justification='center', finalize=True, location=location)
        
        self.fig, self.ax = plt.subplots(figsize=(9, 7))
        self.create_figure(base_instance.recording.channel_ids, base_instance.recording)
        
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
        plot_traces(recording=recording, 
                    backend="matplotlib", 
                    ax=self.ax, 
                    channel_ids=selected_channels, 
                    time_range=time_range,
                    show_channel_ids=True)
        
        self.fig.tight_layout()
        plt.ion()
    
        # Redraw the figure on the existing canvas
        canvas_elem = self.window['-CANVAS-'].TKCanvas  
        self.figure_canvas_agg = FigureCanvasTkAgg(self.fig, canvas_elem)  # Store it as an instance variable
        self.figure_canvas_agg.draw()
        self.figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
        
        toolbar_elem = self.window['-TOOLBAR-'].TKCanvas  # Get the Tkinter canvas element from PySimpleGUI for the toolbar
        self.add_toolbar(toolbar_elem, self.figure_canvas_agg)
    
    def redraw_fig(self, values, event, base_instance):
        try:
            if float(values['time_window_size']) == 0:
                return
        except ValueError:
            return
       
        if event == 'time_window_size':
            self.time_window_size = float(values['time_window_size'])
            
            self.time_slider_resolution = largest_power_of_ten(self.time_window_size)*0.1
            self.window['time_slider'].widget['resolution'] = self.time_slider_resolution
            
            slider_current_postion = float(values['time_slider'])/(self.time_slider_range[0]+self.time_slider_range[1])
            
            time_slider_range_min = float(values['time_slider'])-(self.time_slider_resolution*100*slider_current_postion)
            
            if time_slider_range_min < base_instance.recording.get_times()[0]:
                time_slider_range_min = base_instance.recording.get_times()[0]       
            
            time_slider_range_max = float(values['time_slider'])+self.time_slider_resolution*100*(1-slider_current_postion)
            if time_slider_range_max >= base_instance.recording.get_times()[-1]:
                time_slider_range_max = base_instance.recording.get_times()[-1] - self.time_window_size
            
            self.time_slider_range = (time_slider_range_min, time_slider_range_max)
            self.window['time_slider'].update(range=self.time_slider_range)
        
        if event == 'time_slider': #dynamicly update the range of the slider as it become very hard to control small increamant when recording is long 
            if values['time_slider'] > self.time_slider_range[0]+(self.time_slider_resolution*75) and self.time_slider_range[1] != base_instance.recording.get_times()[-1]:
                time_slider_new_range_min = values['time_slider'] - (self.time_slider_resolution*75)
                time_slider_new_range_max = values['time_slider'] + (self.time_slider_resolution*25)
                if time_slider_new_range_max >= base_instance.recording.get_times()[-1]:
                    time_slider_new_range_max = base_instance.recording.get_times()[-1] - self.time_window_size
                slider_change = True
                    
            elif values['time_slider'] < self.time_slider_range[0]+(self.time_slider_resolution*25) and self.time_slider_range[0] != base_instance.recording.get_times()[0]:
                time_slider_new_range_min = values['time_slider'] - (self.time_slider_resolution*25)
                time_slider_new_range_max = values['time_slider'] + (self.time_slider_resolution*75)
                if time_slider_new_range_min < base_instance.recording.get_times()[0]:
                    time_slider_new_range_min = base_instance.recording.get_times()[0]
                slider_change = True
            
            else:
                slider_change = False
            
            if slider_change:
                self.time_slider_range = (time_slider_new_range_min, time_slider_new_range_max)
                self.window['time_slider'].update(range=self.time_slider_range)
        
        selected_channels = [key.split('channel_checkbox_')[-1] for key, value in values.items() if 'channel_checkbox_' in key and value is True]
        
        if len(selected_channels) == 0:
            sg.popup_error('At least one channel need to be selected')
            return
        
        for indx, channel in enumerate(selected_channels): #this is to prevent crashing when the id are not string in the recording
            if channel not in base_instance.recording.get_channel_ids():
                if int(channel) in base_instance.recording.get_channel_ids():
                    selected_channels[indx] = int(channel)
                elif float(channel) in base_instance.recording.get_channel_ids():
                    selected_channels[indx] = float(channel)
            
        time_range = (values['time_slider'], values['time_slider']+self.time_window_size)
        self.create_figure(selected_channels, base_instance.recording, time_range=time_range)
    
    def event_handler(self, values, event, base_instance):
        if event == sg.WIN_CLOSED:
            self.window.close()
            self.window = None

        elif event == 'time_slider' or event == 'time_window_size' or event == 'refresh_button':
            self.redraw_fig(values, event, base_instance)
        
        elif event in ['select_all_channels', 'deselect_all_channels']:
            selected_channels = [key for key, value in values.items() if 'channel_checkbox_' in key]
            for selected_channel in selected_channels:
                if event == 'select_all_channels':
                    self.window[selected_channel].update(True)
                else:
                    self.window[selected_channel].update(False)
                


        
            