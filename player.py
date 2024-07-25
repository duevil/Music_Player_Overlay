import time
import random
from threading import Thread
from ctypes import windll
import tkinter as tk
from pynput.keyboard import Key, Controller, Listener, GlobalHotKeys
from PIL import Image, ImageTk, ImageDraw
import spotipy
import urllib.request
import io
import subprocess


scope = "user-read-playback-state,user-modify-playback-state,streaming"
sp = spotipy.Spotify(client_credentials_manager=spotipy.SpotifyOAuth(scope=scope))


class CurrentTrack:
    def __init__(self, data):
        item = data['item']
        self.name = item['name']
        self.artist = ', '.join([artist['name'] for artist in item['artists']])
        self.cover = item['album']['images'][2]['url']
        self.length = float(item['duration_ms'] / 1000.0)
        self.progress = float(data['progress_ms'] / 1000.0)
        self.is_playing = data['is_playing']
        
    def __repr__(self):
        return f"CurrentTrack(name={self.name}, artist={self.artist}, cover={self.cover}, length={self.length}, progress={self.progress}, paused={self.is_playing})"
    
    

class WebImage:
    def __init__(self, url):
        with urllib.request.urlopen(url) as u: raw_data = u.read()
        image = Image.open(io.BytesIO(raw_data))
        self.image = ImageTk.PhotoImage(add_corners(image.resize((64, 64)), 3))

    def get(self): return self.image
    
    

def write_text(print=print):
    kbd = Controller()
    mean = 0.076
    std = 0.025
    text = list("Auf dem Bildschirm ist in einem Schreibprogramm ein Drehbuch zu sehen, an dem Big-Me gerade eifrig schreibt, sowie ein Widget eines Musikplayers. Im Hintergrund läuft LEISE MUSIK.")
    
    def _write(text):
        time.sleep(0.3)
        for char in text:
            kbd.tap(char)
            time.sleep(abs(random.normalvariate(mean, std)))
    
    print("Press <ENTER> to start writing")
    with Listener(on_release=lambda k:k!=Key.enter) as l: l.join()
    windll.user32.BlockInput(True)
    _write([Key.enter] + text + ([Key.enter]*2))
    # shorcturt 'ctrl'+'shift'+r
    time.sleep(0.3)
    with kbd.pressed(Key.ctrl), kbd.pressed(Key.shift): kbd.tap('r')
    _write("PUNCH-IN-ZOOM ZU:")
    time.sleep(3)
    windll.user32.BlockInput(False)
    print("Writing finished")
    
    
    
def add_corners(im, rad):
    circle = Image.new('L', (rad * 2, rad * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, rad * 2 - 1, rad * 2 - 1), fill=255)
    alpha = Image.new('L', im.size, 255)
    w, h = im.size
    alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
    alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
    alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
    alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
    im.putalpha(alpha)
    return im



