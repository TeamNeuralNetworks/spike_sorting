# -*- coding: utf-8 -*-
"""
Created on Thu May 16 16:52:38 2024

@author: _LMT
"""
import PySimpleGUI as sg

class Custom_popup_GUI:

    def __init__(self):
        
        self.window = None
        self.window_to_call = None

    def create_window(self, text, buttons, event, window_to_call, title=''):
        
        self.event = event
        self.window_to_call = window_to_call
        
        layout = [
                 [sg.Text(text)],
                 [[sg.Button(button, k=button) for button in buttons]]
             ]
             
        # Create the window
        self.window = sg.Window("Custom Popup", layout, modal=True, finalize=True)
    

    def event_handler(self, values, event, base_instance):
        if event == sg.WIN_CLOSED:
            self.window.close()
            self.window = None
    
        else:
            self.window.close()
            self.window = None
            self.window_to_call.write_event_value(self.event, event)
