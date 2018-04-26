# cam_transfer.py
# File transfer via webcam
# Copyright (C) 2017-2018  u/NASA_Welder
"""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, version 3 of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

class Login(ttk.Frame):
    def __init__(self,app, parent,settings,background = None,*args, **kwargs):
        ttk.Frame.__init__(self, parent,style = "app.TFrame", *args, **kwargs)
        self.app = app
        self.parent = parent
        self.settings = settings
        self.final = None
        self.light = False
        self.moon1 = tk.PhotoImage(file = "misc/moonbutton1.gif")
        self.moon2 = tk.PhotoImage(file = "misc/moonbutton2.gif")
        self.moon3 = tk.PhotoImage(file = "misc/moonbutton3.gif")
        if background:
            self.bg = tk.PhotoImage(file = background)
            self.bglabel = tk.Label(self, image=self.bg)
            self.bglabel.place(x=0, y=0, relwidth=1, relheight=1)


        self.logo = tk.PhotoImage(file = "misc/aeon_logo2.gif")

        self.showLogo = ttk.Label(self,image= self.logo,style = "app.TLabel",cursor = "shuttle")
        #heading = ttk.Label(first,text= "Wallet Options",style = "app.TLabel")
        self.walletFile = FilePicker(self.app,self,"wallet file",askPass = True,start = self.settings["wallet"]["wallet_file"],background = "misc/genericspace.gif",ftypes = [("full","*.keys"),("watchonly","*.keys-watchonly")],idir=os.path.dirname(sys.argv[1]))


        self.testnet = MyWidget(self,self,handle = "testnet",optional = 1,activeStart=self.settings["wallet"]["testnet"])
        if "monero" not in sys.argv[1]:
            self.launch = tk.Button(self,text = "launch!",command =self.launch,cursor = "shuttle",highlightthickness=0,font=('Liberation Mono','12','normal'),foreground = "white",bd = 3,bg = "#2D89A0" )
        else:
            self.launch = tk.Button(self,text = "launch!",command =self.launch,cursor = "shuttle",image = self.moon3,compound = tk.CENTER,height = 18,width = 60,highlightthickness=0,font=('Liberation Mono','12','normal'),foreground = "white",bd = 3,bg = "#900100" )
        #MyWidget(app, parent,handle,choices=None,subs = {},allowEntry = False,optional = False,activeStart=1,ewidth = 8,cwidth = None, cmd = None)
        dstart = None
        try:
            if settings["wallet"]["testnet"]:
                dstart = self.settings["wallet"]["host[:port]"]["testnet"]
            else:
                dstart = self.settings["wallet"]["host[:port]"]["mainnet"]
        except Exception as e:
            print("WARNING: did not understand settings['wallet']['host[:port]'] choice:\n%s"% str(e))
        self.daemon = MyWidget(self,self,handle = "daemon",startVal = self.settings["wallet"]["daemon"],allowEntry = False,cwidth = 18,cipadx = 1,
                                choices = ["None (cold wallet)","local, already running","other, host[:port]",],
                               subs={"other, host[:port]":{"handle":"host[:port]","choices":"entry","ewidth":20,"startVal": dstart,"allowEntry":False},}) # allow Entry not applicable
        #self.daemon.findSubs()
        self.camera_choice = MyWidget(self,self,handle = "camera",startVal = self.settings["app"]["camera"],allowEntry = False,cwidth = 18,cipadx = 1,
                                choices = ["None","webcam (v4l)","raspi cam",])

        self.showLogo.grid(row=0,column=0,rowspan=1,columnspan=2,sticky = tk.E)
        #self.heading.grid(row=0,column=1,sticky=tk.W)
        self.walletFile.grid(row=1,column=0,pady=(5,0),columnspan=2,sticky = tk.W+tk.E)
        self.daemon.grid(row=2,column=0,pady=(10,0),rowspan=1,columnspan=2)
        self.camera_choice.grid(row=3,column=0,pady=(10,15),rowspan=1,columnspan=2)
        self.testnet.grid(row=4,column=0,padx=(5,0),pady=10)
        self.launch.grid(row=4,column=1,padx=(5,0),pady= 5)

    def launch(self):
        wallet = self.walletFile.get()
        vals = {"walletFile": wallet[0],"password": wallet[1],"camera_choice":self.camera_choice.get()[0],"testnet":bool(self.testnet.get()),}
        self.settings["wallet"].update({"wallet_file":vals["walletFile"]})

        self.settings["app"].update({"camera":vals["camera_choice"]})
        daemon = self.daemon.get()
        if daemon[0] == "None (cold wallet)":
            vals.update({"cold":True})
            self.settings["wallet"].update({"daemon":"None (cold wallet)"})
        elif  daemon[0] == "local, already running":
            vals.update({"cold":False})
            self.settings["wallet"].update({"daemon":"local, already running"})
        elif daemon[0] == "other, host[:port]":
            both = daemon[1].split(":")
            host = daemon[1].split(":")[0]
            self.settings["wallet"].update({"daemon":"other, host[:port]"})

            if vals["testnet"]:
                self.settings["wallet"]["host[:port]"].update({"testnet":daemon[1]})
            else:
                self.settings["wallet"]["host[:port]"].update({"mainnet":daemon[1]})
            if len(both)==1:
                vals.update({"daemonHost":daemon[1]})
                vals.update({"cold":False})
            elif len(both) == 2:
                port = daemon[1].split(":")[1]
                vals.update({"daemonAddress":host + ":" + port})
                vals.update({"cold":False})
            else:
                MessageBox.showerror("Login Error","Could not parse daemon host[:port]\n\ne.x. testnet.xmrchain.net\n\ne.x. testnet.xmrchain.net:28081")
                return

        self.final = vals
        self.app.destroy()

class Lunlumo(ttk.Frame):
    def __init__(self,app, parent,settings = {},walletFile = None, password = '',background ="misc/genericspace2.gif",daemonAddress = None, daemonHost = None,testnet = False,cold = True,cmd = "./monero-wallet-cli",camera_choice = None,light = False, *args, **kwargs):
        ttk.Frame.__init__(self, parent,style = "app.TFrame", *args, **kwargs)
        self.app = app
        self.parent = parent
        self.busy = False
        self.cancel = False

        self.settings = settings
        self.background = background




        if camera_choice == "webcam (v4l)":
            from scanner import Scanner_pygame
            self.scanner = Scanner_pygame(app = self)
        elif camera_choice == "raspi cam":
            from scanner import Scanner_picamera
            self.scanner = Scanner_picamera(app = self)
        else:
            self.scanner = None
        self.preview = None
     def preview_request(self):
        if not self.scanner is None:
            if not self.preview:
                self.preview = Preview(self,self)
                self.scanner.add_child(self.preview)
        else:
            self.showerror("Camera Missing","Unable to display feed, as camera not initialized. This should should have been prevented by upstream logic.")

    def preview_cancel(self):
        if self.preview:
            self.scanner.children.remove(self.preview)
            self.preview.close()
            self.preview = None


    def monitor_incoming(self,payload,when_finished,*args,**kwargs):
        if not payload.got_all():
            self._root().after(2000,self.monitor_incoming,payload,when_finished,*args,**kwargs)
        else:
            self.scanner.children.remove(payload)
            self._root().after(50,when_finished,payload,*args,**kwargs)

    def payload_started(self):
        try:
            self.sender.destroy()
        except Exception as e:
            print(str(e))
        self.sender = None

    def save_settings(self):
        try:
            with open(".settings","w") as s:
                json.dump(self.settings,s,indent=3)
        except Exception as e:
            print("WARNING: unable to save settings:\n" + str(e))
            raise
################
class Preview(tk.Toplevel):
    def __init__(self,app,parent,delay = 450,title="Scanner",*args,**kargs):
        tk.Toplevel.__init__(self,background = "black")
        self.app = app
        self.parent = parent
        self._title = title
        self.title(self._title)
        self.delay = delay
        if self.app.light:
            self.delay = self.delay*3
        self.preview_screen = tk.Label(self)
        self.preview_screen.pack()
        self.status_display = tk.Label(self,text = "waiting for codes",background = "black",foreground = "white")
        self.status_display.pack()
        self.status2 = tk.Label(self,text = "waiting for status",wraplength = 250,background = "black",foreground = "white")
        self.status2.pack()
        self.protocol("WM_DELETE_WINDOW", self.kill)

        w, h = self._root().winfo_screenwidth(), self._root().winfo_screenheight()
        self.geometry("+%d+%d" % (int(0),int(h-256*480/640-170)))
        #self.lift()
        self.showme()
        self._root().after(self.delay,self.get_preview)

    def get_preview(self):
        thumb = self.app.scanner.snapshot()
        if thumb:
            #print("making thumb label")
            self.img = ImageTk.PhotoImage(thumb)
            self.preview_screen.config(image = self.img)
            s = ""
            try:
                for child in self.app.scanner.children:
                    try:
                        name = child.crc
                        stat = repr([i+1 for i,v in enumerate(child.bin) if v ==0])
                    except Exception as e:
                        #print(str(e))
                        stat = ""
                        name = ""
                    else:
                        s += " " + name + ": " + stat + ","
            except Exception as e:
                print(str(e))

            else:
                if s:
                    self.status2.configure(text="missing: %s"% s)
                else:
                    self.status2.configure(text="<waiting for status>")
        self._root().after(self.delay,self.get_preview)
        self.attributes('-topmost', 1)

    def digest(self,codes):
        if codes:
            self.status_display.config(text = "found:  " + codes[0].split(":")[0])
        else:
            self.status_display.config(text = "<nothing found>")


    def showme(self):
        #self.grab_set()
        #self.focus()
        #w, h = self._root().winfo_screenwidth(), self._root().winfo_screenheight()
        #print("w:",w,",h:",h)
        #self.geometry("%dx%d+0+0" % (w, h))
        self.lift()
        self.attributes('-topmost', 1)

        #self._root().after(200,self.attributes,'-topmost', 0)
        #self._root().after(210,self._root().attributes,'-topmost', 1)
        #self._root().after(220,self._root().attributes,'-topmost', 0)

        #self._root().after(100,self.geometry,"%dx%d+0+0" % (int(w*.9), h))
        #self.lift()


        #self.attributes('-fullscreen', True)
    def kill(self):
        print("Preview '%s' closed by WM_DELETE_WINDOW" % self._title)
        self.app.preview_cancel()
    def close(self):
        print("Preview '%s' closed" % self._title)
        self.destroy()


class SendTop(tk.Toplevel):
    def __init__(self,app,parent,title="File Sender",*args,**kargs):
        tk.Toplevel.__init__(self,background = "black")
        self.app = app
        self.parent = parent
        self._title = title
        self.title(self._title)
        self.sender = SendFrame(self.app,self, *args,**kargs)

        self.protocol("WM_DELETE_WINDOW", self.close)

        self.sender.pack(anchor = tk.W)
        w, h = self._root().winfo_screenwidth(), self._root().winfo_screenheight()
        self.geometry("%dx%d+%d+0" % (int(w*.85), h,int(w*.14)))
        #self.lift()
        self.showme()

    def showme(self):
        #self.grab_set()
        #self.focus()
        #w, h = self._root().winfo_screenwidth(), self._root().winfo_screenheight()
        #print("w:",w,",h:",h)
        #self.geometry("%dx%d+0+0" % (w, h))
        self.lift()
        self.attributes('-topmost', 1)

        #self._root().after(200,self.attributes,'-topmost', 0)
        #self._root().after(210,self._root().attributes,'-topmost', 1)
        #self._root().after(220,self._root().attributes,'-topmost', 0)

        #self._root().after(100,self.geometry,"%dx%d+0+0" % (int(w*.9), h))
        #self.lift()


        #self.attributes('-fullscreen', True)
    def close(self):
        self.app.cancel = True
        self.attributes('-topmost', 0)
        self.lower()
        try:
            self.app.preview_cancel()
            self.app.scanner.children = []
        except Exception as e:
            self.app.showerror("Cancelation Error",str(e))
        else:
            self.app.showerror("Canceled","Automation procedure canceled by user")
        #print("SendTop '%s' closed by WM_DELETE_WINDOW" % self._title)
        self._root().after(10,self.destroy)

class SendFrame(tk.Frame):
    def __init__(self,app,parent,payloadType,payloadPath,PAGE_SIZE = 700,qrBackground = "gray52",qrForeground = "gray1",qrScale = 8,delay = 850,width = 350, height = 400,*args,**kargs):
        tk.Frame.__init__(self,parent,height = height,background = "black", width = width, *args,**kargs) # style = "app.TFrame"
        #global slides
        self.app = app
        self.checksum = crc(payloadPath)
        self.status_pattern = re.compile("client_status" + r",(?P<crc>[a-z0-9]{7,10}),(?P<rank>[0-9]{1,5})/(?P<total>[0-9]{1,5}):(?P<payload>\S+)")
        self.skip = set([])
        self.parent = parent
        self.payloadType = payloadType
        self.payloadPath = payloadPath
        try:
            self.PAGE_SIZE = self.app.settings["sendqr"]["PAGE_SIZE"]
            self.qrScale = self.app.settings["sendqr"]["qrScale"]
            self.qrBackground = self.app.settings["sendqr"]["qrBackground"]
            self.qrForeground = self.app.settings["sendqr"]["qrForeground"]
            self.delay = self.app.settings["sendqr"]["delay"]
        except Exception as e:
            print("WARNING: unable to understand .settings for qr stream generation:\n" + str(e))
            self.PAGE_SIZE = PAGE_SIZE
            self.qrScale = qrScale
            self.qrBackground = qrBackground
            self.qrForeground = qrForeground
            self.delay = delay
        ##################################
        # settings
        self.moon = tk.PhotoImage(file = "misc/moonbutton1.gif")
        self.settings = tk.Frame(self,background = "black")
        self.title = ttk.Label(self,text = "sending: %s" % (os.path.basename(payloadPath)),style = "app.TLabel",wraplength = 200)
        self.crclbl = ttk.Label(self,text = "crc32: %s" % self.checksum,style = "app.TLabel")
        self.ticker = ttk.Label(self,text = "X / X",style = "app.TLabel")

        self.bytesEntry = MyWidget(self.app,self.settings,handle = "bytes / QR",choices="entry",startVal = self.PAGE_SIZE)
        self.scaleEntry = MyWidget(self.app,self.settings,handle = "size",choices=[str(x) for x in range(4,15)],startVal = self.qrScale)
        self.bgEntry = MyWidget(self.app,self.settings,handle = "bg color",choices=["gray" + str(x) for x in range(1,100)],allowEntry = 1,startVal = self.qrBackground)
        self.fgEntry = MyWidget(self.app,self.settings,handle = "fg Color",choices=["gray" + str(x) for x in range(1,100)],allowEntry = 1,startVal = self.qrForeground)
        self.delayEntry = MyWidget(self.app,self.settings,handle = "delay (ms)",choices="entry",startVal = self.delay)
        self.resetButton = tk.Button(self.settings,text = "apply",command =self.reset,image = self.moon,compound = tk.CENTER,height = 18,width = 60,highlightthickness=0,font=('Liberation Mono','12','normal'),foreground = "light gray",bd = 3,bg = "#900100" )

        self.title.grid(row=0,column = 0,sticky=tk.W)
        self.crclbl.grid(row=1,column = 0,sticky=tk.W,)
        self.ticker.grid(row=1,column = 2,sticky=tk.W,padx=(0,20))

        self.bytesEntry.grid(row = 0,column = 0,sticky = tk.E)
        self.scaleEntry.grid(row = 1,column = 0,sticky = tk.E)
        self.bgEntry.grid(row = 2,column = 0,sticky = tk.E)
        self.fgEntry.grid(row = 3,column = 0,sticky = tk.E)
        self.delayEntry.grid(row = 4,column = 0,sticky = tk.E)
        self.resetButton.grid(row = 5,column = 0,pady=(10,0))
        ##################################
        # Create QR images
        self.slides = []
        self.codes = []
        with open(payloadPath, "rb") as source:
            self.payload = base64.b64encode(source.read())

        self.numQR = ceil(len(self.payload)/self.PAGE_SIZE)
        if self.numQR >= 10000:
            raise Exception("%s QRs!! file really got out of hand, exiting"% self.numQR)

        self.ind = 0
        self.i = 1
        self.x = 0

        self.ready = False
        self.make_slides()
        self._root().after(50, self.idle_refresh,)

        #################################


        self.current = ttk.Label(self,style = "app.TLabel")

        self.settings.grid(row=2,column = 0,sticky=tk.NW,padx = (0,30))

        self.current.grid(row=0,column = 3,rowspan =9,sticky=tk.W)
    def digest(self,codes):
        for code in codes:
            try:
                match = self.status_pattern.fullmatch(code)
                if match:
                    if match.group("crc") == self.checksum:
                        self.skip = eval(match.group("payload")) | self.skip
            except:
                pass
    def reset(self):
        try:
            self.delay = int(self.delayEntry.get()[0])
            self.PAGE_SIZE = int(self.bytesEntry.get()[0])
            self.qrScale = int(self.scaleEntry.get()[0])
            self.qrBackground = self.bgEntry.get()[0]
            self.qrForeground = self.fgEntry.get()[0]
            if self.delay < 150:
                raise Exception("Failed settings check: delay < 150")
            if self.PAGE_SIZE < 10 or self.PAGE_SIZE > 2000:
                raise Exception("Failed settings check: self.PAGE_SIZE < 10 or self.PAGE_SIZE > 2000")
            if self.qrScale < 3 or self.qrScale > 20:
                raise Exception("Failed settings check: self.qrScale < 3 or self.qrScale > 20")
            if not self.qrBackground in self.get_colors():
                print(repr(self.get_colors()))
                raise Exception("Failed settings check: invalid color %s"% self.qrBackground)
            if not self.qrForeground in self.get_colors():
                print(repr(self.get_colors()))
                raise Exception("Failed settings check: invalid color %s"% self.qrForeground)
        except Exception as e:
            self.PAGE_SIZE = self.app.settings["sendqr"]["PAGE_SIZE"]
            self.qrScale = self.app.settings["sendqr"]["qrScale"]
            self.qrBackground = self.app.settings["sendqr"]["qrBackground"]
            self.qrForeground = self.app.settings["sendqr"]["qrForeground"]
            self.delay = self.app.settings["sendqr"]["delay"]

            self.bytesEntry.value.delete(0, tk.END)
            self.bytesEntry.value.insert(0,self.PAGE_SIZE)
            self.scaleEntry.value.set(self.qrScale)
            self.bgEntry.value.set(self.qrBackground)
            self.fgEntry.value.set(self.qrForeground)
            self.delayEntry.value.delete(0, tk.END)
            self.delayEntry.value.insert(0,self.delay)
            #self.lift()
            self.parent.attributes('-topmost', 0)
            self.parent.lower()
            self.app.showerror("Settings Error:",str(e))
            self._root().after(100,self.parent.showme)
            return

        try:
            self.app.settings["sendqr"]["PAGE_SIZE"] = self.PAGE_SIZE
            self.app.settings["sendqr"]["qrScale"] = self.qrScale
            self.app.settings["sendqr"]["qrBackground"] = self.qrBackground
            self.app.settings["sendqr"]["qrForeground"] = self.qrForeground
            self.app.settings["sendqr"]["delay"] = self.delay
            self.app.save_settings()
        except Exception as e:
            print("WARNING: unable to save qr stream generation settings:\n" + str(e))
        self.numQR = ceil(len(self.payload)/self.PAGE_SIZE)
        if self.numQR >= 10000:
            raise Exception("%s QRs!! file really got out of hand, exiting"% self.numQR)
        self.slides = []
        self.skip = []
        self.i = 1
        self.x = 0
        self.ind = 0
        if self.ready: self.make_slides()
        self.ind = 0


    def make_slides(self):
        chunk = self.payload[self.x: self.x+self.PAGE_SIZE]
        if chunk:
            self.ready = False
            heading = self.payloadType + "," + self.checksum + "," + str(self.i) + "/" + str(int(self.numQR)) + ":"
            page = heading + b(chunk)
            qrPage = pyqrcode.create(page,error="L")
            #saved = qrPage.svg(heading.replace(",","_").replace(":","_").replace("/","_") + ".svg")
            code = tk.BitmapImage(data=qrPage.xbm(scale=self.qrScale))
            code.config(background=self.qrBackground,foreground = self.qrForeground )
            #exec("self.i%s = code"% self.i)
            self.slides.append(code)
            self.i+=1
            self.x += self.PAGE_SIZE
            self._root().after(100, self.make_slides)
        else:
            self.ready = True
    def idle_refresh(self,something = None):
        self._root().after_idle(self.refresh)
    def refresh(self):
        #print("refresh :" ,self.ind)
        if self.slides:
            while self.ind in self.skip:
                #print("skipping :",self.ind)
                self.ind += 1
            try:
                slide = self.slides[self.ind]
                self.ticker.configure(text = "%s / %s" % (self.ind+1,self.numQR))
                #print("showing :",self.ind)
                self.current.configure(image=slide)
            except IndexError:
                self.ind = 0
                #print("indexError :",self.ind)
            else:
                self.ind += 1
            if self.ind >= self.numQR:
                #print("end reached :",self.ind)
                self.ind =0

        self._root().after(self.delay, self.idle_refresh,)
    def get_colors(self):
        s = ['snow', 'ghost white', 'white smoke', 'gainsboro', 'floral white', 'old lace',
          'linen', 'antique white', 'papaya whip', 'blanched almond', 'bisque', 'peach puff',
          'navajo white', 'lemon chiffon', 'mint cream', 'azure', 'alice blue', 'lavender',
          'lavender blush', 'misty rose', 'dark slate gray', 'dim gray', 'slate gray',
          'light slate gray', 'gray', 'light grey', 'midnight blue', 'navy', 'cornflower blue', 'dark slate blue',
          'slate blue', 'medium slate blue', 'light slate blue', 'medium blue', 'royal blue',  'blue',
          'dodger blue', 'deep sky blue', 'sky blue', 'light sky blue', 'steel blue', 'light steel blue',
          'light blue', 'powder blue', 'pale turquoise', 'dark turquoise', 'medium turquoise', 'turquoise',
          'cyan', 'light cyan', 'cadet blue', 'medium aquamarine', 'aquamarine', 'dark green', 'dark olive green',
          'dark sea green', 'sea green', 'medium sea green', 'light sea green', 'pale green', 'spring green',
          'lawn green', 'medium spring green', 'green yellow', 'lime green', 'yellow green',
          'forest green', 'olive drab', 'dark khaki', 'khaki', 'pale goldenrod', 'light goldenrod yellow',
          'light yellow', 'yellow', 'gold', 'light goldenrod', 'goldenrod', 'dark goldenrod', 'rosy brown',
          'indian red', 'saddle brown', 'sandy brown',
          'dark salmon', 'salmon', 'light salmon', 'orange', 'dark orange',
          'coral', 'light coral', 'tomato', 'orange red', 'red', 'hot pink', 'deep pink', 'pink', 'light pink',
          'pale violet red', 'maroon', 'medium violet red', 'violet red',
          'medium orchid', 'dark orchid', 'dark violet', 'blue violet', 'purple', 'medium purple',
          'thistle', 'snow2', 'snow3',
          'snow4', 'seashell2', 'seashell3', 'seashell4', 'AntiqueWhite1', 'AntiqueWhite2',
          'AntiqueWhite3', 'AntiqueWhite4', 'bisque2', 'bisque3', 'bisque4', 'PeachPuff2',
          'PeachPuff3', 'PeachPuff4', 'NavajoWhite2', 'NavajoWhite3', 'NavajoWhite4',
          'LemonChiffon2', 'LemonChiffon3', 'LemonChiffon4', 'cornsilk2', 'cornsilk3',
          'cornsilk4', 'ivory2', 'ivory3', 'ivory4', 'honeydew2', 'honeydew3', 'honeydew4',
          'LavenderBlush2', 'LavenderBlush3', 'LavenderBlush4', 'MistyRose2', 'MistyRose3',
          'MistyRose4', 'azure2', 'azure3', 'azure4', 'SlateBlue1', 'SlateBlue2', 'SlateBlue3',
          'SlateBlue4', 'RoyalBlue1', 'RoyalBlue2', 'RoyalBlue3', 'RoyalBlue4', 'blue2', 'blue4',
          'DodgerBlue2', 'DodgerBlue3', 'DodgerBlue4', 'SteelBlue1', 'SteelBlue2',
          'SteelBlue3', 'SteelBlue4', 'DeepSkyBlue2', 'DeepSkyBlue3', 'DeepSkyBlue4',
          'SkyBlue1', 'SkyBlue2', 'SkyBlue3', 'SkyBlue4', 'LightSkyBlue1', 'LightSkyBlue2',
          'LightSkyBlue3', 'LightSkyBlue4', 'SlateGray1', 'SlateGray2', 'SlateGray3',
          'SlateGray4', 'LightSteelBlue1', 'LightSteelBlue2', 'LightSteelBlue3',
          'LightSteelBlue4', 'LightBlue1', 'LightBlue2', 'LightBlue3', 'LightBlue4',
          'LightCyan2', 'LightCyan3', 'LightCyan4', 'PaleTurquoise1', 'PaleTurquoise2',
          'PaleTurquoise3', 'PaleTurquoise4', 'CadetBlue1', 'CadetBlue2', 'CadetBlue3',
          'CadetBlue4', 'turquoise1', 'turquoise2', 'turquoise3', 'turquoise4', 'cyan2', 'cyan3',
          'cyan4', 'DarkSlateGray1', 'DarkSlateGray2', 'DarkSlateGray3', 'DarkSlateGray4',
          'aquamarine2', 'aquamarine4', 'DarkSeaGreen1', 'DarkSeaGreen2', 'DarkSeaGreen3',
          'DarkSeaGreen4', 'SeaGreen1', 'SeaGreen2', 'SeaGreen3', 'PaleGreen1', 'PaleGreen2',
          'PaleGreen3', 'PaleGreen4', 'SpringGreen2', 'SpringGreen3', 'SpringGreen4',
          'green2', 'green3', 'green4', 'chartreuse2', 'chartreuse3', 'chartreuse4',
          'OliveDrab1', 'OliveDrab2', 'OliveDrab4', 'DarkOliveGreen1', 'DarkOliveGreen2',
          'DarkOliveGreen3', 'DarkOliveGreen4', 'khaki1', 'khaki2', 'khaki3', 'khaki4',
          'LightGoldenrod1', 'LightGoldenrod2', 'LightGoldenrod3', 'LightGoldenrod4',
          'LightYellow2', 'LightYellow3', 'LightYellow4', 'yellow2', 'yellow3', 'yellow4',
          'gold2', 'gold3', 'gold4', 'goldenrod1', 'goldenrod2', 'goldenrod3', 'goldenrod4',
          'DarkGoldenrod1', 'DarkGoldenrod2', 'DarkGoldenrod3', 'DarkGoldenrod4',
          'RosyBrown1', 'RosyBrown2', 'RosyBrown3', 'RosyBrown4', 'IndianRed1', 'IndianRed2',
          'IndianRed3', 'IndianRed4', 'sienna1', 'sienna2', 'sienna3', 'sienna4', 'burlywood1',
          'burlywood2', 'burlywood3', 'burlywood4', 'wheat1', 'wheat2', 'wheat3', 'wheat4', 'tan1',
          'tan2', 'tan4', 'chocolate1', 'chocolate2', 'chocolate3', 'firebrick1', 'firebrick2',
          'firebrick3', 'firebrick4', 'brown1', 'brown2', 'brown3', 'brown4', 'salmon1', 'salmon2',
          'salmon3', 'salmon4', 'LightSalmon2', 'LightSalmon3', 'LightSalmon4', 'orange2',
          'orange3', 'orange4', 'DarkOrange1', 'DarkOrange2', 'DarkOrange3', 'DarkOrange4',
          'coral1', 'coral2', 'coral3', 'coral4', 'tomato2', 'tomato3', 'tomato4', 'OrangeRed2',
          'OrangeRed3', 'OrangeRed4', 'red2', 'red3', 'red4', 'DeepPink2', 'DeepPink3', 'DeepPink4',
          'HotPink1', 'HotPink2', 'HotPink3', 'HotPink4', 'pink1', 'pink2', 'pink3', 'pink4',
          'LightPink1', 'LightPink2', 'LightPink3', 'LightPink4', 'PaleVioletRed1',
          'PaleVioletRed2', 'PaleVioletRed3', 'PaleVioletRed4', 'maroon1', 'maroon2',
          'maroon3', 'maroon4', 'VioletRed1', 'VioletRed2', 'VioletRed3', 'VioletRed4',
          'magenta2', 'magenta3', 'magenta4', 'orchid1', 'orchid2', 'orchid3', 'orchid4', 'plum1',
          'plum2', 'plum3', 'plum4', 'MediumOrchid1', 'MediumOrchid2', 'MediumOrchid3',
          'MediumOrchid4', 'DarkOrchid1', 'DarkOrchid2', 'DarkOrchid3', 'DarkOrchid4',
          'purple1', 'purple2', 'purple3', 'purple4', 'MediumPurple1', 'MediumPurple2',
          'MediumPurple3', 'MediumPurple4', 'thistle1', 'thistle2', 'thistle3', 'thistle4',
          'gray1', 'gray2', 'gray3', 'gray4', 'gray5', 'gray6', 'gray7', 'gray8', 'gray9', 'gray10',
          'gray11', 'gray12', 'gray13', 'gray14', 'gray15', 'gray16', 'gray17', 'gray18', 'gray19',
          'gray20', 'gray21', 'gray22', 'gray23', 'gray24', 'gray25', 'gray26', 'gray27', 'gray28',
          'gray29', 'gray30', 'gray31', 'gray32', 'gray33', 'gray34', 'gray35', 'gray36', 'gray37',
          'gray38', 'gray39', 'gray40', 'gray42', 'gray43', 'gray44', 'gray45', 'gray46', 'gray47',
          'gray48', 'gray49', 'gray50', 'gray51', 'gray52', 'gray53', 'gray54', 'gray55', 'gray56',
          'gray57', 'gray58', 'gray59', 'gray60', 'gray61', 'gray62', 'gray63', 'gray64', 'gray65',
          'gray66', 'gray67', 'gray68', 'gray69', 'gray70', 'gray71', 'gray72', 'gray73', 'gray74',
          'gray75', 'gray76', 'gray77', 'gray78', 'gray79', 'gray80', 'gray81', 'gray82', 'gray83',
          'gray84', 'gray85', 'gray86', 'gray87', 'gray88', 'gray89', 'gray90', 'gray91', 'gray92',
          'gray93', 'gray94', 'gray95', 'gray97', 'gray98', 'gray99']
        return s

class FilePicker(ttk.Frame):
    def __init__(self,app, parent,handle,start = None,buttonName = "Select",askPass = False,background = None,ftypes = [("all","*")],idir="./", *args, **kwargs):
        tk.Frame.__init__(self, parent,highlightcolor = "white",highlightbackground = "white",highlightthickness=3,background ="#4C4C4C" , *args, **kwargs)
        self.app = app
        self.parent = parent
        self.handle = handle
        self.ftypes = ftypes
        self.idir = idir
        self.askPass = askPass

        self.moon1 = tk.PhotoImage(file = "misc/moonbutton1.gif")
        self.moon2 = tk.PhotoImage(file = "misc/moonbutton2.gif")
        self.moon3 = tk.PhotoImage(file = "misc/moonbutton3.gif")
        if background:
            self.bg = tk.PhotoImage(file = background)
            self.bglabel = tk.Label(self, image=self.bg)
            self.bglabel.place(x=0, y=0, relwidth=1, relheight=1)

        self.title = ttk.Label(self,text = self.handle,style = "app.TLabel")
        self.displayVar = tk.StringVar()
        self.displayVar.set("*")
        self.selectVar = tk.StringVar()
        self.selectVar.set("")
        self.passlbl = ttk.Label(self,text = "password:",style = "app.TLabel")
        self.password = tk.Entry(self,text = self.handle,insertofftime=5000,show = "*",width = 13,foreground = "white")
        if start:
            self.selectVar.set(start)
            self.displayVar.set(os.path.basename(start))
        self.select = ttk.Label(self,textvariable = self.displayVar,wraplength=210,style = "app.TLabel")
        #self.button = ttk.Button(self,text = buttonName,style = "app.TButton",command =self.dialog )
        if "monero" not in sys.argv[1]:
            self.button = tk.Button(self,text = "select",command =self.dialog,highlightthickness=0,font=('Liberation Mono','12','normal'),foreground = "white",bd = 3,bg = "#2D89A0" )
        else:
            self.button = tk.Button(self,text = "select",command =self.dialog,image = self.moon2,compound = tk.CENTER,height = 18,width = 60,highlightthickness=0,font=('Liberation Mono','12','normal'),foreground = "white",bd = 3,bg = "#900100" )
        self.title.grid(row = 0,column = 0,padx=(5,0))
        self.button.grid(row = 0,column = 1,padx=6,pady = 6)
        self.select.grid(row = 1,column = 0,sticky = tk.W,columnspan = 3,padx=(5,0),pady=(0,3))
        if self.askPass:
            self.passlbl.grid(row = 2,column = 0,sticky = tk.W,padx=(5,3))
            self.password.grid(row = 2,column = 1,sticky = tk.W,padx=(0,7),pady = (0,8))

    def dialog(self):
        choice = FileDialog.askopenfilename(filetypes=self.ftypes,initialdir = self.idir,title = self.handle)
        self.password.delete(0,tk.END)
        if choice:
            self.displayVar.set(os.path.basename(choice))
            self.selectVar.set(choice)
        else:
            self.displayVar.set("*")
            self.selectVar.set("")
    def get(self):
        if not self.askPass:
            if self.selectVar.get() == "":
                return None
            return self.selectVar.get()
        else:
            if self.selectVar.get() == "":
                return None,None
            return self.selectVar.get(),self.password.get()

class MyWidget(ttk.Frame):
    def __init__(self,app, parent,handle,choices=None,subs = {},startVal = None,allowEntry = False,static = False, background = "misc/genericspace.gif",
                 cipadx = 0,optional = False,activeStart=1,ewidth = 8,cwidth = None, cmd = None, *args, **kwargs):
        ttk.Frame.__init__(self, parent,style = "app.TFrame", *args, **kwargs)
        self.app = app
        self.parent = parent
        self.handle = handle
        self.choices = choices
        self.optional = optional
        self.allowEntry = allowEntry
        self.startVal = startVal
        self.cmd = cmd
        self.subs = subs
        self.sub = None

        if background and not self.app.light:
            self.bg = tk.PhotoImage(file = background)
            self.bglabel = tk.Label(self, image=self.bg)
            self.bglabel.place(x=0, y=0, relwidth=1, relheight=1)

        if self.optional:
            self.optState = tk.IntVar()
            self.optBut = ttk.Checkbutton(self,variable = self.optState,onvalue = 1,offvalue=0,command = self._grey,style = "app.TCheckbutton")
            self.optBut.pack(side="left")
        if isinstance(self.choices,__builtins__.list):
            if not allowEntry:
                state = "readonly"
            else:
                state = "enabled"
            if not cwidth: cwidth = len(max(self.choices,key=len))
            self.value = ttk.Combobox(self,values = self.choices,state = state,width=cwidth,postcommand = self.wideMenu,style = "app.TCombobox")
            self.value.bind('<<ComboboxSelected>>',self.findSubs)
            #self.value.bind('<Configure>', self.wideMenu)
        if self.choices == "entry":
            state = "enabled" if not static else "readonly"
            self.value = ttk.Entry(self,width=ewidth,style = "app.TEntry",state = state)
            self._root().after(0,self.findSubs,None,False)

        self.title = ttk.Label(self, text = self.handle,style = "app.TLabel")
        self.title.pack(anchor = tk.W)
        if self.choices:
            self.value.pack(anchor = tk.E,ipadx = cipadx)
            if not self.startVal is None:
                if not self.choices == "entry":
                    self.value.set(self.startVal)
                    self._root().after(0,self.findSubs,None,False)
                else:
                    self.value.insert(0,startVal)
                    self._root().after(0,self.findSubs,None,False)
        if self.optional:
            if activeStart:
                self.optState.set(1)

    def wideMenu(self,event = None):
        try:
            global mystyle
            if self.handle in ["Account"]:
                #print("got Account wideMenu")
                mystyle.configure("TCombobox",postoffset = (0,0,150,0))
                self.value.config(style = "TCombobox")
            elif self.handle in ["Subaddress Book"]:
                mystyle.configure("TCombobox",postoffset = (0,0,100,0))
                self.value.config(style = "TCombobox")
            else:
                mystyle.configure("TCombobox",postoffset = (0,0,0,0))
        except Exception as e:
            print(str(e))


    def get(self):
        #print(self.handle,self.sub,bool(self.sub))
        if self.choices:
            if self.sub:
                val = [self.value.get()]
                try:
                    val.extend(self.sub.get())
                except TypeError:
                    print(self.handle,self.sub,bool(self.sub))
                return val
            return [self.value.get()]
        elif self.optional:
            if self.optState.get():
                if self.sub:
                    val = [self.value.get()]
                    try:
                        val.extend(self.sub.get())
                    except TypeError:
                        print(self.handle,self.sub,bool(self.sub))
                    return val
                return [self.handle]
            else:
                return None
        else:
            print("tried to get:%s" %self.handle)
            return #[self.value.get()]

    def findSubs(self,event = None,not_init = True):
        if self.sub:
            self.sub.destroy()
            self.sub = None
        if self.subs:
            if self.value.get() in self.subs and not self.choices == "entry":
                self.sub = MyWidget(self.app,self,**self.subs[self.value.get()])
                self.sub.pack(anchor = tk.E,pady=3)
            elif self.choices == "entry":
                self.sub = MyWidget(self.app,self,**self.subs["entry"])
                self.sub.pack(anchor = tk.E,pady=3)
            else:
                pass
        if self.cmd and not_init:
            self.cmd()

    def _grey(self,override = False):
        if self.optional and self.choices:
            if not self.optState.get():
                self.value.config(state="disabled")
            else:
                if isinstance(self.value,tkinter.ttk.Combobox):
                    if self.allowEntry:
                        self.value.config(state="enabled")
                    else:
                        self.value.config(state="readonly")
                else:
                    self.value.config(state="enabled")
        if self.sub:
            self.sub._grey()

def crc(fileName):
    prev = 0
    for eachLine in open(fileName,"rb"):
        prev = zlib.crc32(eachLine, prev)
    return "%x"%(prev & 0xFFFFFFFF)
