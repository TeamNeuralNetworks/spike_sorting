# -*- coding: utf-8 -*-
"""
Created on Thu May 16 16:52:38 2024

@author: _LMT
"""

import PySimpleGUI as sg
from additional.toolbox import get_default_param
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt

from plotting.plot_unit_summary import plot_summary_for_unit
from additional.toolbox import load_or_compute_extension

class sorting_summary_plot_GUI:

    def __init__(self):
        
        self.window = None
        self.active_unit_indx = 0
        self.sorter_name = None
        
    def create_window(self, base_instance, default_input_size=(5,2)):
        
        #TODO add the script from coline to remove noise
        self.sorter_name = base_instance.pipeline_parameters['name']
        
        layout = [
                [sg.Canvas(key='-TOOLBAR-')],
                [sg.Canvas(key='-CANVAS-')],  # <-- Now side by side
                [sg.Column([
                            [sg.B('Previous unit', k='previous'), sg.B('Next unit', k='next'), 
                             sg.Combo(list(base_instance.analyzer.unit_ids), default_value=base_instance.analyzer.unit_ids[self.active_unit_indx], key='unit_combo', enable_events=True),
                             sg.B('Save all summary plot', key='save')]
                           ], justification='center')],
                ]
        
        if self.window is not None:
            location = self.window.current_location()
            self.window.close()
        else:
            location = None
            
        self.window = sg.Window('Preprocessing parameters', layout, finalize=True, location=location)
        
        self.fig = plt.figure(figsize=(16, 7))
        load_or_compute_extension(base_instance.analyzer, ['random_spikes', 'waveforms', 'templates', 'spike_locations'])

        self.create_figure(base_instance.analyzer, base_instance.pipeline_parameters['summary_plot_param'])
    
    def update_canvas(self):
        
        canvas_elem = self.window['-CANVAS-'].TKCanvas  
        self.figure_canvas_agg = FigureCanvasTkAgg(self.fig, canvas_elem)  # Store it as an instance variable
        self.figure_canvas_agg.draw()
        self.figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
        
        toolbar_elem = self.window['-TOOLBAR-'].TKCanvas  # Get the Tkinter canvas element from PySimpleGUI for the toolbar
        self.add_toolbar(toolbar_elem, self.figure_canvas_agg)
        
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
    
    def create_figure(self, analyzer, summary_plot_param):
        plt.ioff()  # Disable interactive mode
        self.fig.clf()
        
        # Clear the previous figure from the Tkinter canvas if it exists
        if hasattr(self, 'figure_canvas_agg'):
            self.figure_canvas_agg.get_tk_widget().destroy()  # Remove the old canvas
            

        # Replot the traces on the cleared axes
        plot_summary_for_unit(unit_id=analyzer.unit_ids[self.active_unit_indx],
                              analyzer=analyzer, 
                              sorter_name=self.sorter_name, 
                              summary_plot_param=summary_plot_param,
                              fig=self.fig,
                              )

        
        self.fig.tight_layout()
        plt.ion()
    
        self.update_canvas()
    
    def event_handler(self, values, event, base_instance):
        if event == sg.WIN_CLOSED:
            self.window.close()
            self.window = None
    
        if event in ['next', 'previous']:
            if event == 'next':
                self.active_unit_indx += 1
            else:
                self.active_unit_indx -= 1
            self.create_figure(base_instance.analyzer, base_instance.pipeline_parameters['summary_plot_param'])
            self.window['unit_combo'].update(value=base_instance.analyzer.unit_ids[self.active_unit_indx])
            
        elif event == 'unit_combo':
            self.active_unit_indx = list(base_instance.analyzer.unit_ids).index(values['unit_combo'])
            self.create_figure(base_instance.analyzer, base_instance.pipeline_parameters['summary_plot_param'])
        
        elif event == 'save':
            pass
            