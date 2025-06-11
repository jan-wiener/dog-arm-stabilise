import socket
import time
import keyboard
import threading
import json
import sys
import serial


class Client():
    """
    Transfers data thourgh TCP or UDP protocol to the robot
    Includes keyboard and microbit input parsing tools"""

    def __init__(self, input_type:str = "keyboard", HOST: str = '192.168.192.251', PORT: int = 12345, autostart:bool = False, type_autostart:str = "UDP", mbport:str = "COM4", add_switch_hotkey: bool = True):
        """
        init\n
        :param input_type: Set input type. Accepts 'keyboard' or 'microbit'
        :param mbport: Select the main serial port with your micro:bit connected 
        :param HOST: Set the robot's IP adress to try and connect to
        :param PORT: Set the robot's port
        :param autostart: Set whether to start input listening and broadcasting upon calling __init__
        :param type_autostart: *[only if autostart is allowed]* Sets the communaction method, accepts 'UDP' and 'TCP'
        :param add_switch_hotkey: Sets whether there should be a switch key between microbit and keyboard. Bound to letter B. Defaults to True.
        """
        self.mbport = mbport
        self.HOST = HOST
        self.PORT = PORT
        self.stop_signal = None
        self.msg = {}
        self.broadcaster_thread = None

        self.input_stop_signal = None
        self.input_process_thread = None

        self.current_input_type = input_type

        if add_switch_hotkey:
            keyboard.add_hotkey("b", lambda self=self: self.set_input_type("microbit" if self.current_input_type == "keyboard" else "keyboard"))

        if autostart:
            self.start(type=type_autostart, )


    
    def set_input_type(self, input_type: str):
        """
        Sets input type\n
        :param input_type: Set input type. Accepts 'keyboard' or 'microbit'
        :param mbport: Select the serial port with your micro:bit connected
        """


        if input_type == self.current_input_type and self.input_process_thread: return

        if self.input_process_thread:
            self.input_stop_signal = True
            self.input_process_thread.join()
        
        self.input_stop_signal = None
        self.input_process_thread = None


        if not input_type: return


        if input_type == "keyboard":
            self.msg = {
                "input_type": 0, # 0 = keyboard, 1 = micro:bit
                "w": False,
                "a": False,
                "s": False,
                "d": False,
                "walk_mode": False,
                "walkspeed": 15,
                "turnspeed": 70,
            }
            self.input_process_thread = threading.Thread(target=self.keyboard_control)
        elif input_type == "microbit":
            self.msg = {
                "input_type": 1, # 0 = keyboard, 1 = micro:bit
                "x": 0,
                "y": 0,
                "walk_mode": True,
            }
            self.input_process_thread = threading.Thread(target=self.microbit_control)
        
        self.current_input_type = input_type
        self.input_process_thread.start()


    def start(self, type:str ="UDP"):
        """
        Starts input and broadcast threads\n
        :param type: Sets the communaction method, accepts 'UDP' and 'TCP'
        """

        if self.broadcaster_thread: return

        self.set_input_type(self.current_input_type)

        self.stop_signal = False
        if type=="UDP":
            self.broadcaster_thread = threading.Thread(target=self.connect_udp)
        elif type== "TCP":
            self.broadcaster_thread = threading.Thread(target=self.connect_tcp) # DEPRECATED
        self.broadcaster_thread.start()

    def stop(self):
        """Stops input and broadcast threads"""


        if not self.broadcaster_thread: return


        self.stop_signal = True
        self.broadcaster_thread.join()
        self.broadcaster_thread = None
        self.set_input_type(None)



    def connect_tcp(self):
        """
        Attempts to create a tcp connection with self.HOST:self.PORT and starts sending self.msg
        """

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            while not self.stop_signal:
                try:
                    try: 
                        s.connect((self.HOST, self.PORT))
                    except: 
                        pass

                    while not self.stop_signal:
                        s.sendall(json.dumps(self.msg).encode())
                        time.sleep(0.05)

                except Exception as e:
                    #s.close()
                    print(f"Exception: {e}; restaring in 2s")
                    time.sleep(2)
            s.close()


    def connect_udp(self):
        """
        Starts broadcasting self.msg to self.HOST:self.PORT"""

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            print(f"Transfer started")
            while not self.stop_signal:
                s.sendto(json.dumps(self.msg).encode(), (self.HOST, self.PORT))
                time.sleep(0.1)



    



    def keyboard_control(self):
        """
        Detects keypressed to parse them into self.msg.
        """
        keylist = {}

        keylist["m"] = keyboard.add_hotkey("m", lambda self=self: exec('self.msg["walk_mode"] = False if self.msg["walk_mode"] else True'))

        keylist["up"] = keyboard.add_hotkey("up", lambda self=self: exec('self.msg["walkspeed"] += 1'))
        keylist["down"] = keyboard.add_hotkey("down", lambda self=self: exec('self.msg["walkspeed"] -= 1'))

        keylist["right"] = keyboard.add_hotkey("right", lambda self=self: exec('self.msg["turnspeed"] += 10'))
        keylist["left"] = keyboard.add_hotkey("left", lambda self=self: exec('self.msg["turnspeed"] -= 10'))


        while not self.input_stop_signal:


            self.msg["w"] = keyboard.is_pressed("w")
            self.msg["a"] = keyboard.is_pressed("a")
            self.msg["s"] = keyboard.is_pressed("s")
            self.msg["d"] = keyboard.is_pressed("d")

            time.sleep(0.1)

        for keyobj in keylist.values():
            keyboard.remove_hotkey(keyobj)


    def microbit_control(self): # pip install pyserial
        """
        binds the microbit serial output to self.msg\n
        :param port: Select the serial port with your micro:bit connected
        """

        

        baudrate = 115200
        ser = serial.Serial(self.mbport, baudrate)
        print(f"Connected to {self.mbport}")


        try:
            while not self.input_stop_signal:
                
                mb_dict = ser.readline().decode("utf-8", errors="replace").strip()
            

                try: 
                    mb_dict = json.loads(mb_dict)
                except json.decoder.JSONDecodeError as e:
                    print("Unexpected string found on serial")
                    print(e)
                    continue


                print(mb_dict)

                self.msg.update(mb_dict)

                print(self.msg)




        except KeyboardInterrupt:
            ser.close()
            print("Connection closed.")
            self.stop()



client = Client(autostart=True, input_type="keyboard")


# b = keyboard.add_hotkey("b", lambda client=client: client.set_input_type("keyboard" if client.current_input_type == "microbit" else "microbit"))


while True:
    time.sleep(1)








