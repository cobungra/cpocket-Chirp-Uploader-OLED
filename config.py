# config.py

# UPDATED config.py no longer needed, as profiles are now read dynamically from images/ directory.


# Configuration for Pocket Programmer
# mmaproot is the _root_ path to your radio files. Each named radio will have a folder of radioname.
# (Download will create subfolders as needed.)
# Place upload files for the correctly named radios in their respective folders.
# Example: mmaproot = "/home/pi/Radios" might expect /home/pi/Radios/QYT_KT-WP12/green.img ...
# Button 1 selects from PROFILES below to upload, also the radio type and folder for downloads.

# mmaproot = "/home/pi/Radios"

# PROFILES = [ # Name, RGB tuple-unused, filename, radio model 
#     ("NSWJan23",  (0, 1, 0), "NSW_Q6.img","QYT_KT-WP12"),
#     ("VICDec12",  (1, 1, 1), "VIC_Q7.img","QYT_KT-WP12"),
#     ("yellow", (1, 0.3, 0), "yellow.img","QYT_KT-WP12"),
#     ("blue",   (0, 0.1, 1), "blue.img","QYT_KT-WP12"),
#     ("red",    (1, 0, 0), "red.img","QYT_KT-WP12"),
#     ("NSWJan18",   (1, 0.1, 0.1), "NSW_B4.img","Baofeng_UV-5R"),
#     ("VicJan7",   (0, 1, 1), "VIC_B2.img","Baofeng_UV-5R"),
#     ("purple", (0.3, 0, 1), "purple.img","Baofeng_UV-5R"),
# ]