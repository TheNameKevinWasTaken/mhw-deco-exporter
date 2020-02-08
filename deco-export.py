from pynput import mouse
from pynput import keyboard
from PIL import Image
from PIL import ImageFilter
from PIL import ImageGrab
from tkinter import *
from tkinter.ttk import *
import pyautogui
import time
import pathlib
import PIL.ImageOps
import cv2
import pytesseract
import numpy
import os
import mss
import mss.tools
pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

sizex = 0
sizey = 0
size = 0

root = Tk()

def capture():
    global x1, y1, drawing, num, img, img2, x2, y2


    x1,y1,x2,y2=0,0,0,0
    drawing = False

    mon_num = int(mon_make.get())

    with mss.mss() as sct:
        monitors = sct.monitors
        monitor = sct.monitors[mon_num]
        im = sct.grab(monitor)
        mss.tools.to_png(im.rgb, im.size, output="monitor-1.png")

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
                    cv2.rectangle(img, (x1,y1),(x,y), (0, 255, 0), 2)

        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False
            num += 1
            font = cv2.FONT_HERSHEY_SIMPLEX
            x2 = x
            y2 = y


    key=ord('a')
    img=cv2.imread('monitor-1.png') # reading image
    img2=img.copy()
    cv2.namedWindow("main", cv2.WINDOW_NORMAL)

    movex = 0
    if mon_num > 1:
        monitors[0]['width'] = 0
        for i in range(mon_num):
            movex += monitors[i]["width"]

    cv2.moveWindow("main", movex, 0)
    cv2.setMouseCallback("main", draw_rect)
    cv2.setWindowProperty("main", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    num = 0

    # PRESS w to confirm save selected bounded box
    while key!=ord('w'):
        cv2.imshow("main",img)
        key = cv2.waitKey(1)&0xFF

    #x1 += movex
    #x2 += movex

    error_txt.insert(END,'Region captured at: {0} {1} {2} {3}\n'.format(x1,y1,x2,y2))

    if key==ord('w'):
        #cv2.imwrite('snap.png',img2[y1:y2,x1:x2])
        cv2.destroyAllWindows()
        #print('Saved as snap.png')
        os.remove('monitor-1.png')


def hhcombine():
    export = [line.rstrip('\n') for line in open('hhdata.txt')]
    decos = [line.rstrip('\n') for line in open('decos.txt')]
    zeros = [0] * len(export)

    export_names = []
    export_nums = []
    decos_names = []
    decos_nums = []
    combine = []

    for i in export:
        x = i.split(':')
        export_names.append(x[0])
        export_nums.append(x[1])

    for i in decos:
        x = i.split(':')
        decos_names.append(x[0])
        decos_nums.append(x[1])

    for idx, val in enumerate(decos_names):
        decos_names[idx] = decos_names[idx][1:-1]

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

    error_txt.insert(END,"Done, your decos are in hhexport.txt.\n")


def combine():
    export = [line.rstrip('\n') for line in open('dbdata.txt')]
    decos = [line.rstrip('\n') for line in open('decos.txt')]

    export_names = []
    export_nums = []
    decos_names = []
    decos_nums = []
    combine = []


    for i in export:
        x = i.split(':')
        export_names.append(x[0])
        export_nums.append(x[1])

    for i in decos:
        x = i.split(':')
        decos_names.append(x[0])
        decos_nums.append(x[1])

    for idx, val in enumerate(decos_names):
        if val in export_names:
            export_nums[export_names.index(val)] = decos_nums[idx]

    for idx, val in enumerate(export_nums):
        combine.append(export_names[idx]+':'+export_nums[idx])

    with open('dbexport.txt', 'w') as f:
        f.write('{')
        for index, item in enumerate(combine):
            if index != len(combine)-1:
                f.write("%s," % item)
            else:
                f.write("%s" % item)
        f.write('}')

    error_txt.insert(END,"Done, your decos are in dbexport.txt\n")


def takescreens():
    try:
        print(x1,x2,y1,y2)
    except NameError:
        error_txt.insert(END, "Capture region first\n")
        return

    setamnt()

    if size == 0:
        error_txt.insert(END, "Insert number of decos.\n")
        return
    
    time.sleep(5)

    w = abs(x2-x1)
    h = abs(y2-y1)

    number = size

    def mouseloop(decos):
        pathlib.Path('decos').mkdir(parents=True, exist_ok=True) 
        counter = 0
        while(True):
            for row in range(5):
                for column in range(10):
                    pyautogui.moveTo(x1+(int(w*0.0603+(column*w*0.0961))), y1+(int(h*0.2372+(row*h*0.0961))))
                    #pyautogui.hotkey('alt', 'printscreen')
                    #img = ImageGrab.grabclipboard()
                    img=ImageGrab.grab(bbox=(x1,y1,x2,y2))
                    img.save('decos/deco'+str(counter)+'.png','PNG')
                    counter += 1
                    progress['value']=counter/size*100
                    prog_lbl['text']=str(counter)+'/'+str(size)
                    root.update()
                    if counter >= decos:
                        return
            pyautogui.scroll(-1)
            time.sleep(1)

    mouseloop(number)

    error_txt.insert(END,"Done taking screenshots\n")


def convert_img(imagename):
    image = PIL.Image.open('decos/'+imagename+'.png')
    inverted_image = PIL.ImageOps.invert(image)
    thresh = 200
    fn = lambda x : 255 if x > thresh else 0
    inverted_convert = inverted_image.convert('L').point(fn, mode='1')
    inverted_convert = inverted_convert.filter(ImageFilter.EDGE_ENHANCE_MORE)
    #inverted_convert.save('images/'+imagename+'-inv.png')
    
    pil_image = inverted_convert.convert('RGB') 
    open_cv_image = numpy.array(pil_image)
    
    open_cv_image = open_cv_image[:, :, ::-1].copy()
    
    return(open_cv_image)


def get_text(image, psm):
    text = pytesseract.image_to_string(image, config = psm)
    text_list = text.splitlines()
    text_list = list(filter(None, text_list))
    return(text_list)


def slice_image(img):

    height, width, channels = img.shape

    hgap = int(height*.726)
    h = int(height*.0512)
    lgap = int(width*.0651)
    l = int(width*.8794)

    title = img[hgap:hgap+h,lgap:lgap+l]
    #cv2.imwrite('images/title-sliced.png',title)
    
    hgap = int(height*.9302)
    h = int(height*.0512)
    lgap = int(width*.6726)
    l = int(width*.1417)
    amount = img[hgap:hgap+h,lgap:lgap+l]

    #cv2.imwrite('images/amount-sliced.png',amount)
    return(title,amount)


def alldecos():

    setamnt()

    if size == 0:
        error_txt.insert(END, "Insert number of decos.\n")
        return
    
    x = sizex
    y = sizey

    counter = 0
    decos = size
    output = []
    errors = []

    for i in range(decos):
        counter += 1

        progress['value']=counter/size*100
        prog_lbl['text']=str(counter)+'/'+str(size)
        root.update()

        image = convert_img('deco'+str(i))

        title, amount = slice_image(image)
        name = get_text(title, '--psm 3')
        number = get_text(amount,'--psm 10')
        
        if not name or not number:
            output.append('"ERROR":#')
            errors.append(i)
        elif number[0].isnumeric():
            output.append('"'+str(name[0])+'":'+str(number[0]))
        else:
            output.append('"'+str(name[0])+'":1')

    with open('decos.txt', 'w') as f:
        for item in output:
            if item[:5] == '"lron':
                item = item.replace('"lron', '"Iron')
            f.write("%s\n" % item)

    if errors:
        error_txt.insert(END,"!!!Fix the errors in decos.txt by looking at file(s) below BEFORE moving on!!!\n")

        for index, item in enumerate(errors):
            if index != len(errors)-1:
                error_txt.insert(END,'deco'+str(item)+'.png, ')
            else:
                error_txt.insert(END,'deco'+str(item)+'.png')

        error_txt.insert(END,"\n")
    
    error_txt.insert(END,"Done converting to text. Output in decos.txt.\n")


def setamnt():
    global size

    if size_ent.index("end") == 0:
        size = 0
        return

    size = int(size_ent.get())


root.title("Deco-Exporter 9001")

size_lbl = Label(root, text="Amount of Decos")

size_ent = Entry(root)

size_ent.insert(0, "123")

options = [1, 2, 3, 4]
mon_make = StringVar(root)
mon_choose = OptionMenu(root, mon_make, options[0], *options)
mon_make.set(options[0])

region_btn = Button(root, text="(1) Capture Region", command=capture)

scrn_btn = Button(root, text="(2) Start Screenshots", command=takescreens)
convert_btn = Button(root, text="(3) Start Converting", command=alldecos)
export_btn = Button(root, text="(E) mhw.wiki-db Export", command=combine)
exporthh_btn = Button(root, text="(E) honeyhunterworld Export", command=hhcombine)

mon_lbl = Label(root, text="Select Monitor:")
prog_lbl = Label(root, text="0/X")
error_lbl = Label(root, text="Output:")
error_txt = Text(root, height=4)

progress = Progressbar(root, orient = HORIZONTAL, mode = 'determinate')


size_lbl.grid(row=0, column=0, sticky="nse", padx = 2, pady = 2)
size_ent.grid(row=0, column=1, columnspan=2, sticky="nsew", padx = 2, pady = 2)

mon_lbl.grid(row=1, column=0, sticky="nse", padx = 2, pady = 2)
mon_choose.grid(row=1, column=1, sticky="nsew", padx = 2, pady = 2)

region_btn.grid(row=2, column=0, sticky="nsew", padx = 2, pady = 2)
scrn_btn.grid(row=2, column=1, sticky="nsew", padx = 2, pady = 2)
convert_btn.grid(row=2, column=2, sticky="nsew", padx = 2, pady = 2)

export_btn.grid(row=3, column=0, sticky="nsew", padx = 2, pady = 2)
exporthh_btn.grid(row=3, column=1, sticky="nsew", padx = 2, pady = 2)


progress.grid(row=4, columnspan=2, sticky="nsew", padx = 2, pady = 2)
prog_lbl.grid(row=4, column=2, sticky="nsew", padx = 2, pady = 2)


error_lbl.grid(row=5, column=0, sticky="nsew", padx = 2, pady = 2)
error_txt.grid(row=6, columnspan=3, padx = 2, pady = 2)

root.mainloop()