1. Update the data.pairs file from the Google sheets.
2. From the root folder, call `support-scripts/agendas/update_customlocs.py`
3. From the root folder, call `support-scripts/agendas/generate_hbox.py`
  - Then find the `AGENDAS HBOX COPY HERE` comment in the GUI files and replace the HBOX below with the content of `support-scripts/agendas/output.txt` 