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

def linear_regression_predict(data, point):
    if not data or len(data) < 2:
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

ID = ubinascii.hexlify(machine.unique_id()).decode()

# homescreen stays as is; training screen gets 4 icons
numberofIcons = [len(icons.iconFrames[0])]  # homescreen icons
numberofIcons += [4 if i == 1 else len(icons.iconFrames[i]) for i in range(1, len(icons.iconFrames))]

flags = [[False for _ in range(icon_count)] for icon_count in numberofIcons]
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

playFlag = False
triggered = False

switch_state_up = False
switch_state_down = False
switch_state_select = False

last_switch_state_up = False
last_switch_state_down = False
last_switch_state_select = False

switched_up = False
switched_down = False
switched_select = False

clearscreen = False

s = servo.Servo(Pin(2))
switch_down = Pin(8, Pin.IN)
switch_select = Pin(9, Pin.IN)
switch_up = Pin(10, Pin.IN)
i2c = SoftI2C(scl=Pin(7), sda=Pin(6))
display = icons.SSD1306_SMART(128, 64, i2c, switch_up)

def downpressed(count=-1):
    global playFlag, triggered
    playFlag = False
    time.sleep(0.05)
    if(time.ticks_ms()-lastPressed > 200):
        displayselect(count)
    triggered = True

def uppressed(count=1):
    global playFlag, triggered
    playFlag = False
    time.sleep(0.05)
    if(time.ticks_ms()-lastPressed > 200):
        displayselect(count)
    triggered = True

def displayselect(selectedIcon):
    global screenID, highlightedIcon, lastPressed, previousIcon
    highlightedIcon[screenID][0] = (highlightedIcon[screenID][0] + selectedIcon) % highlightedIcon[screenID][1]
    display.selector(screenID, highlightedIcon[screenID][0], previousIcon)
    previousIcon = highlightedIcon[screenID][0]
    lastPressed = time.ticks_ms()

def selectpressed():
    global flags, triggered
    time.sleep(0.05)
    flags[screenID][highlightedIcon[screenID][0]] = True
    triggered = True

def resettohome():
    global screenID, highlightedIcon, previousIcon, clearscreen
    screenID = 0
    previousIcon = 0
    for idx, numberofIcon in enumerate(numberofIcons):
        if len(highlightedIcon) > idx:
            highlightedIcon[idx] = [0, numberofIcon]
        else:
            highlightedIcon.append([0, numberofIcon])
    display.selector(screenID, highlightedIcon[screenID][0], 0)
    clearscreen = True

def check_switch(p):
    global switch_state_up, switch_state_down, switch_state_select
    global switched_up, switched_down, switched_select
    global last_switch_state_up, last_switch_state_down, last_switch_state_select
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
    global flags, screenID
    for i in range(len(flags[screenID])):
        flags[screenID][i] = False

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

tim = Timer(0)
tim.init(period=50, mode=Timer.PERIODIC, callback=check_switch)
batt = Timer(1)
batt.init(period=3000, mode=Timer.PERIODIC, callback=displaybatt)

display.welcomemessage()
display.selector(screenID, highlightedIcon[screenID][0], -1)
oldpoint = [-1, -1]

while True:
    point = sens.readpoint()
    # Homescreen
    if(screenID == 0):
        if flags[0][0]:   # train
            points = []
            screenID = 1
            clearscreen = True
            display.graph(oldpoint, point, points, 0)
            resetflags()
        elif flags[0][1]:  # play
            screenID = 2
            clearscreen = True
            datapoints = readfile()
            if (datapoints == []):
                display.showmessage("No data saved")
                resettohome()
            else:
                display.graph(oldpoint, point, points, 0)
            resetflags()
    # Training Screen
    elif(screenID == 1):
        if flags[1][0]:  # Play button is pressed
            if (points):
                playFlag = True
                savetofile(points)
                shakemotor(point)
            else:
                cleardatafile()
                display.showmessage("NO DATA")
            resetflags()
        elif flags[1][1]:  # add button is pressed
            points.append(list(point))
            display.graph(oldpoint, point, points, 0)
            shakemotor(point)
            resetflags()
        elif flags[1][2]:  # delete button is pressed
            if(points):
                points.pop()
            display.cleargraph()
            display.graph(oldpoint, point, points, 0)
            resetflags()
        elif flags[1][3]:  # fourth icon: nah I'd win
            screenID = 5
            clearscreen = True
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
    elif(screenID == 5):
        display.fill(0)
        display.showmessage("nah I'd win")
        if any(flags[screenID]):
            screenID = 1
            clearscreen = True
            resetflags()
    if clearscreen:
        display.fill(0)
        display.selector(screenID, highlightedIcon[screenID][0], -1)
        clearscreen = False
