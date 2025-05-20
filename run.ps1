# Set variables
$piUser = "pi"
$piHost = "192.168.192.251"
$remotePath = "/home/pi/Desktop/server.py"
$localPath = ".\server.py"

Write-Output "IP: $piHost
user: $piUser
host: $piHost
remotePath: $remotePath
localpath: $localPath"

# Copy file to Raspberry Pi
scp $localPath "$piUser@${piHost}:$remotePath"

# Run script on Raspberry Pi over SSH
ssh $piUser@$piHost "python3 -u $remotePath"

