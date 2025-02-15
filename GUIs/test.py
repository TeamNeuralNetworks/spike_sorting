import PySimpleGUI as sg

# Sample data for the table
data = [
    ["Alice", "25", "Engineer"],
    ["Bob", "30", "Doctor"],
    ["Charlie", "28", "Artist"]
]
headings = ["Name", "Age", "Profession"]

# Layout
layout = [
    [sg.Table(values=data, headings=headings, 
              auto_size_columns=False, justification='center',
              display_row_numbers=True, key='-TABLE-', enable_events=True, select_mode=sg.TABLE_SELECT_MODE_BROWSE)],

    [sg.Text("Name"), sg.Input(key='-NAME-')],
    [sg.Text("Age"), sg.Input(key='-AGE-')],
    [sg.Text("Profession"), sg.Input(key='-PROF-')],

    [sg.Button("Update"), sg.Button("Exit")]
]

# Create window
window = sg.Window("Editable Table Example", layout)

while True:
    event, values = window.read()
    
    if event == sg.WINDOW_CLOSED or event == "Exit":
        break

    if event == '-TABLE-':  # When user selects a row
        selected_row = values['-TABLE-']
        if selected_row:  # Ensure a row is selected
            row_index = selected_row[0]
            window['-NAME-'].update(data[row_index][0])
            window['-AGE-'].update(data[row_index][1])
            window['-PROF-'].update(data[row_index][2])

    if event == "Update":
        selected_row = values['-TABLE-']
        if selected_row:
            row_index = selected_row[0]
            data[row_index] = [
                values['-NAME-'], 
                values['-AGE-'], 
                values['-PROF-']
            ]
            window['-TABLE-'].update(values=data)  # Refresh table

window.close()
