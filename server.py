from xgolib import XGO
from xgoedu import XGOEDU



dog = XGO(port='/dev/ttyAMA0',version="xgolite")
version=dog.read_firmware()
if version[0]=='M':
    print('XGO-MINI')
    dog = XGO(port='/dev/ttyAMA0',version="xgomini")
    dog_type='M'
else:
    print('XGO-LITE')
    dog_type='L'


edu = XGOEDU()

dog.load_allmotor()
dog.reset()






import time
import math
import threading

def circle(x0, y0, r, x):
    to_root = r**2 - (x - x0)**2

    if to_root < 0:
        return False
    
    return (y0 + math.sqrt(to_root), y0 - math.sqrt(to_root))


def sequence(x0, y0, r, min, max, step, degoffset = -27):
    degdict = {} # degree dictionary
    i = min-1

    while (i < max) and ((i := i + step) or True):
        if i > -30 and i < -15: r -= 0.12  #### eliptic stabilization 
        if i > -15 and i < 15: r -= 0.34
        if i > 15 and i < 33: r -= 0.3
        angle = math.radians(i)
        degdict[i+degoffset] = [x0+r*math.cos(angle), y0+r*math.sin(angle)]

    return degdict


def get_horizontal_coords():
    coord_list = []
    for x in range(-60, 60):
        y = circle(0,15,60,x)[0]
        coord_list.append([x+80, y+32])
    return coord_list




def arm_stabilise(stop_stabilisitation):
    alphax0 = 0
    alphay0 = circle(0,15,60,alphax0)[0]

    degoffset = round(-21 - (alphax0/8.5))
    degree_seq = sequence(alphax0, alphay0, 100, -60, 60, 1, degoffset)

    last = 0
    while not stop_stabilisitation.is_set():
        pitch = dog.read_pitch()
        pitch = round(pitch)

        #if last != pitch: print(f"Pitch: {pitch}")

        if pitch not in degree_seq: continue

        dog.arm(*degree_seq[pitch])
        last = pitch
        # print(pitch)
    
    print("Stabilisation stopped")



stop_stabilisitation = threading.Event()
stabilise = threading.Thread(target=arm_stabilise, args=(stop_stabilisitation,))

stabilise.start()




import socket
import json

HOST = '0.0.0.0'  # Listen on all interfaces
PORT = 12345      # Choose any free port

msg = {}


def action(msg):

    if msg["input_type"] == 0:

        speed = msg["walkspeed"]
        turnspeed = msg["turnspeed"]

        if msg["w"] and not msg["s"]:
            dog.move("x", speed)
        elif msg["s"] and not msg["w"]:
            dog.move("x", -speed)
        else:
            dog.move("x", 0)

        if msg["walk_mode"]:
            dog.move("y", 0)

            if msg["a"] and not msg["d"]:
                dog.turn(turnspeed)
            elif msg["d"] and not msg["a"]:
                dog.turn(-turnspeed)
            else:
                dog.turn(0)
        else:
            dog.turn(0)

            if msg["a"] and not msg["d"]:
                dog.move("y", speed)
            elif msg["d"] and not msg["a"]:
                dog.move("y", -speed)
            else:
                dog.move("y", 0)

    elif msg["input_type"] == 1:
        y = msg["x"] / 42  ## x and y are swapped with micro:bit and robot
        x = msg["y"] / 59


        x = 0 if abs(x) < 5 else int(-x * 1.5) 
        y = 0 if abs(y) < 4 else int(-y)

        
        
        print(f"x {x}; y {y}")
        dog.move("x", x)
        dog.move("y", y)









def tcp_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(1)
        print(f"Listening on {HOST}:{PORT}")
        while True:
            try:
                conn, addr = s.accept()
                with conn:
                    print(f"Connected by {addr}")
                    while True:
                        data = conn.recv(1024)
                        if not data:
                            continue
                        msg = json.loads(data.decode())
                        action(msg)
                        print(f"Received: {data.decode().strip()}")

                        #conn.sendall(b"ACK\n")

            except Exception as e:
                print(f"Exception {e}; reconnecting in 2s")
                time.sleep(2)

def udp_server():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((HOST, PORT))

        print(f"UDP Listening on {HOST}:{PORT}")
        while True:
            data, addr = s.recvfrom(1024)
            if data:
                msg = json.loads(data.decode())
                action(msg)
                print(f"Received: {data.decode().strip()}")




server = threading.Thread(target=udp_server)
server.start()











server.join()




stop_stabilisitation.set()
print(f"done")


