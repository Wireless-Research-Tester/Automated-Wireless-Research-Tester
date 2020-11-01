:: Script to regenerate .py files from the .ui files
pyuic5 graph_mode_ui.ui -o graph_mode_form.py
pyuic5 main_window_ui.ui -o main_window_form.py
pyuic5 meas_display_ui.ui -o meas_display_form.py
pyuic5 pos_control_ui.ui -o pos_control_form.py
pyuic5 progress_ui.ui -o progress_form.py
pyuic5 settings_ui.ui -o settings_form.py
pyuic5 transport_ui.ui -o transport_form.py
