# tcp_client.py
import socket
import time
import keyboard
import threading
import json



HOST = '192.168.213.251'
PORT = 12345

INPUT_TYPE = 0

if INPUT_TYPE == 0:
    msg = {
        "input_type": 0, # 0 = keyboard, 1 = micro:bit
        "w": False,
        "a": False,
        "s": False,
        "d": False,
        "walk_mode": False,
        "walkspeed": 15,
        "turnspeed": 70,
    }
else:
    msg = {
        "input_type": 1, # 0 = keyboard, 1 = micro:bit
        "x": 0,
        "y": 0,
        "walk_mode": False,
    }





def connect_tcp():
    global msg
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        while True:
            try:
                try: s.connect((HOST, PORT))
                except: pass
                while True:

                    s.sendall(json.dumps(msg).encode())
                    time.sleep(0.1)

            except Exception as e:
                #s.close()
                print(f"Exception: {e}; restaring in 2s")
                time.sleep(2)

            #data = s.recv(1024)
    #print('Received from Pi:', data.decode().strip())

def connect_udp():
    global msg
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        while True:
            s.sendto(json.dumps(msg).encode(), (HOST, PORT))
            time.sleep(0.1)
        #data, _ = s.recvfrom(1024)

connect_thread = threading.Thread(target=connect_udp)
connect_thread.start()


#############################test
def test():
    global msg
    while True:
        print(msg)
        time.sleep(1)

#test_thread = threading.Thread(target=test)
#test_thread.start()
########################################



def keyboard_control():
    global msg
    walk_mode = keyboard.add_hotkey("m", lambda: exec('msg["walk_mode"] = False if msg["walk_mode"] else True'))

    add_speed = keyboard.add_hotkey("up", lambda: exec('msg["walkspeed"] += 1'))
    remove_speed = keyboard.add_hotkey("down", lambda: exec('msg["walkspeed"] -= 1'))

    add_turn = keyboard.add_hotkey("right", lambda: exec('msg["turnspeed"] += 10'))
    remove_turn = keyboard.add_hotkey("left", lambda: exec('msg["turnspeed"] -= 10'))
    while True:


        keypress = keyboard.is_pressed("w")
        msg["w"] = keyboard.is_pressed("w")
        msg["a"] = keyboard.is_pressed("a")
        msg["s"] = keyboard.is_pressed("s")
        msg["d"] = keyboard.is_pressed("d")

        time.sleep(0.1)


def microbit_control(port = "COM4"): # pip install pyserial
    global msg
    import serial

    baudrate = 115200
    ser = serial.Serial(port, baudrate)
    print(f"Connected to {port}")


    try:
        while True:
            mb_dict = ser.readline().decode("utf-8", errors="replace").strip()
            mb_dict = json.loads(mb_dict)

            msg.update(mb_dict)

            print(msg)
            #mb_dict = json.loads(mb_dict)



    except KeyboardInterrupt:
        ser.close()
        print("Connection closed.")


if INPUT_TYPE == 0:
    keyboard_control()
elif INPUT_TYPE == 1:
    microbit_control()





