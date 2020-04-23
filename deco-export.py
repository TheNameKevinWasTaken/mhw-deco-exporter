from pynput import mouse
from PIL import Image
from PIL import ImageFilter
from PIL import ImageGrab
from pyautogui import moveTo, scroll
from time import sleep
from mss import mss
from mss.tools import to_png
from numpy import array
from pathlib import Path
from PIL.ImageOps import invert
from difflib import get_close_matches

import PySimpleGUIQt as sg
import os
import traceback
import sys
import PIL
import cv2
import pytesseract

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

pytesseract.pytesseract.tesseract_cmd = resource_path(r"Tesseract-OCR\tesseract.exe")

aod = 0
monitor_number = 0

sg.ChangeLookAndFeel("LightGreen")
layout = [
    [sg.Text("Amount of Deocs"),
     sg.Input(key="amountInput", tooltip="Tip: 50 per page")],
    [sg.Text("Select Monitor MHW is on (default 1)"),
     sg.Drop(values=(1, 2, 3, 4), key="dropdown")],
    [sg.Button(" Default 16:9 Region ",
               tooltip="Use this if you have a 16:9 monitor",
               key="defaultButton"),
     sg.Button(" Select Custom Region ",
               tooltip="Use this if your monitor is not 16:9 or the default doesnt work, drag to make box, \"w\" to confirm ",
               key="customButton"),
     sg.Button(" Start Screenshots (5s delay to alt-tab) ",
               tooltip="You will have 5 seconds to alt-tab into MHW after you press this, make sure you're on your first deco page.",
               key="startButton")],
    [sg.Button(" Start Converting ",
               tooltip="This will convert the images to text, it may take a minute depending on PC speed and number of decos",
               key="convertButton"),
     sg.Button(" Export (fix errors first!) ",
               tooltip="FIX ANY ERRORS BEFORE PRESSING THIS OR IT WONT WORK!!!!!",
               key="exportButton")],
    [sg.Text("Progress:"),
     sg.ProgressBar(100, orientation="h",
                    key="bar"),
     sg.Text("0/X",
             key="bartext")],
    [sg.Output()],
    [sg.Button("Exit")]
]

window = sg.Window("MHW Deco Exporter",
                   location=(800, 400))

window.Layout(layout).Finalize()

# the region caprture method, isnt used if defaultregion() is used instead


def capture():
    global x1, y1, drawing, num, img, img2, x2, y2

    x1, y1, x2, y2 = 0, 0, 0, 0
    drawing = False

    mon_num = values["dropdown"]

    with mss() as sct:
        monitors = sct.monitors
        monitor = sct.monitors[mon_num]
        im = sct.grab(monitor)
        to_png(im.rgb, im.size, output="monitor-1.png")

    def draw_rect(event, x, y, flags, param):
        global x1, y1, drawing, num, img, img2, x2, y2

        if event == cv2.EVENT_LBUTTONDOWN:
            drawing = True
            x1, y1 = x, y

        elif event == cv2.EVENT_MOUSEMOVE:
            if drawing == True:
                a, b = x, y
                if a != x & b != y:
                    img = img2.copy()
                    cv2.rectangle(img, (x1, y1), (x, y), (0, 255, 0), 2)

        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False
            num += 1
            font = cv2.FONT_HERSHEY_SIMPLEX
            x2, y2 = x, y

    key = ord('a')
    img = cv2.imread('monitor-1.png')  # reading image
    img2 = img.copy()
    cv2.namedWindow("main", cv2.WINDOW_NORMAL)

    movex = 0
    if mon_num > 1:
        monitors[0]['width'] = 0
        for i in range(mon_num):
            movex += monitors[i]["width"]

    cv2.moveWindow("main", movex, 0)
    cv2.setMouseCallback("main", draw_rect)
    cv2.setWindowProperty("main", cv2.WND_PROP_FULLSCREEN,
                          cv2.WINDOW_FULLSCREEN)
    num = 0

    # PRESS w to confirm save selected bounded box
    while key != ord('w'):
        cv2.imshow("main", img)
        key = cv2.waitKey(1) & 0xFF

    print(
        f"Region captured at: \n -->Top Left: ({x1}, {y1})\n -->Bottom Right: ({x2}, {y2})")

    if key == ord('w'):
        #cv2.imwrite('snap.png',img2[y1:y2,x1:x2])
        cv2.destroyAllWindows()
        os.remove('monitor-1.png')

