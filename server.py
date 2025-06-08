from xgolib import XGO
from xgoedu import XGOEDU
import os

try:
    dog = XGO(port='/dev/ttyAMA0',version="xgolite")
except Exception as e:
    print(f"{e}\n Shutting down (fixing), restart manually please")
    os.system(f"pkill -f {__file__}") ## linux

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

class Stabilization():

    def __init__(self, autorun = False, dynamic = False, offset = 0):
        self.stop_stabilisitation = threading.Event()
        self.thread = None

        if autorun:
            self.start(dynamic, offset)


    def start(self, dynamic = False, offset = 0):
        if self.thread: return

        final_args = (self.stop_stabilisitation, dynamic, offset)
        self.thread = threading.Thread(target=self.arm_stabilise, args=final_args)
        self.thread.start()
        return self.thread
    

    def stop(self):
        if not self.thread: return

        self.stop_stabilisitation.set()
        self.thread.join()
        self.thread = None
        self.stop_stabilisitation.clear()


    @staticmethod
    def circle(x0, y0, r, x):
        to_root = r**2 - (x - x0)**2

        if to_root < 0:
            return False

        return (y0 + math.sqrt(to_root), y0 - math.sqrt(to_root))

    @staticmethod
    def sequence(x0, y0, r, min, max, step, degoffset = -27):
        degdict = {} # degree dictionary
        i = min-1
        deg_dynamic = 0
    
        while (i < max) and ((i := i + step) or True):
            if i > -30 and i < -15: r -= 0.12  #### eliptic stabilization 
            if i > -15 and i < 15: r -= 0.34
            if i > 15 and i < 37: r -= 0.3
    
            if i > 35 and i < 65: deg_dynamic -= 0.37
            if i > 75 and i < 95: deg_dynamic -= 0.2
            if i+degoffset+int(deg_dynamic) > 80: deg_dynamic += 0.4
    
    
            angle = math.radians(i)
            degdict[i+degoffset+int(deg_dynamic)] = [x0+r*math.cos(angle), y0+r*math.sin(angle)]
            
        degdict = {i: v for i, v in degdict.items() if i > -87}
    
        return degdict
    
    
    def get_horizontal_coords(self):
        coord_list = []
        for x in range(-60, 60):
            y = self.circle(0,15,60,x)[0]
            coord_list.append([x+80, y+32])
        return coord_list
    
    
    
    
    def arm_stabilise(self, stop_stabilisitation, dynamic = True, offset = 0):
        if dynamic:
            print("calculating")
            degree_seq = {}
            for alphax0 in range(-59,50):
                alphay0 = self.circle(0,15,60,alphax0)[0]
                degoffset = round(-21 - (alphax0/8.5))
                print(alphax0, degoffset)
                deg_temp = self.sequence(alphax0, alphay0, 100, -120, 150, 1, degoffset)
    
                acc_range = [i for i in range(-alphax0-40, int(-alphax0+(0.5*abs(alphax0))))]
                for k, v in deg_temp.items():
                    if k in acc_range:
                        degree_seq[k] = v
            print("done")
        else:
            alphax0 = 0
            alphay0 = self.circle(0,15,60,alphax0)[0]
    
            degoffset = round(-21 - (alphax0/8.5))
            degree_seq = self.sequence(alphax0, alphay0, 100, -80, 120, 1, degoffset)
    
    
        if offset:
            degree_seq = {i+offset: v for i, v in degree_seq.items()}
    
    
    
        last = 0
        while not stop_stabilisitation.is_set():
            pitch = dog.read_pitch()
            pitch = round(pitch)
    
            if last != pitch: print(f"Pitch: {pitch}, {degree_seq.get(pitch, 0)}")
    
            if pitch not in degree_seq: continue
            if last != pitch: print(f"/")
            
    
            dog.arm(*degree_seq[pitch])
            last = pitch
            # print(pitch)
        
        print("Stabilisation stopped")



# stop_stabilisitation = threading.Event()
# stabilise = threading.Thread(target=arm_stabilise, args=(stop_stabilisitation, True, -12,))
# stabilise.start()

stab = Stabilization(autorun=False, )
stab.start()



# dog.arm(80,106)


dog.claw(100)

import socket
import json

class Server():
    def __init__(self, HOST = '0.0.0.0', PORT = 12345, autostart = False, type_autostart = "UDP"):
        self.HOST = HOST 
        self.PORT = PORT
        self.s = None


        self.server_stop = threading.Event()
        self.server = None

        if autostart:
            self.start(type_autostart)
    
    def start(self, type="UDP"):
        if self.server: return 

        if type == "UDP":
            self.server = threading.Thread(target=self.udp_server, args=(self.server_stop,))
        elif type == "TCP":
            self.server = threading.Thread(target=self.tcp_server, args=(self.server_stop,))
        else:
            raise BaseException("Only accepts 'UDP' or 'TCP'")
        
        self.server.start()

    
    def stop(self):
        if not self.server or not self.s: return

        try:
            self.s.shutdown(socket.SHUT_RDWR) # s = socket connection 
        except OSError as e:
            if e.errno == 107:
                pass
            else:
                raise e
            
        self.s.close()
        self.server_stop.set()
        self.server.join()
        self.server = None
        self.server_stop.clear()
        



    @staticmethod
    def action(msg):
        global dog

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
            y = 0
            x = msg["y"] / 59 ## x and y are swapped with micro:bit and robot
    
            x = 0 if abs(x) < 5 else int(-x * 1.5) # flip + multiplier
            
            if not msg["walk_mode"]:
                y = msg["x"] / 42  ## x and y are swapped with micro:bit and robot
                y = 0 if abs(y) < 4 else int(-y) # flip
                dog.move("y", y)
                dog.turn(0)
            else:
                turn = msg["x"] / 7
                if x > 0:
                    turn = -turn # flip
                else:
                    turn = 0 if abs(turn) < 10 else -turn # flip
    
                dog.move("y", 0)
                dog.turn(turn)
                
    
            
            
            print(f"x {x}; y {y}")
    
            dog.move("x", x)        
    
    
    def tcp_server(self, server_stop):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.HOST, self.PORT))
            s.listen(1)
            print(f"Listening on {self.HOST}:{self.PORT}")
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
                            self.action(msg)
                            print(f"Received: {data.decode().strip()}")
    
                            #conn.sendall(b"ACK\n")
    
                except Exception as e:
                    print(f"Exception {e}; reconnecting in 2s")
                    time.sleep(2)
    
    def udp_server(self, server_stop):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as self.s:
            
            self.s.bind((self.HOST, self.PORT))
    
    
            print(f"UDP Listening on {self.HOST}:{self.PORT}")
            while not server_stop.is_set():
                data, addr = self.s.recvfrom(1024)
                if data:
                    msg = json.loads(data.decode())
                    self.action(msg)
                    print(f"Received: {data.decode().strip()}")
            self.s.close()



# server_stop = threading.Event()
# server = threading.Thread(target=udp_server, args=(server_stop,))
# server.start()

server = Server()
server.start()

time.sleep(6)
stab.stop()
server.stop()


time.sleep(3)
stab.start()
server.start()








while True:
    time.sleep(1)


# try:
#     server.join()
# except Exception as e:
#     print(f"{e}; \n shutting down")
#     server_stop.set()
#     stop_stabilisitation.set()






