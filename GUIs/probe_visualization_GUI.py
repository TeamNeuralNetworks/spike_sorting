# -*- coding: utf-8 -*-
"""
Created on Tue Jan 28 15:56:56 2025

@author: Pierre.LE-CABEC
"""
import PySimpleGUI as sg
import matplotlib.pyplot as plt
from probeinterface.plotting import plot_probe
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from additional.toolbox import largest_power_of_ten

class probe_visualization_GUI:
    
    
    def __init__(self):
        self.window = None

        
    def create_window(self, probe, recording):
        # PySimpleGUI layout
     
        layout = [ [sg.Canvas(key='-CANVAS-')] ]

        # Create the window
        if self.window is not None:
            location = self.window.current_location()
            self.window.close()
        else:
            location = None
            
        self.window = sg.Window('Probe visualisation window', layout, element_justification='center', finalize=True, location=location)
        
        self.fig, self.ax = plt.subplots(figsize=(9, 7))
        self.create_figure(probe, recording)
        
    def draw_figure(self, canvas):
        figure_canvas_agg = FigureCanvasTkAgg(self.fig, canvas)
        figure_canvas_agg.draw()
        figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
        return figure_canvas_agg

    
    def create_figure(self, probe, recording):
        plt.ioff()  # Disable interactive mode
    
        # Clear the previous figure from the Tkinter canvas if it exists
        if hasattr(self, 'figure_canvas_agg'):
            self.figure_canvas_agg.get_tk_widget().destroy()  # Remove the old canvas
            
    
        # Clear the existing axes to prevent over-plotting
        self.ax.clear()
    
        
        if probe.contact_ids is not None:
            text_on_contact = probe.contact_ids
        elif recording is not None:
            text_on_contact = [None]*len(recording.channel_ids)
            for indx, device_channel_indice in enumerate(probe.device_channel_indices):
                text_on_contact[indx] = recording.channel_ids[device_channel_indice]
        else:
            text_on_contact = None
            
        _ = plot_probe(probe, ax=self.ax, text_on_contact=text_on_contact, show_channel_on_click=True)
        
        self.fig.tight_layout()
        plt.ion()
    
        # Redraw the figure on the existing canvas
        canvas_elem = self.window['-CANVAS-'].TKCanvas  
        self.figure_canvas_agg = FigureCanvasTkAgg(self.fig, canvas_elem)  # Store it as an instance variable
        self.figure_canvas_agg.draw()
        self.figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
        

    def event_handler(self, values, event, base_instance):
        if event == sg.WIN_CLOSED:
            self.window.close()
            self.window = None

                


        
            