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
    """
    Stabilises the robot's arm. Uses math to find the ideal coordinates to send to the robot using xgolib.XGO.arm()"""

    def __init__(self, autorun: bool = False, dynamic: bool = False, offset: int = 0):
        """Initialise

        Args:
            autorun (bool, optional): Sets whether stabilisation should automatically start. Defaults to False.
            dynamic (bool, optional): Sets style of stabilisation. Defaults to False.
            offset (int, optional): Adds offset (in degrees) to the stabilisation useful when holding objects. Defaults to 0.
        """
        self.stop_stabilisitation = False
        self.thread = None

        if autorun:
            self.start(dynamic, offset)


    def start(self, dynamic = False, offset = 0):
        """Starts the stabilisation (thread)

        Args:
            dynamic (bool, optional): Sets style of stabilisation. Defaults to False.
            offset (int, optional): Adds offset (in degrees) to the stabilisation useful when holding objects. Defaults to 0.
        """
        if self.thread: return
        self.stop_stabilisitation = False

        final_args = (self.stop_stabilisitation, dynamic, offset)
        self.thread = threading.Thread(target=self.arm_stabilise, args=final_args)
        self.thread.start()
    

    def stop(self):
        """Stops the stabilisation thread
        """
        if not self.thread: return

        self.stop_stabilisitation = True
        self.thread.join()
        self.thread = None
        self.stop_stabilisitation = False


    @staticmethod
    def circle(x0: float, y0: float, r: float, x: float) -> tuple:
        """Returns 2 value of y when you supply location(x0 and y0) of a circle, radius(r) and x(x) to plug into the function

        Args:
            x0 (float): location x
            y0 (float): location y
            r (float): radius
            x (float): x for the function

        Returns:
            tuple: Two values of y
        """
        to_root = r**2 - (x - x0)**2

        if to_root < 0:
            return False

        return (y0 + math.sqrt(to_root), y0 - math.sqrt(to_root))

    @staticmethod
    def sequence(x0: float, y0: float, r: float, min: float, max: float, step: float, degoffset: int = -27) -> dict:
        """Math sequence, similar to geogebra's 'Sequence', changed for my use case. 

        Supply info about a circle, angle and step, which sets how far the points should be from each other

        Args:
            x0 (float): location x of circle 
            y0 (float): location y of circle 
            r (float): radius of circle 
            min (float): part of angle
            max (float): part of angle
            step (int): distance between points
            degoffset (int, optional): offset to retunred dict. Defaults to -27.

        Returns:
            dict: data
        """

        degdict = {} # degree dictionary
        i = min-1
        deg_dynamic = 0
    
        while (i < max):
            i += step
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
    
    
    
    
    
    def arm_stabilise(self, dynamic = True, offset = 0):
        """Main worker of stabilisation

        Args:
            dynamic (bool, optional): Sets style of stabilisation. Defaults to True.
            offset (int, optional): Adds offset (in degrees) to the stabilisation useful when holding objects. Defaults to 0.
        """
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
        while not self.stop_stabilisitation:
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



import socket
import json

class Server():
    """Listen for info on TCP or UDP and perform actions based on it.
    """

    def __init__(self, HOST: str = '0.0.0.0', PORT:str = 12345, autostart:bool = False, type_autostart:str = "UDP"):
        """Initialise

        Args:
            HOST (str, optional): Host IP. Defaults to '0.0.0.0'.
            PORT (int, optional): Set the PORT. Defaults to 12345.
            autostart (bool, optional): Whether to start upon init. Defaults to False.
            type_autostart (str, optional): [only when autostart is set to True] Type of server to use. Defaults to "UDP".
        """
        self.HOST = HOST 
        self.PORT = PORT
        self.s = None


        self.server_stop = None
        self.server = None

        if autostart:
            self.start(type_autostart)
    

    def start(self, type:str="UDP"):
        """Start the server thread

        Args:
            type (str, optional): Set server type. Defaults to "UDP".

        Raises:
            BaseException: Wrong server type
        """
        if self.server: return 

        self.server_stop = None

        if type == "UDP":
            self.server = threading.Thread(target=self.udp_server)
        elif type == "TCP":
            self.server = threading.Thread(target=self.tcp_server)
        else:
            raise BaseException("Only accepts 'UDP' or 'TCP'")
        
        self.server.start()

    
    def stop(self):
        """Stops the server thread

        Raises:
            e: Shutdown error other than errno. 107 and errno. 9
        """
        if not self.server or not self.s: return

        try:
            self.s.shutdown(socket.SHUT_RDWR) # s = socket connection 
        except OSError as e:
            if e.errno == 107 or e.errno == 9:
                pass
            else:
                raise e
            
        self.s.close()
        self.server_stop = True
        self.server.join()
        self.server = None
        self.server_stop = None
        



    @staticmethod
    def action(msg:dict):
        """Performs actions based on supplied message

        Args:
            msg (dict): Actions to perform
        """

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
    
    
    def tcp_server(self):
        """TCP server, possibly not working
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.HOST, self.PORT))
            s.listen(1)
            print(f"Listening on {self.HOST}:{self.PORT}")
            while not self.server_stop:
                try:
                    conn, addr = s.accept()
                    with conn:
                        print(f"Connected by {addr}")
                        while not self.server_stop:
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
    
    def udp_server(self):
        """UDP server/listener
        """
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as self.s:
            
            self.s.bind((self.HOST, self.PORT))
    
    
            print(f"UDP Listening on {self.HOST}:{self.PORT}")
            while not self.server_stop:
                data, addr = self.s.recvfrom(1024)
                if data:
                    msg = json.loads(data.decode())
                    self.action(msg)
                    print(f"Received: {data.decode().strip()}")
            self.s.close()



# server_stop = threading.Event()
# server = threading.Thread(target=udp_server, args=(server_stop,))
# server.start()


if __name__ == "__main__":
    stab = Stabilization(autorun=False, )
    stab.start()

    dog.claw(100)

    server = Server()
    server.start()


    while True:
        time.sleep(1)


# try:
#     server.join()
# except Exception as e:
#     print(f"{e}; \n shutting down")
#     server_stop.set()
#     stop_stabilisitation.set()






