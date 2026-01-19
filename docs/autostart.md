## Autostart examples

Create a service file:
```
sudo nano /lib/systemd/system/pocket.service
```

Add the configuration like:
```
[Unit]
Description=Pocket programmer
After=multi-user.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/python/pocket/pocket.py
RemainAfterExit=true

[Install]
WantedBy=multi-user.target
```

Pay attention to the exact path where you installed the python script that you are starting.
Change to minimal.py if required..

Save and exit: Ctrl+X, then Ctrl+Y, then Enter

Enable the service:
```
sudo systemctl daemon-reload
sudo systemctl enable pocket.service
```

Reboot the pi

## Useful systemd commands:
``` 
sudo systemclt status pocket.service
sudo systemclt restart pocket.service
etc...
```