class Player_Window:
    def __init__(self, root=tk.Tk()):
        self.root = root
        self.root.title("")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.attributes('-topmost', True, '-alpha', 0.95)
        windll.shcore.SetProcessDpiAwareness(1)
        # dark gray theme
        clr = "grey10"
        self.clr_primary = "#E8EAED"
        self.root.config(bg=clr)
        # bg=clr, relief=tk.FLAT, activebackground=clr, borderwidth=0
        btn_cnf = {'bg':clr, 'relief':tk.FLAT, 'activebackground':clr, 'borderwidth':0}
        
        
        # restyle window title bar
        
        self.root.overrideredirect(True) # turns off title bar, geometry
        
        self.icon_img = ImageTk.PhotoImage(Image.open('./img/music_note.png').resize((24, 24)))
        self.remove_img = ImageTk.PhotoImage(Image.open('./img/remove.png').resize((24, 24)))
        self.close_img = ImageTk.PhotoImage(Image.open('./img/close.png').resize((24, 24)))
        
        title_bar = tk.Frame(self.root, bg=clr, bd=2)
        icon_label = tk.Label(title_bar, image=self.icon_img, bg=clr)
        title_label = tk.Label(title_bar, text="Musik", font=("Segoe UI", 12), bg=clr, fg=self.clr_primary)
        remove_button = tk.Button(title_bar, image=self.remove_img, cnf=btn_cnf)
        close_button = tk.Button(title_bar, image=self.close_img, cnf=btn_cnf, command=self.on_closing)
        
        icon_label.pack(side=tk.LEFT, padx=5, pady=(5,0))
        title_label.pack(side=tk.LEFT, padx=5, pady=(5,0))
        close_button.pack(side=tk.RIGHT, padx=5, pady=(5,0))
        remove_button.pack(side=tk.RIGHT, padx=5, pady=(5,0))
        title_bar.pack(expand=1, fill=tk.X)
        
        # move window with title bar
        self.move_x, self.move_y = 0, 0
        def move_window_start(e): self.move_x, self.move_y = e.x, e.y
        def move_window(e): self.root.geometry('+{0}+{1}'.format(e.x_root - self.move_x, e.y_root - self.move_y))
        title_bar.bind('<ButtonPress-1>', move_window_start)
        title_bar.bind('<B1-Motion>', move_window)


        # cover and song info
        
        self.song_title_var = tk.StringVar()
        self.artist_var = tk.StringVar()
        
        self.cover = ImageTk.PhotoImage(add_corners(Image.open('./img/cover.png').resize((64, 64)), 3))
        
        cover_frame = tk.Frame(self.root, bg=clr)
        self.cover_label = tk.Label(cover_frame, image=self.cover, bg=clr)
        song_title = tk.Label(cover_frame, textvariable=self.song_title_var, font=("Segoe UI", 16, "bold"), bg=clr, fg=self.clr_primary, anchor=tk.NW, width=1)
        artist = tk.Label(cover_frame, textvariable=self.artist_var, font=("Segoe UI", 10), bg=clr, fg="lightgrey", anchor=tk.NW, width=1)
        
        cover_frame.pack(fill=tk.X, side=tk.TOP, padx=20, pady=20)
        self.cover_label.pack(side=tk.LEFT)
        song_title.pack(fill=tk.X, padx=(10,0))
        artist.pack(fill=tk.X, padx=(10,0), pady=(2,0))
        
        
        # media controls
        
        buttton_size_small = (28, 28)
        button_size = (48, 48)
        buttton_size_large = (64, 64)
        self.shuffle_image = ImageTk.PhotoImage(Image.open('./img/shuffle.png').resize(buttton_size_small))
        self.prev_image = ImageTk.PhotoImage(Image.open('./img/skip_previous.png').resize(button_size))
        self.pause_image = ImageTk.PhotoImage(Image.open('./img/pause_circle.png').resize(buttton_size_large))
        self.play_image = ImageTk.PhotoImage(Image.open('./img/play_circle.png').resize(buttton_size_large))
        self.next_image = ImageTk.PhotoImage(Image.open('./img/skip_next.png').resize(button_size))
        self.loop_image = ImageTk.PhotoImage(Image.open('./img/repeat.png').resize(buttton_size_small))
        
        controls_frame = tk.Frame(self.root, bg=clr)
        shuffle_button = tk.Button(controls_frame, image=self.shuffle_image, cnf=btn_cnf)
        prev_button = tk.Button(controls_frame, image=self.prev_image, cnf=btn_cnf, command=self.prev_track)
        self.pause_button = tk.Button(controls_frame, image=self.pause_image, cnf=btn_cnf, command=self.pause)
        self.play_button = tk.Button(controls_frame, image=self.play_image, cnf=btn_cnf, command=self.resume)
        next_button = tk.Button(controls_frame, image=self.next_image, cnf=btn_cnf, command=self.next_track)
        loop_button = tk.Button(controls_frame, image=self.loop_image, cnf=btn_cnf)
    
        controls_frame.pack(anchor=tk.CENTER, expand=True)
        shuffle_button.grid(row=0, column=0, padx=(30,10))
        prev_button.grid(row=0, column=1, padx=10)
        next_button.grid(row=0, column=3, padx=10)
        loop_button.grid(row=0, column=4, padx=(10,30))
        
        
        # progress bar dummy using canvas
        
        self.current_progress_var = tk.StringVar(value="0:00")
        self.song_length_var = tk.StringVar(value="3:00")
        
        progress_frame = tk.Frame(self.root, bg=clr)
        current_progress_label = tk.Label(progress_frame, textvariable=self.current_progress_var, font=("Segoe UI", 10), bg=clr, fg="lightgrey", anchor=tk.NW)
        song_length_label = tk.Label(progress_frame, textvariable=self.song_length_var, font=("Segoe UI", 10), bg=clr, fg="lightgrey", anchor=tk.NE)
        self.progress_canvas = tk.Canvas(progress_frame, bg="grey30", height=5, width=0, highlightthickness=0)
        
        progress_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=20, pady=20)
        current_progress_label.pack(side=tk.LEFT)
        song_length_label.pack(side=tk.RIGHT)
        self.progress_canvas.pack(fill=tk.X, padx=10, pady=(10,0))
        
        
        # initialisation
        
        notify_window = Notification_Window(tk.Toplevel(self.root))
        print_window = Print_Window(tk.Toplevel(self.root))
        
        hks = {'<ctrl>+<alt>+<shift>+'+str(i):self.set_progress(i) for i in range(10)}
        hks['<ctrl>+<alt>+<shift>+<space>'] = Thread(target=write_text, args=(print_window.set_text,), daemon=True).start
        hks['<ctrl>+<alt>+<shift>+#'] = notify_window.slide
        self.listener = GlobalHotKeys(hks)
        self.listener.start()
        
        self.current_track = None
        self.notify_window = Notification_Window(tk.Toplevel(self.root))
        self.update()
        
        
    # set the current progress in 10-percent steps (0-9)
    def set_progress(self, progress):
        def _():
            seek_ms = int(self.current_track.length * progress / 10 * 1000)
            sp.seek_track(seek_ms)
            self.update(False)
        return lambda: Thread(target=_, daemon=True).start()
    
    
    def prev_track(self):
        def _():
            sp.previous_track()
            self.update(False)
        Thread(target=_, daemon=True).start()
        
        
    def next_track(self):
        def _():
            sp.next_track()
            self.update(False)
        Thread(target=_, daemon=True).start()
        
        
    def pause(self):
        def _(): 
            if self.current_track.is_playing: 
                sp.pause_playback()
                self.update(False)
        Thread(target=_, daemon=True).start()
    
    
    def resume(self):
        def _():
            if not self.current_track:
                res = sp.devices()
                if not res: return 
                if res['devices'] == []: # no active devices, open spotify
                    subprocess.run(["spotify.exe"])
                    _()
                    return
                sp.start_playback(device_id=res['devices'][0]['id'])
                self.update(False)
            elif not self.current_track.is_playing: 
                sp.start_playback()
                self.update(False)
        Thread(target=_, daemon=True).start()
        
        
    def update(self, loop=True):
        if loop: self.root.after(1000, self.update)
        def _():
            res = sp.currently_playing()
                
            if not res:
                self.play_button.grid(row=0, column=2, padx=10)
                return
            
            last_play_state = self.current_track.is_playing if self.current_track else None
            self.current_track = CurrentTrack(res)
            
            self.song_title_var.set(self.current_track.name)
            self.artist_var.set(self.current_track.artist)
            
            self.current_progress_var.set(self.format_progress(self.current_track.progress))
            self.song_length_var.set(self.format_progress(self.current_track.length))
            
            self.progress_canvas.update()
            bar_width = self.progress_canvas.winfo_width()
            bar_progress = self.current_track.progress / self.current_track.length * float(bar_width)
            
            self.progress_canvas.delete("progress")
            self.progress_canvas.create_rectangle(0, 0, bar_progress, 5, fill=self.clr_primary, width=0, tags="progress")
            
            if last_play_state == None or last_play_state != self.current_track.is_playing:
                if self.current_track.is_playing:
                    self.play_button.grid_forget()
                    self.pause_button.grid(row=0, column=2, padx=10)
                else:
                    self.pause_button.grid_forget()
                    self.play_button.grid(row=0, column=2, padx=10)
                    
            def _():
                self.cover = WebImage(self.current_track.cover).get()
                self.cover_label.config(image=self.cover)
                
            Thread(target=_, daemon=True).start()
            
        Thread(target=_, daemon=True).start()
        
        
    # turn total seconds into a "0:00" string
    def format_progress(self, seconds):
        seconds = int(seconds)
        mins, seconds = divmod(seconds, 60)
        return f"{mins}:{seconds:02}"
    
    
    def on_closing(self):
        self.listener.stop()
        self.root.destroy()



