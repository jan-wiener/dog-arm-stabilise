# Set variables
$piUser = "pi"
$piHost = "192.168.216.251"
$remotePath = "/home/pi/Desktop/uploaded_script.py"
$localPath = "C:\Users\janwi\Desktop\robot\main.py"

# Copy file to Raspberry Pi
scp $localPath "$piUser@${piHost}:$remotePath"

# Run script on Raspberry Pi over SSH
ssh $piUser@$piHost "python3 -u $remotePath"

