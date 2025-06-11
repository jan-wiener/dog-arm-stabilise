# dog-arm-stabilise
XGO2-Lite robot arm stabilisation



Install the requirements

```powershell
pip install -r requirements.txt
```

Change the IP addresses and ports in server_client.py, server.py (and run.ps1 if you plan to use it)

For the connection to work, you need to have your computer and robot connected to one network, which allows UDP data transfer. It is also theoretically possible to control the robot through the internet if ports forwarding is configured.

When done, you can use run.ps1 to upload server.py to the robot and run it. You'll have to enter the password of the robot's PI two times.
Alternatively, you can other methods to upload server.py onto the robot. i.e. with RealVNC, scp,..

```powershell
.\run.ps1
# might require powershell scripts to be enabled.
```

The client server_client.py can then be ran by running:

```powershell
py .\server_client.py
```

You can control the robot with keyboard or micro:bit.

If you wish to use a micro:bit, you'll need to flash your micro:bit with my code. https://github.com/jan-wiener/serial-transfer-robot-ts/



