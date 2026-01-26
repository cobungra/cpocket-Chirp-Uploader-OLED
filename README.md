# cpocket - Portable Chirp uploader for Raspberry Pi Zero
![pocketpi programmer](https://github.com/cobungra/cpocket/blob/main/assets/OLEDpocket.jpg )

This is a simple device and software to help reprogram ham radios in the field.
The device plugs onto a Raspberry Pi Zero.

With Chirp installed and these python scripts, it can upload preloaded images from the SDcard to the radio, or download the current installed image to a file.

(There are simpler versions of this device which do not need OLED display and dependencies: Refer to https://github.com/cobungra/pocket)


## Quick usage
- Create the desired radio image files using Chirp.
- Save the file as {radioname}_yourtext.img e.g. Baofeng_UV-5R_20260126b.img 
- Copy the images to the /images directory on Pi's SDcard (e.g. into /home/pi/python/pocket/images) using the naming conventions described above.

In the field:
- Run on the Pi (needs GPIO privileges and chirpc accessible in PATH)
- Downloads will be possible when pocket can see an image for required radio in the /images folder. (Otherwise pocket has no way of selecting from the hundreds of possible radio profiles.)
- Use the buttons to upload or download images.

```bash
/path/to/env/bin/python /path/to/pocket.py 
```

## Requires: 
- Raspberry Pi zero or other with the "pocket" GPIO daughterboard (see below)
- Chirp radio software installed (includes chirpc the CLI)
- Required cable from the Pi to the selected radio.

While logged into the pi, `chirpc --list-radios` provides the required {radio} names.
pocket.py uses the radio name at the head of your filename to apply the correct profile for chirpc. 


## In Use:

pocket.py: Three buttons
- Button 1: Select one of the profile names (e.g. Boafeng_KG-UV5_NSW7.img, QYT_KT-WP12_1105v.img ... etc)
- Button 2: Uploads the selected named image using the radioname profile.
- Button 3: Downloads the current image from the radio and saves on the Pi as {radio}_download[n].img in increasing numbers in the /images folder to avoid overwriting existing files.

Stop = Shutdown: Hold Button 3 for two seconds and release. (Pi will shutdown)

---------------------------------------------------------------

Error handling
- Some radios may return transient warnings like: "WARNING: Short reading 1 bytes from the 2 requested." In most cases uploads/downloads still finish successfully.

-------------------------------------------------------------------
## Parts list

PCB or suitable breadboard.

2   20 pin female headers

3   Tactile buttons

1   SSD1306 0.96" display - two colour is nice.


## Construction:

- Straightforward, check the pinout of SSD1306 THEY can DIFFER!
- Perhaps put the pi in a plastic box with exposed pins, but in any case ensure that the board canot short or foul the pi's circuitry!
- I take no reponsibility for unintended consequences of this project.
- The code is minimal and works for me. Improve it as you see fit.


## PCB / Wiring

- GPIO 13 > Switch 1 > Gnd
- GPIO 19 > Switch 2 > Gnd
- GPIO 26 > Switch 3 > Gnd

- GPIO 2  > SSD1306 SDA
- GPIO 3  > SSD1306 SCL
- 3.3v    > SSD1306 Vcc
- Gnd     > SSD1306 Gnd

## Programming in Python venv

This is a good idea because Python will need extensive libraries like luma..

*n.b. These are only examples of code.*

- Create your venv: 
```bash
$ python -m venv pocket
```
- Copy the requirements.txt and the .py files to the env directory
- Activate the venv and install the python requirements
```bash
$ source pocket/bin/activate
(pocket) 
$ pip3 install -r requirements.txt
$ deactivate
```
- Test the program:
```bash
/path/to/env/bin/python /path/to/pocket.py 
```

To run headless I recommend starting the program automatically at boot using systemd. (see docs/autostart for an example)


![PCB](https://github.com/cobungra/cpocket/blob/main/assets/oledpcb.png)



VK3MBT