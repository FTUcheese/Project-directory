# standalone.py
# This is the code that controls Smart Motor behavior.
# To change the functionality of the Smart Motor, you should only have to change this file.

from machine import Pin, SoftI2C, PWM, ADC
from files import *
import time
from machine import Timer
import servo
import icons
import os
import sys
import ubinascii
import machine

import sensors
sens = sensors.SENSORS()

# --- REGRESSION LOGIC REPLACES NEAREST NEIGHBOR ---

def linear_regression_predict(data, point):
    """
    Given data as a list of [x, y] pairs and a single point (x,),
    fit a linear regression y = a * x + b, return predicted y for point[0]
    """
    if not data or len(data) < 2:
        # Not enough data for regression; fallback to last y or zero
        if data:
            return data[-1][1]
        else:
            return 0

    xs = [d[0] for d in data]
    ys = [d[1] for d in data]
    n = len(data)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n

    numer = sum((xs[i] - mean_x) * (ys[i] - mean_y) for i in range(n))
    denom = sum((xs[i] - mean_x) ** 2 for i in range(n))

    if denom == 0:
        a = 0
    else:
        a = numer / denom
    b = mean_y - a * mean_x

    x_query = point[0] if isinstance(point, (list, tuple)) else point
    y_pred = a * x_query + b
    return y_pred

# Unique name

ID = ubinascii.hexlify(machine.unique_id()).decode()
numberofIcons = [len(icons.iconFrames[0]) + 1] + [len(icons.iconFrames[i]) for i in range(1, len(icons.iconFrames))]  # Homescreen +1 icon
highlightedIcon = []
for numberofIcon in numberofIcons:
    highlightedIcon.append([0, numberofIcon])

screenID = 1
lastPressed = 0
previousIcon = 0
filenumber = 0

currentlocaltime = 0
oldlocaltime = 0

points = []

# Defining all flags
# Make sure flags covers ALL icons on ALL screens!
flags = [False for _ in range(max(numberofIcons))]

playFlag = False
triggered = False

# switch flags
switch_state_up = False
switch_state_down = False
switch_state_select = False

last_switch_state_up = False
last_switch_state_down = False
last_switch_state_select = False

switched_up = False
switched_down = False
switched_select = False

# mainloop flags
clearscreen = False

# define buttons , sensors and motors
# servo
s = servo.Servo(Pin(2))

# nav switches
switch_down = Pin(8, Pin.IN)
switch_select = Pin(9, Pin.IN)
switch_up = Pin(10, Pin.IN)

i2c = SoftI2C(scl=Pin(7), sda=Pin(6))
display = icons.SSD1306_SMART(128, 64, i2c, switch_up)

# interrupt functions

def downpressed(count=-1):
    global playFlag
    global triggered
    playFlag = False
    time.sleep(0.05)
    if(time.ticks_ms()-lastPressed > 200):
        displayselect(count)
    triggered = True #log file

def uppressed(count=1):
    global playFlag
    global triggered
    playFlag = False
    time.sleep(0.05)
    if(time.ticks_ms()-lastPressed > 200):
        displayselect(count)
    triggered = True #log file

def displayselect(selectedIcon):
    global screenID
    global highlightedIcon
    global lastPressed
    global previousIcon

    highlightedIcon[screenID][0] = (highlightedIcon[screenID][0] + selectedIcon) % highlightedIcon[screenID][1]
    display.selector(screenID, highlightedIcon[screenID][0], previousIcon)
    previousIcon = highlightedIcon[screenID][0]
    lastPressed = time.ticks_ms()

def selectpressed():
    global flags
    global triggered
    time.sleep(0.05)
    # set the flag for the currently highlighted icon on this screen
    flags[highlightedIcon[screenID][0]] = True
    triggered = True

def resettohome():
    global screenID
    global highlightedIcon
    global previousIcon
    global clearscreen
    screenID = 0
    previousIcon = 0
    for numberofIcon in numberofIcons:
        highlightedIcon.append([0, numberofIcon])
    display.selector(screenID, highlightedIcon[screenID][0], 0)
    clearscreen = True

