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

from probeinterface.generator import generate_linear_probe, generate_multi_columns_probe, generate_tetrode
from probeinterface.utils import combine_probes
from probeinterface import Probe, ProbeGroup
from probeinterface.plotting import plot_probe
from probeinterface.io import write_probeinterface

from additional.toolbox import get_default_param, availabled_dtype, count_decimals

class probe_tool_GUI:

    def __init__(self):
        
        self.window = None
        self.number_of_possible_shank = 5
        
        self.recording_channel_ids = None
        self.probe = None
        
        self.electrode_row_index_clicked_on = None
    
    def create_base_probe(self, default_input_size=(5,2)):
        electrode_arrangement_layout_dict = {
                                      'linear' : lambda x: [[sg.T("Number of channel"), sg.Input('16', key=('popup_base_info', 'channel_number', f'shank{x}', 'linear'), size=default_input_size)],
                                                            [sg.T('ypitch'), sg.Input('20', key=('popup_base_info', 'ypitch', f'shank{x}', 'linear'), size=default_input_size)],
                                                            [sg.T('contact_shapes'), sg.Combo(['circle', 'rect', 'square'], default_value='circle', key=('popup_base_info', 'contact_shapes', f'shank{x}', 'linear'), enable_events=True)],
                                                            [sg.pin(sg.Column([[sg.T('radius'), sg.Input('6', key=('popup_base_info', 'radius', f'shank{x}', 'linear'), size=(7,2))]], key=('popup_base_info', 'radius_column', f'shank{x}', 'linear'), visible=True))],
                                                            [sg.pin(sg.Column([[sg.T('width'), sg.Input('6', key=('popup_base_info', 'width', f'shank{x}', 'linear'), size=(7,2))]], key=('popup_base_info', 'width_column', f'shank{x}', 'linear'), visible=False))],
                                                            [sg.pin(sg.Column([[sg.T('height'), sg.Input('6', key=('popup_base_info', 'height', f'shank{x}', 'linear'), size=(7,2))]], key=('popup_base_info', 'height_column', f'shank{x}', 'linear'), visible=False))],
                                                            ],
                                       'multi-column' : lambda x: [[sg.T("Number of colmuns"), sg.Input('3', key=('popup_base_info', 'columns_number', f'shank{x}', 'multi-column'), size=default_input_size)],
                                                                   [sg.T("Number of electrode per colmun", tooltip='Can be a single number or one number per column separated by ";"'), sg.Input('10', key=('popup_base_info', 'electrodes_per_columns_number', f'shank{x}', 'multi-column'), size=default_input_size, tooltip='Can be a single number or one number per column separated by ";"')],
                                                                     [sg.T('xpitch'), sg.Input('20', key=('popup_base_info', 'xpitch', f'shank{x}', 'multi-column'), size=default_input_size)],
                                                                     [sg.T('ypitch'), sg.Input('20', key=('popup_base_info', 'ypitch', f'shank{x}', 'multi-column'), size=default_input_size)],
                                                                     [sg.T('y shift per column', tooltip='Can be a single number or one number per column separated by ";"'), sg.Input('0; -37.5; 0', key=('popup_base_info', 'y_shift_per_column', f'shank{x}', 'multi-column'), size=(10, 2), tooltip='Can be a single number or one number per column separated by ";"')],
                                                                     [sg.T('contact_shapes'), sg.Combo(['circle', 'rect', 'square'], default_value='circle', key=('popup_base_info', 'contact_shapes', f'shank{x}', 'multi-column'), enable_events=True)],
                                                                     [sg.pin(sg.Column([[sg.T('radius'), sg.Input('6', key=('popup_base_info', 'radius', f'shank{x}', 'multi-column'), size=(7,2))]], key=('popup_base_info', 'radius_column', f'shank{x}', 'multi-column'), visible=True))],
                                                                     [sg.pin(sg.Column([[sg.T('width'), sg.Input('6', key=('popup_base_info', 'width', f'shank{x}', 'multi-column'), size=(7,2))]], key=('popup_base_info', 'width_column', f'shank{x}', 'multi-column'), visible=False))],
                                                                     [sg.pin(sg.Column([[sg.T('height'), sg.Input('6', key=('popup_base_info', 'height', f'shank{x}', 'multi-column'), size=(7,2))]], key=('popup_base_info', 'height_column', f'shank{x}', 'multi-column'), visible=False))],
                                                                     ],
                                      #TODO currently broken
                                      # 'tetrodes' : lambda x: [[sg.T("Number of tetrodes"), sg.Input('1', key=('popup_base_info', 'number_of_tetrodes', f'shank{x}', 'tetrodes'), size=default_input_size)],
                                      #                           [sg.T('Distance multiplier for the positions'), sg.Input('10.0', key=('popup_base_info', 'r', f'shank{x}', 'tetrodes'), size=default_input_size)],
                                      #                           [sg.T('Distance between tetrodes'), sg.Input('50', key=('popup_base_info', 'distance_between_tetrodes', f'shank{x}', 'tetrodes'), size=default_input_size)],
                                      #                           ],
}
        
        self.electrode_arrangement_list = list(electrode_arrangement_layout_dict.keys())
        default_electrode_arrangement = self.electrode_arrangement_list[0]
        self.electrode_arrangement_dict = {}
        
        default_electrode_arrangement_dict_shank = {'electrode_arrangement': default_electrode_arrangement, 
                                                    'contact_shapes': 'circle'}
        
        shank_rows = []
        for shank_indx in range(1, self.number_of_possible_shank+1):
            shank_visible = True if shank_indx == 1 else False
            
            electrode_arrangement_rows = []
            if shank_visible:
                self.electrode_arrangement_dict[f'shank{shank_indx}'] =  default_electrode_arrangement_dict_shank
            
            for electrode_arrangement in self.electrode_arrangement_list:
                electrode_arrangement_visible = True if electrode_arrangement == default_electrode_arrangement else False
                electrode_arrangement_layout = electrode_arrangement_layout_dict[electrode_arrangement](shank_indx)
                if shank_indx > 1:
                    electrode_arrangement_layout.append([sg.Text("Vertical distance with previous shank"), sg.Input('0', key=('popup_base_info', 'y_distance_with_previous_shank', f'shank{shank_indx}', electrode_arrangement), size=default_input_size)])
                    electrode_arrangement_layout.append([sg.Text("Horizontal distance with previous shank"), sg.Input('150', key=('popup_base_info', 'x_distance_with_previous_shank', f'shank{shank_indx}', electrode_arrangement), size=default_input_size)])
                    
                electrode_arrangement_rows.append([sg.pin(sg.Column(electrode_arrangement_layout, key=('popup_base_info', f'{electrode_arrangement}_column', f'shank{shank_indx}'), visible=electrode_arrangement_visible))])
            
            current_shank_layout = [
                                    [sg.Text('Electrode arrangement'), 
                                     sg.Combo(self.electrode_arrangement_list, default_value=default_electrode_arrangement, key=('popup_base_info', 'electrode_arrangement', f'shank{shank_indx}'), enable_events=True)],
                                    electrode_arrangement_rows,
                                    ]
            
            shank_rows.append([sg.pin(sg.Frame(f'Shank {shank_indx}', current_shank_layout, key=('popup_base_info', 'shank_frame', f'shank{shank_indx}'), visible=shank_visible))])
           
        layout = [
            [sg.Text("Number of shanks"), sg.Combo(list(range(1, 11)), default_value=1, key=('popup_base_info', 'shank_number'), enable_events=True)],
            shank_rows,
            [sg.Button("Generate probe", key=('popup_base_info', 'generate_probe')), sg.Button("Cancel")]
        ]
        
        self.window = sg.Window("Enter base info for probe generation", layout, finalize=True)
    
    def  create_edit_table_window(self, default_input_size=(5,2)):

        self.probe_df = self.probe.to_dataframe()
        if self.probe.device_channel_indices is not None:
            self.probe_df['device_channel_indices'] = self.probe.device_channel_indices
        else:
            self.probe_df['device_channel_indices'] = ''
            
        # Layout
        layout = [
            [sg.Column([[sg.Table(values=self.probe_df.values.tolist(), headings=list(self.probe_df.columns), 
                      auto_size_columns=True, justification='center', num_rows=44, display_row_numbers=False, 
                      key=('edit_table_window', 'probe_param_table'), enable_cell_editing=True, enable_click_events=True,
                      tooltip='contact_ids refere to the name of this channel in your recording (probably set by the amplifier)\ndevice_channel_indices refere the indice of this electrode on the recording (indice 0 is the first trace of the recording)')],
                     [sg.Button("Delete row", k=('edit_table_window', 'delete_row')), sg.Button("add row", k=('edit_table_window', 'add_row')),
                      sg.Button("Set all electrodes to selected value", k=('edit_table_window', 'set_all_electrodes_to_selected_value'))],
                     ]),
            sg.Column([[sg.Canvas(key=('edit_table_window', 'probe_canvas'))],
                       [sg.Button("Update probe", k=('edit_table_window', 'update_probe')), 
                        sg.Button("Use probe for current analyses", k=('edit_table_window', 'use_current_probe')),
                        sg.Button("Save probe", k=('edit_table_window', 'save_probe'))],
                       ])],
        ]
        
        if self.window is not None:
            location = self.window.current_location()
            self.window.close()
        else:
            location = None
            
        self.window = sg.Window('Probe tool', layout, finalize=True, location=location)
        self.fig, self.ax = plt.subplots(figsize=(9, 7))
        self.create_figure()
    
    def create_window(self, mode='create_base_probe', default_input_size=(5,2)):
        self.mode = mode 
        
        if mode == 'create_base_probe':
            self.create_base_probe(default_input_size=default_input_size)
        
        elif mode == 'edit_table_window':
            self.create_edit_table_window(default_input_size=default_input_size)
            
    
    def draw_figure(self, canvas):
        figure_canvas_agg = FigureCanvasTkAgg(self.fig, canvas)
        figure_canvas_agg.draw()
        figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
        return figure_canvas_agg

    
    def create_figure(self):
        plt.ioff()  # Disable interactive mode
    
        # Clear the previous figure from the Tkinter canvas if it exists
        if hasattr(self, 'figure_canvas_agg'):
            self.figure_canvas_agg.get_tk_widget().destroy()  # Remove the old canvas
            
        self.ax.clear()
        
        if self.probe.contact_ids is not None:
            text_on_contact = self.probe.contact_ids
        elif self.recording_channel_ids is not None and self.probe.device_channel_indices is not None:
            text_on_contact = [None]*len(self.recording_channel_ids)
            for indx, device_channel_indice in enumerate(self.probe.device_channel_indices):
                text_on_contact[indx] = self.recording_channel_ids[device_channel_indice]
        else:
            text_on_contact = None
            
        self.contact_poly, self.probe_poly = plot_probe(self.probe, 
                                                        ax=self.ax, 
                                                        text_on_contact=text_on_contact, 
                                                        show_channel_on_click=True)
        
        self.fig.tight_layout()
        plt.ion()
        
        # Redraw the figure on the existing canvas
        canvas_elem = self.window[('edit_table_window', 'probe_canvas')].TKCanvas  
        self.figure_canvas_agg = FigureCanvasTkAgg(self.fig, canvas_elem)  # Store it as an instance variable
        self.figure_canvas_agg.draw()
        self.figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    
    def generate_probe_based_on_popup_base_info(self, values):
        
        probes_list = []
        x_distance_with_previous_shank_list = []
        y_distance_with_previous_shank_list = []
        
        for shank in sorted(self.electrode_arrangement_dict.keys()):
            
            shank_dict = self.electrode_arrangement_dict[shank]
            
            if int(shank.split('shank')[-1]) > 1:
                x_distance_with_previous_shank_list.append(float(values[('popup_base_info', 'x_distance_with_previous_shank', shank, shank_dict['electrode_arrangement'])]))
                y_distance_with_previous_shank_list.append(float(values[('popup_base_info', 'y_distance_with_previous_shank', shank, shank_dict['electrode_arrangement'])]))
            else:
                x_distance_with_previous_shank_list.append(0)
                y_distance_with_previous_shank_list.append(0)
            
            
            if shank_dict['electrode_arrangement'] == 'linear':
                num_elec = int(values[('popup_base_info', 'channel_number', shank, 'linear')])
                ypitch = float(values[('popup_base_info', 'ypitch', shank, 'linear')])
                contact_shapes = values[('popup_base_info', 'contact_shapes', shank, 'linear')]
                if contact_shapes == 'circle':
                    contact_shape_params = {'radius': float(values[('popup_base_info', 'radius', shank, 'linear')])}
                elif contact_shapes == 'square':
                    contact_shape_params = {'width': float(values[('popup_base_info', 'width', shank, 'linear')])}
                elif contact_shapes == 'rect':
                    contact_shape_params = {'height': float(values[('popup_base_info', 'height', shank, 'linear')]),
                                            'width': float(values[('popup_base_info', 'width', shank, 'linear')]),
                                            }
                
                probes_list.append(generate_linear_probe(num_elec=num_elec, ypitch=ypitch, contact_shapes=contact_shapes, contact_shape_params=contact_shape_params))
                
                
            elif shank_dict['electrode_arrangement'] == 'multi-column':
                num_columns = int(values[('popup_base_info', 'columns_number', shank, 'multi-column')])
                if ';' in values[('popup_base_info', 'y_shift_per_column', shank, 'multi-column')]:
                    num_contact_per_column = [int(value) for value in values[('popup_base_info', 'electrodes_per_columns_number', shank, 'multi-column')].split(';')]
                else:
                    num_contact_per_column = int(values[('popup_base_info', 'electrodes_per_columns_number', shank, 'multi-column')])
                    
                xpitch = float(values[('popup_base_info', 'xpitch', shank, 'multi-column')])
                ypitch = float(values[('popup_base_info', 'ypitch', shank, 'multi-column')])
                if ';' in values[('popup_base_info', 'y_shift_per_column', shank, 'multi-column')]:
                    y_shift_per_column = [float(value) for value in values[('popup_base_info', 'y_shift_per_column', shank, 'multi-column')].split(';')]
                else:
                    y_shift_per_column = [float(values[('popup_base_info', 'y_shift_per_column', shank, 'multi-column')]) for columns in range(num_columns)]
                contact_shapes = values[('popup_base_info', 'contact_shapes', shank, 'multi-column')]
                if contact_shapes == 'circle':
                    contact_shape_params = {'radius': float(values[('popup_base_info', 'radius', shank, 'multi-column')])}
                elif contact_shapes == 'square':
                    contact_shape_params = {'width': float(values[('popup_base_info', 'width', shank, 'multi-column')])}
                elif contact_shapes == 'rect':
                    contact_shape_params = {'height': float(values[('popup_base_info', 'height', shank, 'multi-column')]),
                                            'width': float(values[('popup_base_info', 'width', shank, 'multi-column')]),
                                            }
                probes_list.append(generate_multi_columns_probe(num_columns=num_columns, 
                                                                num_contact_per_column=num_contact_per_column, 
                                                                xpitch=xpitch, ypitch=ypitch, 
                                                                y_shift_per_column=y_shift_per_column, 
                                                                contact_shapes=contact_shapes, 
                                                                contact_shape_params=contact_shape_params))
                
            elif shank_dict['electrode_arrangement'] == 'tetrodes':
                r = float(values[('popup_base_info', 'r', shank, 'tetrodes')])
                probegroup = ProbeGroup()
                for i in range(int(values[('popup_base_info', 'number_of_tetrodes', shank, 'tetrodes')])):
                    tetrode = generate_tetrode(r=r)
                    tetrode.move([i * float(values[('popup_base_info', 'distance_between_tetrodes', shank, 'tetrodes')]), 0])
                    probegroup.add_probe(tetrode)   
                probes_list.append(probegroup)
       
        if len(probes_list) == 1:
            probe = probes_list[0]
        else:
            probes = []
            for shank_indx, (probe, x_distance, y_distance) in enumerate(zip(probes_list, x_distance_with_previous_shank_list, y_distance_with_previous_shank_list)):
                if shank_indx == 0:
                    shank_pitch_x = x_distance
                    shank_pitch_y = y_distance
                else:
                    shank_pitch_x += x_distance
                    shank_pitch_y += y_distance
                    
                probe.move([shank_pitch_x, shank_pitch_y])
                probes.append(probe)

            probe = combine_probes(probes)
        
        return probe
    
    def update_probe_df_with_displayed_table(self):
        table_data = self.window[('edit_table_window', 'probe_param_table')].Values  # Replace with your table key
        table_headers = self.window[('edit_table_window', 'probe_param_table')].Widget["columns"]
            
        # Convert to DataFrame
        self.probe_df = pd.DataFrame(table_data, columns=table_headers)
        self.probe_df = self.probe_df.sort_values(by=['x', 'y'])
    
    def convert_df_to_probe(self):
        
        self.update_probe_df_with_displayed_table()
        self.window[('edit_table_window', 'probe_param_table')].update(values=self.probe_df.values.tolist())
        
        probe = Probe(ndim=2, si_units='um')
        shapes = np.array(self.probe_df['contact_shapes'])
        contact_ids = np.array(self.probe_df['contact_ids'])
        shank_ids = np.array(self.probe_df['shank_ids'])
        positions = np.array([self.probe_df['x'], self.probe_df['y']]).T
        shape_params_list = []
        for row_index, row in self.probe_df.iterrows():
            if row['contact_shapes'] == 'circle':
                if 'radius' in self.probe_df.columns:
                    shape_params = {'radius': row['radius']}
                else:
                    shape_params = {'radius': row['width']}
                    
            elif row['contact_shapes'] in ['rect', 'rectangle']:
                if 'width' in self.probe_df.columns:
                    shape_params = {'width': row['width']}
                    if 'height' in self.probe_df.columns:
                        shape_params['height'] = row['width']
                    else:
                        shape_params['height'] = row['width']
                else:
                    shape_params = {'width': row['radius'], 'height': row['radius']}
                
            elif row['contact_shapes'] == 'square':
                if 'width' in self.probe_df.columns:
                    shape_params = {'width': row['width']}
                else:
                    shape_params = {'width': row['radius']}

            shape_params_list.append(shape_params)
        
        probe.set_contacts(positions=positions, 
                            shapes=shapes,
                            shape_params=shape_params_list,
                            contact_ids=contact_ids,
                            shank_ids=shank_ids
                            )
        
        device_channel_indices = self.probe_df['device_channel_indices'].tolist()
        device_channel_indices = [x for x in device_channel_indices if x != '']
        
        if len(device_channel_indices) > 0:
            if len(device_channel_indices) != len(self.probe_df):
                sg.popup_error('Unable to set device_channel_indices. All electrodes must be properly labeled.')
            else:
                probe.set_device_channel_indices(device_channel_indices)
        
        if self.probe.probe_planar_contour is None:
            probe.create_auto_shape()
        else:
            probe.set_planar_contour(self.probe.probe_planar_contour)
            
        return probe
    
    def event_handler(self, values, event, base_instance):
        if event == sg.WIN_CLOSED:
            self.window.close()
            self.window = None
        
        elif event[0] == 'popup_base_info':
            if event[1] == 'cancel':
                self.window.close()
                self.window = None
                
            if event[1] == 'generate_probe':
                self.probe = self.generate_probe_based_on_popup_base_info(values)
                self.window.close()
                self.window = None
                self.create_window(mode='edit_table_window')
            
            elif event[1] == 'shank_number':
                self.shank_number = int(values[event])
                for shank_indx in range(1, self.number_of_possible_shank+1):
                    visible = True if self.shank_number >= shank_indx else False
                    self.window[('popup_base_info', 'shank_frame', f'shank{shank_indx}')].update(visible=visible)
                    if visible:
                        self.electrode_arrangement_dict[f'shank{shank_indx}'] = {'electrode_arrangement': values[('popup_base_info', 'electrode_arrangement', f'shank{shank_indx}')]}
                        if self.electrode_arrangement_dict[f'shank{shank_indx}']['electrode_arrangement'] != 'tetrodes':
                            self.electrode_arrangement_dict[f'shank{shank_indx}']['contact_shapes'] = values[('popup_base_info', 'contact_shapes', f'shank{shank_indx}', self.electrode_arrangement_dict[f'shank{shank_indx}']['electrode_arrangement'])]
                    else:
                        if f'shank{shank_indx}' in self.electrode_arrangement_dict.keys():
                            del self.electrode_arrangement_dict[f'shank{shank_indx}']
                        
            elif event[1] == 'electrode_arrangement':
                self.electrode_arrangement_dict[event[2]] = {'electrode_arrangement': values[event]}
                if values[event] != 'tetrodes':
                    self.electrode_arrangement_dict[event[2]]['contact_shapes'] = values[('popup_base_info', 'contact_shapes', event[2], values[event])]
                    
                for electrode_arrangement in self.electrode_arrangement_list:
                    visible = True if electrode_arrangement == values[event] else False
                    self.window[('popup_base_info', f'{electrode_arrangement}_column', event[2])].update(visible=visible)
            
            elif event[1] == 'contact_shapes':
                radius_visible = False
                width_visible = False
                height_visible = False
                if values[event] == 'circle':
                    radius_visible = True
                elif values[event] == 'square':
                    width_visible = True
                elif values[event] == 'rect':
                    width_visible = True   
                    height_visible = True
                self.window[('popup_base_info', 'radius_column', event[2], event[3])].update(visible=radius_visible)
                self.window[('popup_base_info', 'width_column', event[2], event[3])].update(visible=width_visible)
                self.window[('popup_base_info', 'height_column', event[2], event[3])].update(visible=height_visible)
                
        
        elif event[0] == 'edit_table_window':

            if event[1] == 'delete_row':
                self.probe_df = self.probe_df.drop(self.electrode_row_index_clicked_on)
                self.electrode_row_index_clicked_on = None
                self.window[('edit_table_window', 'probe_param_table')].update(values=self.probe_df.values.tolist())
            
            elif event[1] == 'add_row':
                if self.electrode_row_index_clicked_on is not None:
                    row_to_add = pd.DataFrame([self.probe_df.iloc[self.electrode_row_index_clicked_on]])
                    self.probe_df = pd.concat([self.probe_df.iloc[:self.electrode_row_index_clicked_on], 
                                               row_to_add,
                                               self.probe_df.iloc[self.electrode_row_index_clicked_on:], 
                                               ], ignore_index=True)
                else:
                    row_to_add = pd.DataFrame([self.probe_df.iloc[len(self.probe_df)-1]])
                    print(row_to_add)
                    self.probe_df = pd.concat([self.probe_df, 
                                               row_to_add], ignore_index=True)
                    
                self.window[('edit_table_window', 'probe_param_table')].update(values=self.probe_df.values.tolist())
            
            elif event[1] == 'set_all_electrodes_to_selected_value':
                self.update_probe_df_with_displayed_table()
                slected_value = self.probe_df.iat[self.electrode_row_index_clicked_on, self.electrode_column_index_clicked_on]
                self.probe_df[self.probe_df.columns[self.electrode_column_index_clicked_on]] = slected_value
                self.window[('edit_table_window', 'probe_param_table')].update(values=self.probe_df.values.tolist())
            
            elif event[1] == 'update_probe':
                self.probe = self.convert_df_to_probe()
                self.create_figure()
            
            elif event[1] == 'use_current_probe':
                base_instance.probe = self.probe
                base_instance.Main_GUI_instance.window['Load_probe_file'].update(button_color='green')
            
            elif event[1] == 'save_probe':
                path = sg.popup_get_file('Save probe', save_as=True, no_window=True)
                if path is not None:
                    write_probeinterface(path, self.probe)
                    base_instance.probe = self.probe
                    base_instance.Main_GUI_instance.window['Load_probe_file'].update(button_color='green')
                        

        elif '+CLICKED+' in event:
            if event[0] == ('edit_table_window', 'probe_param_table'):
                if event[2][0] is not None:
                    self.electrode_row_index_clicked_on = event[2][0]
                    self.electrode_column_index_clicked_on = event[2][1]
                    electrode_row_clicked_on = self.probe_df.iloc[event[2][0]]
                        
                    electrode_x_position = electrode_row_clicked_on['x']
                    electrode_y_position = electrode_row_clicked_on['y']
                    
                    if 'radius' in self.probe_df.columns:
                        value_x_to_add = -(electrode_row_clicked_on['radius'])
                        value_y_to_add = 0
                    elif 'height' in self.probe_df.columns:
                        value_x_to_add = electrode_row_clicked_on['width']/2
                        value_y_to_add = electrode_row_clicked_on['height']/2
                    else:
                        value_x_to_add = electrode_row_clicked_on['width']/2
                        value_y_to_add = electrode_row_clicked_on['width']/2
                    
                    color_list = []
                    for i, path in enumerate(self.contact_poly.get_paths()):  # Each path is a polygon
                        vertices = path.vertices  # Array of (x, y) points
                        x_vals, y_vals = vertices[:, 0][0]+value_x_to_add, vertices[:, 1][0]+value_y_to_add
                        if x_vals == electrode_x_position and y_vals == electrode_y_position:
                            color_list.append('red')
                        else:
                            color_list.append('orange')
                    self.contact_poly.set_color(color_list)
                    self.figure_canvas_agg.draw()
                    

            