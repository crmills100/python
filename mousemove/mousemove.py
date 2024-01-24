import pyautogui
import time
import random

border = 100 # border around the edge
sleep = 30 # average sleep 
text = " "

def move_mouse():
    # generate random

    x = random.randint(border, max_x)
    y = random.randint(border, max_y)
    pyautogui.moveTo(x, y, duration=1)



def send_keyboard_input(text, interval=0.1):
    """
    Send keyboard input using pyautogui.

    Parameters:
    - text (str): The text to be typed.
    - interval (float): The time interval between key presses. Defaults to 0.1 seconds.
    """
    time.sleep(5)  # Give some time to focus on the input field
    pyautogui.typewrite(text, interval=interval)




size = pyautogui.size();
print(size)

max_x = size.width - (border * 2)
max_y = size.height - (border * 2)

(last_x, last_y) = pyautogui.position()
while (True):
    (x, y) = pyautogui.position()
    print(f"x: {x} y: {y}")

    if (last_x == x and last_y == y):
        # if mouse has not moved
        move_mouse()
        send_keyboard_input(text)

    last_x = x
    last_y = y

    s = random.randint(0, sleep * 2)
    print("sleeping for ", s, " seconds")
    time.sleep(s)



