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

        if last != pitch: print(f"Pitch: {pitch}")

        if pitch not in degree_seq: continue

        dog.arm(*degree_seq[pitch])
        last = pitch
        # print(pitch)
    
    print("Stabilisation stopped")



stop_stabilisitation = threading.Event()
stabilise = threading.Thread(target=arm_stabilise, args=(stop_stabilisitation,))

stabilise.start()






    



dog.arm_mode(1)
dog.imu(0)





stabilise.join()
exit()
##############
dog.move("x", 10)



time.sleep(6)
dog.stop()

time.sleep(5)
stop_stabilisitation.set()
print(f"done")