def check_switch(p):
    global switch_state_up
    global switch_state_down
    global switch_state_select

    global switched_up
    global switched_down
    global switched_select

    global last_switch_state_up
    global last_switch_state_down
    global last_switch_state_select

    switch_state_up = switch_up.value()
    switch_state_down = switch_down.value()
    switch_state_select = switch_select.value()

    if switch_state_up != last_switch_state_up:
        switched_up = True

    elif switch_state_down != last_switch_state_down:
        switched_down = True

    elif switch_state_select != last_switch_state_select:
        switched_select = True

    if switched_up:
        if switch_state_up == 0:
            uppressed()
        switched_up = False
    elif switched_down:
        if switch_state_down == 0:
            downpressed()
        switched_down = False
    elif switched_select:
        if switch_state_select == 0:
            selectpressed()
        switched_select = False

    last_switch_state_up = switch_state_up
    last_switch_state_down = switch_state_down
    last_switch_state_select = switch_state_select

def displaybatt(p):
    batterycharge = sens.readbattery()
    display.showbattery(batterycharge)
    return batterycharge

def resetflags():
    global flags
    for i in range(len(flags)):
        flags[i] = False

def shakemotor(point):
    motorpos = point[1]
    for i in range(2):
        s.write_angle(min(180, motorpos + 5))
        time.sleep(0.1)
        s.write_angle(max(0, motorpos - 5))
        time.sleep(0.1)

def readdatapoints():
    datapoints = readfile()
    if(datapoints):
        numberofdata = len(datapoints)
        return datapoints[-1]
    else:
        return ([])

points = readdatapoints()
if points == []:
    highlightedIcon[1][0] = 1  # go to add if there are no data saved

# setting up Timers
tim = Timer(0)
tim.init(period=50, mode=Timer.PERIODIC, callback=check_switch)
batt = Timer(1)
batt.init(period=3000, mode=Timer.PERIODIC, callback=displaybatt)

# setup with homescreen  #starts with screenID=0
display.welcomemessage()
display.selector(screenID, highlightedIcon[screenID][0], -1)
oldpoint = [-1, -1]

while True:
    point = sens.readpoint()

    # Homescreen (screenID 0)
    if(screenID == 0):
        if flags[0]:   # train
            points = []
            screenID = 1
            clearscreen = True
            display.graph(oldpoint, point, points, 0)
            resetflags()
        elif flags[1]:  # play
            screenID = 2
            clearscreen = True
            datapoints = readfile()
            if (datapoints == []):
                display.showmessage("No data saved")
                resettohome()
            else:
                display.graph(oldpoint, point, points, 0)
            resetflags()
        elif flags[2]:  # new icon: "nah Id win"
            screenID = 5
            clearscreen = True
            resetflags()

    # Training Screen
    elif(screenID == 1):
        if(flags[0]):  # Play button is pressed
            if (points):
                playFlag = True
                savetofile(points)
                shakemotor(point)
            else:
                cleardatafile()
                display.showmessage("NO DATA")
            resetflags()

        elif(flags[1]):  # add button is pressed
            points.append(list(point))
            display.graph(oldpoint, point, points, 0)
            shakemotor(point)
            resetflags()

        elif(flags[2]):  # delete button is pressed
            if(points):
                points.pop()
            display.cleargraph()
            display.graph(oldpoint, point, points, 0)
            resetflags()

        if(playFlag):
            if(not point == oldpoint):
                x_point = point[0]
                y_point = linear_regression_predict(points, point)
                s.write_angle(int(y_point))
                display.graph(oldpoint, (x_point, y_point), points, 1)
                oldpoint = (x_point, y_point)

        else:
            if(not point == oldpoint):
                s.write_angle(point[1])
                display.graph(oldpoint, point, points, 0)
            oldpoint = point

    # Add your extra screenID 5
    elif(screenID == 5):
        display.fill(0)
        display.showmessage("nah Id win")
        # Go back to home on any button press
        if any(flags):
            resettohome()
            resetflags()

    if clearscreen:
        display.fill(0)
        display.selector(screenID, highlightedIcon[screenID][0], -1)
        clearscreen = False