# just formats the decos.txt file to match what is used on https://honeyhunterworld.com/mhwbi/
def combine():
    export = [line.rstrip('\n') for line in open(resource_path('hhdata.txt'))]
    decos = [line.rstrip('\n') for line in open('decos.txt')]
    zeros = [0] * len(export)

    export_names = []
    export_nums = []
    decos_names = []
    decos_nums = []

    for i in export:
        x = i.split(':')
        export_names.append(x[0])
        export_nums.append(x[1])

    for i in decos:
        x = i.split(':')
        decos_names.append(x[0])
        decos_nums.append(x[1])

    for idx, val in enumerate(decos_names):
        decos_names[idx] = decos_names[idx]

    for idx, val in enumerate(decos_names):
        if val in export_names:
            maxdeco = int(export_nums[export_names.index(val)])
            if int(decos_nums[idx]) >= maxdeco:
                zeros[export_names.index(val)] = maxdeco
            else:
                zeros[export_names.index(val)] = decos_nums[idx]

    with open('hhexport.txt', 'w') as f:
        for index, item in enumerate(zeros):
            if index != len(zeros)-1:
                f.write("%s," % item)
            else:
                f.write("%s" % item)

    print("Done, your decos are in hhexport.txt")


# mouse automation for screenshots
def takescreens():
    try:
        x1, x2, y1, y2
    except NameError:
        print("Capture region first.")
        return

    setamnt()

    if aod == 0:
        print("Insert number of decos.")
        return

    print("Screenshots will begin in 5 seconds, switch to MHW and click on the game.")
    window.refresh()

    for i in range(5, 0, -1):
        print(f"{i}...", end="")
        window.refresh()
        sleep(1)

    print("")
    window.refresh()

    w = abs(x2-x1)
    h = abs(y2-y1)

    number = aod

    def mouseloop(decos):
        Path('decos').mkdir(parents=True, exist_ok=True)
        counter = 0
        while(True):
            for row in range(5):
                for column in range(10):
                    moveTo(x1+(int(w*0.0603+(column*w*0.0965))),
                           y1+(int(h*0.2372+(row*h*0.0945))))
                    sleep(0.1)
                    img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
                    img.save('decos/deco'+str(counter)+'.png', 'PNG')
                    counter += 1
                    window["bar"].update_bar(counter, max=aod)
                    window["bartext"].update(f"{counter}/{aod}")
                    window.refresh()
                    if counter >= decos:
                        return
            scroll(-1)
            sleep(1)

    mouseloop(number)

    print("Done taking screenshots")

# converts the screenshot to inverted b&w open_cv for use in splitter/reader


def convert_img(imagename):
    image = PIL.Image.open('decos/'+imagename+'.png')
    image = invert(image)

    thresh = 200
    def fn(x): return 255 if x > thresh else 0
    image = image.convert('L').point(fn, mode='1')
    image = image.filter(ImageFilter.EDGE_ENHANCE_MORE)
    # inverted_convert.save('images/'+imagename+'-inv.png')

    pil_image = image.convert('RGB')
    open_cv_image = array(pil_image)
    open_cv_image = open_cv_image[:, :, ::-1].copy()

    return(open_cv_image)

# uses image_to_string to get the text on the split images, psm value is changed for name vs amount


def get_text(image, psm):
    text = pytesseract.image_to_string(image, config=psm)
    text_list = text.splitlines()
    text_list = list(filter(None, text_list))
    return(text_list)

