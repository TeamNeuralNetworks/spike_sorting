# -*- coding: utf-8 -*-
"""
Created on Thu May 16 16:52:38 2024

@author: _LMT
"""
import PySimpleGUI as sg
from probeinterface.generator import generate_linear_probe, generate_multi_columns_probe, generate_tetrode
from probeinterface.utils import combine_probes
from probeinterface import Probe, ProbeGroup

from additional.toolbox import get_default_param, availabled_dtype

class probe_tool_GUI:

    def __init__(self):
        
        self.window = None
        self.number_of_possible_shank = 5
        
    def create_window(self, mode='create_base_probe', default_input_size=(5,2)):
        
        if mode == 'create_base_probe':
            electrode_arrangement_layout_dict = {
                                          'linear' : lambda x: [[sg.T("Number of channel"), sg.Input('16', key=('popup_base_info', 'channel_number', f'shank{x}', 'linear'), size=default_input_size)],
                                                                [sg.T('ypitch'), sg.Input('20', key=('popup_base_info', 'ypitch', f'shank{x}', 'linear'), size=default_input_size)],
                                                                [sg.T('contact_shapes'), sg.Combo(['circle', 'rect', 'square'], default_value='circle', key=('popup_base_info', 'contact_shapes', f'shank{x}', 'linear'), enable_events=True)],
                                                                [sg.pin(sg.Column([[sg.T('radius'), sg.Input('6', key=('popup_base_info', 'radius', f'shank{x}', 'linear'), size=(7,2))]], key=('popup_base_info', 'radius_column', f'shank{x}', 'linear'), visible=True))],
                                                                [sg.pin(sg.Column([[sg.T('width'), sg.Input('6', key=('popup_base_info', 'width', f'shank{x}', 'linear'), size=(7,2))]], key=('popup_base_info', 'width_column', f'shank{x}', 'linear'), visible=False))],
                                                                [sg.pin(sg.Column([[sg.T('height'), sg.Input('6', key=('popup_base_info', 'height', f'shank{x}', 'linear'), size=(7,2))]], key=('popup_base_info', 'height_column', f'shank{x}', 'linear'), visible=False))],
                                                                ],
                                           'multi-column' : lambda x: [[sg.T("Number of colmuns"), sg.Input('3', key=('popup_base_info', 'columns_number', f'shank{x}', 'multi-column'), size=default_input_size)],
                                                                       [sg.T("Number of electrode per colmun"), sg.Input('10', key=('popup_base_info', 'electrodes_per_columns_number', f'shank{x}', 'multi-column'), size=default_input_size)],
                                                                         [sg.T('xpitch'), sg.Input('20', key=('popup_base_info', 'xpitch', f'shank{x}', 'multi-column'), size=default_input_size)],
                                                                         [sg.T('ypitch'), sg.Input('20', key=('popup_base_info', 'ypitch', f'shank{x}', 'multi-column'), size=default_input_size)],
                                                                         [sg.T('contact_shapes'), sg.Combo(['circle', 'rect', 'square'], default_value='circle', key=('popup_base_info', 'contact_shapes', f'shank{x}', 'multi-column'), enable_events=True)],
                                                                         [sg.pin(sg.Column([[sg.T('radius'), sg.Input('6', key=('popup_base_info', 'radius', f'shank{x}', 'multi-column'), size=(7,2))]], key=('popup_base_info', 'radius_column', f'shank{x}', 'multi-column'), visible=True))],
                                                                         [sg.pin(sg.Column([[sg.T('width'), sg.Input('6', key=('popup_base_info', 'width', f'shank{x}', 'multi-column'), size=(7,2))]], key=('popup_base_info', 'width_column', f'shank{x}', 'multi-column'), visible=False))],
                                                                         [sg.pin(sg.Column([[sg.T('height'), sg.Input('6', key=('popup_base_info', 'height', f'shank{x}', 'multi-column'), size=(7,2))]], key=('popup_base_info', 'height_column', f'shank{x}', 'multi-column'), visible=False))],
                                                                         ],
                                          'tetrodes' : lambda x: [[sg.T("Number of tetrodes"), sg.Input('1', key=('popup_base_info', 'number_of_tetrodes', f'shank{x}', 'tetrodes'), size=default_input_size)],
                                                                    [sg.T('Distance multiplier for the positions'), sg.Input('10.0', key=('popup_base_info', 'r', f'shank{x}', 'tetrodes'), size=default_input_size)],
                                                                    [sg.T('Distance between tetrodes'), sg.Input('50', key=('popup_base_info', 'distance_between_tetrodes', f'shank{x}', 'tetrodes'), size=default_input_size)],
                                                                    ],
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
                    electrode_arrangement_rows.append([sg.pin(sg.Column(electrode_arrangement_layout_dict[electrode_arrangement](shank_indx), key=('popup_base_info', f'{electrode_arrangement}_column', f'shank{shank_indx}'), visible=electrode_arrangement_visible))])
                
                current_shank_layout = [
                                        [sg.Text('Electrode arrangement'), 
                                         sg.Combo(self.electrode_arrangement_list, default_value=default_electrode_arrangement, key=('popup_base_info', 'electrode_arrangement', f'shank{shank_indx}'), size=(10,2), enable_events=True)],
                                        electrode_arrangement_rows,
                                        ]
                
                shank_rows.append([sg.pin(sg.Frame(f'Shank {shank_indx}', current_shank_layout, key=('popup_base_info', 'shank_frame', f'shank{shank_indx}'), visible=shank_visible))])
               
            
            layout = [
                [sg.Text("Number of shanks"), sg.Combo(list(range(1, 11)), default_value=1, key=('popup_base_info', 'shank_number'), enable_events=True)],
                [sg.Text("Vertical distance between shank"), sg.Input('150', key=('popup_base_info', 'x_distance_between_shanks'), size=default_input_size)], 
                [sg.Text("Horizontal distance between shank"), sg.Input('150', key=('popup_base_info', 'y_distance_between_shanks'), size=default_input_size)],
                shank_rows,
                [sg.Button("Generate probe", key=('popup_base_info', 'generate_probe')), sg.Button("Cancel")]
            ]
            
            self.window = sg.Window("Enter base info for probe generation", layout, finalize=True)
        
        elif mode == 'edit_table_window':
        
            #TODO could be nice to be abale to load a dummy probe just so people understand the different parameters
            #need to have a preview of the probe beeing created 
            #might be worth merging with probe visualization GUI
    
            headings = ["contact_positions", 
                        "contact_shapes", 
                        "contact_shape_params", 
                        "contact_plane_axes", 
                        "probe_planar_contour", 
                        "device_channel_indices",
                        "shank_ids"]
            
            data = [['__']*len(headings)]*self.number_of_channel #TODO automaticly load data if probe is not None
            
            input_rows = [[sg.Text(headings_name), sg.Input(key=headings_name, size=default_input_size)] for headings_name in headings]
            
            # Layout
            layout = [
                [sg.Table(values=data, headings=headings, 
                          auto_size_columns=False, justification='center',
                          display_row_numbers=True, key='-TABLE-', enable_events=True, select_mode=sg.TABLE_SELECT_MODE_BROWSE)],
            
                input_rows,
            
                [sg.Button("Update"), sg.Button("Exit")]
            ]
            
            if self.window is not None:
                location = self.window.current_location()
                self.window.close()
            else:
                location = None
                
            self.window = sg.Window('Probe tool', layout, finalize=True, location=location)
    
    def generate_probe_based_on_popup_base_info(self, values):
        
        probes_list = []
        for shank, shank_dict in self.electrode_arrangement_dict.items():
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
                num_contact_per_column = int(values[('popup_base_info', 'electrodes_per_columns_number', shank, 'multi-column')])
                xpitch = float(values[('popup_base_info', 'xpitch', shank, 'multi-column')])
                ypitch = float(values[('popup_base_info', 'ypitch', shank, 'multi-column')])
                contact_shapes = values[('popup_base_info', 'contact_shapes', shank, 'multi-column')]
                if contact_shapes == 'circle':
                    contact_shape_params = {'radius': float(values[('popup_base_info', 'radius', shank, 'multi-column')])}
                elif contact_shapes == 'square':
                    contact_shape_params = {'width': float(values[('popup_base_info', 'width', shank, 'multi-column')])}
                elif contact_shapes == 'rect':
                    contact_shape_params = {'height': float(values[('popup_base_info', 'height', shank, 'multi-column')]),
                                            'width': float(values[('popup_base_info', 'width', shank, 'multi-column')]),
                                            }
                probes_list.append(generate_multi_columns_probe(num_columns=num_columns, num_contact_per_column=num_contact_per_column, xpitch=xpitch, ypitch=ypitch, contact_shapes=contact_shapes, contact_shape_params=contact_shape_params))
                
            elif shank_dict['electrode_arrangement'] == 'tetrodes':
                r = float(values[('popup_base_info', 'r', shank, 'tetrodes-column')])
                probegroup = ProbeGroup()
                for i in range(int(values[('popup_base_info', 'number_of_tetrodes', shank, 'tetrodes-column')])):
                    tetrode = generate_tetrode(r=r)
                    tetrode.move([i * float(values[('popup_base_info', 'distance_between_tetrodes', shank, 'tetrodes-column')]), 0])
                    probegroup.add_probe(tetrode)   
                probes_list.append(probegroup)
       
        if len(probes_list) == 1:
            self.probe = probes_list[0]
        else:
            shank_pitch_x = float(values[('popup_base_info', 'x_distance_between_shanks')])
            shank_pitch_y = float(values[('popup_base_info', 'y_distance_between_shanks')])
            probes = []
            for shank_indx, probe in enumerate(probes_list):
                if shank_indx > 0:
                    probe.move([shank_pitch_x, shank_pitch_y] * shank_indx)
                probes.append(probe)

            self.probe  = combine_probes(probes)
        
    def event_handler(self, values, event, base_instance):
        if event == sg.WIN_CLOSED:
            current_param = self.save_parameters()
            if current_param != base_instance.pipeline_parameters['preprocessing_param']:
                if base_instance.state is not None:
                    save_changes_answer = sg.popup_yes_no('Parameters can not while a analysis is in progress. Close anyway?')
                    if save_changes_answer == 'Yes':
                        self.window.close()
                        self.window = None
                else:
                    save_changes_answer = sg.popup_yes_no('Save changes?')
                    if save_changes_answer == 'Yes':
                        base_instance.pipeline_parameters['preprocessing_param'] = current_param
                    self.window.close()
                    self.window = None
            else:
                self.window.close()
                self.window = None
        
        elif event[0] == 'popup_base_info':
            if event[1] == 'generate_probe':
                self.generate_probe_based_on_popup_base_info(values)
                base_instance.probe = self.probe
            
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
                
        
        elif event[1] == 'table_window':
            if event[1] == 'save':
                response = 'Yes'
                if base_instance.probe is not None:
                    response = sg.popup_yes_no('A probe has already been loaded. Do you want to create a new one and discared it?')
                if response == 'Yes':
                    base_instance.probe = self.probe
                    #TODO attach to recording