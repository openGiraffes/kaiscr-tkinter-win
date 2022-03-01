import threading
import time
import kaiscr
import sys,os
import tkinter
from PIL import Image
from PIL import ImageTk
from io import BytesIO

os.system('adb root && adb forward tcp:6000 localfilesystem:/data/local/debugger-socket')

root = tkinter.Tk()
root.title('KaiLive')
root.geometry('240x320')
cv = tkinter.Canvas(root, width=240, height=320, background='white')
cv.pack(fill=tkinter.BOTH, expand=tkinter.YES)

takescreenshot = kaiscr.TakeScreenshot()
screenshot = takescreenshot.screenshot
bye = takescreenshot.close
stop = False


def quit(*args):
    global stop
    stop = True 
    bye()   
    root.destroy()
    
    
root.protocol("WM_DELETE_WINDOW", quit)
 
def update_pic():
    global cv,root
    global takescreenshot
    try:
        while not stop:
            png = screenshot() 
            im = Image.open(BytesIO(png))
            img = ImageTk.PhotoImage(image=im )
            cv.create_image(120, 160, image=img)
            root.update()
            #time.sleep(0)
            
    except Exception as e:
        print(e) 
        
update_pic()