# slices the image to grab the name and amount of decorations


def slice_image(img):

    height, width, channels = img.shape

    hgap = int(height*.726)
    h = int(height*.0512)
    lgap = int(width*.0651)
    l = int(width*.8794)

    title = img[hgap:hgap+h, lgap:lgap+l]
    # cv2.imwrite('images/title-sliced.png',title)

    hgap = int(height*.9302)
    h = int(height*.0512)
    lgap = int(width*.6726)
    l = int(width*.1417)
    amount = img[hgap:hgap+h, lgap:lgap+l]

    # cv2.imwrite('images/amount-sliced.png',amount)
    return(title, amount)

# the main logic behind prepairing images for ocr and then extracting the text. Also handles errors in the extracted text.


def alldecos():

    setamnt()

    if aod == 0:
        print("Insert number of decos.")
        return

    counter = 0
    export_names = []
    export_nums = []
    output = []
    errors = []

    export = [line.rstrip('\n') for line in open(resource_path('hhdata.txt'))]

    for i in export:
        x = i.split(':')
        export_names.append(x[0])
        export_nums.append(x[1])

    print("Starting Convertion")
    for i in range(aod):

        counter += 1
        window["bar"].update_bar(counter, max=aod)
        window["bartext"].update(f"{counter}/{aod}")
        window.refresh()

        image = convert_img('deco'+str(i))

        title, amount = slice_image(image)
        name = get_text(title, '--psm 3')
        number = get_text(amount, '--psm 10')

        if str(name[0][:4]) == 'lron' or str(name[0][:4]) == '1ron':
            name[0] = name[0].replace('lron', 'Iron')

        if not name or not number:
            output.append('"ERROR-ERROR-ERROR":#')
            errors.append(i)
        elif f'{name[0]}' not in export_names:
            matches = get_close_matches(f'{name[0]}', export_names)
            print(f"    {name[0]}")
            print("      got corrected to (not an error unless its wrong):")
            print(f"    {matches[0]}")
            output.append(f'{matches[0]}:{number[0]}')
        elif number[0].isnumeric():
            output.append(f"{name[0]}:{number[0]}")
        else:
            output.append(f"{name[0]}:1")

    with open('decos.txt', 'w') as f:
        for item in output:
            f.write("%s\n" % item)

    if errors:
        print("")
        print("!!! Fix the errors in decos.txt by looking at file(s) below BEFORE moving on !!!")

        for index, item in enumerate(errors):
            if index != len(errors)-1:
                print(f"deco{item}.png, ", end='')
            else:
                print(f"deco{item}.png")

    print("")
    print("Done converting to text. Output in decos.txt.")

# sets the region to the default for 16:9 monitors


def defaultregion():
    global x1, y1, x2, y2

    mon_num = values["dropdown"]

    with mss() as sct:
        monitors = sct.monitors
        monitor = sct.monitors[mon_num]

    w = monitor['width']
    h = monitor['height']

    x1, y1, x2, y2 = w*0.0724, h*.1426, w*0.3932, h*0.7417
    print("Region set to 16:9 defaults.")


# sets the global variable to the amount of decorations the user wants to export
def setamnt():
    global aod

    if int(values["amountInput"]) == 0:
        aod = 0
        return

    aod = int(values["amountInput"])


while True:
    try:
        button, values = window.read(timeout=1)
        if button in ("Exit", None):
            sys.exit(0)
        elif button == "defaultButton":
            try:
                defaultregion()
            except IndexError:
                print("Can't find selected monitor.")
        elif button == "customButton":
            try:
                capture()
            except IndexError:
                print("Can't find selected monitor.")
        elif button == "startButton":
            try:
                takescreens()
            except ValueError:
                print("Please enter decos in number format (i.e: 185)")
        elif button == "convertButton":
            alldecos()
        elif button == "exportButton":
            combine()
    except Exception as err:
        print(f"Error: {err}")
        traceback.print_exc()
