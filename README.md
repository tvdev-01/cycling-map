# A QT based utility to create a heatmap of Garmin activities.

Create an activities directory at same level as python files.
Copy your Garmin fit files to this directory. Thus:

```
    activities
        activity-1.fit
        activity_2.fit
        activity_3.fit
            ...
            ...
    coord_worker.py
    main_helpers.py
    main_print.py
    main.py
    README.md
```
The python script requires the following modules:
```
    pip install folium
    pip install pandas
    pip install numpy
    pip install garmin_fit_sdk
    pip install PyQt6
    pip install PyQt6-WebEngine
```
Run the main.py script.

You can generate a printable png file from within the application.<br>
To control the print area, uncomment and adjust the min/max latitude/longitude to better suit your location in the file `main_print.py`.


