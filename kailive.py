import threading
import time
import kaiscr
import sys
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf, GLib, Gdk

takescreenshot = kaiscr.TakeScreenshot()
screenshot = takescreenshot.screenshot
bye = takescreenshot.close
img = None
stop = False


def quit(*args):
    global stop
    stop = True
    bye()
    Gtk.main_quit()

def on_keypress(widget, event):
    if event.keyval == 113: # q key
        quit()

def update_pic():
    global img
    global takescreenshot
    try:
        while not stop:
            loader = GdkPixbuf.PixbufLoader()
            png = screenshot()
            loader.write(png)
            pb = loader.get_pixbuf()
            if not img:
                img = Gtk.Image.new_from_pixbuf(pb)
            else:
                img.set_from_pixbuf(pb)
            loader.close()
    except Exception as e:
        print(e)


threading.Thread(target=update_pic).start()
window = Gtk.Window()
window.connect("destroy", quit)
window.connect("key-press-event", on_keypress)
window.set_type_hint(Gdk.WindowTypeHint.UTILITY)
while not img:
    time.sleep(0.1)
window.add(img)
window.show_all()
Gtk.main()
