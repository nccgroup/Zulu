#!/usr/bin/env python
# -*- coding: utf-8 -*-

# wxGlade powered

import wx
import serial
import threading
import time
from serialEvent import *
from settingsDialog import SerialDialog
from displayDialog import DisplayDialog
import time
from globals import *

ID_CONNECT = wx.NewId()
ID_DISCONNECT = wx.NewId()
ID_PORT_SETTINGS = wx.NewId()
ID_DISPLAY_SETTINGS = wx.NewId()



outputCnt = 0

def parseInitFile(f, serial, settings):
    d = [line[:-1].strip() for line in f.readlines()]
    #parse not comment starts with # and [serial] information
    a = [line for line in d if line != '' and line[0] != '[' and line[0] != '#']
    ee = [c.split('#',1)[0].strip().split('=') for c in a]
    qq = [(a[0].strip(),a[1].strip()) for a in ee]
    for name, value in qq:
        #parity='N' or'O' can not be eval()
        if name == 'parity':
            serial.parity = value
        #sometimes port = '/dev/ttyS0'
        elif name == 'port':
            try: serial.port = int(value)
            except: serial.port = value
        #font format as "fontname-pointsize" as "Courier 10 Pitch-10"
        elif name == 'font':
            x,y = value.split('-')
            #utf-8 is always our choice :D
            try:
                settings.font = wx.Font(eval(y), wx.DEFAULT, wx.NORMAL, wx.NORMAL, False, x)
            except UnicodeDecodeError:
                settings.font = wx.Font(eval(y), wx.DEFAULT, wx.NORMAL, wx.NORMAL, False, x.decode('utf-8'))
        #for other attrs, we just set there attr by setattr and got their value by eval()
        else:
            if hasattr(serial, name):
                setattr(serial,name, eval(value))
            else:
                setattr(settings,name, eval(value))
                
def writeInitFile(f, serial, settings):
    serial_para = ['port', 'baudrate', 'bytesize', 'stopbits',
                   'parity',  'rtscts', 'xonxoff']
    settings_para = ['echo', 'newline', 'unprintable', 'forecolor', 'backcolor']
    f.write('[serial]\n')
    for item in serial_para:
        f.write('%s = %s\n'%(item, str(getattr(serial, item))))
    f.write('[settings]\n')
    for item in settings_para:
        f.write('%s = %s\n'%(item, str(getattr(settings, item))))
    #we need to process the font class before we write
    try:
        f.write('font = %s-%d\n' % (settings.font.GetFaceName(),
                                    settings.font.GetPointSize()))
    except UnicodeEncodeError:
        # utf-8 will be all right?
        f.write('font = %s-%d\n' % (settings.font.GetFaceName().encode('utf-8'),
                                    settings.font.GetPointSize()))
    
class TerminalSettings:
    """for the display setting of the terminal
    """
    def __init__(self, echo = False, unprintable = True, newline = CRLF):
        self.echo = echo
        self.unprintable = unprintable
        self.newline = newline
        self.forecolor = None
        self.backcolor = None
        self.font = None
    
class ComThread(threading.Thread):
    """Read the serial port continously in this thread,
    timeout sets to 0.3s"""
    def __init__(self, parent):
        threading.Thread.__init__(self)
        self.parent = parent
        self.serial = self.parent.serial
        self.alive = threading.Event()
        self.alive.set()
        self.setDaemon(1)
    def run(self):
        while(self.alive.isSet()):
            #print 'thread run...'
            text = self.serial.read(1)          #read one, with timout
            if text:                            #check if not timeout
                n = self.serial.inWaiting()     #look if there is more to read
                if n:
                    text = text + self.serial.read(n) #get it
                #newline transformation
                if self.parent.settings.newline == CR:
                    text = text.replace('\r', '\n')
                elif self.parent.settings.newline == LF:
                    pass
                elif self.parent.settings.newline == CRLF:
                    text = text.replace('\r\n', '\n') #
                #this is an elegant way to update the GUI in the not-main-thread
                event = SerialRxEvent(self.parent.GetId(), text)
                self.parent.GetEventHandler().AddPendingEvent(event)
    def stopRun(self):
        self.alive.clear()
        
