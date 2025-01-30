import pyautogui
import time
import random
import sys
import argparse
import pygetwindow

border = 100 # border around the edge
sleep = 30 # average sleep 
text = " "

# program options
timeout = None # exit after timeout
send_input = True # send logical text after mouse movement
wait = None # time to wait at startup in minutes
window_title = None # text to match with the active window title

parser = argparse.ArgumentParser()
parser.add_argument("--timeout", help="exit after timeout minutes", type=int)
parser.add_argument("--no_input", help="do not send logical text after mouse movement", action="store_true")
parser.add_argument("--wait", help="sleep at startup for wait minutes", type=int)
parser.add_argument("--window_title", help="only perform actions if active window title contains window_title")

args = parser.parse_args()

if (args.timeout):
    timeout = args.timeout

print(f"timeout: {timeout}")
    
if (args.no_input):
    send_input = not args.no_input

print(f"send_input: {send_input}")

if (args.wait):
    wait = args.wait

print(f"wait: {wait}")

if (args.window_title):
    window_title = args.window_title

print(f"window_title: {window_title}")


def move_mouse():
    # generate random

    x = random.randint(border, max_x)
    y = random.randint(border, max_y)
    pyautogui.moveTo(x, y, duration=1)


def active_window_matches(window_title):
    if (not window_title):
        return True
        
    if (window_title):
        awt = str(pygetwindow.getActiveWindowTitle())
        if (window_title in awt):
            print(f"'{window_title}' matches '{awt}'")
            return True

    
    print(f"'{window_title}' does not match '{awt}'")

    return False


def send_keyboard_input(text, interval=0.1):
    """
    Send keyboard input using pyautogui.

    Parameters:
    - text (str): The text to be typed.
    - interval (float): The time interval between key presses. Defaults to 0.1 seconds.
    """
    time.sleep(5)  # Give some time to focus on the input field
    pyautogui.typewrite(text, interval=interval)

def timedout(start_time, timeout):

    if (timeout is None):
        return False

    current_time = time.time()
    minutes_since_start = (current_time - start_time) / 60

    if (minutes_since_start > timeout):
        return True
    
    return False
    
    
start_time = time.time()


size = pyautogui.size();
print(size)

if (wait):
    print(f"waiting for {wait} minutes")
    time.sleep(wait * 60)


max_x = size.width - (border * 2)
max_y = size.height - (border * 2)

(last_x, last_y) = pyautogui.position()
print(f"intial sleep for {sleep} seconds")
time.sleep(sleep)


while (not timedout(start_time, timeout)):
    if (active_window_matches(window_title)):

        (x, y) = pyautogui.position()
        print(f"x: {x} y: {y}")

        if (last_x == x and last_y == y):
            # if mouse has not moved
            move_mouse()
            if (send_input):
                send_keyboard_input(text)

        last_x = x
        last_y = y

    s = random.randint(0, sleep * 2)
    print("sleeping for ", s, " seconds")
    time.sleep(s)