class Notification_Window:
    def __init__(self, root):       
        self.root = root
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        clr = '#123456'
        self.root.attributes('-transparentcolor', clr)
        windll.shcore.SetProcessDpiAwareness(1) 
        self.root.overrideredirect(True)
        self.img = ImageTk.PhotoImage(Image.open('./img/notification.png'))
        self.label = tk.Label(self.root, image=self.img, bg=clr)
        self.label.pack()
        self.root.update()
        self.width, self.height = self.root.winfo_width(), self.root.winfo_height()
        self.root.geometry(f"+{-self.width}+0") # hide window off screen
        self.slide_state = False
        self.root.bind("<Button-1>", lambda _: Thread(target=self.slide, daemon=True).start())
    
    
    def slide(self):
        self.root.attributes('-topmost', True)
        offset = 64  # offset from bottom right corner
        start = -self.width - offset if not self.slide_state else offset
        end = offset if not self.slide_state else -self.width - offset
        steps = 100
        for step in range(steps + 1):
            t = step / steps
            eased_t = t * t * (3 - 2 * t)
            x = start + (end - start) * eased_t
            self.root.geometry(f"+{int(x)}+{1440 - self.height - offset}")
            time.sleep(0.0015)
        self.slide_state = not self.slide_state
        
        
    def on_closing(self): self.root.destroy()
    
    
class Print_Window:
    def __init__(self, root):
        windll.shcore.SetProcessDpiAwareness(1) 
        self.root = root
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.config(bg='black')
        self.root.geometry("2560x1440")
        self.root.attributes('-topmost', True, '-transparentcolor', self.root['bg'])
        self.root.overrideredirect(True)
        self.text = tk.StringVar(value="Hello World")
        label = tk.Label(self.root, textvariable=self.text, font=("Segoe UI", 72), bg=self.root['bg'], fg='#010101')
        label.pack(anchor=tk.CENTER, expand=True, pady=(0, 100))
        self.root.attributes('-alpha', 0)
        
    def set_text(self, text):
        self.text.set(text)
        self.root.attributes('-alpha', 1)
        time.sleep(1.5)
        # fade out
        for i in range(100):
            self.root.attributes('-alpha', 1 - i/100)
            time.sleep(0.01)
        self.root.attributes('-alpha', 0)
        
    def on_closing(self): self.root.destroy()
        
      
      
      
# Main
if __name__ == "__main__": Player_Window().root.mainloop()