class FrameTerminal(wx.Frame):
    """main frame of the serial assist
    """
    def __init__(self, output_window, *args, **kwds):
        # begin wxGlade: FrameTerminal.__init__
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.frame_statusbar = self.CreateStatusBar(1, 0)
        
	self.outputwin = output_window

	self.linebuffer = ""
	self.currentchar = ""
	self.inputdata = ""
	self.linebufferlist = []
	
        # Tool Bar
        self.frame_toolbar = wx.ToolBar(self, -1)
        self.SetToolBar(self.frame_toolbar)

	path = self.outputwin.workingdir


        self.frame_toolbar.AddLabelTool(ID_CONNECT, "connect",
                                        wx.Bitmap(path + "/../images/play.png", wx.BITMAP_TYPE_ANY),
                                        wx.NullBitmap, wx.ITEM_NORMAL,
                                        "Connect to serial port",
                                        "Connect to serial port")
        self.frame_toolbar.AddLabelTool(ID_DISCONNECT, "disconnect",
                                        wx.Bitmap(path + "/../images/stop.png", wx.BITMAP_TYPE_ANY),
                                        wx.NullBitmap, wx.ITEM_NORMAL,
                                        "Disconnect from serial port",
                                        "Disconnect from serial port")
        self.frame_toolbar.AddLabelTool(ID_PORT_SETTINGS, "SerialportSettings",
                                        wx.Bitmap(path + "/../images/configure.png", wx.BITMAP_TYPE_ANY),
                                        wx.NullBitmap, wx.ITEM_NORMAL,
                                        "Port settings",
                                        "Port settings")
        self.frame_toolbar.AddLabelTool(ID_DISPLAY_SETTINGS, "DisplaySettings",
                                        wx.Bitmap(path + "/../images/configure_display.png", wx.BITMAP_TYPE_ANY),
                                        wx.NullBitmap, wx.ITEM_NORMAL,
                                        "Display settings",
                                        "Display settings")
        # Tool Bar end
        self.text_ctrl_output = wx.TextCtrl(self, -1, "",
                                            style=wx.TE_PROCESS_TAB|wx.TE_MULTILINE
                                            |wx.TE_READONLY|wx.HSCROLL|wx.TE_RICH2
                                            |wx.TE_LINEWRAP)

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_TOOL, self.onConnect, id=ID_CONNECT)
        self.Bind(wx.EVT_TOOL, self.onDisconnect, id=ID_DISCONNECT)
        self.Bind(wx.EVT_TOOL, self.onPortSettings, id=ID_PORT_SETTINGS)
        self.Bind(wx.EVT_TOOL, self.onDisplaySettings, id=ID_DISPLAY_SETTINGS)
        # end wxGlade
        self.settings = TerminalSettings() #init display settings
        self.serial = serial.Serial()
	self.outputwin.ser = self.serial
        self.comThread = None
        self.title = DEFAULT_TITLE
        self.SetTitle(self.title)
        self.f = None                 #file for autosaving
        self.settings.font = wx.Font(12, wx.DEFAULT,
                                     wx.NORMAL, wx.NORMAL,
                                     False, u'Courier 10 Pitch')
        
        self.text_ctrl_output.Bind(wx.EVT_CHAR, self.onChar, id = -1)
        self.Bind(EVT_SERIALRX, self.onSerialRead)
        self.Bind(wx.EVT_CLOSE, self.onClose)
        wx.CallLater(AUTOSAVE_PERIOD, self.autoSave)
        self.frame_toolbar.EnableTool(ID_DISCONNECT, False)
        self.preData = WELCOME_INFO  #used for autosave to diff if new character are there
        D_DEFAULT_FONT = wx.Font(12, wx.DEFAULT,
                                 wx.NORMAL, wx.NORMAL,
                                 False, u'Courier 10 Pitch')
        self.__parse_initial()
        self.updateTextctrl()
        self.light = -2
        self.text_ctrl_output.WriteText(WELCOME_INFO)

    def __set_properties(self):
        # begin wxGlade: FrameTerminal.__set_properties
        #self.SetTitle("serialAssist")
        _icon = wx.EmptyIcon()

	path = self.outputwin.workingdir

        _icon.CopyFromBitmap(wx.Bitmap(path + "/../images/zulu_logo16x16.png", wx.BITMAP_TYPE_ANY))
        self.SetIcon(_icon)
        #self.SetSize((543, 433))
        self.SetSize((743, 560))
        self.frame_statusbar.SetStatusWidths([-1])
        # statusbar fields
        frame_statusbar_fields = [""]
        for i in range(len(frame_statusbar_fields)):
            self.frame_statusbar.SetStatusText(frame_statusbar_fields[i], i)
        self.frame_toolbar.SetToolBitmapSize((32, 32))
        self.frame_toolbar.SetToolSeparation(9)
        self.frame_toolbar.Realize()
        self.text_ctrl_output.SetFont(wx.Font(11, wx.DEFAULT,
                                              wx.NORMAL, wx.NORMAL, 0, ""))
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: FrameTerminal.__do_layout
        sizer_5 = wx.BoxSizer(wx.VERTICAL)
        sizer_5.Add(self.text_ctrl_output, 2, wx.ALL|wx.EXPAND, 10)
        self.SetSizer(sizer_5)
        self.Layout()
        # end wxGlade
        
    def __parse_initial(self):


	path = self.outputwin.workingdir

        try:
            f = open(path + '/serial_init.txt', 'r')
            parseInitFile(f, self.serial, self.settings)
            f.close()
        #if load init file fails, we reload the defaults
        except Exception, e:
            print e
            self.serial.port = S_PORT
            self.serial.baudrate = S_BAUDRATE
            self.serial.bytesize = S_BYTESIZE
            self.serial.stopbits = S_STOPBITS
            self.serial.parity = S_PARITY
            self.serial.rtscts = S_RTSCTS
            self.serial.xonxoff = S_XONXOFF
            self.settings.echo = D_ECHO
            self.settings.newline = D_NEWLINE
            self.settings.unprintable = D_UNPRINTABLE
            self.settings.forecolor = D_FOREGROUND_COLOR
            self.settings.backcolor = D_BACKGROUND_COLOR
            self.settings.font = wx.Font(13, wx.DEFAULT, wx.NORMAL,
                                         wx.NORMAL, False, u'Courier 10 Pitch')
	    self.outputwin.ser = self.serial        

    def updateTextctrl(self):
        """update the output text ctrl by diplay settings
        """
        if self.settings.forecolor is not None:
            self.text_ctrl_output.SetForegroundColour(self.settings.forecolor)
        if self.settings.backcolor is not None:
            self.text_ctrl_output.SetBackgroundColour(self.settings.backcolor)
        if self.settings.font is not None:
            self.text_ctrl_output.SetFont(self.settings.font)
        text = self.text_ctrl_output.GetValue()
        self.text_ctrl_output.Clear()
        self.text_ctrl_output.SetValue(text)
        self.text_ctrl_output.Update()
    # print data to widget text_ctrl_ouptput
    
    def printt(self, data):
        """print to text control(terminal)
        """
        self.text_ctrl_output.AppendText(data)
    
    def printTitle(self, data):
        """information stay as title for 1.8 seconds
        """
	#try:
        #	wx.CallLater(1800, lambda x: x.SetTitle(self.title), self)
	#except:
	#	return
        #self.SetTitle(data)
        pass

    def printStatusbar(self, data):
        """information stay at statusbar for 1.8 seconds
        """
	try:
        	#wx.CallLater(1800, lambda x: x.SetStatusText(''), self.frame_statusbar)
        	self.frame_statusbar.SetStatusText(data)
	except:
		pass
                
    def autoSave(self):
        """auto save callback function for saving the serial output and input
        """
        data = self.text_ctrl_output.GetValue()
        if data != self.preData:
            path = self.outputwin.workingdir + "/../logs/serial_log" + time.strftime("_%Y-%m-%d_%H-%M-%S", time.localtime()) + ".log"
            self.f = open(path, 'w')
            self.f.write('recent saved at : %s\n' % time.asctime())
            self.f.write(data)
            self.f.close()
            self.preData = data
        wx.CallLater(AUTOSAVE_PERIOD, self.autoSave)
    
    def connect(self):
        status = False
        try:
            self.serial.timeout = 0.3   #set serial polling timeout to 0.3s.
            if self.serial.port is None: self.serial.port = 0
            status = self.serial.open()
            self.title = "Serial Terminal on %s [%s, %s%s%s%s%s]" % (
                                self.serial.portstr,
                                self.serial.baudrate,
                                self.serial.bytesize,
                                self.serial.parity,
                                self.serial.stopbits,
                                self.serial.rtscts and ' RTS/CTS' or '',
                                self.serial.xonxoff and ' Xon/Xoff' or '',
                            )
            self.SetTitle(self.title)
        except Exception, e:
            dlg = wx.MessageDialog(self,'exception occured: %s, please check your configuration'%str(e), style = wx.OK|wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.SetTitle(DEFAULT_TITLE)
            return
        if status is False:
            self.printTitle('choose the right com for connecting~')
            return
        self.printTitle('connection build...')
        self.frame_toolbar.EnableTool(ID_DISCONNECT, True)
        self.frame_toolbar.EnableTool(ID_CONNECT, False)
        self.comThread = ComThread(self)
        self.comThread.start()
        
    def onConnect(self, event): # wxGlade: FrameTerminal.<event_handler>
        self.connect()
    
    def disconnect(self):
        if self.comThread is not None:
            self.comThread.stopRun()
            self.comThread.join()
            self.comThread = None
            self.printTitle('disconnect success...')
        self.serial.close()   #it doesn't matter if you call close when serial was closed
        self.title = DEFAULT_TITLE
        self.frame_toolbar.EnableTool(ID_DISCONNECT, False)
        self.frame_toolbar.EnableTool(ID_CONNECT, True)
                
    def onDisconnect(self, event): # wxGlade: FrameTerminal.<event_handler>
        #self.disconnect()
	self.onClose(1)

    def onPortSettings(self, event): # wxGlade: FrameTerminal.<event_handler>
        self.disconnect()
        serial_dialog = SerialDialog(self.outputwin, self, -1, "", serial = self.serial)
        status = serial_dialog.ShowModal()
        serial_dialog.Destroy()
        #self.connect()

    def onDisplaySettings(self, event): # wxGlade: FrameTerminal.<event_handler>
        serial_dialog = DisplayDialog(self.outputwin, self, -1, "", parent = self)
        serial_dialog.ShowModal()
        serial_dialog.Destroy()
        
    def onSerialRead(self, event):
        global outputCnt
        text = event.data

	if text != "\x0d" and text != "\x0a":
		self.inputdata += text
	
	if (text == "\x0d" or text == "\x0a") and len(self.inputdata) > 0:
		tmplist = []
		tmplist.append("127.0.0.2")
		tmplist.append(20)
		self.outputwin.packets.append([tmplist,self.inputdata])
		self.inputdata = ""


        if self.settings.unprintable:
            for i in text:
                outputCnt+=1
                if outputCnt%OUTPUT_PERLINE == 0:
                    self.printt('\n')
                self.printt(repr(i)[1:-1])
        else:
            for i in text:
                if i == '\b':
                    beg = self.text_ctrl_output.GetLastPosition()
                    end = beg - 1
                    self.text_ctrl_output.Remove(beg, end)
                else: self.printt(i)
        
    def onClose(self, event):
        if self.comThread is not None:
            self.comThread.stopRun()
            self.comThread.join()
            self.serial.close()
         #we must ensure the file was closed before exit.
        if self.f is not None: self.f.close()
        f = open('serial_init.txt', 'w')
        writeInitFile(f, self.serial, self.settings)
        f.close()
	self.outputwin.serial_capture = True
	self.outputwin.process_input_data()

	self.outputwin.mb.Enable(self.outputwin.ID_Start_Capture, True)
	self.outputwin.mb.Enable(self.outputwin.ID_Configure_Proxy, True)
	self.outputwin.mb.Enable(self.outputwin.ID_Open_Session, True)
	self.outputwin.mb.Enable(self.outputwin.ID_Save_Session, True)
	self.outputwin.mb.Enable(self.outputwin.ID_Configure_Logfile, True)
	self.outputwin.mb.Enable(self.outputwin.ID_Configure_Email, True)
	self.outputwin.mb.Enable(self.outputwin.ID_Import_PCAP, True)
	self.outputwin.mb.Enable(self.outputwin.ID_Start_Serial_Capture, True)
	self.outputwin.mb.Enable(self.outputwin.ID_Import_USB, True)

	self.outputwin.mb.Enable(self.outputwin.ID_Configure_VMware, True)
	self.outputwin.mb.Enable(self.outputwin.ID_Network_Fuzzer, True)
	self.outputwin.mb.Enable(self.outputwin.ID_File_Fuzzer, True)
	self.outputwin.mb.Enable(self.outputwin.ID_USB_Fuzzer, True)
	self.outputwin.mb.Enable(self.outputwin.ID_Serial_Fuzzer, True)
	self.outputwin.mb.Enable(self.outputwin.ID_Import_File, True)

	self.outputwin.tb.EnableTool(self.outputwin.ID_toolProxyStart, True)
	self.outputwin.tb.EnableTool(self.outputwin.ID_toolConfigure, True)
	self.outputwin.tb.EnableTool(self.outputwin.ID_toolOpenFile, True)
	self.outputwin.tb.EnableTool(self.outputwin.ID_toolSaveFile, True)
	self.outputwin.tb.EnableTool(self.outputwin.ID_toolFindNext, True)

        self.Destroy()
        
    def onChar(self, event):
        char = event.GetKeyCode()
        if char == 19:               #Ctrl+S connect to serial port
            if self.light == -2:
                self.connect()
                self.light = -1
            return
        elif char == 4:
            if self.light == -1:
                self.disconnect()  #Ctrl+D disconnect to the serial port
                self.light = -2
            return
        else:
            if self.serial.isOpen() is False:
                self.printTitle('You should connect to the serial port first~')
                return
            if chr(char) == '\r':    #'\r' is when the return key is pressed.
		
		self.linebuffer += chr(char)
		tmplist = []
		tmplist.append("127.0.0.1")
		tmplist.append(10)
		self.outputwin.packets.append([tmplist,self.linebuffer])
		self.linebuffer = ""
		#print self.outputwin.packets

                if self.settings.newline == CR:
                    self.serial.write('\r')
                elif self.settings.newline == LF:
                    self.serial.write('\n')
                elif self.settings.newline == CRLF:
                    self.serial.write('\r\n')
                if self.settings.echo == True:
                    self.printt('\n')
            else:
                self.serial.write(chr(char))
		self.linebuffer += chr(char)
		self.currentchar = chr(char)
                if self.settings.echo == True:
                    if chr(char) == '\b':
                        beg = self.text_ctrl_output.GetLastPosition()
                        end = beg - 1
                        self.text_ctrl_output.Remove(beg, end)
                    else:
                        self.printt(chr(char))
# end of class FrameTerminal


if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame_terminal = FrameTerminal(None, -1, "")
    app.SetTopWindow(frame_terminal)
    frame_terminal.Show()
    app.MainLoop()
