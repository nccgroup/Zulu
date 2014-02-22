
# Zulu - the interactive fuzzer
#
# Release History:
#
# 14 February 2014 - v1.21 - First public release

#!/usr/bin/python

import wx
import serial
import ctypes
import shutil 
import sys
import string
import time
import win32api
import SendKeys
import random
import subprocess
import dpkt
import os
from socket import *
from winappdbg import *
from threading import Thread
import smtplib 
from email.mime.multipart import MIMEMultipart 
from email.mime.text import MIMEText 
import wx.lib.agw.advancedsplash as AS
import custom

sys.path.append("./serial")

import easyshell

SHOW_BAUDRATE   = 1<<0
SHOW_FORMAT     = 1<<1
SHOW_FLOW       = 1<<2
SHOW_TIMEOUT    = 1<<3
SHOW_ALL = SHOW_BAUDRATE|SHOW_FORMAT|SHOW_FLOW|SHOW_TIMEOUT

wildcard = "All files (*.*)|*.*"

TBFLAGS = ( wx.TB_HORIZONTAL
            | wx.NO_BORDER
            | wx.TB_FLAT
            #| wx.TB_TEXT
            #| wx.TB_HORZ_LAYOUT
            )

USE_GENERIC = 0

if USE_GENERIC:
    from wx.lib.stattext import GenStaticText as StaticText
else:
    StaticText = wx.StaticText
	
#--- Classes ------------------------------------------------------------------------------------------------------------------------------

class SerialConfigDialog(wx.Dialog):
    """Serial Port confiuration dialog, to be used with pyserial 2.0+
       When instantiating a class of this dialog, then the "serial" keyword
       argument is mandatory. It is a reference to a serial.Serial instance.
       the optional "show" keyword argument can be used to show/hide different
       settings. The default is SHOW_ALL which coresponds to 
       SHOW_BAUDRATE|SHOW_FORMAT|SHOW_FLOW|SHOW_TIMEOUT. All constants can be
       found in ths module (not the class)."""
    
    def __init__(self, output_window, *args, **kwds):
        #grab the serial keyword and remove it from the dict
        self.serial = kwds['serial']
        del kwds['serial']
        self.show = SHOW_ALL
	self.outputwin = output_window

	self.serial.timeout = 0.3

        if kwds.has_key('show'):
            self.show = kwds['show']
            del kwds['show']
        # begin wxGlade: SerialConfigDialog.__init__
        # end wxGlade
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE
        wx.Dialog.__init__(self, *args, **kwds)
        self.label_2 = wx.StaticText(self, -1, "Port")
        self.combo_box_port = wx.ComboBox(self, -1, choices=["dummy1", "dummy2", "dummy3", "dummy4", "dummy5"], style=wx.CB_DROPDOWN)
        if self.show & SHOW_BAUDRATE:
            self.label_1 = wx.StaticText(self, -1, "Baudrate")
            self.choice_baudrate = wx.Choice(self, -1, choices=["choice 1"])
        if self.show & SHOW_FORMAT:
            self.label_3 = wx.StaticText(self, -1, "Data Bits")
            self.choice_databits = wx.Choice(self, -1, choices=["choice 1"])
            self.label_4 = wx.StaticText(self, -1, "Stop Bits")
            self.choice_stopbits = wx.Choice(self, -1, choices=["choice 1"])
            self.label_5 = wx.StaticText(self, -1, "Parity")
            self.choice_parity = wx.Choice(self, -1, choices=["choice 1"])
        if self.show & SHOW_TIMEOUT:
            self.checkbox_timeout = wx.CheckBox(self, -1, "Target IP address")
            self.text_ctrl_timeout = wx.TextCtrl(self, -1, self.outputwin.serial_ip_address)

            self.label_6 = wx.StaticText(self, -1, "")
        if self.show & SHOW_FLOW:
            self.checkbox_rtscts = wx.CheckBox(self, -1, "RTS/CTS")
            self.checkbox_xonxoff = wx.CheckBox(self, -1, "Xon/Xoff")
        self.button_ok = wx.Button(self, -1, "OK")
        self.button_cancel = wx.Button(self, -1, "Cancel")

        self.__set_properties()
        self.__do_layout()
        #fill in ports and select current setting
        index = 0
        self.combo_box_port.Clear()
        for n in range(20):
            portname = serial.device(n)
            self.combo_box_port.Append(portname)
            if self.serial.portstr == portname:
                index = n
        if self.serial.portstr is not None:
            self.combo_box_port.SetValue(str(self.serial.portstr))
        else:
            self.combo_box_port.SetSelection(index)
        if self.show & SHOW_BAUDRATE:
            #fill in badrates and select current setting
            self.choice_baudrate.Clear()
            for n, baudrate in enumerate(self.serial.BAUDRATES):
                self.choice_baudrate.Append(str(baudrate))
                if self.serial.baudrate == baudrate:
                    index = n
            self.choice_baudrate.SetSelection(index)
        if self.show & SHOW_FORMAT:
            #fill in databits and select current setting
            self.choice_databits.Clear()
            for n, bytesize in enumerate(self.serial.BYTESIZES):
                self.choice_databits.Append(str(bytesize))
                if self.serial.bytesize == bytesize:
                    index = n
            self.choice_databits.SetSelection(index)
            #fill in stopbits and select current setting
            self.choice_stopbits.Clear()
            for n, stopbits in enumerate(self.serial.STOPBITS):
                self.choice_stopbits.Append(str(stopbits))
                if self.serial.stopbits == stopbits:
                    index = n
            self.choice_stopbits.SetSelection(index)
            #fill in parities and select current setting
            self.choice_parity.Clear()
            for n, parity in enumerate(self.serial.PARITIES):
                self.choice_parity.Append(str(serial.PARITY_NAMES[parity]))
                if self.serial.parity == parity:
                    index = n
            self.choice_parity.SetSelection(index)
        if self.show & SHOW_TIMEOUT:
            #set the timeout mode and value
            if self.serial.timeout is None:
                self.checkbox_timeout.SetValue(False)
                self.text_ctrl_timeout.Enable(False)
            else:
                self.checkbox_timeout.SetValue(True)
                self.text_ctrl_timeout.Enable(True)
                self.text_ctrl_timeout.SetValue(self.outputwin.serial_ip_address)
        if self.show & SHOW_FLOW:
            #set the rtscts mode
            self.checkbox_rtscts.SetValue(self.serial.rtscts)
            #set the rtscts mode
            self.checkbox_xonxoff.SetValue(self.serial.xonxoff)
        #attach the event handlers
        self.__attach_events()

    def __set_properties(self):
        # begin wxGlade: SerialConfigDialog.__set_properties
        # end wxGlade
        self.SetTitle("Serial fuzzer configuration")
        if self.show & SHOW_TIMEOUT:
            self.text_ctrl_timeout.Enable(0)
        self.button_ok.SetDefault()

    def __do_layout(self):
        # begin wxGlade: SerialConfigDialog.__do_layout
        # end wxGlade
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_basics = wx.StaticBoxSizer(wx.StaticBox(self, -1, "Basics"), wx.VERTICAL)
        sizer_5 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_5.Add(self.label_2, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 4)
        sizer_5.Add(self.combo_box_port, 1, 0, 0)
        sizer_basics.Add(sizer_5, 0, wx.RIGHT|wx.EXPAND, 0)
        if self.show & SHOW_BAUDRATE:
            sizer_baudrate = wx.BoxSizer(wx.HORIZONTAL)
            sizer_baudrate.Add(self.label_1, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 4)
            sizer_baudrate.Add(self.choice_baudrate, 1, wx.ALIGN_RIGHT, 0)
            sizer_basics.Add(sizer_baudrate, 0, wx.EXPAND, 0)
        sizer_2.Add(sizer_basics, 0, wx.EXPAND, 0)
        if self.show & SHOW_FORMAT:
            sizer_8 = wx.BoxSizer(wx.HORIZONTAL)
            sizer_7 = wx.BoxSizer(wx.HORIZONTAL)
            sizer_6 = wx.BoxSizer(wx.HORIZONTAL)
            sizer_format = wx.StaticBoxSizer(wx.StaticBox(self, -1, "Data Format"), wx.VERTICAL)
            sizer_6.Add(self.label_3, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 4)
            sizer_6.Add(self.choice_databits, 1, wx.ALIGN_RIGHT, 0)
            sizer_format.Add(sizer_6, 0, wx.EXPAND, 0)
            sizer_7.Add(self.label_4, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 4)
            sizer_7.Add(self.choice_stopbits, 1, wx.ALIGN_RIGHT, 0)
            sizer_format.Add(sizer_7, 0, wx.EXPAND, 0)
            sizer_8.Add(self.label_5, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 4)
            sizer_8.Add(self.choice_parity, 1, wx.ALIGN_RIGHT, 0)
            sizer_format.Add(sizer_8, 0, wx.EXPAND, 0)
            sizer_2.Add(sizer_format, 0, wx.EXPAND, 0)
        if self.show & SHOW_TIMEOUT:
            sizer_timeout = wx.StaticBoxSizer(wx.StaticBox(self, -1, "Instrumentation"), wx.HORIZONTAL)
            sizer_timeout.Add(self.checkbox_timeout, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 4)
            sizer_timeout.Add(self.text_ctrl_timeout, 0, 0, 0)
            sizer_timeout.Add(self.label_6, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 4)
            sizer_2.Add(sizer_timeout, 0, 0, 0)
        if self.show & SHOW_FLOW:
            sizer_flow = wx.StaticBoxSizer(wx.StaticBox(self, -1, "Flow Control"), wx.HORIZONTAL)
            sizer_flow.Add(self.checkbox_rtscts, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 4)
            sizer_flow.Add(self.checkbox_xonxoff, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 4)
            sizer_flow.Add((10,10), 1, wx.EXPAND, 0)
            sizer_2.Add(sizer_flow, 0, wx.EXPAND, 0)
        sizer_3.Add(self.button_ok, 0, 0, 0)
        sizer_3.Add(self.button_cancel, 0, 0, 0)
        sizer_2.Add(sizer_3, 0, wx.ALL|wx.ALIGN_RIGHT, 4)
        self.SetAutoLayout(1)
        self.SetSizer(sizer_2)
        sizer_2.Fit(self)
        sizer_2.SetSizeHints(self)
        self.Layout()

    def __attach_events(self):
        wx.EVT_BUTTON(self, self.button_ok.GetId(), self.OnOK)
        wx.EVT_BUTTON(self, self.button_cancel.GetId(), self.OnCancel)
        if self.show & SHOW_TIMEOUT:
            wx.EVT_CHECKBOX(self, self.checkbox_timeout.GetId(), self.OnTimeout)

    def OnOK(self, events):
        success = True
        self.serial.port     = str(self.combo_box_port.GetValue())
        if self.show & SHOW_BAUDRATE:
            self.serial.baudrate = self.serial.BAUDRATES[self.choice_baudrate.GetSelection()]
        if self.show & SHOW_FORMAT:
            self.serial.bytesize = self.serial.BYTESIZES[self.choice_databits.GetSelection()]
            self.serial.stopbits = self.serial.STOPBITS[self.choice_stopbits.GetSelection()]
            self.serial.parity   = self.serial.PARITIES[self.choice_parity.GetSelection()]
        if self.show & SHOW_FLOW:
            self.serial.rtscts   = self.checkbox_rtscts.GetValue()
            self.serial.xonxoff  = self.checkbox_xonxoff.GetValue()
        if self.show & SHOW_TIMEOUT:
            if self.checkbox_timeout.GetValue():
                try:
                    self.outputwin.serial_ip_address = self.text_ctrl_timeout.GetValue()
                except ValueError:
                    dlg = wx.MessageDialog(self, 'IP address is invalid',
                                                'Value Error', wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
                    success = False
            else:
                self.serial.timeout = None
        if success:
            self.EndModal(wx.ID_OK)
	
    def OnCancel(self, events):
        self.EndModal(wx.ID_CANCEL)

    def OnTimeout(self, events):
        if self.checkbox_timeout.GetValue():
            self.text_ctrl_timeout.Enable(True)
        else:
            self.text_ctrl_timeout.Enable(False)

#------------------------------------------------------------------------------------------------------------------------------------------

class UDPProxy(Thread):
    """ used to proxy single udp connection 
    """
    BUFFER_SIZE = 4096 
    def __init__(self, output_window, listening_address, forward_address):
        	Thread.__init__(self)
        	self.bind = listening_address
        	self.target = forward_address
		self.output_win = output_window

    def run(self):

        target = socket(AF_INET, SOCK_DGRAM)

        try:
		target.connect(self.target)
	except:
		wx.MessageBox("Could not connect to target", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self.output_win)
		self.output_win.StopCapture(1)
            	return

        s = socket(AF_INET, SOCK_DGRAM)

        try:
            	s.bind(self.bind)
        except error, err:
		wx.MessageBox("Could not bind to port", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self.output_win)
		self.output_win.StopCapture(1)
            	return

        while (self.output_win.capturing == True):
            	(datagram,addr) = s.recvfrom(self.BUFFER_SIZE)
            	if not datagram:
                	break
            	length = len(datagram)
            	sent = target.send(datagram)

		self.output_win.packets.append([addr,datagram])
		text = "Status: Captured #%d packets" % len (self.output_win.packets)  
		self.output_win.statusbar.SetStatusText(text, 2)

            	if length != sent:
                	print 'cannot send to %r, %r !+ %r' % (self.s, length, sent)
            	datagram = target.recv(self.BUFFER_SIZE)
            	if not datagram:
                	break
            	length = len(datagram)
            	sent = s.sendto(datagram,addr)

		self.output_win.packets.append([target.getpeername(),datagram])
		text = "Status: Captured #%d packets" % len (self.output_win.packets)  
		self.output_win.statusbar.SetStatusText(text, 2)

            	if length != sent:
                	print 'cannot send to %r, %r !+ %r' % (self.s, length, sent)
        s.close()

#------------------------------------------------------------------------------------------------------------------------------------------

class PipeThread( Thread ):
    pipes = []
    def __init__( self, output_window, source, sink ):
        Thread.__init__( self )
	self.output_win = output_window
        self.source = source
        self.sink = sink
        
        PipeThread.pipes.append(self)

    def run(self):
	
        while (self.output_win.capturing == True):
            try:
                data = self.source.recv( 1500 )
                if not data: break
                self.sink.send( data )

		#print self.source.getpeername()
		#print repr(data)
		#print

		self.output_win.packets.append([self.source.getpeername(),data])
		text = "Status: Captured #%d packets" % len (self.output_win.packets)  
		self.output_win.statusbar.SetStatusText(text, 2)

            except:
                break

	self.output_win.sock.close()

        PipeThread.pipes.remove( self )

#------------------------------------------------------------------------------------------------------------------------------------------

class Pinhole(Thread):
    def __init__( self, output_window, port, newhost, newport ):
	Thread.__init__( self )

	self.output_win = output_window
	
        self.newhost = newhost
        self.newport = newport
        self.sock = socket( AF_INET, SOCK_STREAM )

	self.output_win.sock = self.sock
	try:
        	self.sock.bind(( '', port ))
	except:
		wx.MessageBox("Could not bind to local port", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self.output_win)
		self.output_win.StopCapture(1)
		return

        self.sock.listen(5)
   
    def run( self ):

        while (self.output_win.capturing == True):
            	newsock, address = self.sock.accept()
            	fwd = socket( AF_INET, SOCK_STREAM )
		try:
            		fwd.connect(( self.newhost, self.newport ))
		except:
			wx.MessageBox("Could not connect to target", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self.output_win)
			self.output_win.StopCapture(1)
			return

            	PipeThread( self.output_win, newsock, fwd ).start()
            	PipeThread( self.output_win, fwd, newsock ).start()

#------------------------------------------------------------------------------------------------------------------------------------------

class TestSearchCtrl(wx.SearchCtrl):
    maxSearches = 5
    
    def __init__(self, parent, id=-1, value="",
                 pos=wx.DefaultPosition, size=wx.DefaultSize, style=0,
                 doSearch=None):
        style |= wx.TE_PROCESS_ENTER
        wx.SearchCtrl.__init__(self, parent, id, value, pos, size, style)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnTextEntered)
        self.Bind(wx.EVT_MENU_RANGE, self.OnMenuItem, id=1, id2=self.maxSearches)
        self.doSearch = doSearch
        self.searches = []

    def OnTextEntered(self, evt):
        text = self.GetValue()
        if self.doSearch(text):
            self.searches.append(text)
            if len(self.searches) > self.maxSearches:
                del self.searches[0]
            self.SetMenu(self.MakeMenu())            
        self.SetValue("")

    def OnMenuItem(self, evt):
        text = self.searches[evt.GetId()-1]
        self.doSearch(text)
        
    def MakeMenu(self):
        menu = wx.Menu()
        item = menu.Append(-1, "Recent Searches")
        item.Enable(False)
        for idx, txt in enumerate(self.searches):
            menu.Append(1+idx, txt)
        return menu

#------------------------------------------------------------------------------------------------------------------------------------------
#--- Main panel ---------------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------------

class MainPanel(wx.Panel):
    def __init__(self, parent, frame=None):
        wx.Panel.__init__(
            self, parent, -1,
            style=wx.TAB_TRAVERSAL|wx.CLIP_CHILDREN|wx.NO_FULL_REPAINT_ON_RESIZE
            )

        self.parent = parent
        self.frame = frame
                    
        self.SetBackgroundColour("White")
        self.Refresh()

#------------------------------------------------------------------------------------------------------------------------------------------
# Global variables

	self.capturing = False
	self.capture_data = False
	self.fuzzing = False
	self.port = 1234
	self.targethost = "127.0.0.1"
	self.targetport = 445
	self.max_packets = 200
	self.packets = []
	self.packets_to_send = []
	self.fuzzpoints = []
	self.packets_captured = 0
	self.current_packet_number = 0
	self.total_unique_packets = 0
	self.tc_packetlist_displaybuffer = ""
	self.fuzzcases = 0
	self.fuzzer_testcases = [] 
	self.all_fuzzer_testcases = []
	self.logfilepath = "../logs/Zulu_logfile_"
	self.session_changed = False
	self.sessionfile = ""
	self.last_packet_data_list = []
	self.workingdir = os.getcwd()
	self.PoC_filename = ""
	self.DoubleOffset_list = ["0","+1"]
	self.QuadOffset_list = ["0","+1","+2","+3"]
	self.DoubleOffset = 0
	self.QuadOffset = 0
	self.FindNext = False
	self.current_search_location = 0
	self.search_found = 0
	self.searchtermfound = ""
	self.udp = False
	self.Showalert = False
	self.receivepacketfirst = False
	self.custom_script = False
	self.all_bytes_selected = []
	self.wiresharkpath = ""
	self.wireshark_enabled = False
	self.pcappath = ""
	self.fuzz_delay = 0
	self.fuzz_retries = 2
	self.fuzzing_paused = False
	self.fuzzer = "Network"
	self.capture_type = "Network"
	self.latest_PoC = ""
	self.PacketNumberToRemove = -1
	self.FuzzPointToRemove = 0
	self.Receive_timeout = 0.1
	self.buffer_overflow = False
	self.formatstring = False
	self.singlebyte = False
	self.doublebyte = False
	self.quadbyte = False
	self.nullcase = False
	self.unixcase = False
	self.windowscase = False
	self.xmlcase = False
	self.userdefined = False
	self.controlcase = False
	self.extendedcase = False
	self.bitbyte = False
	self.bitword = False
	self.bitlong = False
	self.bitbyteinv = False
	self.bitwordinv = False
	self.bitlonginv = False
	self.selection_start = 0
	self.selection_end = 0
	self.tc_captured_has_focus = False
	self.tc_captured_asc_has_focus = False
	self.LengthEndian = 0
	self.length_start = 0
	self.length_end = 0
	self.LengthFields = []
	self.testcaseselected = 0

######## VMware settings ################################################

	self.VMware_OS_username = "administrator"
	self.VMware_OS_password = "password"
	self.VMware_OS_process_name = "c:\\windows\\system32\\notepad.exe"
	self.VMware_VM_path = ""
	self.VMware_vmrun_path = ""
	self.VMware_product = "Workstation"
	self.VMwareMode = "Process"
	self.VMwareEnabled = False
	self.VMware_timeout = 1

#########################################################################

######## Email settings #################################################

	self.smtp_server = "smtp.gmail.com:587"
	self.smtp_login = "username@googlemail.com"
	self.smtp_password = "*************"
	self.smtp_from = "username@googlemail.com"
	self.smtp_to = "username@ngssecure.com"
	self.tls = True

#########################################################################

######## File fuzzer settings ###########################################

	self.process_to_fuzz = "C:\\Program Files\\Windows Media Player\\wmplayer.exe"
	self.process_command_args = ""
	self.process_run_time = 5.0
	self.process_termiate_type = "Kill"
	self.file_extension = ""
	self.file_counter = 0
	self.current_file_data = ""

#########################################################################

######## USB fuzzer settings ############################################

	self.GraphicUSB_path = "C:\\Program Files (x86)\\MQP Electronics\\GraphicUSB\\GraphicUsb.exe"
	self.usb_target_ip_address = "10.33.33.117"
	self.usb_temp_gen_script = ""

#########################################################################

######## Serial fuzzer settings #########################################

	self.serial_ip_address = "127.0.0.1"

#########################################################################

#------------------------------------------------------------------------------------------------------------------------------------------
# Create IDs   
     
	self.ID_About = wx.NewId()
	self.ID_Start_Capture = wx.NewId()
	self.ID_Stop_Capture = wx.NewId()
	self.ID_Start_Fuzzing = wx.NewId()
	self.ID_Pause_Fuzzing = wx.NewId()
	self.ID_Stop_Fuzzing = wx.NewId()
	self.ID_SendUnchanged = wx.NewId()
	self.ID_AddFuzzPoint = wx.NewId()
	self.ID_ClearAllFuzzPoints = wx.NewId()
	self.ID_Configure_Proxy = wx.NewId()
	self.ID_toolConfigure = wx.NewId()
	self.ID_toolOpenFile = wx.NewId()
	self.ID_toolSaveFile = wx.NewId()
	self.ID_toolFindNext = wx.NewId()
	self.ID_toolProxyLabel = wx.NewId()
	self.ID_toolProxyStart = wx.NewId()
	self.ID_toolProxyStop = wx.NewId()
	self.ID_toolFuzzerLabel = wx.NewId()
	self.ID_toolFuzzerStart = wx.NewId()
	self.ID_toolFuzzerStop = wx.NewId()
	self.ID_Configure_Logfile = wx.NewId()
	self.ID_toolFuzzerPause = wx.NewId()
	self.ID_Open_Session = wx.NewId()
	self.ID_Save_Session = wx.NewId()
	self.ID_AddAllBytes = wx.NewId()
	self.ID_AddAllDoubleBytes = wx.NewId()
	self.ID_AddAllQuadBytes = wx.NewId()
	self.ID_DoubleOffset = wx.NewId()
	self.ID_QuadOffset = wx.NewId()
	self.ID_Configure_Email = wx.NewId()
	self.ID_Import_PCAP = wx.NewId()
	self.ID_Configure_VMware = wx.NewId()
	self.ID_Network_Fuzzer = wx.NewId()
	self.ID_File_Fuzzer = wx.NewId()
	self.ID_Import_File = wx.NewId()
	self.ID_toolExploit = wx.NewId()
	self.ID_AddFuzzPointRange = wx.NewId()
	self.ID_RemoveFuzzPoint = wx.NewId()
	self.ID_Import_USB = wx.NewId()
	self.ID_USB_Fuzzer = wx.NewId()
	self.ID_PacketTest = wx.NewId()
	self.ID_Start_Serial_Capture = wx.NewId()
	self.ID_Stop_Serial_Capture = wx.NewId()
	self.ID_Serial_Fuzzer = wx.NewId()
	self.ID_Save_As_Session = wx.NewId()

#------------------------------------------------------------------------------------------------------------------------------------------
# Splash screen

	pn = os.path.normpath(os.path.join(".", "../images/splash.png"))
	bitmap = wx.Bitmap(pn, wx.BITMAP_TYPE_PNG)
	shadow = wx.WHITE
	frame = AS.AdvancedSplash(self, bitmap=bitmap, timeout=4000)

#------------------------------------------------------------------------------------------------------------------------------------------
# Create menu
        
	self.mb = wx.MenuBar()

	file_menu = wx.Menu()

	file_menu.Append(self.ID_Open_Session, "&Open...") 
	file_menu.Append(self.ID_Save_Session, "&Save") 
	file_menu.Append(self.ID_Save_As_Session, "&Save As...") 
	file_menu.Append(self.ID_Configure_Logfile, "&Configure Log File") 
	file_menu.Append(self.ID_About, "&About")   
	file_menu.AppendSeparator()
	file_menu.Append(wx.ID_EXIT, "Exit")

	self.mb.Append(file_menu, "File")

	configuration_menu = wx.Menu() 

	configuration_menu.Append(self.ID_Configure_Proxy, "&Proxy Settings") 
	configuration_menu.Append(self.ID_Configure_Email, "&Email Notification Settings")
	configuration_menu.Append(self.ID_Configure_VMware, "&VMware Settings")

	self.mb.Append(configuration_menu, "Configuration")

	capture_menu = wx.Menu() 

	capture_menu.Append(self.ID_Start_Capture, "&Start Network Proxy")
	capture_menu.Append(self.ID_Stop_Capture, "&Stop Network Proxy") 
	capture_menu.Append(self.ID_Import_PCAP, "&Import PCAP") 
	capture_menu.Append(self.ID_Import_File, "&Import File")
	capture_menu.Append(self.ID_Import_USB, "&Import USB Generator Script")
	capture_menu.Append(self.ID_Start_Serial_Capture, "&Serial Data Capture")

	self.mb.Append(capture_menu, "Input Method")

	output_menu = wx.Menu() 

	output_menu.Append(self.ID_Network_Fuzzer, "&Network Fuzzer")
	output_menu.Append(self.ID_File_Fuzzer, "&File Fuzzer") 
	output_menu.Append(self.ID_USB_Fuzzer, "&USB Fuzzer") 
	output_menu.Append(self.ID_Serial_Fuzzer, "&Serial Fuzzer") 

	self.mb.Append(output_menu, "Output Method")

	fuzzing_menu = wx.Menu() 

	fuzzing_menu.Append(self.ID_Start_Fuzzing, "&Start Fuzzing")
	fuzzing_menu.Append(self.ID_Pause_Fuzzing, "&Pause Fuzzing")
	fuzzing_menu.Append(self.ID_Stop_Fuzzing, "&Stop Fuzzing")

	self.mb.Append(fuzzing_menu, "Fuzzing")

	self.parent.SetMenuBar(self.mb)

#------------------------------------------------------------------------------------------------------------------------------------------
# Create toolbar

	self.tb = self.parent.CreateToolBar( TBFLAGS )
	
	self.tb.AddSimpleTool(self.ID_toolConfigure, 
			 wx.Image('../images/configure.png',
			 wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 
			 'Configure proxy settings')	

	self.tb.AddSimpleTool(self.ID_toolOpenFile, 
			 wx.Image('../images/open.png',
			 wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 
			 'Open session file')	

	self.tb.AddSimpleTool(self.ID_toolSaveFile, 
			 wx.Image('../images/save.png',
			 wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 
			 'Save session file')
	
	self.tb.AddSeparator()

	self.tb.AddControl(wx.StaticText(self.tb, 
		      self.ID_toolProxyLabel, 
		      label =' Proxy:', 
		      name = 'lblProxy',
		      size = (40,-1), 
		      style = 0)) 

	self.tb.AddSimpleTool(self.ID_toolProxyStart, 
			 wx.Image('../images/play.png',
			 wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 
			 'Start network proxy')	

	self.tb.AddSimpleTool(self.ID_toolProxyStop, 
			 wx.Image('../images/stop.png',
			 wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 
			 'Stop network proxy')	

	self.tb.AddSeparator()

	self.tb.AddControl(wx.StaticText(self.tb, 
		      self.ID_toolFuzzerLabel, 
		      label =' Fuzzer:', 
		      name = 'lblProxy',
		      size = (40,-1), 
		      style = 0)) 

	self.tb.AddSimpleTool(self.ID_toolFuzzerStart, 
			 wx.Image('../images/play.png',
			 wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 
			 'Start fuzzer')

	self.tb.AddSimpleTool(self.ID_toolFuzzerPause, 
			 wx.Image('../images/pause.png',
			 wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 
			 'Pause fuzzer')	

	self.tb.AddSimpleTool(self.ID_toolFuzzerStop, 
			 wx.Image('../images/stop.png',
			 wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 
			 'Stop fuzzer')

	self.tb.AddSimpleTool(self.ID_toolExploit, 
			 wx.Image('../images/exploit.png',
			 wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 
			 'Launch latest PoC')

	self.tb.AddSeparator()

	self.search = TestSearchCtrl(self.tb, size=(150,-1), doSearch=self.DoSearch)
        self.tb.AddControl(self.search)

	self.tb.AddSimpleTool(self.ID_toolFindNext, 
			 wx.Image('../images/forward.png',
			 wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 
	 		 'Find next')
	
	self.tb.Realize()

#------------------------------------------------------------------------------------------------------------------------------------------
# Create status bar

	self.statusbar = self.parent.CreateStatusBar(4, wx.ST_SIZEGRIP)
	self.statusbar.SetStatusWidths([-1,-1,-1,-1])
	self.statusbar.SetStatusText("", 0)
	self.statusbar.SetStatusText("", 1) 
	self.statusbar.SetStatusText("", 2)
	self.statusbar.SetStatusText("", 3)
	self.statusbar.SetStatusText("Status: Idle", 3)
	self.statusbar.SetStatusText("Fuzzer selected: Network Fuzzer", 1)
  
#------------------------------------------------------------------------------------------------------------------------------------------
# Text controls and static text 

	text = wx.StaticText(self, -1, "Input data:",pos=(10,10))
	text.SetBackgroundColour('White')
	font = wx.Font(9, wx.SWISS, wx.NORMAL, wx.NORMAL)
	text.SetFont(font)

	self.tc_packetlist = wx.TextCtrl(self, -1,"",size=(290, 277), pos=(10, 30), style=wx.TE_MULTILINE|wx.TE_RICH2|wx.TE_READONLY|wx.TE_NOHIDESEL)
	self.tc_packetlist.SetBackgroundColour("WHITE")
	f = wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL)
	self.tc_packetlist.SetDefaultStyle(wx.TextAttr((0,0,80), wx.NullColour, f))
	self.tc_packetlist.Bind(wx.EVT_CONTEXT_MENU, self.NullFunction) 

	text = wx.StaticText(self, -1, "Mutation points:",pos=(312,10))
	text.SetBackgroundColour('White')
	font = wx.Font(9, wx.SWISS, wx.NORMAL, wx.NORMAL)
	text.SetFont(font)

	self.tc_fuzzpoints = wx.TextCtrl(self, -1,"",size=(245, 230), pos=(312, 30), style=wx.TE_MULTILINE|wx.TE_RICH2|wx.TE_READONLY)
	self.tc_fuzzpoints.SetBackgroundColour("WHITE")
	f = wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL)
	self.tc_fuzzpoints.SetDefaultStyle(wx.TextAttr((0,0,80), wx.NullColour, f))
	self.tc_fuzzpoints.Bind(wx.EVT_CONTEXT_MENU, self.NullFunction) 

	text = wx.StaticText(self, -1, "Input data bytes:",pos=(10,310))
	text.SetBackgroundColour('White')
	font = wx.Font(9, wx.SWISS, wx.NORMAL, wx.NORMAL)
	text.SetFont(font)

	self.tc_captured = wx.TextCtrl(self, -1,"",size=(790, 295), pos=(10, 330), style=wx.TE_MULTILINE|wx.TE_RICH2|wx.TE_READONLY|wx.TE_NOHIDESEL)	
	self.tc_captured.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
	self.tc_captured.SetBackgroundColour("WHITE")
	f = wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL)
	self.tc_captured.SetDefaultStyle(wx.TextAttr((0,0,80), wx.NullColour, f))

	self.tc_captured_asc = wx.TextCtrl(self, -1,"",size=(300, 295), pos=(812, 330), style=wx.TE_MULTILINE|wx.TE_RICH2|wx.TE_READONLY|wx.TE_NOHIDESEL)
	self.tc_captured.SetBackgroundColour("WHITE")
	f = wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL)
	self.tc_captured_asc.SetDefaultStyle(wx.TextAttr((0,0,80), wx.NullColour, f))
	self.tc_captured_asc.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu) 

	text = wx.StaticText(self, -1, "Status:",pos=(10,630))
	text.SetBackgroundColour('White')
	font = wx.Font(9, wx.SWISS, wx.NORMAL, wx.NORMAL)
	text.SetFont(font)

	self.tc_output = wx.TextCtrl(self, -1,"",size=(1000, 70), pos=(10, 650), style=wx.TE_MULTILINE|wx.TE_RICH2|wx.TE_READONLY)
	self.tc_output.SetBackgroundColour("WHITE")
	f = wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL)
	self.tc_output.SetDefaultStyle(wx.TextAttr((0,0,80), wx.NullColour, f))
	self.tc_output.Bind(wx.EVT_CONTEXT_MENU, self.NullFunction) 

#------------------------------------------------------------------------------------------------------------------------------------------
# Images

	image_file = '../images/zulu_logo.png'
	image = wx.Bitmap(image_file)
	image_size = image.GetSize()
	bm = wx.StaticBitmap(self, wx.ID_ANY, image, size=image_size, pos=(1040,10))
	
	image_file = '../images/alert.png'
	image = wx.Bitmap(image_file)
	image_size = image.GetSize()
	self.bmCrash = wx.StaticBitmap(self, wx.ID_ANY, image, size=image_size, pos=(1045,670))
	self.bmCrash.Hide()

#------------------------------------------------------------------------------------------------------------------------------------------
# Set windows icon
	
 	image = wx.Image('../images/zulu_logo16x16.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap() 
	icon = wx.EmptyIcon() 
	icon.CopyFromBitmap(image) 
	self.parent.SetIcon(icon) 

#------------------------------------------------------------------------------------------------------------------------------------------
# Buttons
  

	self.btn_SendUnchanged = wx.Button(self, self.ID_SendUnchanged, "Send data unmodified", (327, 275))
	self.Bind(wx.EVT_BUTTON, self.AddPacket, self.btn_SendUnchanged)
	self.btn_SendUnchanged.SetSize(self.btn_SendUnchanged.GetBestSize())
	self.btn_SendUnchanged.Enable(False)

	self.btn_PacketTest = wx.Button(self, self.ID_PacketTest, "    Packet data test     ", (327, 300))
	self.Bind(wx.EVT_BUTTON, self.PacketTest, self.btn_PacketTest)
	self.btn_PacketTest.SetSize(self.btn_PacketTest.GetBestSize())
	self.btn_PacketTest.Enable(False)

	self.btn_ClearAllFuzzPoints = wx.Button(self, self.ID_ClearAllFuzzPoints, "Clear all", (466, 275))
	self.Bind(wx.EVT_BUTTON, self.ClearAllFuzzPoints, self.btn_ClearAllFuzzPoints)
	self.btn_ClearAllFuzzPoints.SetSize(self.btn_ClearAllFuzzPoints.GetBestSize())

	self.btn_AddAllBytes = wx.Button(self, self.ID_AddAllBytes, "All bytes", (563, 275))
	self.Bind(wx.EVT_BUTTON, self.AddAllBytes, self.btn_AddAllBytes)
	self.btn_AddAllBytes.SetSize(self.btn_AddAllBytes.GetBestSize())

	self.btn_AddAllDoubleBytes = wx.Button(self, self.ID_AddAllDoubleBytes , "All words", (645, 275))
	self.Bind(wx.EVT_BUTTON, self.AddAllDoubleBytes, self.btn_AddAllDoubleBytes)
	self.btn_AddAllDoubleBytes.SetSize(self.btn_AddAllDoubleBytes.GetBestSize())

	self.btn_AddAllQuadBytes = wx.Button(self, self.ID_AddAllQuadBytes , "All dwords", (725, 275))
	self.Bind(wx.EVT_BUTTON, self.AddAllQuadBytes, self.btn_AddAllQuadBytes)
	self.btn_AddAllQuadBytes.SetSize(self.btn_AddAllQuadBytes.GetBestSize())

#------------------------------------------------------------------------------------------------------------------------------------------
# Combo boxes

	self.cbDoubleOffset = wx.ComboBox(self, self.ID_DoubleOffset, "0", (645, 300), 
                         (76, -1), self.DoubleOffset_list,
                         wx.CB_DROPDOWN
                         )
	self.cbQuadOffset = wx.ComboBox(self, self.ID_DoubleOffset, "0", (725, 300), 
                         (76, -1), self.QuadOffset_list,
                         wx.CB_DROPDOWN
                         )

	text = wx.StaticText(self, -1, "Add offsets:",pos=(570,302))
	text.SetBackgroundColour('White')
	font = wx.Font(9, wx.SWISS, wx.NORMAL, wx.NORMAL)
	text.SetFont(font)

#------------------------------------------------------------------------------------------------------------------------------------------
# Checkboxes

	text = wx.StaticText(self, -1, "Mutators:",pos=(580,10))
	text.SetBackgroundColour('White')
	font = wx.Font(9, wx.SWISS, wx.NORMAL, wx.NORMAL)
	text.SetFont(font)

	self.cb_overflow = wx.CheckBox(self, -1, "Long strings", (580,35))
	self.cb_format = wx.CheckBox(self, -1, "Format strings", (580,55))
	self.cb_single_byte = wx.CheckBox(self, -1, "Single byte brute force", (580,75))
	self.cb_double_byte = wx.CheckBox(self, -1, "Double byte attacks", (580,95))
	self.cb_quad_byte = wx.CheckBox(self, -1, "Quad byte attacks", (580,115))
	self.cb_null = wx.CheckBox(self, -1, "Null representations", (580,135))
	self.cb_commandu = wx.CheckBox(self, -1, "Unix command execution", (580,155))
	self.cb_commandw = wx.CheckBox(self, -1, "Windows command execution", (580,175))
	self.cb_xml = wx.CheckBox(self, -1, "XML attacks", (580,195))
	self.cb_control = wx.CheckBox(self, -1, "ASCII Control chars", (580,215))
	self.cb_extended = wx.CheckBox(self, -1, "Extended ASCII", (580,235))

	self.cb_userdefined = wx.CheckBox(self, -1, "User defined", (812,35))
	self.cb_bitbyte = wx.CheckBox(self, -1, "Bit sweep (byte)", (812,55))
	self.cb_bitword = wx.CheckBox(self, -1, "Bit sweep (double byte)", (812,75))
	self.cb_bitlong = wx.CheckBox(self, -1, "Bit sweep (quad byte)", (812,95))
	self.cb_bitbyteinv = wx.CheckBox(self, -1, "Inverted bit sweep (byte)", (812,115))
	self.cb_bitwordinv = wx.CheckBox(self, -1, "Inverted bit sweep (double byte)", (812,135))
	self.cb_bitlonginv = wx.CheckBox(self, -1, "Inverted bit sweep (quad byte)", (812,155))

	self.cb_zuluscript = wx.CheckBox(self, -1, "Enable ZuluScript (see \"/bin/custom.py\")", (812,195))
	self.cb_wireshark = wx.CheckBox(self, -1, "Enable Wireshark integration", (812,215))
	self.cb_vmware = wx.CheckBox(self, -1, "Enable VMware integration", (812,235))

#------------------------------------------------------------------------------------------------------------------------------------------
# More buttons

	image_file = '../images/open_small.png'
	image = wx.Bitmap(image_file)
	image_size = image.GetSize()

	bmbtn_overflows = wx.BitmapButton(self, -1, image, (670,35), style = wx.NO_BORDER)
	bmbtn_format = wx.BitmapButton(self, -1, image, (680,55), style = wx.NO_BORDER)
	bmbtn_null = wx.BitmapButton(self, -1, image, (700,135), style = wx.NO_BORDER)
	bmbtn_unix = wx.BitmapButton(self, -1, image, (730,155), style = wx.NO_BORDER)
	bmbtn_windows = wx.BitmapButton(self, -1, image, (750,175), style = wx.NO_BORDER)
	bmbtn_xml = wx.BitmapButton(self, -1, image, (660,195), style = wx.NO_BORDER)
	bmbtn_user = wx.BitmapButton(self, -1, image, (900,35), style = wx.NO_BORDER)
	bmbtn_zuluscript = wx.BitmapButton(self, -1, image, (1030,195), style = wx.NO_BORDER)

#------------------------------------------------------------------------------------------------------------------------------------------
# Bindings 

	self.parent.Bind(wx.EVT_MENU, self.About, id=self.ID_About)
	self.parent.Bind(wx.EVT_MENU, self.CloseMe, id=wx.ID_EXIT) 
	self.parent.Bind(wx.EVT_MENU, self.SaveSession, id=self.ID_Save_Session) 
	self.parent.Bind(wx.EVT_MENU, self.SaveAsSession, id=self.ID_Save_As_Session) 
	self.parent.Bind(wx.EVT_MENU, self.SaveSession, id=self.ID_toolSaveFile)
	self.parent.Bind(wx.EVT_MENU, self.OpenSession, id=self.ID_Open_Session) 
	self.parent.Bind(wx.EVT_MENU, self.OpenSession, id=self.ID_toolOpenFile)
	self.parent.Bind(wx.EVT_MENU, self.StartCapture, id=self.ID_Start_Capture)  
	self.parent.Bind(wx.EVT_MENU, self.StartCapture, id=self.ID_toolProxyStart) 
	self.parent.Bind(wx.EVT_MENU, self.StartSerialCapture, id=self.ID_Start_Serial_Capture)  

	self.parent.Bind(wx.EVT_MENU, self.StopCapture, id=self.ID_Stop_Capture) 
	self.parent.Bind(wx.EVT_MENU, self.StopCapture, id=self.ID_toolProxyStop)
	self.parent.Bind(wx.EVT_MENU, self.ImportPCAP, id=self.ID_Import_PCAP)
	self.parent.Bind(wx.EVT_MENU, self.StartFuzzing, id=self.ID_Start_Fuzzing)
	self.parent.Bind(wx.EVT_MENU, self.StartFuzzing, id=self.ID_toolFuzzerStart)
	self.parent.Bind(wx.EVT_MENU, self.PauseFuzzing, id=self.ID_Pause_Fuzzing)
	self.parent.Bind(wx.EVT_MENU, self.PauseFuzzing, id=self.ID_toolFuzzerPause)
	self.parent.Bind(wx.EVT_MENU, self.LaunchPoC, id=self.ID_toolExploit)
	self.parent.Bind(wx.EVT_MENU, self.ImportUSB, id=self.ID_Import_USB)

	self.parent.Bind(wx.EVT_MENU, self.StopFuzzing, id=self.ID_Stop_Fuzzing)
	self.parent.Bind(wx.EVT_MENU, self.StopFuzzing, id=self.ID_toolFuzzerStop)
	self.parent.Bind(wx.EVT_MENU, self.ConfigureConnection, id=self.ID_Configure_Proxy)
	self.parent.Bind(wx.EVT_MENU, self.ConfigureConnection, id=self.ID_toolConfigure)
	self.parent.Bind(wx.EVT_MENU, self.ConfigureLogfile, id=self.ID_Configure_Logfile)
	self.parent.Bind(wx.EVT_MENU, self.FindNextSearch, id=self.ID_toolFindNext)
	self.parent.Bind(wx.EVT_MENU, self.ConfigureSMTP, id=self.ID_Configure_Email)
	self.parent.Bind(wx.EVT_MENU, self.ConfigureVMware, id=self.ID_Configure_VMware)

	self.parent.Bind(wx.EVT_MENU, self.ConfigureNetworkFuzzer, id=self.ID_Network_Fuzzer)
	self.parent.Bind(wx.EVT_MENU, self.ConfigureFileFuzzer, id=self.ID_File_Fuzzer)
	self.parent.Bind(wx.EVT_MENU, self.ConfigureUSBFuzzer, id=self.ID_USB_Fuzzer)
	self.parent.Bind(wx.EVT_MENU, self.ConfigureSerialFuzzer, id=self.ID_Serial_Fuzzer)
	self.parent.Bind(wx.EVT_MENU, self.ImportFile, id=self.ID_Import_File)

	self.parent.Bind(wx.EVT_CHECKBOX, self.TC_BufferOverflow, self.cb_overflow)
	self.parent.Bind(wx.EVT_CHECKBOX, self.TC_FormatString, self.cb_format)
	self.parent.Bind(wx.EVT_CHECKBOX, self.TC_SingleByte, self.cb_single_byte)
	self.parent.Bind(wx.EVT_CHECKBOX, self.TC_DoubleByte, self.cb_double_byte)
	self.parent.Bind(wx.EVT_CHECKBOX, self.TC_QuadByte, self.cb_quad_byte)
	self.parent.Bind(wx.EVT_CHECKBOX, self.TC_null, self.cb_null)
	self.parent.Bind(wx.EVT_CHECKBOX, self.TC_CommandUnix, self.cb_commandu)
	self.parent.Bind(wx.EVT_CHECKBOX, self.TC_CommandWindows, self.cb_commandw)
	self.parent.Bind(wx.EVT_CHECKBOX, self.TC_Xml, self.cb_xml)

	self.parent.Bind(wx.EVT_CHECKBOX, self.TC_UserDefined, self.cb_userdefined)
	self.parent.Bind(wx.EVT_CHECKBOX, self.TC_Control, self.cb_control)
	self.parent.Bind(wx.EVT_CHECKBOX, self.TC_Extended, self.cb_extended)
	self.parent.Bind(wx.EVT_CHECKBOX, self.TC_BitByte, self.cb_bitbyte)
	self.parent.Bind(wx.EVT_CHECKBOX, self.TC_BitWord, self.cb_bitword)
	self.parent.Bind(wx.EVT_CHECKBOX, self.TC_BitLong, self.cb_bitlong)
	self.parent.Bind(wx.EVT_CHECKBOX, self.TC_BitByteInv, self.cb_bitbyteinv)
	self.parent.Bind(wx.EVT_CHECKBOX, self.TC_BitWordInv, self.cb_bitwordinv)
	self.parent.Bind(wx.EVT_CHECKBOX, self.TC_BitLongInv, self.cb_bitlonginv)

	self.parent.Bind(wx.EVT_CHECKBOX, self.EnableZuluScript, self.cb_zuluscript)	
	self.parent.Bind(wx.EVT_CHECKBOX, self.EnableWireshark, self.cb_wireshark)	
	self.parent.Bind(wx.EVT_CHECKBOX, self.EnableVMware, self.cb_vmware)

	self.Bind(wx.EVT_COMBOBOX, self.AddDoubleOffset, self.cbDoubleOffset)
	self.Bind(wx.EVT_COMBOBOX, self.AddQuadOffset, self.cbQuadOffset)

	self.tc_packetlist.Bind(wx.EVT_LEFT_DOWN, self.tc_packetlistLeftDown)
	self.tc_packetlist.Bind(wx.EVT_KEY_DOWN, self.tc_packetlistLeftDown)

	self.tc_captured.Bind(wx.EVT_LEFT_UP, self.tc_capturedLeftUp)
	self.tc_captured_asc.Bind(wx.EVT_LEFT_UP, self.tc_capturedLeftUp)

	self.tc_captured.Bind(wx.EVT_SET_FOCUS, self.tc_capturedFocus)
	self.tc_captured_asc.Bind(wx.EVT_SET_FOCUS, self.tc_captured_ascFocus)

	self.parent.Bind(wx.EVT_BUTTON, self.OpenBufferTestcase, bmbtn_overflows)
	self.parent.Bind(wx.EVT_BUTTON, self.OpenFormatTestcase, bmbtn_format)
	self.parent.Bind(wx.EVT_BUTTON, self.OpenNullTestcase, bmbtn_null)
	self.parent.Bind(wx.EVT_BUTTON, self.OpenUnixTestcase, bmbtn_unix)
	self.parent.Bind(wx.EVT_BUTTON, self.OpenWindowsTestcase, bmbtn_windows)
	self.parent.Bind(wx.EVT_BUTTON, self.OpenXMLTestcase, bmbtn_xml)
	self.parent.Bind(wx.EVT_BUTTON, self.OpenUserTestcase, bmbtn_user)
	self.parent.Bind(wx.EVT_BUTTON, self.OpenCustom, bmbtn_zuluscript)

#------------------------------------------------------------------------------------------------------------------------------------------
#--- Main code ----------------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------------

	path = self.logfilepath + time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()) + ".log"
	self.fplog = file(path, 'a')	# open logfile for writing
	self.fplog.write("\n\n**** Zulu Log file ****\n\n")

	self.firstloaded = True
	self.OpenSession(1)

	self.mb.Enable(self.ID_Save_Session, False)
	self.tb.EnableTool(self.ID_toolSaveFile, False)
	self.tb.EnableTool(self.ID_toolExploit, False)
	self.tb.EnableTool(self.ID_toolFuzzerStart, False)
	self.tb.EnableTool(self.ID_toolFuzzerPause, False)
	self.tb.EnableTool(self.ID_toolFuzzerStop, False)

	self.mb.Enable(self.ID_Start_Fuzzing, False)
	self.mb.Enable(self.ID_Pause_Fuzzing, False)
	self.mb.Enable(self.ID_Stop_Fuzzing, False)

	self.mb.Enable(self.ID_Stop_Capture, False)
	self.tb.EnableTool(self.ID_toolProxyStop, False)
	self.btn_ClearAllFuzzPoints.Enable(False)

	self.btn_AddAllBytes.Enable(False)
	self.btn_AddAllDoubleBytes.Enable(False)
	self.btn_AddAllQuadBytes.Enable(False)
	self.cbDoubleOffset.Enable(False)
	self.cbQuadOffset.Enable(False)

	self.EnableCheckboxes()

#------------------------------------------------------------------------------------------------------------------------------------------
#--- Fuzzer Modules -----------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------------

#------------------------------------------------------------------------------------------------------------------------------------------
#--- Serial Fuzzer Module -----------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------------
# ConfigureSerialFuzzer()
# StartSerialCapture()
# Choose_serial_fuzzer()
# serial_fuzzer()
#------------------------------------------------------------------------------------------------------------------------------------------

    def	ConfigureSerialFuzzer(self,event):
	self.Choose_serial_fuzzer(1)
	self.ser = serial.Serial()
        
	while 1:
		dialog_serial_cfg = SerialConfigDialog(self, None, -1, "", serial=self.ser)
		result = dialog_serial_cfg.ShowModal()
		if result == wx.ID_OK:
			break
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)
	self.ser.close()

    def	StartSerialCapture(self,event):
	self.ResetEverything()
	self.session_changed = True
	self.targethost = "127.0.0.2"
	self.targetport = 20
	self.capture_type = "Serial"
	self.Choose_serial_fuzzer(1)

	self.mb.Enable(self.ID_Start_Capture, False)
	self.mb.Enable(self.ID_Configure_Proxy, False)
	self.mb.Enable(self.ID_Open_Session, False)
	self.mb.Enable(self.ID_Save_Session, False)
	self.mb.Enable(self.ID_Configure_Logfile, False)
	self.mb.Enable(self.ID_Configure_Email, False)
	self.mb.Enable(self.ID_Import_PCAP, False)
	self.mb.Enable(self.ID_Start_Serial_Capture, False)
	self.mb.Enable(self.ID_Import_USB, False)

	self.mb.Enable(self.ID_Configure_VMware, False)
	self.mb.Enable(self.ID_Network_Fuzzer, False)
	self.mb.Enable(self.ID_File_Fuzzer, False)
	self.mb.Enable(self.ID_USB_Fuzzer, False)
	self.mb.Enable(self.ID_Serial_Fuzzer, False)
	self.mb.Enable(self.ID_Import_File, False)

	self.tb.EnableTool(self.ID_toolProxyStart, False)
	self.tb.EnableTool(self.ID_toolConfigure, False)
	self.tb.EnableTool(self.ID_toolOpenFile, False)
	self.tb.EnableTool(self.ID_toolSaveFile, False)
	self.tb.EnableTool(self.ID_toolFindNext, False)

	self.frame_terminal = easyshell.FrameTerminal(self, None, -1, "")
   	self.frame_terminal.Show()

    def	Choose_serial_fuzzer(self, event):
	if self.fuzzer == "Serial":
		return	
	
	self.fuzzer = "Serial"
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)
	self.statusbar.SetStatusText("Fuzzer selected: Serial Fuzzer", 1)
	self.tc_output.AppendText("Status: Fuzzer set to Serial Fuzzer\n")
	self.tc_output.ShowPosition(self.tc_output.GetLastPosition()-1)
	self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
	self.fplog.write("\nStatus: Fuzzer set to Serial Fuzzer\n")
	return	

    def serial_fuzzer(self, packet_data_list):
	if self.fuzzing == False:
		return
	try: 		
		self.ping(self.serial_ip_address) 
	except:
		self.TargetHasCrashed()
	try:
		self.ser.open()
	except:
		wx.MessageBox("Serial connection error", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
		return 1
	x = 0
	while x < len (packet_data_list):
		if self.fuzzing == True:
			if self.fuzzing_paused == True:
				while (1):
					if self.fuzzing_paused == False:
						break
					try:
						wx.Yield()
					except:
						pass

			data = packet_data_list[x][1]
			
			if self.receivepacketfirst == False:
				try:
					wx.Yield()
				except:
					pass
				packetnum = packet_data_list[x][0]
				recv_packetnum = packetnum + 1
				#----------------- send packet------------------------------
				out =  "Sending packet #%d" % packetnum
				print time.strftime("%H:%M:%S  ", time.localtime()),
				print out
				self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
				self.fplog.write(out)
				self.fplog.write("\n")
				try:
					self.ser.write(data)
					print time.strftime("%H:%M:%S  ", time.localtime()),
					print repr(data)
					self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
					self.fplog.write(repr(data))
					self.fplog.write("\n")
					print
				except:
			 		self.TargetHasCrashed()
				#----------------- receive packet---------------------------
				out =  "Receiving packet #%d" % recv_packetnum
				print time.strftime("%H:%M:%S  ", time.localtime()),
				print out
				self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
				self.fplog.write(out)
				self.fplog.write("\n")
				try:
					buf = self.ser.read(5000)
					print time.strftime("%H:%M:%S  ", time.localtime()),
					print repr(buf)
					self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
					self.fplog.write(repr(buf))
					self.fplog.write("\n")
					print
				except:
			 		out =  "Error receiving packet #%d" % recv_packetnum
					print time.strftime("%H:%M:%S  ", time.localtime()),
					print out
					self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
					self.fplog.write(out)
					self.fplog.write("\n")
					print
			else:
				try:
					wx.Yield()
				except:
					pass
				recv_packetnum = packet_data_list[x][0]
				packetnum = recv_packetnum + 1
				out =  "Receiving packet #%d" % packetnum
				print time.strftime("%H:%M:%S  ", time.localtime()),
				print out
				self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
				self.fplog.write(out)
				self.fplog.write("\n")
				#----------------- receive packet---------------------------
				out =  "Receiving packet #%d" % recv_packetnum
				print time.strftime("%H:%M:%S  ", time.localtime()),
				print out
				self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
				self.fplog.write(out)
				self.fplog.write("\n")
				try:
					buf = self.ser.read(5000)
					print time.strftime("%H:%M:%S  ", time.localtime()),
					print repr(buf)
					self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
					self.fplog.write(repr(buf))
					self.fplog.write("\n")
					print	
				except:
			 		out =  "Error receiving packet #%d" % recv_packetnum
					print time.strftime("%H:%M:%S  ", time.localtime()),
					print out
					self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
					self.fplog.write(out)
					self.fplog.write("\n")
					print
				#----------------- send packet------------------------------
				out =  "Sending packet #%d" % packetnum
				print time.strftime("%H:%M:%S  ", time.localtime()),
				print out
				self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
				self.fplog.write(out)
				self.fplog.write("\n")
				try:
					self.ser.write(data)
					print time.strftime("%H:%M:%S  ", time.localtime()),
					print repr(data)
					self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
					self.fplog.write(repr(data))
					self.fplog.write("\n")
					print
				except:
			 		self.TargetHasCrashed()
				#----------------- receive packet---------------------------
				out =  "Receiving packet #%d" % recv_packetnum
				print time.strftime("%H:%M:%S  ", time.localtime()),
				print out
				self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
				self.fplog.write(out)
				self.fplog.write("\n")
				try:
					buf = self.ser.read(5000)
					print time.strftime("%H:%M:%S  ", time.localtime()),
					print repr(buf)
					self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
					self.fplog.write(repr(buf))
					self.fplog.write("\n")
					print	
				except:
			 		out =  "Error receiving packet #%d" % recv_packetnum
					print time.strftime("%H:%M:%S  ", time.localtime()),
					print out
					self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
					self.fplog.write(out)
					self.fplog.write("\n")
					print
		else:
			return

		self.ser.close()
		x+=1
		self.last_packet_data_list = []
		count = 0
		while count < len (packet_data_list):
			thispacket = packet_data_list[count][1]
			self.last_packet_data_list.append(thispacket)
			count +=1

#------------------------------------------------------------------------------------------------------------------------------------------
#--- File Fuzzer Module -------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------------
# CreateFileConfWindow()
# ConfigureFileFuzzer()
# ConfFileProcToFuzz()
# ConfFileProcArgs()
# ConfFileProcRuntime()
# ConfFileProcShutdown()
# OnOkFileConf()
# ImportFile()
# Choose_file_fuzzer()
# file_fuzzer()
# my_event_handler()
# file_debugger()
#------------------------------------------------------------------------------------------------------------------------------------------	

    def CreateFileConfWindow (self):
	win = wx.Frame(self, -1, "File Fuzzer configuration",size=(350,200), style=wx.TAB_TRAVERSAL | wx.FRAME_FLOAT_ON_PARENT | wx.CAPTION | wx.FRAME_TOOL_WINDOW)
	win.Center()
	win.Show(True)
	win.SetBackgroundColour("White")
	path = self.workingdir
	path = path + "\\..\\images\\zulu_logo16x16.png"
	image = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap() 
	icon = wx.EmptyIcon() 
	icon.CopyFromBitmap(image) 
	win.SetIcon(icon) 
	return win

    def	ConfigureFileFuzzer (self,evt):
	self.Choose_file_fuzzer(1)
	self.btn_PacketTest.Enable(False)
	runtime = ["0.5","1.0","1.5","2.0","2.5","3.0","3.5","4.0","4.5","5.0","10"]
	shutdown = ["Kill()", "TerminateProcess()"]
	self.OkFileConf = False
	self.fileconfwin = self.CreateFileConfWindow()
	self.fileconfwin.SetFocus()
	vs = wx.BoxSizer( wx.VERTICAL )
	box1_title = wx.StaticBox( self.fileconfwin, -1, "Configue file fuzzer settings" )
	box1 = wx.StaticBoxSizer( box1_title, wx.VERTICAL )
	grid1 = wx.FlexGridSizer( 0, 2, 0, 0 )
	self.conf_ctrls = []      
	text1 = wx.StaticText(self.fileconfwin, -1, "Process to fuzz:")
	b_fuzzproc_path = wx.Button(self.fileconfwin, 20, "    Select path     ", (20, 20))
	text2 = wx.StaticText(self.fileconfwin, -1, "Commandline args:")
	text3 = wx.TextCtrl(self.fileconfwin, -1, self.process_command_args)
	text4 = wx.StaticText(self.fileconfwin, -1, "Process run time:")
	cb_proc_runtime = wx.ComboBox(self.fileconfwin, 600, "%.1f" % self.process_run_time, wx.DefaultPosition, wx.DefaultSize, runtime, wx.CB_DROPDOWN)
	text5 = wx.StaticText(self.fileconfwin, -1, "Shutdown method:")
	cb_proc_shutdown = wx.ComboBox(self.fileconfwin, 700, self.process_termiate_type, wx.DefaultPosition, wx.DefaultSize, shutdown, wx.CB_DROPDOWN)
	grid1.Add( text1, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( b_fuzzproc_path, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( text2, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( text3, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( text4, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( cb_proc_runtime, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( text5, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( cb_proc_shutdown, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	box1.Add( grid1, 0, wx.ALIGN_CENTRE|wx.ALL, 5 )
	vs.Add( box1, 0, wx.ALIGN_CENTRE|wx.ALL, 5 )
	button = wx.Button(self.fileconfwin, 1005, "OK")
	self.fileconfwin.Bind(wx.EVT_BUTTON, self.OnOkFileConf, button)
	vs.Add( button, 0, wx.ALIGN_CENTRE|wx.ALL, 5 )
	self.fileconfwin.Bind(wx.EVT_BUTTON, self.ConfFileProcToFuzz, b_fuzzproc_path)
	self.fileconfwin.Bind(wx.EVT_TEXT, self.ConfFileProcArgs, text3)
	self.fileconfwin.Bind(wx.EVT_COMBOBOX, self.ConfFileProcRuntime, cb_proc_runtime)
	self.fileconfwin.Bind(wx.EVT_COMBOBOX, self.ConfFileProcShutdown, cb_proc_shutdown)	
	self.fileconfwin.SetSizer( vs )
	vs.Fit( self.fileconfwin )
	while self.OkFileConf == False:
		try:
			wx.Yield()
		except:
			pass

    def ConfFileProcToFuzz (self, event):
	path = ""
	dir = "C:\\"

	dlg = wx.FileDialog(
        	self, message="Choose a file", defaultDir=dir, 
        	defaultFile="", wildcard="*.*", style=wx.OPEN | wx.MULTIPLE | wx.CHANGE_DIR
        	)

	dlg.SetFilterIndex(2)

	if dlg.ShowModal() == wx.ID_OK:
		path = dlg.GetPath()
		dlg.Destroy()
		if path == "":
			return 1

	if not os.path.exists(path):
		wx.MessageBox("File does not exist", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
		return 1

	self.process_to_fuzz = "\"" + path + "\""
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)
	
    def	ConfFileProcArgs (self, event):
	try:
		self.process_command_args = event.GetString()
		self.session_changed = True
		self.mb.Enable(self.ID_Save_Session, True)
		self.tb.EnableTool(self.ID_toolSaveFile, True)
	except:
		pass

    def ConfFileProcRuntime (self, event):
	try:
		selected = event.GetString()
		self.process_run_time = float (selected)
		self.session_changed = True
		self.mb.Enable(self.ID_Save_Session, True)
		self.tb.EnableTool(self.ID_toolSaveFile, True)
	except:
		pass

    def ConfFileProcShutdown (self, event):
	try:
		shut = event.GetString()
		self.session_changed = True
		self.mb.Enable(self.ID_Save_Session, True)
		self.tb.EnableTool(self.ID_toolSaveFile, True)
	except:
		pass

	if shut == "kill()":
		self.process_termiate_type = "Kill"
	elif shut == "TerminateProcess()":
		self.process_termiate_type = "Terminate"

    def OnOkFileConf (self, event):
	self.OkFileConf = True
	self.fileconfwin.Close()

    def ImportFile (self,event):
	if len(self.packets) > 0:
		dlg = wx.MessageDialog(self,'Are you sure you want to start a new session?','Zulu', style=wx.YES | wx.NO | wx.ICON_INFORMATION)        
		val = dlg.ShowModal()
		if val == wx.ID_YES:
			dlg.Destroy()
			pass
		if val == wx.ID_NO:
			dlg.Destroy()
			return
	self.ResetEverything()
	path = ""
	dir = self.workingdir
	dlg = wx.FileDialog(
            self, message="Choose a file", defaultDir=dir, 
            defaultFile="default", wildcard="*.*", style=wx.OPEN | wx.MULTIPLE | wx.CHANGE_DIR
            )
	dlg.SetFilterIndex(2)
	if dlg.ShowModal() == wx.ID_OK:
		path = dlg.GetPath()
		dlg.Destroy()
		if path == "":
			return 1
		if not os.path.exists(path):
			wx.MessageBox("File does not exist", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
			return 1
		try:
			fp = file(path, 'rb')	# open file for reading
		except:
			wx.MessageBox("Error opening file", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
		data = fp.read()
		try:
			temp = []
			temp = os.path.basename(path).split('.')
			if len(temp) < 1:
				self.file_extension = temp[len(temp)-1]
			else:
				self.file_extension = ''
		except:
			pass
		tmp_list = []
		tmp_list.append("127.0.0.1")
		tmp_list.append(1)
		self.packets.append([tmp_list,data])
		self.Choose_file_fuzzer(1)
		self.process_input_data()

    def	Choose_file_fuzzer(self, event):
	if self.fuzzer == "File":
		return	
	
	self.fuzzer = "File"
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)
	self.statusbar.SetStatusText("Fuzzer selected: File Fuzzer", 1)
	self.tc_output.AppendText("Status: Fuzzer set to File Fuzzer\n")
	self.tc_output.ShowPosition(self.tc_output.GetLastPosition()-1)
	self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
	self.fplog.write("\nStatus: Fuzzer set to File Fuzzer\n")
	return

    def	file_fuzzer(self, packet_data_list):
	if self.fuzzing == False:
		return
	else:
		if self.fuzzing_paused == True:
			while (1):
				if self.fuzzing_paused == False:
					break
				try:
					wx.Yield()
				except:
					pass
		data = packet_data_list[0][1]
		self.current_file_data = data
		filename = "temp" + "%d" % self.file_counter
		self.file_counter+=1
		if self.file_extension != "":
			filename += "."
			filename += self.file_extension 
		p = self.workingdir
		p = p[:-4] 
		path = p + "\\tempfiles\\" + filename
		removepath = p + "\\tempfiles\\" 
		fileList = os.listdir(removepath)
		for fileName in fileList:
			try:
 				os.remove(removepath + "\\" + fileName)
			except:
				pass
		try:
			fd = os.open(path, os.O_RDWR|os.O_CREAT|os.O_BINARY)
			os.write(fd, self.current_file_data)
			os.close(fd)
		except:
			wx.MessageBox("Error creating fuzz file", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
			return 1
		path = "\"" + path + "\""
		command = self.process_to_fuzz
		if command[0] != "\"":
			command = "\"" + command + "\""
		if command == "":
			wx.MessageBox("No process selected to fuzz", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
			return 1
		to_run = command + " " + path
		print to_run
		try:
			process = subprocess.Popen(to_run, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		except:
			wx.MessageBox("Error starting target process", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
			return 1
		#----------- debugger stuff --------------------------------
		self.file_debugger(process.pid, self.process_run_time)
		#-----------------------------------------------------------
		try:
			wx.Yield()
		except:
			pass
		time.sleep(0.5)
		try:
			wx.Yield()
		except:
			pass
		if self.process_termiate_type == "Terminate":
			try:
				win32api.TerminateProcess(int(process._handle), -1)
			except:
				pass
		elif self.process_termiate_type == "Kill":
			try:
				process.kill()
			except:
				pass

    def	my_event_handler(self,event):
	code = event.get_event_code()
	pid = event.get_pid()
	tid = event.get_tid()
	pc = event.get_thread().get_pc()
	if code == 1:
		exception_info = event.get_exception_description() 
		if exception_info == "Access violation":
			out = "process %d crashed at address 0x%08x\n" % (pid,pc)
			print "-----------------------------------------------------------------------------"
			print time.strftime("%H:%M:%S  ", time.localtime()),
			print out
			print "-----------------------------------------------------------------------------"
			print 
			self.Showalert = True
			path = self.workingdir
			path = path + "\\..\\images\\alert.png"
			image_file = path
			image = wx.Bitmap(image_file)
			image_size = image.GetSize()
			self.tc_output.AppendText(out)
			self.tc_output.ShowPosition(self.tc_output.GetLastPosition()-1)
			self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
			self.fplog.write(out)				
			self.bmCrash = wx.StaticBitmap(self, wx.ID_ANY, image, size=image_size, pos=(1045,670))
			# save file to crashfiles directory
			newfile = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
			destpath = self.workingdir[:-4]
			if self.file_extension != "":
				destpath = destpath + "\\crashfiles\\Crash_" + newfile + "." + self.file_extension
			else:
				destpath = destpath + "\\crashfiles\\Crash_" + newfile
			try:
				fd = os.open(destpath, os.O_RDWR|os.O_CREAT|os.O_BINARY)
				os.write(fd, self.current_file_data)
				os.close(fd)
			except:
				wx.MessageBox("Error writing crash file", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
				return 1
			self.StopFuzzing(1)

    def	file_debugger(self, pid, wait_time):
	debug = Debug(self.my_event_handler)
	print time.strftime("%H:%M:%S  ", time.localtime()),
	print "PID = %d" % pid
	print time.strftime("%H:%M:%S  ", time.localtime()),
	print "Delay = %.1f" % wait_time
	try:
		debug.attach(pid)
	except:
		pass
	try:
		maxTime = time.time() + wait_time    # timeout
		while time.time() < maxTime:
			try:
				wx.Yield()
			except:
				pass
			try:
				event = debug.wait(1000)
			except WindowsError, e:
				if ctypes.winerror(e) in (ctypes.ERROR_SEM_TIMEOUT, ctypes.WAIT_TIMEOUT):
					continue
				raise
			try:
				debug.dispatch(event)
			finally:
				debug.cont(event)
	finally:
		debug.stop()

#------------------------------------------------------------------------------------------------------------------------------------------
#--- USB Fuzzer Module --------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------------
# ImportUSB()
# CreateUSBConfWindow()
# ConfigureUSBFuzzer()
# ConfGraphicUSB()
# ConfUSBInstrumentation()
# OnOkUSBConf()
# Choose_usb_fuzzer()
# usb_fuzzer()
#------------------------------------------------------------------------------------------------------------------------------------------

    def	ImportUSB(self,event):
	datalist = []
	tmplist = []
	self.packets = []
	path = ""
	self.targethost = "127.0.0.2"
	self.targetport = 20
	dir = "C:\\"
	dlg = wx.FileDialog(
          	self, message="Choose a file", defaultDir=dir, 
           	defaultFile="default", wildcard="*.mgen", style=wx.OPEN | wx.MULTIPLE | wx.CHANGE_DIR
           	)
	dlg.SetFilterIndex(2)
	if dlg.ShowModal() == wx.ID_OK:
		path = dlg.GetPath()
		dlg.Destroy()
		if path == "":
			return 1
	if not os.path.exists(path):
		wx.MessageBox("File does not exist", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
		return 1
	try:
		fp = file(path, 'r')	# open file for reading
	except:
		wx.MessageBox("Error opening file", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
	data = fp.read()
	datalist = data.split('\n')
	self.usb_file_locations = []
	line = ""
	x = 0
	while x < len(datalist):
		line = datalist[x]
		tmplist = []
		if len(line) > 3:
			if line[0] == "\x09" and line[1] != "C":
				line = string.replace(line,"\x09","")
				line = string.replace(line,"0x","")
				line = string.replace(line," ","")
				tmpline = ""
				y = 0
				while y < len(line)-1:
					tmpline += "%c" % int((line[y]+line[y+1]),16)
					y+=2
				tmplist.append("127.0.0.1")
				tmplist.append(10)
				self.packets.append([tmplist,tmpline])
				self.usb_file_locations.append(x)
			elif line[0] == ";" and (line[1] == "\x09" or line[2] == "\x09") and line[2] != "C":
				line = string.replace(line,"\x09","")
				line = string.replace(line,";","")
				line = string.replace(line,"0x","")
				line = string.replace(line," ","")
				tmpline = ""
				y = 0
				while y < len(line)-1:
					tmpline += "%c" % int((line[y]+line[y+1]),16)
					y+=2
				tmplist.append("127.0.0.2")
				tmplist.append(20)
				self.packets.append([tmplist,tmpline])
				self.usb_file_locations.append(x)
		x+=1
	self.capture_type = "USB"
	self.Choose_usb_fuzzer(1)
	self.process_input_data()
	fp.close()
	newfile = "USB_gen_" + time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()) + ".txt"
	path = self.workingdir[:-4] + "\\tempfiles\\" + newfile
	self.usb_temp_gen_script = path
	try:
		fp = file(path, 'w')
	except:
		wx.MessageBox("Error opening file", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
	try:
		fp.write(data)
	except:
		wx.MessageBox("Error writing temporary file", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
	fp.close()

    def CreateUSBConfWindow (self):
	win = wx.Frame(self, -1, "USB Fuzzer configuration",size=(350,200), style=wx.TAB_TRAVERSAL | wx.FRAME_FLOAT_ON_PARENT | wx.CAPTION | wx.FRAME_TOOL_WINDOW)
	win.Center()
	win.Show(True)
	win.SetBackgroundColour("White")
	path = self.workingdir
	path = path + "\\..\\images\\zulu_logo16x16.png"
 	image = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap() 
	icon = wx.EmptyIcon() 
	icon.CopyFromBitmap(image) 
	win.SetIcon(icon) 
	return win

    def	ConfigureUSBFuzzer (self,evt):
	self.Choose_usb_fuzzer(1)
	self.btn_PacketTest.Enable(False)
	self.OkUSBConf = False
	self.usbconfwin = self.CreateUSBConfWindow()
	self.usbconfwin.SetFocus()
	vs = wx.BoxSizer( wx.VERTICAL )
	box1_title = wx.StaticBox(self.usbconfwin, -1, "Configue USB fuzzer settings")
	box1 = wx.StaticBoxSizer( box1_title, wx.VERTICAL )
	grid1 = wx.FlexGridSizer( 0, 2, 0, 0 )
	self.conf_ctrls = []       
	text1 = wx.StaticText(self.usbconfwin, -1, "Path to GraphicUSB:")
	b_graphicusb_path = wx.Button(self.usbconfwin, 20, "    Select path     ", (20, 20))
	text2 = wx.StaticText(self.usbconfwin, -1, "Target IP address:")
	text3 = wx.TextCtrl(self.usbconfwin, -1, self.usb_target_ip_address)
	grid1.Add( text1, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( b_graphicusb_path, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( text2, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( text3, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	box1.Add( grid1, 0, wx.ALIGN_CENTRE|wx.ALL, 5 )
	vs.Add( box1, 0, wx.ALIGN_CENTRE|wx.ALL, 5 )
	button = wx.Button(self.usbconfwin, 1005, "OK")
	self.usbconfwin.Bind(wx.EVT_BUTTON, self.OnOkUSBConf, button)
	vs.Add( button, 0, wx.ALIGN_CENTRE|wx.ALL, 5 )
	self.usbconfwin.Bind(wx.EVT_BUTTON, self.ConfGraphicUSB, b_graphicusb_path)
	self.usbconfwin.Bind(wx.EVT_TEXT, self.ConfUSBInstrumentation, text3)
	self.usbconfwin.SetSizer( vs )
	vs.Fit(self.usbconfwin)
	while self.OkUSBConf == False:
		try:
			wx.Yield()
		except:
			pass

    def ConfGraphicUSB (self, event):
	path = ""
	dir = "C:\\Program Files (x86)\\MQP Electronics\\GraphicUSB\\"

	dlg = wx.FileDialog(
        	self, message="Choose a file", defaultDir=dir, 
        	defaultFile="", wildcard="*.exe", style=wx.OPEN | wx.MULTIPLE | wx.CHANGE_DIR
        	)
	dlg.SetFilterIndex(2)
	if dlg.ShowModal() == wx.ID_OK:
		path = dlg.GetPath()
		dlg.Destroy()
		if path == "":
			return 1
	if not os.path.exists(path):
		wx.MessageBox("File does not exist", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
		return 1
	self.GraphicUSB_path = "\"" + path + "\""
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)

    def	ConfUSBInstrumentation (self, event):
	try:
		self.usb_target_ip_address = event.GetString()
		self.session_changed = True
		self.mb.Enable(self.ID_Save_Session, True)
		self.tb.EnableTool(self.ID_toolSaveFile, True)
	except:
		pass

    def OnOkUSBConf (self, event):
	self.OkUSBConf = True
	self.usbconfwin.Close()

    def	Choose_usb_fuzzer(self, event):
	if self.fuzzer == "USB":
		return
	self.fuzzer = "USB"
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)
	self.statusbar.SetStatusText("Fuzzer selected: USB Fuzzer", 1)
	self.tc_output.AppendText("Status: Fuzzer set to USB Fuzzer\n")
	self.tc_output.ShowPosition(self.tc_output.GetLastPosition()-1)
	self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
	self.fplog.write("\nStatus: Fuzzer set to USB Fuzzer\n")
	return

    def	usb_fuzzer(self, packet_data_list):
	if self.fuzzing == False:
		return
	#if not os.path.exists(self.GraphicUSB_path):
	#	wx.MessageBox("GraphicUSB path is not configured", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
	#	return 1
	original_data = ""
	original_datalist = []
	if self.fuzzing_paused == True:
		while (1):
			if self.fuzzing_paused == False:
				break
			try:
				wx.Yield()
			except:
				pass
	path = self.usb_temp_gen_script
	try:
		fp = file(path, 'r')	# open file for reading
	except:
		wx.MessageBox("Error opening file", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
		return 1
	try:
		original_data = fp.read()
	except:
		wx.MessageBox("Error reading file", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
		return 1
	original_datalist = original_data.split('\n')
	x = 0
	while x < len (packet_data_list):
		txtdata = ""
		newdata = ""
		packetnum = packet_data_list[x][0]
		data = packet_data_list[x][1]
		y = 0
		while y < len(data):
			txtdata += "0x%02x " % ord(data[y])
			y+=1
		print time.strftime("%H:%M:%S  ", time.localtime()),
		print txtdata
		print
		txtdata = "\x09" + txtdata
		loc = self.usb_file_locations[packetnum]
		original_datalist[loc] = txtdata	# update original data (in a list) with fuzz data
		y = 0
		while y < len(original_datalist):
			newdata += original_datalist[y] + "\n"	# put data back into a string buffer
			y+=1
		newfile = "USB_gen_fuzz.mgen"
		path = self.workingdir[:-4] + "\\tempfiles\\" + newfile
		try:
			fp = file(path, 'w')
		except:
			wx.MessageBox("Error opening file", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
			return 1
		try:
			fp.write(newdata)
		except:
			wx.MessageBox("Error writing temporary file", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
			return 1
		fp.close()
		if self.GraphicUSB_path[0] != "\"":
			self.GraphicUSB_path = "\"" + self.GraphicUSB_path + "\""
		process = subprocess.Popen(self.GraphicUSB_path + " " + path + "\n", shell=True, stdout=subprocess.PIPE)
		SendKeys.SendKeys("""
    			{PAUSE 1}
    			{F7}
    			{PAUSE 2}
    			{F5}
    			{PAUSE 4.5} 
    			{ESC}
			%f
			x
		""")
		try:
			wx.Yield()
		except:
			pass
		if self.usb_target_ip_address != "":
			try: 
				self.ping(self.usb_target_ip_address) 
			except:
				self.TargetHasCrashed()
		x+=1

#------------------------------------------------------------------------------------------------------------------------------------------
#--- Network Fuzzer Module ----------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------------
# StartCapture()
# StopCapture()
# CreateConnectConfWindow()
# ConfigureConnection()
# ConfConEvtTargetIP()
# ConfConEvtTargetPort()
# ConfConEvtLocalPort()
# ConfConEvtMaxPackets()
# OnOkConConf()
# CreateNetworkConfWindow()
# ConfigureNetworkFuzzer()
# ConfNetTargetHost()
# ConfNetTargetPort()
# ConfNetConnectRetries()
# ConfNetTimeout()
# ConfNetFuzzcaseDelay()
# OnOkNetworkConf()
# Choose_network_fuzzer()
# network_fuzzer()
#------------------------------------------------------------------------------------------------------------------------------------------

    def StartCapture(self,event):
	if self.capturing == True:
		return
	if self.fuzzing == True:
		return
	self.mb.Enable(self.ID_Stop_Capture, True)
	self.tb.EnableTool(self.ID_toolProxyStop, True)
	self.mb.Enable(self.ID_Start_Capture, False)
	self.mb.Enable(self.ID_Configure_Proxy, False)
	self.mb.Enable(self.ID_Open_Session, False)
	self.mb.Enable(self.ID_Save_Session, False)
	self.mb.Enable(self.ID_Save_As_Session, False)
	self.mb.Enable(self.ID_Configure_Logfile, False)
	self.mb.Enable(self.ID_Configure_Email, False)
	self.mb.Enable(self.ID_Import_PCAP, False)
	self.mb.Enable(self.ID_Configure_VMware, False)
	self.mb.Enable(self.ID_Network_Fuzzer, False)
	self.mb.Enable(self.ID_File_Fuzzer, False)
	self.mb.Enable(self.ID_USB_Fuzzer, False)
	self.mb.Enable(self.ID_Serial_Fuzzer, False)
	self.mb.Enable(self.ID_Import_File, False)
	self.mb.Enable(self.ID_Start_Serial_Capture, False)
	self.mb.Enable(self.ID_Import_USB, False)
	self.tb.EnableTool(self.ID_toolProxyStart, False)
	self.tb.EnableTool(self.ID_toolConfigure, False)
	self.tb.EnableTool(self.ID_toolOpenFile, False)
	self.tb.EnableTool(self.ID_toolSaveFile, False)
	self.tb.EnableTool(self.ID_toolFindNext, False)
	if len(self.packets) > 0:
		dlg = wx.MessageDialog(self,'Are you sure you want to start a new session?','Zulu', style=wx.YES | wx.NO | wx.ICON_INFORMATION)        
		val = dlg.ShowModal()
		if val == wx.ID_YES:
			dlg.Destroy()
			pass
		if val == wx.ID_NO:
			dlg.Destroy()
			return
	self.network_capture = True
	self.Choose_network_fuzzer(1)
	self.ResetEverything()
	self.packets = []
	self.capture_data = False
	self.capturing = True
	self.tc_output.AppendText("Status: Capture started: Listening on port %d, target = %s:%d\n" % (self.port, self.targethost,self.targetport))
	self.tc_output.ShowPosition(self.tc_output.GetLastPosition()-1)
	self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
	self.fplog.write("Status: Capture started: Listening on port %d, target = %s:%d\n" % (self.port, self.targethost,self.targetport))
	self.statusbar.SetStatusText("Status: Capturing", 3)
	if self.udp == False:
		Pinhole(self, self.port, self.targethost, self.targetport).start()
	else:
		LISTEN = ("0.0.0.0", self.port)
		TARGET = (self.targethost, self.targetport)	
		proxy = UDPProxy(self, LISTEN, TARGET).start()
	temp_packet_len = len (self.packets)
	while self.capturing == True:
		try:
			wx.Yield()
		except:
			pass
		if len (self.packets) > temp_packet_len:
			self.process_input_data()
		temp_packet_len = len (self.packets)
		if temp_packet_len > self.max_packets:
			wx.MessageBox("Max packets limit reached", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
			self.StopCapture(1)

    def StopCapture(self,event):
	if self.fuzzing == True:
		return
	if self.capturing == False:
		return
	self.capturing = False
	self.mb.Enable(self.ID_Stop_Capture, False)
	self.tb.EnableTool(self.ID_toolProxyStop, False)
	self.mb.Enable(self.ID_Start_Capture, True)
	self.mb.Enable(self.ID_Configure_Proxy, True)
	self.mb.Enable(self.ID_Open_Session, True)
	self.mb.Enable(self.ID_Save_Session, True)
	self.mb.Enable(self.ID_Save_As_Session, True)
	self.mb.Enable(self.ID_Configure_Logfile, True)
	self.mb.Enable(self.ID_Configure_Email, True)
	self.mb.Enable(self.ID_Import_PCAP, True)
	self.mb.Enable(self.ID_Configure_VMware, True)
	self.mb.Enable(self.ID_Network_Fuzzer, True)
	self.mb.Enable(self.ID_File_Fuzzer, True)
	self.mb.Enable(self.ID_USB_Fuzzer, True)
	self.mb.Enable(self.ID_Serial_Fuzzer, True)
	self.mb.Enable(self.ID_Import_File, True)
	self.mb.Enable(self.ID_Start_Serial_Capture, True)
	self.mb.Enable(self.ID_Import_USB, True)
	self.tb.EnableTool(self.ID_toolProxyStart, True)
	self.tb.EnableTool(self.ID_toolConfigure, True)
	self.tb.EnableTool(self.ID_toolOpenFile, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)
	self.tb.EnableTool(self.ID_toolFindNext, True)

	if self.wiresharkpath != "":
		self.GeneratePCAP()
		self.StartWireshark()
	self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
	self.tc_output.AppendText("Status: Capture stopped\n")
	self.tc_output.ShowPosition(self.tc_output.GetLastPosition()-1)
	self.fplog.write("Status: Capture stopped\n")
	self.statusbar.SetStatusText("Status: Idle", 3)
	if self.udp == False:
		self.ConnectionToClose()

    def CreateConnectConfWindow (self):
	win = wx.Frame(self, -1, "Proxy configuration",size=(350,200), style=wx.TAB_TRAVERSAL | wx.FRAME_FLOAT_ON_PARENT | wx.CAPTION | wx.FRAME_TOOL_WINDOW)
	win.Center()
	win.Show(True)
	win.SetBackgroundColour("White")
	path = self.workingdir
	path = path + "\\..\\images\\zulu_logo16x16.png"
 	image = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap() 
	icon = wx.EmptyIcon() 
	icon.CopyFromBitmap(image) 
	win.SetIcon(icon) 
	return win

    def	ConfigureConnection (self,evt):
	if self.capturing == True:
		return
	if self.fuzzing == True:
		return
	self.OkConConf = False
	self.connectconfwin = self.CreateConnectConfWindow()
	self.connectconfwin.SetFocus()
	vs = wx.BoxSizer( wx.VERTICAL )
	box1_title = wx.StaticBox( self.connectconfwin, -1, "Configue proxy settings" )
	box1 = wx.StaticBoxSizer( box1_title, wx.VERTICAL )
	grid1 = wx.FlexGridSizer( 0, 2, 0, 0 )
	self.conf_ctrls = []       
	text1 = wx.StaticText(self.connectconfwin, -1, "Target host:")
	text2 = wx.TextCtrl( self.connectconfwin, -1, self.targethost)
	text3 = wx.StaticText(self.connectconfwin, -1, "Target port:")
	text4 = wx.TextCtrl( self.connectconfwin, -1, "%d" % self.targetport)
	text5 = wx.StaticText(self.connectconfwin, -1, "Local port:")
	text6 = wx.TextCtrl( self.connectconfwin, -1, "%d" % self.port)
	text7 = wx.StaticText(self.connectconfwin, -1, "Max packets:")
	text8 = wx.TextCtrl( self.connectconfwin, -1, "%d" % self.max_packets)
	cb_UDP = wx.CheckBox(self.connectconfwin, -1, "Use UDP")
	if self.udp == True:
		cb_UDP.SetValue(True)
	grid1.Add( text1, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( text2, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( text3, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( text4, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( text5, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( text6, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( text7, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( text8, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( cb_UDP, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	box1.Add( grid1, 0, wx.ALIGN_CENTRE|wx.ALL, 5 )
	vs.Add( box1, 0, wx.ALIGN_CENTRE|wx.ALL, 5 )
	button = wx.Button(self.connectconfwin, 1005, "OK")
	self.connectconfwin.Bind(wx.EVT_BUTTON, self.OnOkConConf, button)
	vs.Add( button, 0, wx.ALIGN_CENTRE|wx.ALL, 5 )
	self.connectconfwin.Bind(wx.EVT_TEXT, self.ConfConEvtTargetIP, text2)
	self.connectconfwin.Bind(wx.EVT_TEXT, self.ConfConEvtTargetPort, text4)
	self.connectconfwin.Bind(wx.EVT_TEXT, self.ConfConEvtLocalPort, text6)
	self.connectconfwin.Bind(wx.EVT_TEXT, self.ConfConEvtMaxPackets, text8)
	self.connectconfwin.Bind(wx.EVT_CHECKBOX, self.SetUDPMode, cb_UDP)
	self.connectconfwin.SetSizer( vs )
	vs.Fit( self.connectconfwin )
	while self.OkConConf == False:
		try:
			wx.Yield()
		except:
			pass

    def	ConfConEvtTargetIP (self, event):
	try:
		self.targethost = event.GetString()	
		self.session_changed = True
		self.mb.Enable(self.ID_Save_Session, True)
		self.tb.EnableTool(self.ID_toolSaveFile, True)
	except:
		pass

    def ConfConEvtTargetPort (self, event):
	try:
		self.targetport = int(event.GetString())
		self.session_changed = True
		self.mb.Enable(self.ID_Save_Session, True)
		self.tb.EnableTool(self.ID_toolSaveFile, True)
	except:
		pass

    def ConfConEvtLocalPort (self, event):
	try:
		self.port = int(event.GetString())
		self.session_changed = True
		self.mb.Enable(self.ID_Save_Session, True)
		self.tb.EnableTool(self.ID_toolSaveFile, True)
	except:
		pass

    def	ConfConEvtMaxPackets (self,event):
	try:
		self.max_packets = int(event.GetString())
		self.session_changed = True
		self.mb.Enable(self.ID_Save_Session, True)
		self.tb.EnableTool(self.ID_toolSaveFile, True)
	except:
		pass

    def OnOkConConf (self, event):
	self.OkConConf = True
	self.targethost = gethostbyname (self.targethost) 
	self.connectconfwin.Close()

    def CreateNetworkConfWindow (self):
	win = wx.Frame(self, -1, "Network Fuzzer configuration",size=(350,200), style=wx.TAB_TRAVERSAL | wx.FRAME_FLOAT_ON_PARENT | wx.CAPTION | wx.FRAME_TOOL_WINDOW)
	win.Center()
	win.Show(True)
	win.SetBackgroundColour("White")
	path = self.workingdir
	path = path + "\\..\\images\\zulu_logo16x16.png"
	image = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap() 
	icon = wx.EmptyIcon() 
	icon.CopyFromBitmap(image) 
	win.SetIcon(icon) 
	return win

    def	ConfigureNetworkFuzzer (self,evt):
	self.Choose_network_fuzzer(1)
	retries = ["0","1","2","4","8","16","32","64"]
	delay = ["0.0", "0.1", "0.2", "0.3", "0.4", "0.5", "0.6", "0.7", "0.8", "0.9","1.0","2.0","3.0","4.0","5.0","6.0","7.0","8.0","9.0","10.0"]
	timeout = ["0.1","0.2","0.3","0.4","0.5","0.6","0.7","0.8","0.9","1.0"]
	self.OkNetworkConf = False
	self.networkconfwin = self.CreateNetworkConfWindow()
	self.networkconfwin.SetFocus()
	vs = wx.BoxSizer( wx.VERTICAL )
	box1_title = wx.StaticBox( self.networkconfwin, -1, "Configue network fuzzer settings" )
	box1 = wx.StaticBoxSizer( box1_title, wx.VERTICAL )
	grid1 = wx.FlexGridSizer( 0, 2, 0, 0 )
	self.conf_ctrls = []       
	text1 = wx.StaticText(self.networkconfwin, -1, "Target host:")
	text2 = wx.TextCtrl(self.networkconfwin, -1, self.targethost)
	text3 = wx.StaticText(self.networkconfwin, -1, "Target port:")
	text4 = wx.TextCtrl(self.networkconfwin, -1, "%d" % self.targetport)
	text5 = wx.StaticText(self.networkconfwin, -1, "TCP Connect retries:")
	cb_net_retries = wx.ComboBox(self.networkconfwin, 600, "%d" % self.fuzz_retries, wx.DefaultPosition, wx.DefaultSize, retries, wx.CB_DROPDOWN)
	text6 = wx.StaticText(self.networkconfwin, -1, "Receive timeout:")
	cb_net_timeout = wx.ComboBox(self.networkconfwin, 650, "%.1f" % self.Receive_timeout, wx.DefaultPosition, wx.DefaultSize, timeout, wx.CB_DROPDOWN)
	text7 = wx.StaticText(self.networkconfwin, -1, "Delay between fuzzcases (seconds):")
	cb_net_delay = wx.ComboBox(self.networkconfwin, 700, "%.1f" % self.fuzz_delay, wx.DefaultPosition, wx.DefaultSize, delay, wx.CB_DROPDOWN)
	cb_UDP = wx.CheckBox(self.networkconfwin, -1, "Use UDP")
	grid1.Add( text1, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( text2, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( text3, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( text4, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( text5, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( cb_net_retries, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( text6, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( cb_net_timeout, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( text7, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( cb_net_delay, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( cb_UDP, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	box1.Add( grid1, 0, wx.ALIGN_CENTRE|wx.ALL, 5 )
	vs.Add( box1, 0, wx.ALIGN_CENTRE|wx.ALL, 5 )
	button = wx.Button(self.networkconfwin, 1005, "OK")
	self.networkconfwin.Bind(wx.EVT_BUTTON, self.OnOkNetworkConf, button)
	vs.Add( button, 0, wx.ALIGN_CENTRE|wx.ALL, 5 )
	self.networkconfwin.Bind(wx.EVT_TEXT, self.ConfNetTargetHost, text2)
	self.networkconfwin.Bind(wx.EVT_TEXT, self.ConfNetTargetPort, text4)
	self.networkconfwin.Bind(wx.EVT_COMBOBOX, self.ConfNetConnectRetries, cb_net_retries)
	self.networkconfwin.Bind(wx.EVT_COMBOBOX, self.ConfNetFuzzcaseDelay, cb_net_delay)
	self.networkconfwin.Bind(wx.EVT_COMBOBOX, self.ConfNetTimeout, cb_net_timeout)
	self.networkconfwin.Bind(wx.EVT_CHECKBOX, self.SetUDPMode, cb_UDP)
	self.networkconfwin.SetSizer( vs )
	vs.Fit(self.networkconfwin)
	while self.OkNetworkConf == False:
		try:
			wx.Yield()
		except:
			pass

    def	ConfNetTargetHost (self, event):
	try:
		self.targethost = event.GetString()
		self.session_changed = True
		self.mb.Enable(self.ID_Save_Session, True)
		self.tb.EnableTool(self.ID_toolSaveFile, True)
	except:
		pass

    def	ConfNetTargetPort (self, event):
	try:
		self.targetport = int(event.GetString())
		self.session_changed = True
		self.mb.Enable(self.ID_Save_Session, True)
		self.tb.EnableTool(self.ID_toolSaveFile, True)
	except:
		pass

    def ConfNetConnectRetries (self, event):
	try:
		selected = event.GetString()
        	self.fuzz_retries = int (selected)
		self.session_changed = True
		self.mb.Enable(self.ID_Save_Session, True)
		self.tb.EnableTool(self.ID_toolSaveFile, True)
	except:
		pass

    def	ConfNetTimeout (self,event):
	try:
		selected = event.GetString()
        	self.Receive_timeout = float (selected)
		self.session_changed = True
		self.mb.Enable(self.ID_Save_Session, True)
		self.tb.EnableTool(self.ID_toolSaveFile, True)
	except:
		pass

    def ConfNetFuzzcaseDelay (self, event):
	try:
		selected = event.GetString()
		self.fuzz_delay = float (selected)
		self.session_changed = True
		self.mb.Enable(self.ID_Save_Session, True)
		self.tb.EnableTool(self.ID_toolSaveFile, True)
	except:
		pass

    def OnOkNetworkConf (self, event):
	self.OkNetworkConf = True
	self.networkconfwin.Close()

    def	Choose_network_fuzzer(self, event):
	if self.fuzzer == "Network":
		return	
	self.fuzzer = "Network"
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)
	self.statusbar.SetStatusText("Fuzzer selected: Network Fuzzer", 1)
	self.tc_output.AppendText("Status: Fuzzer set to Network Fuzzer\n")
	self.tc_output.ShowPosition(self.tc_output.GetLastPosition()-1)
	self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
	self.fplog.write("\nStatus: Fuzzer set to Network Fuzzer\n")
	return

    def network_fuzzer(self, packet_data_list):
	if self.fuzzing == False:
		return
	connect_success = False
	if self.udp == False:
		self.fuzz_sock = socket(AF_INET, SOCK_STREAM)
	else:
		self.fuzz_sock = socket(AF_INET, SOCK_DGRAM)
	self.fuzz_sock.settimeout(self.Receive_timeout)
	connect_success = False
	attempts = 1
	while (attempts < self.fuzz_retries+1):
		if connect_success == True:
			break
		try:
			self.fuzz_sock.connect((self.targethost, self.targetport))
			connect_success = True
		except:
			message = "Fuzzing: Connect error - attempt #%d\n" % attempts
			print "----------------------------------------------------"
			print time.strftime("%H:%M:%S  ", time.localtime()),
			print message
			print "----------------------------------------------------"
			self.tc_output.AppendText(message)
			self.tc_output.ShowPosition(self.tc_output.GetLastPosition()-1)
			self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
			self.fplog.write(message)
			time.sleep(1)
		attempts += 1
	if connect_success == False:
		try:
			self.fuzz_sock.connect((self.targethost, self.targetport))
		except:
			self.TargetHasCrashed()
	x = 0
	while x < len (packet_data_list):
		if self.fuzzing == True:
			if self.fuzzing_paused == True:
				while (1):
					if self.fuzzing_paused == False:
						break
					try:
						wx.Yield()
					except:
						pass
			data = packet_data_list[x][1]
			if self.receivepacketfirst == False:
				try:
					wx.Yield()
				except:
					pass
				packetnum = packet_data_list[x][0]
				recv_packetnum = packetnum + 1
				#----------------- send packet------------------------------
				out =  "Sending packet #%d" % packetnum
				print time.strftime("%H:%M:%S  ", time.localtime()),
				print out
				self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
				self.fplog.write(out)
				self.fplog.write("\n")
				try:
					self.fuzz_sock.send(data)
					print time.strftime("%H:%M:%S  ", time.localtime()),
					print repr(data)
					self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
					self.fplog.write(repr(data))
					self.fplog.write("\n")
					print
				except:
			 		out =  "Error sending packet #%d" % packetnum
					print time.strftime("%H:%M:%S  ", time.localtime()),
					print out
					self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
					self.fplog.write(out)
					self.fplog.write("\n")
					print
				#----------------- receive packet---------------------------
				out =  "Receiving packet #%d" % recv_packetnum
				print time.strftime("%H:%M:%S  ", time.localtime()),
				print out
				self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
				self.fplog.write(out)
				self.fplog.write("\n")
				try:
					buf = self.fuzz_sock.recv(5000)
					print time.strftime("%H:%M:%S  ", time.localtime()),
					print repr(buf)
					self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
					self.fplog.write(repr(buf))
					self.fplog.write("\n")
					print
				except:
			 		out =  "Error receiving packet #%d" % recv_packetnum
					print time.strftime("%H:%M:%S  ", time.localtime()),
					print out
					self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
					self.fplog.write(out)
					self.fplog.write("\n")
					print
			else:
				try:
					wx.Yield()
				except:
					pass
				recv_packetnum = packet_data_list[x][0]
				packetnum = recv_packetnum + 1
				out =  "Receiving packet #%d" % packetnum
				print time.strftime("%H:%M:%S  ", time.localtime()),
				print out
				self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
				self.fplog.write(out)
				self.fplog.write("\n")
				#----------------- receive packet---------------------------
				out =  "Receiving packet #%d" % recv_packetnum
				print time.strftime("%H:%M:%S  ", time.localtime()),
				print out
				self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
				self.fplog.write(out)
				self.fplog.write("\n")
				try:
					buf = self.fuzz_sock.recv(5000)
					print time.strftime("%H:%M:%S  ", time.localtime()),
					print repr(buf)
					self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
					self.fplog.write(repr(buf))
					self.fplog.write("\n")
					print
				except:
			 		out =  "Error receiving packet #%d" % recv_packetnum
					print time.strftime("%H:%M:%S  ", time.localtime()),
					print out
					self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
					self.fplog.write(out)
					self.fplog.write("\n")
					print
				#----------------- send packet------------------------------
				out =  "Sending packet #%d" % packetnum
				print time.strftime("%H:%M:%S  ", time.localtime()),
				print out
				self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
				self.fplog.write(out)
				self.fplog.write("\n")
				try:
					self.fuzz_sock.send(data)
					print time.strftime("%H:%M:%S  ", time.localtime()),
					print repr(data)
					self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
					self.fplog.write(repr(data))
					self.fplog.write("\n")
					print
				except:
			 		out =  "Error sending packet #%d" % packetnum
					print time.strftime("%H:%M:%S  ", time.localtime()),
					print out
					self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
					self.fplog.write(out)
					self.fplog.write("\n")
					print
				#----------------- receive packet---------------------------
				out =  "Receiving packet #%d" % recv_packetnum
				print time.strftime("%H:%M:%S  ", time.localtime()),
				print out
				self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
				self.fplog.write(out)
				self.fplog.write("\n")
				try:
					buf = self.fuzz_sock.recv(5000)
					print time.strftime("%H:%M:%S  ", time.localtime()),
					print repr(buf)
					self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
					self.fplog.write(repr(buf))
					self.fplog.write("\n")
					print
				except:
			 		out =  "Error receiving packet #%d" % recv_packetnum
					print time.strftime("%H:%M:%S  ", time.localtime()),
					print out
					self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
					self.fplog.write(out)
					self.fplog.write("\n")
					print
		else:
			return
		x+=1
		self.last_packet_data_list = []
		count = 0
		while count < len (packet_data_list):
			thispacket = packet_data_list[count][1]
			self.last_packet_data_list.append(thispacket)
			count +=1
		
		
#------------------------------------------------------------------------------------------------------------------------------------------
#--- Fuzzing Engine -----------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------------
# menu_AddFuzzPoint()
# menu_DelFuzzPoint()
# menu_AddFuzzRange()
# menu_RemoveLengthField()
# menu_AddLengthField()
# NullFunction()
# RemoveLengthField()
# IncludeLengthField()
# UpdateLengthField()
# CreateLengthConfWindow()
# AddLengthField()
# ConfEndian()
# OnOkLengthConf()
# EnableZuluScript()
# TC_BufferOverflow()
# TC_FormatString()
# TC_SingleByte()
# PopulateSingleByte()
# TC_DoubleByte()
# PopulateDoubleByte()
# TC_QuadByte()
# PopulateQuadByte()
# TC_null()
# TC_CommandUnix()
# TC_CommandWindows()
# TC_Xml()
# TC_UserDefined()
# TC_Control()
# PopulateControl()
# TC_Extended()
# PopulateExtended()
# TC_BitByte()
# PopulateBitByte()
# TC_BitWord()
# PopulateBitWord()
# TC_BitLong()
# PopulateBitLong()
# TC_BitByteInv()
# PopulateBitByteInv()
# TC_BitWordInv()
# PopulateBitWordInv()
# TC_BitLongInv()
# PopulateBitLongInv()
# PopulateTestcases()
# RemoveTestcase()
# StartFuzzing()
# PauseFuzzing()
# StopFuzzing()
# ClearAllFuzzPoints()
# AddFuzzPoint()
# AddAllBytes()
# AddFuzzPointRange()
# CreateFuzzpointRemoveWindow()
# RemoveFuzzPoint()
# AddAllDoubleBytes()
# AddAllQuadBytes()
# AddDoubleOffset()
# AddQuadOffset()
# TargetHasCrashed()
#------------------------------------------------------------------------------------------------------------------------------------------

    def menu_AddFuzzPoint(self, event):
	self.AddFuzzPoint(1)

    def menu_DelFuzzPoint(self, event):
	self.RemoveFuzzPoint()

    def menu_AddFuzzRange(self, event):
	self.AddFuzzPointRange(1)

    def menu_RemoveLengthField(self, event):
	self.RemoveLengthField()

    def menu_AddLengthField(self, event):
	self.length_start = self.selection_start
	self.length_end = self.selection_end
	field_size = (self.selection_end+1) - self.selection_start
	if field_size > 4:
		wx.MessageBox("Length field too long", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
		return
	if field_size == 3:
		wx.MessageBox("Odd length field", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
		return
	if field_size == 0:
		wx.MessageBox("Nothing selected", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
		return
	self.AddLengthField()

    def NullFunction (self, event):
	return

    def RemoveLengthField (self):
	x = 0
	while x < len (self.LengthFields):
		field_size = self.LengthFields[x][0]
		field_pos = self.LengthFields[x][1]
		packet = self.LengthFields[x][4]
		field_pos_end = field_pos + field_size -1
		if packet == self.current_packet_number and field_pos == self.selection_start and field_pos_end == self.selection_end:
			self.LengthFields.pop(x)
		x+=1
	self.UpdateDataModificationPoints()	
	self.OutputPacketDetail(self.current_packet_number)

    def	IncludeLengthField(self, packet_number, data, testcase_len, fuzzpoint_start, fuzzpoint_end):
	datalist = []
	resultlist = []
	x = 0
	while x < len(data):
		datalist.append(data[x])
		x+=1
	x = 0
	while x < len (self.LengthFields):
		field_size = self.LengthFields[x][0]
		field_pos = self.LengthFields[x][1]
		start = self.LengthFields[x][2]
		end = self.LengthFields[x][3]
		packet = self.LengthFields[x][4]
		order = self.LengthFields[x][5]
		temp_len = testcase_len
		if packet == packet_number:
			if fuzzpoint_start > end:
				testcase_len = 0	# Length field doesn't need updating
			if start > fuzzpoint_end:
				testcase_len = 0	# only increment the appropriate length field
			resultlist = self.UpdateLengthField(field_size, field_pos, start, end + testcase_len, packet, order, datalist)
			datalist = resultlist 
		testcase_len = temp_len  
		x+=1
	x = 0
	result = ""
	while x < len (resultlist):
		result += resultlist[x]
		x+=1
	return result

    def	UpdateLengthField(self, field_size, field_pos, start, end, packet_num, byte_order, data):
    
    	# UpdateLengthField() - Updates a length field within a packet after fuzz data has been inserted

    	# field_size - The size of the length field in bytes (1, 2 or 4)
    	# field_pos - The index into the packet where the length field is situated
    	# start - the index of the first byte of those bytes to be counted
    	# end - the index of the last byte of those bytes to be counted 
    	# packet_num - the number of the packet containing the length field
	# byte_order - 0 = 00000001, 1 = 10000000
  
	length = 0
	hexlength = ""
	length_lst = []
	end+=1
	length = end - start
	if field_size == 1:
		if length > 255:
			print "Error - length field overflow"
			return
		hexlength = "%02x" % length
	elif field_size == 2:
		if length > 65535:
			print "Error - length field overflow"
			return
		hexlength = "%04x" % length
	elif field_size == 4:
		hexlength = "%08x" % length
	else:
		print "invalid length field"
		return
	if byte_order == 0:
		if len(hexlength) > 0:
			length_lst.append("%c" % int((hexlength[0] + hexlength[1]),16))
		if len(hexlength) > 3:
			length_lst.append("%c" % int((hexlength[2] + hexlength[3]),16))
		if len(hexlength) > 7:
			length_lst.append("%c" % int((hexlength[4] + hexlength[5]),16))
			length_lst.append("%c" % int((hexlength[6] + hexlength[7]),16))
	elif byte_order == 1:
		if len(hexlength) > 7:
			length_lst.append("%c" % int((hexlength[6] + hexlength[7]),16))
			length_lst.append("%c" % int((hexlength[4] + hexlength[5]),16))
		if len(hexlength) > 3:
			length_lst.append("%c" % int((hexlength[2] + hexlength[3]),16))
		if len(hexlength) > 0:
			length_lst.append("%c" % int((hexlength[0] + hexlength[1]),16))
	y = 0
	x = field_pos
	while x < field_pos+field_size:
		data[x] = length_lst[y]
		x+=1
		y+=1
	return data

    def CreateLengthConfWindow (self):
	win = wx.Frame(self, -1, "Add length field",size=(450,200), style=wx.FRAME_FLOAT_ON_PARENT | wx.CAPTION | wx.FRAME_TOOL_WINDOW)
	win.Center(wx.HORIZONTAL)
	win.Show(True)
	win.SetBackgroundColour("White")
	path = self.workingdir
	path = path + "\\..\\images\\zulu_logo16x16.png"
 	image = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap() 
	icon = wx.EmptyIcon() 
	icon.CopyFromBitmap(image) 
	win.SetIcon(icon) 
	return win

    def	AddLengthField (self):
	self.LengthEndian = 0
	if len(self.packets) == 0:
		return
	if self.fuzzer == "Network":
		tmp = self.packets[self.current_packet_number][0][1]
		if tmp == self.targetport:
			wx.MessageBox("Cannot add a length field to inbound data", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
			return
	endian = ["Big endian","Little endian"]
	self.OkLengthConf = False
	self.lengthconfwin = self.CreateLengthConfWindow()
	self.lengthconfwin.SetFocus()
	vs = wx.BoxSizer( wx.VERTICAL )
	box1_title = wx.StaticBox( self.lengthconfwin, -1, "" )
	box1 = wx.StaticBoxSizer( box1_title, wx.VERTICAL )
	grid1 = wx.FlexGridSizer( 0, 2, 0, 0 )
	self.conf_ctrls = []       
	text1 = wx.StaticText(self.lengthconfwin, -1, "Now highlight the bytes to be counted then click OK")	
	text2 = wx.StaticText(self.lengthconfwin, -1, "")
	text3 = wx.StaticText(self.lengthconfwin, -1, "Select byte order:")	
	cb_endian = wx.ComboBox(self.lengthconfwin, 600, "Big endian", wx.DefaultPosition, wx.DefaultSize, endian, wx.CB_DROPDOWN)
	grid1.Add( text1, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( text2, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( text3, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( cb_endian, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	box1.Add( grid1, 0, wx.ALIGN_CENTRE|wx.ALL, 5 )
	vs.Add( box1, 0, wx.ALIGN_CENTRE|wx.ALL, 5 )
	button = wx.Button(self.lengthconfwin, 1009, "OK")
	self.lengthconfwin.Bind(wx.EVT_BUTTON, self.OnOkLengthConf, button)
	vs.Add( button, 0, wx.ALIGN_CENTRE|wx.ALL, 5 )
	self.lengthconfwin.Bind(wx.EVT_TEXT, self.ConfEndian, cb_endian)
	self.lengthconfwin.SetSizer(vs)
	vs.Fit(self.lengthconfwin)
	while self.OkLengthConf == False:
		try:
			wx.Yield()
		except:
			pass

    def	ConfEndian (self, event):
	try:
		selected = event.GetString()
		if selected == "Big endian":
			self.LengthEndian = 0
		else:
			self.LengthEndian = 1
		self.session_changed = True
		self.mb.Enable(self.ID_Save_Session, True)
		self.tb.EnableTool(self.ID_toolSaveFile, True)
	except:
		pass

    def OnOkLengthConf (self, event):
	self.OkLengthConf = True
	field_size = (self.length_end+1) - self.length_start
	field_pos = self.length_start
	start = self.selection_start
	end = self.selection_end 
	packet_num = self.current_packet_number
	byte_order = self.LengthEndian
	length = end - start
	if length == 0 or self.length_start == self.selection_start:
		wx.MessageBox("No bytes selected", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
		self.lengthconfwin.Close()
		return
	if field_size == 1:
		if length > 255: 
			wx.MessageBox("Selected length too long for length field", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
			self.lengthconfwin.Close()
			return
	if field_size == 2:
		if length > 65535: 
			wx.MessageBox("Selected length too long for length field", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
			self.lengthconfwin.Close()
			return
	tmp = []
	tmp.append(field_size)
	tmp.append(field_pos)
	tmp.append(start)
	tmp.append(end)
	tmp.append(packet_num)
	tmp.append(byte_order)
	self.LengthFields.append(tmp)
	self.OutputPacketDetail(self.current_packet_number)
	self.UpdateDataModificationPoints()
	self.btn_ClearAllFuzzPoints.Enable(True)
	self.lengthconfwin.Close()

    def	EnableZuluScript(self,event):
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)
	if event.IsChecked() == 1:
		self.custom_script = True
		reload (custom)
		self.tc_output.AppendText("Status: ZuluScript enabled\n")
		self.tc_output.ShowPosition(self.tc_output.GetLastPosition()-1)
	else:
		self.custom_script = False
		self.tc_output.AppendText("Status: ZuluScript disabled\n")
		self.tc_output.ShowPosition(self.tc_output.GetLastPosition()-1)

    def	TC_BufferOverflow (self,evt):
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)
	if evt.IsChecked() == 1:
		self.buffer_overflow = True
		self.PopulateTestcases("buffer-overflows.txt")
		self.testcaseselected +=1
	else:
		self.RemoveTestcase("buffer-overflows")
		self.buffer_overflow = False
		self.testcaseselected -=1

    def	TC_FormatString (self,evt):
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)
	if evt.IsChecked() == 1:
		self.formatstring = True
		self.PopulateTestcases("format-strings.txt")
		self.testcaseselected +=1
	else:
		self.RemoveTestcase("format-strings")
		self.formatstring = False
		self.testcaseselected -=1

    def	TC_SingleByte (self,evt):
	self.session_changed = True
	self.tb.EnableTool(self.ID_toolSaveFile, True)
	self.mb.Enable(self.ID_Save_Session, True)
	if evt.IsChecked() == 1:
		self.singlebyte = True
		self.PopulateSingleByte()
		self.testcaseselected +=1
	else:
		self.RemoveTestcase("singlebyte")
		self.singlebyte = False
		self.testcaseselected -=1

    def PopulateSingleByte (self):
	x = 0
	datalist = []
	tmplist = []
	while x < 256:
		datalist.append("%c" % x)
		x+=1
	tmplist = ["singlebyte", datalist]
	self.fuzzer_testcases.append (tmplist)

    def	TC_DoubleByte (self,evt):
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)
	if evt.IsChecked() == 1:
		self.doublebyte = True
		self.PopulateDoubleByte()
		self.testcaseselected +=1
	else:
		self.RemoveTestcase("doublebyte")
		self.doublebyte = False
		self.testcaseselected -=1

    def PopulateDoubleByte (self):
	datalist = []
	tmplist = []
	datalist.append ("\x00\x00")
	datalist.append ("\x00\x01")
	datalist.append ("\x00\x7f")
	datalist.append ("\x00\x80")
	datalist.append ("\x00\xfe")
	datalist.append ("\x00\xff")
	datalist.append ("\x01\x00")
	datalist.append ("\x7f\x00")
	datalist.append ("\x80\x00")
	datalist.append ("\xfe\x00")
	datalist.append ("\xff\x00")
	datalist.append ("\xff\x01")
	datalist.append ("\xff\x7f")
	datalist.append ("\xff\x80")
	datalist.append ("\xff\xfe")
	datalist.append ("\x01\xff")
	datalist.append ("\x7f\xff")
	datalist.append ("\x80\xff")
	datalist.append ("\xfe\xff")	
	datalist.append ("\xff\xff")
	tmplist = ["doublebyte", datalist]
	self.fuzzer_testcases.append (tmplist)

    def TC_QuadByte (self,evt):
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)
	if evt.IsChecked() == 1:	
		self.quadbyte = True
		self.PopulateQuadByte()
		self.testcaseselected +=1
	else:
		self.RemoveTestcase("quadbyte")
		self.quadbyte = False
		self.testcaseselected -=1

    def PopulateQuadByte (self):
	datalist = []
	tmplist = []
	datalist.append ("\x00\x00\x00\x00")
	datalist.append ("\x00\x00\x00\x01")
	datalist.append ("\x00\x00\x00\x7f")
	datalist.append ("\x00\x00\x00\x80")
	datalist.append ("\x00\x00\x00\xfe")
	datalist.append ("\x00\x00\x00\xff")
	datalist.append ("\x01\x00\x00\x00")
	datalist.append ("\x7f\x00\x00\x00")
	datalist.append ("\x80\x00\x00\x00")
	datalist.append ("\xfe\x00\x00\x00")
	datalist.append ("\xff\x00\x00\x00")
	datalist.append ("\x00\x00\xff\x00")
	datalist.append ("\x00\x00\xff\x01")
	datalist.append ("\x00\x00\xff\x7f")
	datalist.append ("\x00\x00\xff\x80")
	datalist.append ("\x00\x00\xff\xfe")
	datalist.append ("\x00\x00\xff\xff")
	datalist.append ("\x00\xff\x00\x00")
	datalist.append ("\x01\xff\x00\x00")
	datalist.append ("\x7f\xff\x00\x00")
	datalist.append ("\x80\xff\x00\x00")
	datalist.append ("\xfe\xff\x00\x00")
	datalist.append ("\xff\xff\x00\x00")
	datalist.append ("\x00\xff\xff\x00")
	datalist.append ("\x00\xff\xff\x01")
	datalist.append ("\x00\xff\xff\x7f")
	datalist.append ("\x00\xff\xff\x80")
	datalist.append ("\x00\xff\xff\xfe")
	datalist.append ("\x00\xff\xff\xff")
	datalist.append ("\x00\xff\xff\x00")
	datalist.append ("\x01\xff\xff\x00")
	datalist.append ("\x7f\xff\xff\x00")
	datalist.append ("\x80\xff\xff\x00")
	datalist.append ("\xfe\xff\xff\x00")
	datalist.append ("\xff\xff\xff\x00")
	datalist.append ("\xff\xff\xff\x00")
	datalist.append ("\xff\xff\xff\x01")
	datalist.append ("\xff\xff\xff\x7f")
	datalist.append ("\xff\xff\xff\x80")
	datalist.append ("\xff\xff\xff\xfe")
	datalist.append ("\xff\xff\xff\xff")
	tmplist = ["quadbyte", datalist]
	self.fuzzer_testcases.append (tmplist)

    def TC_null (self,evt):
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)
	if evt.IsChecked() == 1:
		self.nullcase = True
		self.PopulateTestcases("null.txt")
		self.testcaseselected +=1
	else:
		self.RemoveTestcase("null")
		self.nullcase = False
		self.testcaseselected -=1

    def TC_CommandUnix (self,evt):
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)
	if evt.IsChecked() == 1:
		self.unixcase = True
		self.PopulateTestcases("command-execution-unix.txt")
		self.testcaseselected +=1
	else:
		self.RemoveTestcase("command-execution-unix")
		self.unixcase = False
		self.testcaseselected -=1

    def	TC_CommandWindows (self,evt):
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)
	if evt.IsChecked() == 1:
		self.windowscase = True
		self.PopulateTestcases("command-inject-windows.txt")
		self.testcaseselected +=1
	else:
		self.RemoveTestcase("command-inject-windows")
		self.windowscase = False
		self.testcaseselected -=1

    def TC_Xml (self,evt):
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)
	if evt.IsChecked() == 1:
		self.xmlcase = True
		self.PopulateTestcases("xml-attacks.txt")
		self.testcaseselected +=1
	else:
		self.RemoveTestcase("xml-attacks")
		self.xmlcase = False
		self.testcaseselected -=1

    def	TC_UserDefined (self,evt):
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)
	if evt.IsChecked() == 1:
		self.userdefined = True
		self.PopulateTestcases("user-defined.txt")
		self.testcaseselected +=1
	else:
		self.RemoveTestcase("user-defined")
		self.userdefined = False
		self.testcaseselected -=1

    def	TC_Control (self,evt):
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)
	if evt.IsChecked() == 1:
		self.controlcase = True
		self.PopulateControl()
		self.testcaseselected +=1
	else:
		self.RemoveTestcase("control")
		self.controlcase = False
		self.testcaseselected -=1

    def PopulateControl (self):
	x = 80
	datalist = []
	tmplist = []
	while x < 256:	
		datalist.append("%c" % x)
		x+=1
	tmplist = ["control", datalist]
	self.fuzzer_testcases.append (tmplist)

    def	TC_Extended (self,evt):
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)
	if evt.IsChecked() == 1:
		self.extendedcase = True
		self.PopulateExtended()	
		self.testcaseselected +=1	
	else:
		self.RemoveTestcase("extended")
		self.extendedcase = False
		self.testcaseselected -=1

    def PopulateExtended (self):
	x = 0
	datalist = []
	tmplist = []
	while x < 32:	
		datalist.append("%c" % x)
		x+=1
	tmplist = ["extended", datalist]
	self.fuzzer_testcases.append (tmplist)

    def	TC_BitByte (self,evt):
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)
	if evt.IsChecked() == 1:
		self.bitbyte = True
		self.PopulateBitByte()
		self.testcaseselected +=1
	else:
		self.RemoveTestcase("bitbyte")
		self.bitbyte = False
		self.testcaseselected -=1

    def PopulateBitByte (self):
	datalist = []
	tmplist = []
	datalist.append ("%c" % int('00000000',2))
	datalist.append ("%c" % int('00000001',2))
	datalist.append ("%c" % int('00000010',2))
	datalist.append ("%c" % int('00000100',2))
	datalist.append ("%c" % int('00001000',2))
	datalist.append ("%c" % int('00010000',2))
	datalist.append ("%c" % int('00100000',2))
	datalist.append ("%c" % int('01000000',2))
	datalist.append ("%c" % int('10000000',2))
	tmplist = ["bitbyte", datalist]
	self.fuzzer_testcases.append (tmplist)

    def	TC_BitWord (self,evt):
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)
	if evt.IsChecked() == 1:
		self.bitword = True
		self.PopulateBitWord()
		self.testcaseselected +=1
	else:
		self.RemoveTestcase("bitword")
		self.bitword = False
		self.testcaseselected -=1

    def PopulateBitWord (self):
	datalist = []
	tmplist = []
	datalist.append ("\x00" + "%c" % int('00000001',2))
	datalist.append ("\x00" + "%c" % int('00000010',2))
	datalist.append ("\x00" + "%c" % int('00000100',2))
	datalist.append ("\x00" + "%c" % int('00001000',2))
	datalist.append ("\x00" + "%c" % int('00010000',2))
	datalist.append ("\x00" + "%c" % int('00100000',2))
	datalist.append ("\x00" + "%c" % int('01000000',2))
	datalist.append ("\x00" + "%c" % int('10000000',2))
	datalist.append ("%c" % int('00000001',2) + "\x00")
	datalist.append ("%c" % int('00000010',2) + "\x00")
	datalist.append ("%c" % int('00000100',2) + "\x00")
	datalist.append ("%c" % int('00001000',2) + "\x00")
	datalist.append ("%c" % int('00010000',2) + "\x00")
	datalist.append ("%c" % int('00100000',2) + "\x00")
	datalist.append ("%c" % int('01000000',2) + "\x00")
	datalist.append ("%c" % int('10000000',2) + "\x00")
	tmplist = ["bitword", datalist]
	self.fuzzer_testcases.append (tmplist)

    def	TC_BitLong (self,evt):
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)
	if evt.IsChecked() == 1:
		self.bitlong = True
		self.PopulateBitLong()
		self.testcaseselected +=1
	else:
		self.RemoveTestcase("bitlong")
		self.bitlong = False
		self.testcaseselected -=1

    def PopulateBitLong (self):
	datalist = []
	tmplist = []
	datalist.append ("\x00\x00\x00" + "%c" % int('00000001',2))
	datalist.append ("\x00\x00\x00" + "%c" % int('00000010',2))
	datalist.append ("\x00\x00\x00" + "%c" % int('00000100',2))
	datalist.append ("\x00\x00\x00" + "%c" % int('00001000',2))
	datalist.append ("\x00\x00\x00" + "%c" % int('00010000',2))
	datalist.append ("\x00\x00\x00" + "%c" % int('00100000',2))
	datalist.append ("\x00\x00\x00" + "%c" % int('01000000',2))
	datalist.append ("\x00\x00\x00" + "%c" % int('10000000',2))
	datalist.append ("\x00\x00" + "%c" % int('00000001',2) + "\x00")
	datalist.append ("\x00\x00" + "%c" % int('00000010',2) + "\x00")
	datalist.append ("\x00\x00" + "%c" % int('00000100',2) + "\x00")
	datalist.append ("\x00\x00" + "%c" % int('00001000',2) + "\x00")
	datalist.append ("\x00\x00" + "%c" % int('00010000',2) + "\x00")
	datalist.append ("\x00\x00" + "%c" % int('00100000',2) + "\x00")
	datalist.append ("\x00\x00" + "%c" % int('01000000',2) + "\x00")
	datalist.append ("\x00\x00" + "%c" % int('10000000',2) + "\x00")
	datalist.append ("\x00" + "%c" % int('00000001',2) + "\x00\x00")
	datalist.append ("\x00" + "%c" % int('00000010',2) + "\x00\x00")
	datalist.append ("\x00" + "%c" % int('00000100',2) + "\x00\x00")
	datalist.append ("\x00" + "%c" % int('00001000',2) + "\x00\x00")
	datalist.append ("\x00" + "%c" % int('00010000',2) + "\x00\x00")
	datalist.append ("\x00" + "%c" % int('00100000',2) + "\x00\x00")
	datalist.append ("\x00" + "%c" % int('01000000',2) + "\x00\x00")
	datalist.append ("\x00" + "%c" % int('10000000',2) + "\x00\x00")
	datalist.append ("%c" % int('00000001',2) + "\x00\x00\x00")
	datalist.append ("%c" % int('00000010',2) + "\x00\x00\x00")
	datalist.append ("%c" % int('00000100',2) + "\x00\x00\x00")
	datalist.append ("%c" % int('00001000',2) + "\x00\x00\x00")
	datalist.append ("%c" % int('00010000',2) + "\x00\x00\x00")
	datalist.append ("%c" % int('00100000',2) + "\x00\x00\x00")
	datalist.append ("%c" % int('01000000',2) + "\x00\x00\x00")
	datalist.append ("%c" % int('10000000',2) + "\x00\x00\x00")
	tmplist = ["bitlong", datalist]
	self.fuzzer_testcases.append (tmplist)

    def	TC_BitByteInv (self,evt):
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)
	if evt.IsChecked() == 1:
		self.bitbyteinv = True
		self.PopulateBitByteInv()
		self.testcaseselected +=1
	else:
		self.RemoveTestcase("bitbyteinv")
		self.bitbyteinv = False
		self.testcaseselected -=1

    def PopulateBitByteInv (self):
	datalist = []
	tmplist = []
	datalist.append ("%c" % int('11111110',2))
	datalist.append ("%c" % int('11111101',2))
	datalist.append ("%c" % int('11111011',2))
	datalist.append ("%c" % int('11110111',2))
	datalist.append ("%c" % int('11101111',2))
	datalist.append ("%c" % int('11011111',2))
	datalist.append ("%c" % int('10111111',2))
	datalist.append ("%c" % int('01111111',2))
	tmplist = ["bitbyteinv", datalist]
	self.fuzzer_testcases.append (tmplist)

    def	TC_BitWordInv (self,evt):
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)
	if evt.IsChecked() == 1:
		self.bitwordinv = True
		self.PopulateBitWordInv()
		self.testcaseselected +=1
	else:
		self.RemoveTestcase("bitwordinv")
		self.bitwordinv = False
		self.testcaseselected -=1

    def PopulateBitWordInv (self):
	datalist = []
	tmplist = []
	datalist.append ("\xff" + "%c" % int('11111110',2))
	datalist.append ("\xff" + "%c" % int('11111101',2))
	datalist.append ("\xff" + "%c" % int('11111011',2))
	datalist.append ("\xff" + "%c" % int('11110111',2))
	datalist.append ("\xff" + "%c" % int('11101111',2))
	datalist.append ("\xff" + "%c" % int('11011111',2))
	datalist.append ("\xff" + "%c" % int('10111111',2))
	datalist.append ("\xff" + "%c" % int('01111111',2))
	datalist.append ("%c" % int('11111110',2) + "\xff")
	datalist.append ("%c" % int('11111101',2) + "\xff")
	datalist.append ("%c" % int('11111011',2) + "\xff")
	datalist.append ("%c" % int('11110111',2) + "\xff")
	datalist.append ("%c" % int('11101111',2) + "\xff")
	datalist.append ("%c" % int('11011111',2) + "\xff")
	datalist.append ("%c" % int('10111111',2) + "\xff")
	datalist.append ("%c" % int('01111111',2) + "\xff")
	tmplist = ["bitwordinv", datalist]
	self.fuzzer_testcases.append (tmplist)

    def	TC_BitLongInv (self,evt):
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)
	if evt.IsChecked() == 1:
		self.bitlonginv = True
		self.PopulateBitLongInv()
		self.testcaseselected +=1
	else:
		self.RemoveTestcase("bitlonginv")
		self.bitlonginv = False
		self.testcaseselected -=1

    def PopulateBitLongInv (self):
	datalist = []
	tmplist = []
	datalist.append ("\xff\xff\xff" + "%c" % int('11111110',2))
	datalist.append ("\xff\xff\xff" + "%c" % int('11111101',2))
	datalist.append ("\xff\xff\xff" + "%c" % int('11111011',2))
	datalist.append ("\xff\xff\xff" + "%c" % int('11110111',2))
	datalist.append ("\xff\xff\xff" + "%c" % int('11101111',2))
	datalist.append ("\xff\xff\xff" + "%c" % int('11011111',2))
	datalist.append ("\xff\xff\xff" + "%c" % int('10111111',2))
	datalist.append ("\xff\xff\xff" + "%c" % int('01111111',2))
	datalist.append ("\xff\xff" + "%c" % int('11111110',2) + "\xff")
	datalist.append ("\xff\xff" + "%c" % int('11111101',2) + "\xff")
	datalist.append ("\xff\xff" + "%c" % int('11111011',2) + "\xff")
	datalist.append ("\xff\xff" + "%c" % int('11110111',2) + "\xff")
	datalist.append ("\xff\xff" + "%c" % int('11101111',2) + "\xff")
	datalist.append ("\xff\xff" + "%c" % int('11011111',2) + "\xff")
	datalist.append ("\xff\xff" + "%c" % int('10111111',2) + "\xff")
	datalist.append ("\xff\xff" + "%c" % int('01111111',2) + "\xff")
	datalist.append ("\xff" + "%c" % int('11111110',2) + "\xff\xff")
	datalist.append ("\xff" + "%c" % int('11111101',2) + "\xff\xff")
	datalist.append ("\xff" + "%c" % int('11111011',2) + "\xff\xff")
	datalist.append ("\xff" + "%c" % int('11110111',2) + "\xff\xff")
	datalist.append ("\xff" + "%c" % int('11101111',2) + "\xff\xff")
	datalist.append ("\xff" + "%c" % int('11011111',2) + "\xff\xff")
	datalist.append ("\xff" + "%c" % int('10111111',2) + "\xff\xff")
	datalist.append ("\xff" + "%c" % int('01111111',2) + "\xff\xff")
	datalist.append ("%c" % int('11111110',2) + "\xff\xff\xff")
	datalist.append ("%c" % int('11111101',2) + "\xff\xff\xff")
	datalist.append ("%c" % int('11111011',2) + "\xff\xff\xff")
	datalist.append ("%c" % int('11110111',2) + "\xff\xff\xff")
	datalist.append ("%c" % int('11101111',2) + "\xff\xff\xff")
	datalist.append ("%c" % int('11011111',2) + "\xff\xff\xff")
	datalist.append ("%c" % int('10111111',2) + "\xff\xff\xff")
	datalist.append ("%c" % int('01111111',2) + "\xff\xff\xff")
	tmplist = ["bitlonginv", datalist]
	self.fuzzer_testcases.append (tmplist)

    def PopulateTestcases (self, filename):
	data = ""
	tmp = ""
	datalist = []
	tmplist = []
	path = self.workingdir
	path = path + "\\..\\fuzzdb\\" + filename
	error = "Error opening testcase file %s" % filename 
	try:
		fp = file(path, 'rb')	# open file for reading
	except:
		wx.MessageBox(error, style=wx.OK|wx.ICON_ERROR, parent=self)
	data = fp.read()
	datalist = data.split('\n')
	x = 0
	while x < len(datalist):
		tmp = datalist[x]
		datalist[x] = string.replace(tmp, "\r", "")
		x+=1
	x = 0
	while x < len(datalist):
		tmp = datalist[x]
		if tmp[0] == "#" and tmp[1] == "#":
			datalist.pop(x)
			x-=1
		x+=1
	filename = filename[:-4]
	tmplist = [filename,datalist]
	self.fuzzer_testcases.append(tmplist)
	fp.close

    def	RemoveTestcase(self, filename):
	x = 0
	while x < len (self.fuzzer_testcases):
		if self.fuzzer_testcases[x][0] == filename:
			self.fuzzer_testcases.pop(x)
		x+=1

    def	StartFuzzing(self,evt):
	if self.fuzzing_paused == True:
		self.fuzzing_paused = False
		self.tc_output.AppendText("Status: Fuzzing restarted\n")
		self.tc_output.ShowPosition(self.tc_output.GetLastPosition()-1)
		self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
		self.fplog.write("Status: Fuzzing restarted\n")
		self.tb.EnableTool(self.ID_toolFuzzerPause, True)
		self.mb.Enable(self.ID_Pause_Fuzzing, True)
		self.tb.EnableTool(self.ID_toolFuzzerStart, False)
		self.mb.Enable(self.ID_Start_Fuzzing, False)
		return
	if self.fuzzing == True:
		return
	if len(self.fuzzer_testcases) == 0:
		wx.MessageBox("Cannot start fuzzer: no mutators selected", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
		return
	self.Showalert == False
	self.bmCrash.Hide()
	self.tb.EnableTool(self.ID_toolFuzzerStart, False)
	self.mb.Enable(self.ID_Start_Fuzzing, False)
	self.tb.EnableTool(self.ID_toolFuzzerPause, True)
	self.tb.EnableTool(self.ID_toolFuzzerStop, True)
	self.mb.Enable(self.ID_Pause_Fuzzing, True)
	self.mb.Enable(self.ID_Stop_Fuzzing, True)
	self.mb.Enable(self.ID_Open_Session, False)
	self.mb.Enable(self.ID_Save_Session, False)
	self.mb.Enable(self.ID_Configure_Logfile, False)
	self.mb.Enable(self.ID_Configure_Proxy, False)
	self.mb.Enable(self.ID_Configure_Email, False)
	self.mb.Enable(self.ID_Configure_VMware, False)
	self.mb.Enable(self.ID_Start_Capture, False)
	self.mb.Enable(self.ID_Import_PCAP, False)
	self.mb.Enable(self.ID_Import_File, False)
	self.mb.Enable(self.ID_Network_Fuzzer, False)
	self.mb.Enable(self.ID_File_Fuzzer, False)
	self.mb.Enable(self.ID_Import_USB, False)
	self.mb.Enable(self.ID_USB_Fuzzer, False)
	self.mb.Enable(self.ID_Serial_Fuzzer, False)
	self.mb.Enable(self.ID_Start_Serial_Capture, False)
	self.tb.EnableTool(self.ID_toolConfigure, False)
	self.tb.EnableTool(self.ID_toolOpenFile, False)
	self.tb.EnableTool(self.ID_toolSaveFile, False)
	self.tb.EnableTool(self.ID_toolProxyStart, False)
	self.tb.EnableTool(self.ID_toolFindNext, False)
	self.cb_overflow.Enable(False) 
	self.cb_format.Enable(False)
	self.cb_single_byte.Enable(False)
	self.cb_double_byte.Enable(False)
	self.cb_quad_byte.Enable(False)
	self.cb_null.Enable(False)
	self.cb_commandu.Enable(False)
	self.cb_commandw.Enable(False)
	self.cb_xml.Enable(False)
	self.cb_control.Enable(False)
	self.cb_extended.Enable(False)
	self.cb_userdefined.Enable(False)
	self.cb_bitbyte.Enable(False)
	self.cb_bitword.Enable(False)
	self.cb_bitlong.Enable(False)
	self.cb_bitbyteinv.Enable(False)
	self.cb_bitwordinv.Enable(False)
	self.cb_bitlonginv.Enable(False)
	self.cb_zuluscript.Enable(False)
	self.cb_wireshark.Enable(False)
	self.cb_vmware.Enable(False)
	self.btn_SendUnchanged.Enable(False)
	self.btn_PacketTest.Enable(False)
	self.btn_ClearAllFuzzPoints.Enable(False)
	self.btn_AddAllBytes.Enable(False)
	self.btn_AddAllDoubleBytes.Enable(False)
	self.btn_AddAllQuadBytes.Enable(False)
	self.cbDoubleOffset.Enable(False)
	self.cbQuadOffset.Enable(False)
	self.tc_output.SetBackgroundColour("WHITE")
	f = wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL)
	self.tc_output.SetDefaultStyle(wx.TextAttr((0,0,80), wx.NullColour, f))
	if self.Showalert == True:
		self.bmCrash.Hide()
	buffer = ""
	total_fuzz_points = 0
	y = 0
	fuzzer_state = []
	temp_list = []
	tmp_list = []
	packet_data_list = []
	self.all_fuzzer_testcases = []
	self.all_fuzzer_testcase_names = []

	x = 0
	y = 0
	while x < len(self.fuzzer_testcases):
		tmplist = self.fuzzer_testcases[x][1]
		tmplist1 = self.fuzzer_testcases[x][0]
		y = 0
		while y < len (tmplist):
			self.all_fuzzer_testcases.append(tmplist[y])
			self.all_fuzzer_testcase_names.append(tmplist1)
			y+=1
		x+=1
	x = 0
	while x < len (self.packets_to_send):
		y = self.packets_to_send[x][1][0]
		if y != -1:
			total_fuzz_points+=1
			temp_list = [self.packets_to_send[x][0],self.packets_to_send[x][1][0], self.packets_to_send[x][1][1]]
			fuzzer_state.append(temp_list)
		x+=1
		
	self.fuzzcases = total_fuzz_points * len(self.all_fuzzer_testcases)
	out = "Number of fuzzcases = %d, do you want to start fuzzing?" % self.fuzzcases
	
	dlg = wx.MessageDialog(self,out,'Zulu Fuzzer', style=wx.YES | wx.NO | wx.ICON_INFORMATION)        
	val = dlg.ShowModal()
	if val == wx.ID_YES:
		dlg.Destroy() 
		pass
	if val == wx.ID_NO:
		dlg.Destroy()
		self.fuzzing = True
		self.StopFuzzing(1)
		return
		
	print "-----------------------------------------------------"
	print "New fuzzing session"
	print "-----------------------------------------------------"
	print	
	self.fuzzing = True
	self.tc_output.AppendText("Status: Fuzzing started\n")
	self.tc_output.ShowPosition(self.tc_output.GetLastPosition()-1)
	self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
	self.fplog.write("Status: Fuzzing started\n")
	
	if self.fuzzcases == 0:
		wx.MessageBox("Cannot start fuzzer: no mutators selected", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
		return
	out = "Total fuzzcases = %d\n" % self.fuzzcases
	print out
	self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
	self.fplog.write(out)
	self.tc_output.AppendText(out)
	self.tc_output.ShowPosition(self.tc_output.GetLastPosition()-1)
	current_fuzzcase = 0
	fuzzer_testcase_names_count = 0
	current_testcase_name = ""
	fuzz_points = 0
	while (fuzz_points < total_fuzz_points):
		fuzzer_testcase_names_count = 0
		current_testcase_name = ""
		current_fuzzpoint = fuzzer_state[fuzz_points]
		fuzz_iterations = 0 #these are fuzz testcases
		while fuzz_iterations < len(self.all_fuzzer_testcases):
			#-----------------make changes to fuzz points here---------------------
			testcase = self.all_fuzzer_testcases[fuzz_iterations]
			x = 0
			temp_list = []
			packet_data_list = []
			while x < len (self.packets_to_send):
				packetnum = self.packets_to_send[x][0]
				temp_list = [packetnum, self.packets[packetnum][1]]
				packet_data_list.append(temp_list)
				x+=1
			# packet_data_list now contains all the original packets (from packets[] list), selected in self.packets_to_send[]
			# current_fuzzpoint contains a list entry of [packet num, start, end]
			fuzz_packet_number = current_fuzzpoint[0]
			fuzz_packet_start = current_fuzzpoint[1]
			fuzz_packet_end = current_fuzzpoint[2]
			fuzz_packet_data = ""
			temp_fuzz_packet = ""
			x = 0
			while x < len (packet_data_list):
				if packet_data_list[x][0] == fuzz_packet_number:
					fuzz_packet_data = packet_data_list[x][1]	
				x+=1
			# fuzz_packet_data contains the data packet for the current fuzzpoint
			# testcase = current fuzz testcase 
			x = 0
			while x < fuzz_packet_start:
				temp_fuzz_packet += fuzz_packet_data[x]
				x+=1
			temp_fuzz_packet += testcase		# insert current fuzzer testcase into packet
			x = fuzz_packet_end+1
			while x < len (fuzz_packet_data):
				temp_fuzz_packet += fuzz_packet_data[x]
				x+=1
			# temp_fuzz_packet now contains the modified packet
			x = 0
			while x < len (packet_data_list):
				if (packet_data_list[x][0] == fuzz_packet_number):
					packet_data_list[x][1] = temp_fuzz_packet
				x+=1
			packet_data_list = self.uniq(packet_data_list)
			#-------------------------------------------------------------------------------------	
			# packet_data_list now contains all the original packets, including the updated packet
			#-------------------------------------------------------------------------------------
			x = 0
			while x < len (packet_data_list):
				data = packet_data_list[x][1]
				#---------------------------------------------------------------------------
				if self.custom_script == True:
					self.packets_selected_to_send = packet_data_list
					self.all_packets_captured = self.packets
					self.modified_data = []
					y = 0
					while y < len(data):	
						self.modified_data.append(data[y])
						y+=1
					self.current_packet_number = x
					#-------------------------------------------------------------------
					script = custom.ZuluScript(self)
					#-------------------------------------------------------------------
					packet_data_list = self.packets_selected_to_send
					self.packets = self.all_packets_captured
					data = ""
					y = 0
					while y < len (self.modified_data):
						data += self.modified_data[y]
						y+=1
				#------ Update length fields -------------------------------------------------
				if len(self.LengthFields) > 0:
					fuzzpoint_size = fuzz_packet_end - fuzz_packet_start + 1
					additional_bytes = len(testcase) - fuzzpoint_size 
					packetnumber = self.packets_to_send[x][0]
					modified_data = self.IncludeLengthField(packetnumber, data, additional_bytes,fuzz_packet_start, fuzz_packet_end)	# if a length field has been selected, update it here
					if modified_data != "":
						data = modified_data
					packet_data_list[x][1] = data 
				x+=1
			#----------------------------------------------------------------------------------------	
			# packet_data_list now contains the updated packets based on zuluscript and length fields
			#----------------------------------------------------------------------------------------
			if self.all_fuzzer_testcase_names[fuzz_iterations] == current_testcase_name:
				fuzzer_testcase_names_count += 1
			else:
				fuzzer_testcase_names_count = 0
			out = "Fuzzpoint %d/%d, " % (fuzz_points,total_fuzz_points-1)
			out = out + "Testcase %d/%d " % (fuzz_iterations, len(self.all_fuzzer_testcases)-1)
			self.statusbar.SetStatusText(out, 3)
			out = out + "Test type: %s" % self.all_fuzzer_testcase_names[fuzz_iterations]
			out = out + ", Test #%d" % fuzzer_testcase_names_count
			print "---------------------------------------------------------------------------------"
			print out
			print "---------------------------------------------------------------------------------"
			print
			out = out + "\n"
			self.fplog.write ("\n")
			self.fplog.write ("-----------------------------------------------------------------------------------\n")
			self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
			self.fplog.write(out)
			self.fplog.write ("-----------------------------------------------------------------------------------\n\n")
			current_testcase_name = self.all_fuzzer_testcase_names[fuzz_iterations]
			#-----------------------------------------------------------
			# Call fuzzing module here
			#-----------------------------------------------------------
			if self.fuzzer == "Network":
				err = self.network_fuzzer(packet_data_list)
				if err == 1:
					self.StopFuzzing(1)
			if self.fuzzer == "USB":
				err = self.usb_fuzzer(packet_data_list)
				if err == 1:
					self.StopFuzzing(1)
			if self.fuzzer == "File":
				err = self.file_fuzzer(packet_data_list)
				if err == 1:
					self.StopFuzzing(1)
			if self.fuzzer == "Serial":
				err = self.serial_fuzzer(packet_data_list)
				if err == 1:
					self.StopFuzzing(1)
			#-----------------------------------------------------------
			if self.fuzzing == False:
				return
			fuzz_iterations +=1
			current_fuzzcase +=1
			sleep_time = 0
			while sleep_time < self.fuzz_delay:
				time.sleep(0.1)
				wx.Yield()
				sleep_time+=0.1
		fuzz_points +=1

	self.tc_output.AppendText("Status: Fuzzing complete\n")
	self.tc_output.ShowPosition(self.tc_output.GetLastPosition()-1)
	self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
	self.fplog.write("Status: Fuzzing complete\n")
	self.fuzzing = False
	self.tb.EnableTool(self.ID_toolFuzzerStart, True)
	self.mb.Enable(self.ID_Start_Fuzzing, True)
	self.tb.EnableTool(self.ID_toolFuzzerPause, False)
	self.tb.EnableTool(self.ID_toolFuzzerStop, False)
	self.mb.Enable(self.ID_Pause_Fuzzing, False)
	self.mb.Enable(self.ID_Stop_Fuzzing, False)
	self.mb.Enable(self.ID_Open_Session, True)
	self.mb.Enable(self.ID_Save_Session, True)
	self.mb.Enable(self.ID_Configure_Logfile, True)
	self.mb.Enable(self.ID_Configure_Proxy, True)
	self.mb.Enable(self.ID_Configure_Email, True)
	self.mb.Enable(self.ID_Configure_VMware, True)
	self.mb.Enable(self.ID_Start_Capture, True)
	self.mb.Enable(self.ID_Import_PCAP, True)
	self.mb.Enable(self.ID_Import_File, True)
	self.mb.Enable(self.ID_Network_Fuzzer, True)
	self.mb.Enable(self.ID_File_Fuzzer, True)
	self.tb.EnableTool(self.ID_toolConfigure, True)
	self.tb.EnableTool(self.ID_toolOpenFile, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)
	self.tb.EnableTool(self.ID_toolProxyStart, True)
	self.tb.EnableTool(self.ID_toolFindNext, True)
	self.cb_overflow.Enable(True) 
	self.cb_format.Enable(True)
	self.cb_single_byte.Enable(True)
	self.cb_double_byte.Enable(True)
	self.cb_quad_byte.Enable(True)
	self.cb_null.Enable(True)
	self.cb_commandu.Enable(True)
	self.cb_commandw.Enable(True)
	self.cb_xml.Enable(True)
	self.cb_control.Enable(True)
	self.cb_extended.Enable(True)
	self.cb_userdefined.Enable(True)
	self.cb_bitbyte.Enable(True)
	self.cb_bitword.Enable(True)
	self.cb_bitlong.Enable(True)
	self.cb_bitbyteinv.Enable(True)
	self.cb_bitwordinv.Enable(True)
	self.cb_bitlonginv.Enable(True)
	self.cb_zuluscript.Enable(True)
	self.cb_wireshark.Enable(True)
	self.cb_vmware.Enable(True)
	self.btn_SendUnchanged.Enable(True)
	self.btn_ClearAllFuzzPoints.Enable(True)
	self.btn_AddAllBytes.Enable(True)
	self.btn_AddAllDoubleBytes.Enable(True)
	self.btn_AddAllQuadBytes.Enable(True)
	self.cbDoubleOffset.Enable(True)
	self.cbQuadOffset.Enable(True)
	return

    def	PauseFuzzing(self,evt):
	if self.fuzzing_paused == True:
		return
	self.fuzzing_paused = True
	self.tb.EnableTool(self.ID_toolFuzzerStart, True)
	self.mb.Enable(self.ID_Start_Fuzzing, True)
	self.tb.EnableTool(self.ID_toolFuzzerPause, False)
	self.tb.EnableTool(self.ID_toolFuzzerStop, True)
	self.mb.Enable(self.ID_Pause_Fuzzing, False)
	self.mb.Enable(self.ID_Stop_Fuzzing, True)
	self.statusbar.SetStatusText("Status: Fuzzing paused", 3)
	self.tc_output.AppendText("Status: Fuzzing paused\n")
	self.tc_output.ShowPosition(self.tc_output.GetLastPosition()-1)
	self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
	self.fplog.write("Status: Fuzzing paused\n")

    def	StopFuzzing(self,evt):
	if self.fuzzing_paused == True:
		self.fuzzing_paused = False
	if self.fuzzing == False:
		return
	self.fuzzing = False
	self.tb.EnableTool(self.ID_toolFuzzerStart, True)
	self.mb.Enable(self.ID_Start_Fuzzing, True)
	self.tb.EnableTool(self.ID_toolFuzzerPause, False)
	self.tb.EnableTool(self.ID_toolFuzzerStop, False)
	self.mb.Enable(self.ID_Pause_Fuzzing, False)
	self.mb.Enable(self.ID_Stop_Fuzzing, False)
	self.mb.Enable(self.ID_Open_Session, True)
	self.mb.Enable(self.ID_Save_Session, True)
	self.mb.Enable(self.ID_Configure_Logfile, True)
	self.mb.Enable(self.ID_Configure_Proxy, True)
	self.mb.Enable(self.ID_Configure_Email, True)
	self.mb.Enable(self.ID_Configure_VMware, True)
	self.mb.Enable(self.ID_Start_Capture, True)
	self.mb.Enable(self.ID_Import_PCAP, True)
	self.mb.Enable(self.ID_Import_File, True)
	self.mb.Enable(self.ID_Network_Fuzzer, True)
	self.mb.Enable(self.ID_File_Fuzzer, True)
	self.mb.Enable(self.ID_Import_USB, True)
	self.mb.Enable(self.ID_USB_Fuzzer, True)
	self.mb.Enable(self.ID_Serial_Fuzzer, True)
	self.mb.Enable(self.ID_Start_Serial_Capture, True)
	self.tb.EnableTool(self.ID_toolConfigure, True)
	self.tb.EnableTool(self.ID_toolOpenFile, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)
	self.tb.EnableTool(self.ID_toolProxyStart, True)
	self.tb.EnableTool(self.ID_toolFindNext, True)
	self.cb_overflow.Enable(True) 
	self.cb_format.Enable(True)
	self.cb_single_byte.Enable(True)
	self.cb_double_byte.Enable(True)
	self.cb_quad_byte.Enable(True)
	self.cb_null.Enable(True)
	self.cb_commandu.Enable(True)
	self.cb_commandw.Enable(True)
	self.cb_xml.Enable(True)
	self.cb_control.Enable(True)
	self.cb_extended.Enable(True)
	self.cb_userdefined.Enable(True)
	self.cb_bitbyte.Enable(True)
	self.cb_bitword.Enable(True)
	self.cb_bitlong.Enable(True)
	self.cb_bitbyteinv.Enable(True)
	self.cb_bitwordinv.Enable(True)
	self.cb_bitlonginv.Enable(True)
	self.cb_zuluscript.Enable(True)
	self.cb_wireshark.Enable(True)
	self.cb_vmware.Enable(True)
	self.btn_PacketTest.Enable(True)
	self.btn_SendUnchanged.Enable(True)
	self.btn_ClearAllFuzzPoints.Enable(True)
	self.btn_AddAllBytes.Enable(True)
	self.btn_AddAllDoubleBytes.Enable(True)
	self.btn_AddAllQuadBytes.Enable(True)
	self.cbDoubleOffset.Enable(True)
	self.cbQuadOffset.Enable(True)
	self.statusbar.SetStatusText("Status: Idle", 3)
	self.tc_output.AppendText("Status: Fuzzing stopped\n")
	self.tc_output.ShowPosition(self.tc_output.GetLastPosition()-1)
	self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
	self.fplog.write("Status: Fuzzing stopped\n")

    def	AddPacket(self,evt):
	if len(self.packets) == 0:
		return
	tmp = self.packets[self.current_packet_number][0][1]
	if tmp == self.targetport:
		wx.MessageBox("Cannot select inbound packets", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
		return
	y = 0
	if (self.capture_data == False):
		return
	x = 0
	while x < len (self.packets_to_send):
		if self.packets_to_send[x][0] == self.current_packet_number and self.packets_to_send[x][1][0] != -1:
			wx.MessageBox("Fuzzpoint already been selected on packet", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
			return
		x+=1
	try:
		tmp_list = [self.current_packet_number,[-1,-1]]
		y = self.packets_to_send.index(tmp_list)
	except:
		y = -1
	if y == -1:
		tmp_list = [self.current_packet_number, [-1, -1]] 
		self.packets_to_send.append (tmp_list)
		self.total_unique_packets +=1
		loc = self.current_packet_number * 30
		self.tc_packetlist.SetStyle(loc, loc+28, wx.TextAttr("WHITE", (0,150,0)))
	else:
		del self.packets_to_send[y]	
		self.total_unique_packets -=1
		loc = self.current_packet_number * 30
		self.tc_packetlist.SetStyle(loc, loc+28, wx.TextAttr("WHITE", (69,109,228)))
	self.btn_ClearAllFuzzPoints.Enable(True)
	self.UpdateDataModificationPoints()

    def	ClearAllFuzzPoints(self,evt):
	if (self.capture_data == False):
		return
	self.tb.EnableTool(self.ID_toolFuzzerStart, False)
	self.mb.Enable(self.ID_Start_Fuzzing, False)
	self.tc_fuzzpoints.Clear()
	self.all_bytes_selected = []
	self.LengthFields = []
	self.packets_to_send = []
	self.total_unique_packets = 0
	loc = self.current_packet_number * 30
	self.tc_packetlist.SetStyle(loc, loc+28, wx.TextAttr("WHITE",(69,109,228)))
	self.OutputPacketDetail(self.current_packet_number)
	displaybuffer = self.tc_packetlist_displaybuffer
	x = 0
	while x < len (displaybuffer)-2:
		if displaybuffer[x] == "O" and displaybuffer[x+1] == "u" and displaybuffer[x+2] == "t":
			self.tc_packetlist.SetStyle(x-13, x+15, wx.TextAttr("WHITE", (69,109,228)))
		x+=1
	self.btn_ClearAllFuzzPoints.Enable(False)
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)

    def	AddFuzzPoint(self,evt):
	if len(self.packets) == 0:
		return
	text = ""
	if self.fuzzer == "Network" or self.fuzzer == "USB":
		tmp = self.packets[self.current_packet_number][0][1]
		if tmp == self.targetport:
			wx.MessageBox("Cannot fuzz inbound data", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
			return
		try:
			tmp_list = [self.current_packet_number,[-1,-1]]
			y = self.packets_to_send.index(tmp_list)
		except:
			y = -1
		if y != -1:
			wx.MessageBox("Packet already selected to be sent unmodified", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
			return
	if (self.capture_data == False):
		return
	start, end = self.tc_captured.GetSelection()
	text = self.tc_captured.GetStringSelection()
	if start == end:
		wx.MessageBox("Nothing highlighted", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
		return
	if start != end:	# selection from hex
		tmp = string.replace(text, " ", "" )
		if len(tmp) % 2 != 0:
			wx.MessageBox("Odd highlighted section", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
			return
		pos_text = text
		if text[0] == " ":
			start +=1
			pos_text = text[1:] 	# remove leading space
		pos_start = start / 3
		pos_end = pos_start + ((len(tmp) / 2)-1)
	try:
		tmp_list = [self.current_packet_number,[pos_start,pos_end]]
		y = self.packets_to_send.index(tmp_list)
	except:
		y = -1
	if y != -1:
		wx.MessageBox("Fuzzpoint already set", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
		return
	x = 0
	duplicate = False
	while x < len (self.packets_to_send):
		if self.packets_to_send[x][0] == self.current_packet_number:
			duplicate = True
			break
		x+=1
	if duplicate == False:
		self.total_unique_packets +=1
	tmp_list = [self.current_packet_number, [pos_start, pos_end]] 
	self.packets_to_send.append (tmp_list)
	self.UpdateDataModificationPoints()
	loc = self.current_packet_number * 30
	self.tc_packetlist.SetStyle(loc, loc+28, wx.TextAttr("WHITE", (226,132,68)))
	self.OutputPacketDetail(self.current_packet_number)
	self.tc_packetlist.ShowPosition((self.current_packet_number * 30) -1)
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)
	self.tb.EnableTool(self.ID_toolFuzzerStart, True)
	self.mb.Enable(self.ID_Start_Fuzzing, True)
	self.btn_ClearAllFuzzPoints.Enable(True)
	self.tc_fuzzpoints.ShowPosition(0)

    def	AddAllBytes(self,evt):
	if len(self.packets) == 0:
		return
	text = ""
	if self.fuzzer == "Network" or self.fuzzer == "USB":
		tmp = self.packets[self.current_packet_number][0][1]
		if tmp == self.targetport:
			wx.MessageBox("Cannot fuzz inbound data", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
			return
		try:
			tmp_list = [self.current_packet_number,[-1,-1]]
			y = self.packets_to_send.index(tmp_list)
		except:
			y = -1
		if y != -1:
			wx.MessageBox("Packet already selected to be sent unmodified", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
			return
	if (self.capture_data == False):
		return
	self.all_bytes_selected.append(self.current_packet_number)
	x=0
	while x < len (self.all_bytes_selected):
		if self.all_bytes_selected[x] == self.current_packet_number:
			self.tc_captured.SetStyle(0, self.tc_captured.GetLastPosition(), wx.TextAttr("WHITE", (226,132,68)))
		x+=1
	pos_start = 0
	pos_end = 0
	while pos_end < len (self.packets[self.current_packet_number][1]):
		tmp_list = [self.current_packet_number, [pos_start, pos_end]] 
		self.packets_to_send.append (tmp_list)
		pos_start +=1
		pos_end +=1
	self.UpdateDataModificationPoints()	
	self.tb.EnableTool(self.ID_toolFuzzerStart, True)
	self.mb.Enable(self.ID_Start_Fuzzing, True)
	self.btn_ClearAllFuzzPoints.Enable(True)
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)

    def	AddFuzzPointRange(self,evt):
	if len(self.packets) == 0:
		return
	text = ""
	if self.fuzzer == "Network" or self.fuzzer == "USB":
		tmp = self.packets[self.current_packet_number][0][1]
		if tmp == self.targetport:
			wx.MessageBox("Cannot fuzz inbound data", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
			return
		try:
			tmp_list = [self.current_packet_number,[-1,-1]]
			y = self.packets_to_send.index(tmp_list)
		except:
			y = -1
		if y != -1:
			wx.MessageBox("Packet already selected to be sent unmodified", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
			return
	if (self.capture_data == False):
		return
	start, end = self.tc_captured.GetSelection()
	text = self.tc_captured.GetStringSelection()
	if start == end:
		wx.MessageBox("Nothing highlighted", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
		return
	if start != end:	# selection from hex
		tmp = string.replace(text, " ", "" )
		if len(tmp) % 2 != 0:
			wx.MessageBox("Odd highlighted section", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
			return
		pos_text = text
		if text[0] == " ":
			start +=1
			pos_text = text[1:] 	# remove leading space
		pos_start = start / 3
		pos_end = pos_start + ((len(tmp) / 2)-1)
	while pos_start < pos_end+1:
		try:
			tmp_list = [self.current_packet_number,[pos_start,pos_start]]
			y = self.packets_to_send.index(tmp_list)
		except:
			y = -1
		if y != -1:
			wx.MessageBox("Fuzzpoint already set", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
			return
		tmp_list = [self.current_packet_number, [pos_start, pos_start]] 
		self.packets_to_send.append (tmp_list)
		pos_start +=1
	self.UpdateDataModificationPoints()
	self.tb.EnableTool(self.ID_toolFuzzerStart, True)
	self.mb.Enable(self.ID_Start_Fuzzing, True)
	self.btn_ClearAllFuzzPoints.Enable(True)
	loc = self.current_packet_number * 30
	self.tc_packetlist.SetStyle(loc, loc+28, wx.TextAttr("WHITE", (226,132,68)))
	self.OutputPacketDetail(self.current_packet_number)
	self.tc_packetlist.ShowPosition((self.current_packet_number * 30) -1)
	self.tc_fuzzpoints.ShowPosition(0)
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)

    def CreateFuzzpointRemoveWindow (self):
	win = wx.Frame(self, -1, "Remove fuzzpoint",size=(350,200), style=wx.TAB_TRAVERSAL | wx.FRAME_FLOAT_ON_PARENT | wx.CAPTION | wx.FRAME_TOOL_WINDOW)
	win.Center()
	win.Show(True)
	win.SetBackgroundColour("White")
	path = self.workingdir
	path = path + "\\..\\images\\zulu_logo16x16.png"
 	image = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap() 
	icon = wx.EmptyIcon() 
	icon.CopyFromBitmap(image) 
	win.SetIcon(icon) 
	return win

    def	RemoveFuzzPoint (self):
	x = 0
	while x < len (self.packets_to_send):
		if self.packets_to_send[x][0] == self.current_packet_number and self.packets_to_send[x][1][0] == self.selection_start:
			self.packets_to_send.pop(x)
		x+=1
	y = 0
	y = self.UpdateDataModificationPoints()
	if y==0:
		self.tb.EnableTool(self.ID_toolFuzzerStart, False)
		self.tb.EnableTool(self.ID_toolFuzzerPause, False)
		self.tb.EnableTool(self.ID_toolFuzzerStop, False)
		self.mb.Enable(self.ID_Start_Fuzzing, False)
		self.mb.Enable(self.ID_Pause_Fuzzing, False)
		self.mb.Enable(self.ID_Stop_Fuzzing, False)
		self.btn_ClearAllFuzzPoints.Enable(False)
	self.process_input_data()
	self.OutputPacketDetail(self.current_packet_number)
	self.tc_fuzzpoints.ShowPosition(self.selection_start)
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)

    def	AddAllDoubleBytes(self,evt):
	if len(self.packets) == 0:
		return
	text = ""
	if self.fuzzer == "Network" or self.fuzzer == "USB":
		tmp = self.packets[self.current_packet_number][0][1]
		if tmp == self.targetport:
			wx.MessageBox("Cannot fuzz inbound data", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
			return
		try:
			tmp_list = [self.current_packet_number,[-1,-1]]
			y = self.packets_to_send.index(tmp_list)
		except:
			y = -1
		if y != -1:
			wx.MessageBox("Packet already selected to be sent unmodified", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
			return
	if (self.capture_data == False):
		return
	self.all_bytes_selected.append(self.current_packet_number)
	x=0
	while x < len (self.all_bytes_selected):
		if self.all_bytes_selected[x] == self.current_packet_number:
			self.tc_captured.SetStyle(0, self.tc_captured.GetLastPosition(), wx.TextAttr("WHITE", (226,132,68)))
		x+=1
	pos_start = 0 + self.DoubleOffset
	pos_end = 1 + self.DoubleOffset
	while pos_end < len (self.packets[self.current_packet_number][1]) -1:
		tmp_list = [self.current_packet_number, [pos_start, pos_end]] 
		self.packets_to_send.append (tmp_list)
		pos_start +=2
		pos_end +=2
	self.UpdateDataModificationPoints()
	self.tb.EnableTool(self.ID_toolFuzzerStart, True)
	self.mb.Enable(self.ID_Start_Fuzzing, True)
	self.btn_ClearAllFuzzPoints.Enable(True)
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)

    def	AddAllQuadBytes(self,evt):
	if len(self.packets) == 0:
		return
	text = ""
	if self.fuzzer == "Network" or self.fuzzer == "USB":
		tmp = self.packets[self.current_packet_number][0][1]
		if tmp == self.targetport:
			wx.MessageBox("Cannot fuzz inbound data", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
			return
		try:
			tmp_list = [self.current_packet_number,[-1,-1]]
			y = self.packets_to_send.index(tmp_list)
		except:
			y = -1
		if y != -1:
			wx.MessageBox("Packet already selected to be sent unmodified", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
			return
	if (self.capture_data == False):
		return
	self.all_bytes_selected.append(self.current_packet_number)
	x=0
	while x < len (self.all_bytes_selected):
		if self.all_bytes_selected[x] == self.current_packet_number:
			self.tc_captured.SetStyle(0, self.tc_captured.GetLastPosition(), wx.TextAttr("WHITE", (226,132,68)))
		x+=1
	pos_start = 0 + self.QuadOffset
	pos_end = 3 + self.QuadOffset
	while pos_end < len (self.packets[self.current_packet_number][1]) -3:
		tmp_list = [self.current_packet_number, [pos_start, pos_end]] 
		self.packets_to_send.append (tmp_list)
		pos_start +=4
		pos_end +=4
	self.UpdateDataModificationPoints()
	self.tb.EnableTool(self.ID_toolFuzzerStart, True)
	self.mb.Enable(self.ID_Start_Fuzzing, True)
	self.btn_ClearAllFuzzPoints.Enable(True)
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)

    def	AddDoubleOffset (self,event):
	tmp =  event.GetString()
	if tmp == "0":
		self.DoubleOffset = 0
	if tmp == "+1":
		self.DoubleOffset = 1
        event.Skip()

    def	AddQuadOffset (self,event):
	tmp =  event.GetString()
	if tmp == "0":
		self.QuadOffset = 0
	if tmp == "+1":
		self.QuadOffset = 1
	if tmp == "+2":
		self.QuadOffset = 2
	if tmp == "+3":
		self.QuadOffset = 3
        event.Skip()

    def	TargetHasCrashed(self):
	print "-------------------------------------------------------------------------------"
	print time.strftime("%H:%M:%S  ", time.localtime()),
	print "Fuzzing: Connect error - check if target has crashed"
	print "-------------------------------------------------------------------------------"
	self.Showalert = True
	path = self.workingdir
	path = path + "\\..\\images\\alert.png"
	image_file = path
	image = wx.Bitmap(image_file)
	image_size = image.GetSize()
	self.tc_output.AppendText("Fuzzing: Connect error - check if target has crashed\n")
	self.tc_output.ShowPosition(self.tc_output.GetLastPosition()-1)
	self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
	self.fplog.write("Fuzzing: Connect error - check if target has crashed\n")
	self.bmCrash = wx.StaticBitmap(self, wx.ID_ANY, image, size=image_size, pos=(1045,670))
	if self.fuzzer == "Network":
		self.CreatePoc()
	if self.VMwareEnabled == True:
		self.tc_output.AppendText("Status: Fuzzing paused\n")
		self.tc_output.ShowPosition(self.tc_output.GetLastPosition ()-1)
		self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
		self.fplog.write("Status: Fuzzing paused\n")
		self.ControlVM()
		self.tc_output.AppendText("Status: Fuzzing restarted\n")
		self.tc_output.ShowPosition(self.tc_output.GetLastPosition()-1)
		self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
		self.fplog.write("Status: Fuzzing restarted\n")
	else:
		self.PauseFuzzing(1)
		self.tc_output.AppendText("Fuzzing: Press \"Stop\" to end this fuzzing session\n")
		self.tc_output.ShowPosition(self.tc_output.GetLastPosition()-1)

#------------------------------------------------------------------------------------------------------------------------------------------
#--- GUI Control --------------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------------
# tc_capturedFocus()
# tc_captured_ascFocus()
# OnContextMenu()
# EnableCheckboxes()
# OpenBufferTestcase()
# OpenFormatTestcase()
# OpenNullTestcase()
# OpenUnixTestcase()
# OpenWindowsTestcase()
# OpenXMLTestcase()
# OpenUserTestcase()
# OpenCustom()
# OpenTestcaseFile()
# process_input_data()
# ResetEverything()
# UpdateDataModificationPoints()
# tc_capturedLeftUp()
# tc_capturedPosition()
# tc_packetlistLeftDown()
# tc_packetlistPosition()
# OutputPacketDetail()
# CloseMe()
# uniq()
# FindNextSearch()
# DoSearch()
# About()
#------------------------------------------------------------------------------------------------------------------------------------------

    def	tc_capturedFocus (self,event):
	self.tc_captured_has_focus = True
	self.tc_captured_asc_has_focus = False

    def	tc_captured_ascFocus (self, event):
	self.tc_captured_asc_has_focus = True
	self.tc_captured_has_focus = False

    def	OnContextMenu(self, event):
	if len(self.packets) == 0:
		return     
	if not hasattr(self, "popupID1"):
		self.popupID1 = wx.NewId()
		self.popupID2 = wx.NewId()
		self.popupID3 = wx.NewId()
		self.popupID4 = wx.NewId()
		self.popupID5 = wx.NewId()
		self.Bind(wx.EVT_MENU, self.menu_AddFuzzPoint, id=self.popupID1)
		self.Bind(wx.EVT_MENU, self.menu_DelFuzzPoint, id=self.popupID2)
		self.Bind(wx.EVT_MENU, self.menu_AddFuzzRange, id=self.popupID3)
		self.Bind(wx.EVT_MENU, self.menu_AddLengthField, id=self.popupID4)
		self.Bind(wx.EVT_MENU, self.menu_RemoveLengthField, id=self.popupID5)
	menu = wx.Menu()
	menu.Append(self.popupID1, "Add Fuzzpoint")
	menu.Append(self.popupID2, "Del Fuzzpoint")
	menu.Append(self.popupID3, "Add Fuzz Range")
	menu.Append(self.popupID4, "Add Length Field")
	menu.Append(self.popupID5, "Remove Length Field")
	self.PopupMenu(menu)
	menu.Destroy()

    def EnableCheckboxes(self):
	if self.buffer_overflow == True:
		self.cb_overflow.SetValue(True)
		self.PopulateTestcases("buffer-overflows.txt")
		self.testcaseselected +=1
	if self.formatstring == True:
		self.cb_format.SetValue(True)
		self.PopulateTestcases("format-strings.txt")
		self.testcaseselected +=1
	if self.singlebyte == True:
		self.cb_single_byte.SetValue(True)
		self.PopulateSingleByte()
		self.testcaseselected +=1
	if self.doublebyte == True:
		self.cb_double_byte.SetValue(True)
		self.PopulateDoubleByte()
		self.testcaseselected +=1
	if self.quadbyte == True:
		self.cb_quad_byte.SetValue(True)
		self.PopulateQuadByte()
		self.testcaseselected +=1
	if self.nullcase == True:
		self.cb_null.SetValue(True)
		self.PopulateTestcases("null.txt")
		self.testcaseselected +=1
	if self.unixcase == True:
		self.cb_commandu.SetValue(True)
		self.PopulateTestcases("command-execution-unix.txt")
		self.testcaseselected +=1
	if self.windowscase == True:
		self.cb_commandw.SetValue(True)
		self.PopulateTestcases("command-inject-windows.txt")
		self.testcaseselected +=1
	if self.xmlcase == True:
		self.cb_xml.SetValue(True)
		self.PopulateTestcases("xml-attacks.txt")
		self.testcaseselected +=1
	if self.userdefined == True:
		self.cb_userdefined.SetValue(True)
		self.PopulateTestcases("user-defined.txt")
		self.testcaseselected +=1
	if self.controlcase == True:
		self.cb_control.SetValue(True)
		self.PopulateControl()
		self.testcaseselected +=1
	if self.extendedcase == True:
		self.cb_extended.SetValue(True)
		self.PopulateExtended()
		self.testcaseselected +=1
	if self.bitbyte == True:
		self.cb_bitbyte.SetValue(True)
		self.PopulateBitByte()
		self.testcaseselected +=1
	if self.bitword == True:
		self.cb_bitword.SetValue(True)
		self.PopulateBitWord()
		self.testcaseselected +=1
	if self.bitlong == True:
		self.cb_bitlong.SetValue(True)
		self.PopulateBitLong()
		self.testcaseselected +=1
	if self.bitbyteinv == True:
		self.cb_bitbyteinv.SetValue(True)
		self.PopulateBitByteInv()
		self.testcaseselected +=1
	if self.bitwordinv == True:
		self.cb_bitwordinv.SetValue(True)
		self.PopulateBitWordInv()
		self.testcaseselected +=1
	if self.bitlonginv == True:
		self.cb_bitlonginv.SetValue(True)
		self.PopulateBitLongInv()
		self.testcaseselected +=1
	if self.VMwareEnabled == True:
		self.cb_vmware.SetValue(True)
	if self.wireshark_enabled == True:
		self.cb_wireshark.SetValue(True)
	if self.custom_script == True:
		self.cb_zuluscript.SetValue(True)

    def	OpenBufferTestcase (self, event):
	self.OpenTestcaseFile("buffer-overflows.txt")

    def	OpenFormatTestcase (self, event):
	self.OpenTestcaseFile("format-strings.txt")

    def	OpenNullTestcase (self, event):
	self.OpenTestcaseFile("null.txt")

    def	OpenUnixTestcase (self, event):
	self.OpenTestcaseFile("command-execution-unix.txt")

    def	OpenWindowsTestcase (self, event):
	self.OpenTestcaseFile("command-inject-windows.txt")

    def	OpenXMLTestcase (self, event):
	self.OpenTestcaseFile("xml-attacks.txt")

    def	OpenUserTestcase (self, event):
	self.OpenTestcaseFile("user-defined.txt")

    def	OpenCustom (self, event):
	self.OpenTestcaseFile("..\\bin\\custom.py")

    def OpenTestcaseFile (self, filename):
	p = self.workingdir
	path = p + "\\..\\fuzzdb\\" + filename
	command = "notepad.exe " + " " + path
	process = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    def	process_input_data(self):
	self.tc_packetlist.Clear()
	displaybuffer = ""
	if self.packets:
		if self.fuzzer == "Network":
			self.btn_PacketTest.Enable(True)
		if self.fuzzer == "Network" or self.fuzzer == "USB" or self.fuzzer == "Serial":
			self.btn_SendUnchanged.Enable(True)
			self.btn_PacketTest.Enable(True)
			if len(self.packets) > 1 and (self.capture_type == "Network" or self.capture_type == "PCAP"):
				self.targethost = self.packets[1][0][0]
				self.targetport = self.packets[1][0][1]
			self.capture_data = True
			
			if self.capture_type == "PCAP":
				x=0
				while x < len (self.packets):
					if len(self.packets[x][1]) == 0:
						self.packets.pop(x)
						x-=1
					x+=1
			
			x = 0
			while x < len (self.packets):
				tmp = self.packets[x][0][1]
				if self.capture_type == "Network" or self.capture_type == "USB" or self.capture_type == "PCAP":
					displaybuffer += "Packet #"
				else:
					displaybuffer += "Async  #"
				displaybuffer += "%04d" % x
				if tmp != self.targetport:
					displaybuffer += " Out(%04x bytes) " % len(self.packets[x][1]) 
				else:
					displaybuffer += " In (%04x bytes) " % len(self.packets[x][1])
					if x == 0:
						self.receivepacketfirst = True
				if x < len (self.packets) -1:
					displaybuffer += "\n"
				x+=1
		elif self.fuzzer == "File":
				self.capture_data = True
				displaybuffer += "File loaded                 \n"      
	else:
		return
	self.tc_packetlist_displaybuffer = displaybuffer
	self.tc_packetlist.AppendText(displaybuffer)
	self.tc_packetlist.ShowPosition(0)
	if self.fuzzer == "Network" or self.fuzzer == "USB" or self.fuzzer == "Serial":
		x = 0
		while x < len (displaybuffer)-2:
			if displaybuffer[x] == "O" and displaybuffer[x+1] == "u" and displaybuffer[x+2] == "t":
				self.tc_packetlist.SetStyle(x-13, x+15, wx.TextAttr("WHITE", (69,109,228)))
			x+=1

	x = 0
	while x < len(self.packets):
		y = 0
		while y < len(self.packets_to_send):
			if self.packets_to_send[y][0] == x:
				if self.packets_to_send[y][1][0] == -1:		
					loc = x * 30
					self.tc_packetlist.SetStyle(loc, loc+28, wx.TextAttr("WHITE", (0,150,0)))
				else:
					loc = x * 30
					self.tc_packetlist.SetStyle(loc, loc+28, wx.TextAttr("WHITE", (226,132,68)))
			y+=1
		x+=1
	self.tc_packetlist.ShowPosition(0)
	self.OutputPacketDetail(self.current_packet_number)

    def	ResetEverything(self):
	self.tc_output.SetBackgroundColour("WHITE")
	f = wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL)
	self.tc_output.SetDefaultStyle(wx.TextAttr((0,0,80), "WHITE", f))
	self.statusbar.SetStatusText("", 2)
	self.statusbar.SetStatusText("Status: Idle", 3)
	self.latest_PoC = ""
	self.tb.EnableTool(self.ID_toolExploit, False)
	self.tb.EnableTool(self.ID_toolFuzzerStart, False)
	self.tb.EnableTool(self.ID_toolFuzzerPause, False)
	self.tb.EnableTool(self.ID_toolFuzzerStop, False)
	self.mb.Enable(self.ID_Start_Fuzzing, False)
	self.mb.Enable(self.ID_Pause_Fuzzing, False)
	self.mb.Enable(self.ID_Stop_Fuzzing, False)
	self.btn_ClearAllFuzzPoints.Enable(False)
	self.btn_AddAllBytes.Enable(False)
	self.btn_AddAllDoubleBytes.Enable(False)
	self.btn_AddAllQuadBytes.Enable(False)
	self.cbDoubleOffset.Enable(False)
	self.cbQuadOffset.Enable(False)
	self.btn_SendUnchanged.Enable(False)
	self.btn_PacketTest.Enable(False)
	self.capture_data = False
	self.capture_type = "Network"
	self.packets = []
	self.packets_to_send = []
	self.fuzzpoints = []
	self.packets_captured = 0
	self.current_packet_number = 0
	self.total_unique_packets = 0
	self.last_packet_data_list = []
	self.FindNext = False
	self.current_search_location = 0
	self.search_found = 0
	self.searchtermfound = ""
	self.current_save_path = ""	
	self.tc_packetlist.Clear()
	self.tc_fuzzpoints.Clear()
	self.tc_captured.Clear()
	self.tc_captured_asc.Clear()
	self.tc_output.Clear()
	self.all_bytes_selected = []
	self.LengthFields = []

	if self.Showalert == True:
		self.bmCrash.Hide()

    def UpdateDataModificationPoints (self):
	self.tc_fuzzpoints.Clear()
	x = 0
	while x < len (self.LengthFields):
		field_size = self.LengthFields[x][0]
		field_pos = self.LengthFields[x][1]
		packet_num = self.LengthFields[x][4]
		field_pos_end = field_pos + field_size 
		tmppkt = "%d\n" % packet_num	
		tmp = "Length:%d-%d " % (field_pos, field_pos_end-1)
		self.tc_fuzzpoints.AppendText(tmp)
		if self.fuzzer == "Network" or self.fuzzer == "USB" or self.fuzzer == "Serial":
			self.tc_fuzzpoints.AppendText("Pkt:")
			self.tc_fuzzpoints.AppendText(tmppkt)
		else:
			self.tc_fuzzpoints.AppendText("\n")
		x+=1
	x = 0
	y = 0
	while x < len (self.packets_to_send):
		tmppkt = "%d\n" % self.packets_to_send[x][0]
		if self.packets_to_send[x][1][0] != -1:
			y+=1
			tmp = "Fuzzpoint:%d-%d " % (self.packets_to_send[x][1][0], self.packets_to_send[x][1][01])
			self.tc_fuzzpoints.AppendText(tmp)
			if self.fuzzer == "Network" or self.fuzzer == "USB":
				self.tc_fuzzpoints.AppendText("Pkt:")
				self.tc_fuzzpoints.AppendText(tmppkt)
			else:
				self.tc_fuzzpoints.AppendText("\n")
		else:
			self.tc_fuzzpoints.AppendText("Unmodified Pkt:")
			self.tc_fuzzpoints.AppendText(tmppkt)
		x+=1
	self.tc_fuzzpoints.ShowPosition(0)
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)
	return y

    def tc_capturedLeftUp(self, evt):
	evt.Skip()
	wx.CallAfter(self.tc_capturedPosition, evt)

    def	tc_capturedPosition(self,evt):
	if self.tc_captured_has_focus == True:
		start,end = self.tc_captured.GetSelection()
		start +=1
		end +=1
		if start % 3 == 0:
			start +=1
		elif (start+1) % 3 == 0:
			start -=1
		if end % 3 == 0:
			end +=1
		elif (end+1) % 3 == 0:
			end +=2
		start -=1
		end -=1
		self.tc_captured.SetSelection(start,end)
		asc_start = start / 3
		asc_end = end / 3
		self.selection_start = asc_start
		self.selection_end = asc_end-1
		modifier = asc_start / 32
		modifier2 = asc_end / 32
		asc_start += modifier
		asc_end += modifier2
		self.tc_captured_asc.SetSelection(asc_start,asc_end)
	elif self.tc_captured_asc_has_focus == True:
		start,end = self.tc_captured_asc.GetSelection()
		modifier = start / 32
		modifier2 = end / 32
		start -= modifier
		end -= modifier2
		self.selection_start = start
		self.selection_end = end-1
		start = start * 3
		end = end * 3
		self.tc_captured.SetSelection(start,end)
	else:
		pass

    def tc_packetlistLeftDown(self, evt):
	evt.Skip()
	wx.CallAfter(self.tc_packetlistPosition, evt)

    def tc_packetlistPosition(self, evt):
	ip = self.tc_packetlist.GetInsertionPoint()
	ip = ip /30
	if (self.capture_data == False):
		return
	self.tc_packetlist.SetSelection(ip * 30,ip * 30 + 28)
	self.current_packet_number = ip
	self.OutputPacketDetail(ip)

    def OutputPacketDetail(self,index): 
	packet = "Selected packet = "
	packet += "%d" % index
	self.statusbar.SetStatusText(packet, 2)
	displaybuffer = ""
	self.tc_captured.Clear()
	if (self.capture_data == False):
		return
	self.btn_AddAllBytes.Enable(True)
	self.btn_AddAllDoubleBytes.Enable(True)
	self.btn_AddAllQuadBytes.Enable(True)
	self.cbDoubleOffset.Enable(True)
	self.cbQuadOffset.Enable(True)
	data = self.packets[index][1]
	x = 0
	while x < len (data):
		tmp = hex(ord(data[x]))	# print final byte
		tmp = tmp[2:]
		if len(tmp) == 1:
			tmp = "0" + tmp
		displaybuffer += tmp
		displaybuffer += " "
		x+=1
	self.tc_captured.AppendText(displaybuffer)
	self.tc_captured.ShowPosition(0)
	displaybuffer = ""
	self.tc_captured_asc.Clear()	# clear text control
	x = 0
	while x < len (data):
		if (x % 32) == 0 and x > 0:
			displaybuffer += "\n"
		temp = ord(data[x])
		if (temp > 31) and (temp < 127):
			displaybuffer += data[x]
		else:
			displaybuffer += "."
		x+=1
	self.tc_captured_asc.AppendText(displaybuffer)
	self.tc_captured_asc.ShowPosition(0)
	x = 0
	newlist = []
	tmplist = []
	y = 0
	while (y < len(self.packets_to_send)):
		if self.packets_to_send[y][0] == index and self.packets_to_send[y][1][0] != -1:
			tmplist = [self.packets_to_send[y][1][0], self.packets_to_send[y][1][1]]
			newlist.append(tmplist)
		y += 1
	if len(newlist) > 0:
		self.tb.EnableTool(self.ID_toolFuzzerStart, True)
		self.mb.Enable(self.ID_Start_Fuzzing, True)
		self.btn_ClearAllFuzzPoints.Enable(True)
	# --------------highlight fuzzpoint range in red in the hex window --------------------------
	if len (self.all_bytes_selected) > 0:
		self.btn_ClearAllFuzzPoints.Enable(True)
		self.tb.EnableTool(self.ID_toolFuzzerStart, True)
		self.mb.Enable(self.ID_Start_Fuzzing, True)
	if len(self.all_bytes_selected) > 0:
		x=0
		while x < len (self.all_bytes_selected):
			if self.all_bytes_selected[x] == self.current_packet_number:
				self.tc_captured.SetStyle(0, self.tc_captured.GetLastPosition(), wx.TextAttr("WHITE", (226,132,68)))
			x+=1
	# --------------highlight length field in green in the hex window --------------------------	
	if len (self.LengthFields) > 0:
		self.btn_ClearAllFuzzPoints.Enable(True)
	x = 0
	r1 = 180
	g1 = 193
	b1 = 61
	r2 = 228
	g2 = 233
	b2 = 185
	while x < len (self.LengthFields):
		field_size = self.LengthFields[x][0]
		field_pos = self.LengthFields[x][1]
		field_pos_end = field_pos + field_size 
		start = self.LengthFields[x][2]
		end = self.LengthFields[x][3]
		packet = self.LengthFields[x][4]
		field_pos *= 3
		field_pos_end *= 3
		end +=1
		start *= 3
		end *= 3
		if packet == self.current_packet_number:
			self.tc_captured.SetStyle(field_pos,field_pos_end, wx.TextAttr("WHITE", (r1,g1,b1)))	# colour length field green
			self.tc_captured.SetStyle(start,end, wx.TextAttr("BLACK", (r2,g2,b2)))	# colour length data light green
		r1 -=50
		if r1 < 0:
			r1 = 180
		r2 -=50
		if r2 < 0:
			r2 = 228
		x+=1
		self.tc_captured.ShowPosition(start)
	# --------------highlight length field in green in the ASCII window --------------------------
	x = 0
	r1 = 180
	g1 = 193
	b1 = 61
	r2 = 228
	g2 = 233
	b2 = 185
	while x < len (self.LengthFields):
		field_size = self.LengthFields[x][0]
		field_pos = self.LengthFields[x][1]
		field_pos_end = field_pos + field_size 
		start = self.LengthFields[x][2]
		end = self.LengthFields[x][3]
		packet = self.LengthFields[x][4]
		modifier = start / 32
		modifier2 = end / 32
		start+=modifier
		end+=modifier2
		end +=1		
		modifier = field_pos / 32
		modifier2 = field_pos_end / 32
		field_pos+=modifier
		field_pos_end+=modifier2
		field_pos_end +=1		
		if packet == self.current_packet_number:
			self.tc_captured_asc.SetStyle(field_pos,field_pos_end, wx.TextAttr("WHITE", (r1,g1,b1)))	# colour length field green
			self.tc_captured_asc.SetStyle(start,end, wx.TextAttr("BLACK", (r2,g2,b2)))	# colour length data light green
		r1 -=50
		if r1 < 0:
			r1 = 180
		r2 -=50
		if r2 < 0:
			r2 = 228
		x+=1
		self.tc_captured_asc.ShowPosition(start)
	# --------------highlight individual fuzzpoints in red in the hex window --------------------------
	x = 0
	while x < len (newlist):
		start = newlist[x][0]
		end = newlist[x][1]
		end +=1
		start *= 3
		end *= 3
		self.tc_captured.SetStyle(start, end, wx.TextAttr("WHITE", (226,132,68)))
		x+=1
		self.tc_captured.ShowPosition(0)
	# --------------highlight individual fuzzpoints in red in the ASCII window --------------------------
	x = 0
	while x < len (newlist):
		start = newlist[x][0]
		end = newlist[x][1]
		end +=1
		modifier = start / 32
		modifier2 = end / 32
		start+=modifier
		end+=modifier2
		self.tc_captured_asc.SetStyle(start, end, wx.TextAttr("WHITE", (226,132,68)))
		x+=1
		self.tc_captured_asc.ShowPosition(0)
        
    def CloseMe(self, event):
	if self.session_changed == True:
		dlg = wx.MessageDialog(self,'Do you want to save the changes?','Zulu', style=wx.YES | wx.NO | wx.CANCEL | wx.ICON_INFORMATION)        
		val = dlg.ShowModal()
		if val == wx.ID_YES:
			dlg.Destroy()
			self.SaveSession(1)
		if val == wx.ID_NO:
			dlg.Destroy()                
		if val == wx.ID_CANCEL:
			dlg.Destroy()
			return
	self.parent.Close(True)
	self.fplog.close()
  
    def uniq(self,input): 
	output = [] 
	for x in input: 
		if x not in output: 
			output.append(x) 
	return output 

    def	FindNextSearch(self,event):
		self.FindNext = True
		self.DoSearch(1)

    def	DoSearch(self,event):
	if not self.packets:
		return
	searchlen = 0
	searchterm = ""
	if self.FindNext == False:
		searchterm = self.search.GetValue()
		if searchterm[0] != "\"" or searchterm[len(searchterm)-1] != "\"" and self.FindNext == False:
			if len (searchterm) % 2 != 0:						# not a string term
				searchterm = "0" + searchterm					# odd number of bytes
			searchlen = len(searchterm) / 2
			tmpterm = ""
			x = 0
			while x < len (searchterm)-1:
				try:
					value = int(searchterm[x] + searchterm[x+1],16)
				except:
					wx.MessageBox("Search term invalid: not hex bytes", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
					return
				tmpterm += "%c" % value
				x+=2
			searchterm = tmpterm
		else:
			searchterm = searchterm[1:-1]	# remove the quotes
	else:
		searchterm = self.searchtermfound
	searchlen = len(searchterm)
	data = ""
	loc = 0
	if self.FindNext == True:
		self.current_search_packet = self.search_found
	else:
		self.search_found = 0
		self.current_search_location = 0
		self.current_search_packet = 0
		self.searchtermfound = ""
	while self.current_search_packet < len (self.packets):
		data = self.packets[self.current_search_packet][1]
		if self.FindNext == True:
			loc = data.find(searchterm,self.current_search_location,len(data)-1)
		else:
			loc = data.find(searchterm)
		if loc != -1:
			self.current_search_location = loc + 1
			self.search_found = self.current_search_packet
			self.searchtermfound = searchterm
			self.OutputPacketDetail(self.current_search_packet)
			ip = self.current_search_packet
			self.tc_packetlist.SetSelection(ip * 30,ip * 30 + 29)
			self.current_packet_number = ip
			loc2 = loc+(searchlen)
			asc_loc = loc
			asc_loc2 = loc2
			loc *= 3
			loc2 *= 3
			self.tc_captured.SetSelection(loc,loc2-1)
			modifier = asc_loc / 33
			modifier2 = asc_loc2 / 33
			asc_loc += modifier 
			asc_loc2 += modifier2
			self.tc_captured_asc.SetSelection(asc_loc,asc_loc2)
			self.FindNext = False
			return
		else:
			self.current_search_location = 0
		self.current_search_packet +=1
	self.FindNext = False

    def About(self, event):
        wx.MessageBox("Zulu v1.21: Andy Davis, NCC Group 2014", caption="Information", style=wx.OK|wx.ICON_INFORMATION, parent=self)
        return(1)

#------------------------------------------------------------------------------------------------------------------------------------------
#--- Wireshark and PCAP -------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------------
# ImportPCAP()
# GeneratePCAP()
# StartWireshark()
# EnableWireshark()
#------------------------------------------------------------------------------------------------------------------------------------------

    def ImportPCAP (self,event):
	if len(self.packets) > 0:
		dlg = wx.MessageDialog(self,'Are you sure you want to start a new session?','Zulu', style=wx.YES | wx.NO | wx.ICON_INFORMATION)        
		val = dlg.ShowModal()
		if val == wx.ID_YES:
			dlg.Destroy()
			pass			
		if val == wx.ID_NO:
			dlg.Destroy()
			return
	self.ResetEverything()
	self.fuzzer = "Network"
	self.capture_type = "PCAP"
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)
	path = ""
	dir = self.workingdir
	dlg = wx.FileDialog(
            self, message="Choose a file", defaultDir=dir, 
            defaultFile="default", wildcard="*.*", style=wx.OPEN | wx.MULTIPLE | wx.CHANGE_DIR
            )
	dlg.SetFilterIndex(2)
	if dlg.ShowModal() == wx.ID_OK:
		path = dlg.GetPath()
		dlg.Destroy()
		if path == "":
			return 1
		if not os.path.exists(path):
			wx.MessageBox("File does not exist", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
			return 1
		try:
			pcapReader = dpkt.pcap.Reader(file(path, "rb"))
		except:
			wx.MessageBox("Error opening file", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
		for ts, data in pcapReader:
			tmp_list = []
    			ether = dpkt.ethernet.Ethernet(data)
    			ip = ether.data
    			src = inet_ntoa(ip.src)
    			dst = inet_ntoa(ip.dst)
    			tcp = ip.data  
			tmp_list.append(src)
			tmp_list.append(tcp.sport)
			self.packets.append([tmp_list,tcp.data])
		self.process_input_data()

    def	GeneratePCAP(self):
	filename = "zulu_pcap" + time.strftime("_%Y-%m-%d_%H-%M-%S", time.localtime()) + ".pcap"
	path = self.workingdir
	path = path + "\\..\\pcap\\" + filename
	self.pcappath = path
	fpcap = file(path, 'wb')
	pcap = ""
	pcap_global_header =  "\xd4\xc3\xb2\xa1" 	# pcap_glob_magic_number
	pcap_global_header += "\x20\x00" 		# pcap_glob_version_major
	pcap_global_header += "\x04\x00" 		# pcap_glob_version_minor
	pcap_global_header += "\x00\x00\x00\x00" 	# pcap_glob_thiszone
	pcap_global_header += "\x00\x00\x00\x00" 	# pcap_glob_sigfigs
	pcap_global_header += "\xff\xff\x00\x00" 	# pcap_glob_snaplen
	pcap_global_header += "\x01\x00\x00\x00" 	# pcap_glob_network
	pcap_ethernet_header1 = "\x5c\x26\x0a\x2a\x2c\x98\x00\x0c\x29\x28\xd0\xd7\x08\x00"
	pcap_ethernet_header2 = "\x00\x0C\x29\x28\xD0\xD7\x5C\x26\x0A\x2A\x2C\x98\x08\x00"
	timestmp = 0
	seq = 342342
	ack = 768678
	pcap += pcap_global_header
	x = 0
	while x < len (self.packets):
		ip_source_ipaddress = self.packets[x][0][0]
		tcp_source_port = self.packets[x][0][1]
		tcp_data = self.packets[x][1]
		udp_length = 8 + len(tcp_data)	
		if tcp_source_port != self.targetport:
			if len(self.packets) > 1:
				tcp_dest_port = self.packets[1][0][1]
			else:
				tcp_dest_port = 1234
		if tcp_source_port == self.targetport:
			pcap_ethernet_header = pcap_ethernet_header1
		else:
			pcap_ethernet_header = pcap_ethernet_header2
		if tcp_source_port == self.targetport and ip_source_ipaddress == "127.0.0.1":
			ip_dest_ipaddress = "127.0.0.2"
		else:
			ip_dest_ipaddress = self.targethost
		if self.udp == True:
			ip_total_length = 28 + len(tcp_data)
		else:
			ip_total_length = 40 + len(tcp_data)
		total_length = len(pcap_ethernet_header) + ip_total_length
		ip_id = random.randint(0, 65535)
		ip_source_ipaddress = ip_source_ipaddress.split('.')
		ip_source_ipaddress = ''.join(("%02x" % int(i) for i in ip_source_ipaddress))
		c = 0
		ip_source_ipaddress_txt = ""
		while c < len(ip_source_ipaddress)-1:
			ip_source_ipaddress_txt += "%c" % int(ip_source_ipaddress[c] + ip_source_ipaddress[c+1],16)
			c+=2
		ip_dest_ipaddress = ip_dest_ipaddress.split('.')
		ip_dest_ipaddress = ''.join(("%02x" % int(i) for i in ip_dest_ipaddress))
		c = 0
		ip_dest_ipaddress_txt = ""
		while c < len(ip_dest_ipaddress)-1:
			ip_dest_ipaddress_txt += "%c" % int(ip_dest_ipaddress[c] + ip_dest_ipaddress[c+1],16)
			c+=2
		tmp_port = "%04x" % tcp_source_port
		tcp_source_port_txt =  "%c" % int(tmp_port[0] + tmp_port[1],16) 
		tcp_source_port_txt += "%c" % int(tmp_port[2] + tmp_port[3],16)
		tmp_port = "%04x" % tcp_dest_port
		tcp_dest_port_txt =  "%c" % int(tmp_port[0] + tmp_port[1],16) 
		tcp_dest_port_txt += "%c" % int(tmp_port[2] + tmp_port[3],16)
		tmp_len = "%04x" % ip_total_length
		ip_total_length_txt =  "%c" % int(tmp_len[0] + tmp_len[1],16) 
		ip_total_length_txt += "%c" % int(tmp_len[2] + tmp_len[3],16)
		tmp_len = "%04x" % udp_length
		udp_length_txt =  "%c" % int(tmp_len[0] + tmp_len[1],16) 
		udp_length_txt += "%c" % int(tmp_len[2] + tmp_len[3],16)
		tmp_id = "%04x" % ip_id
		ip_id_txt =  "%c" % int(tmp_id[0] + tmp_id[1],16) 
		ip_id_txt += "%c" % int(tmp_id[2] + tmp_id[3],16)
		tmp_len = "%08x" % total_length
		total_length_txt =  "%c" % int(tmp_len[6] + tmp_len[7],16) 
		total_length_txt += "%c" % int(tmp_len[4] + tmp_len[5],16)
		total_length_txt +=  "%c" % int(tmp_len[2] + tmp_len[3],16) 
		total_length_txt += "%c" % int(tmp_len[0] + tmp_len[1],16)
		tmp_seq = "%08x" % seq
		tcp_seq_txt =  "%c" % int(tmp_seq[0] + tmp_seq[1],16) 
		tcp_seq_txt += "%c" % int(tmp_seq[2] + tmp_seq[3],16)
		tcp_seq_txt += "%c" % int(tmp_seq[4] + tmp_seq[5],16) 
		tcp_seq_txt += "%c" % int(tmp_seq[6] + tmp_seq[7],16)
		tmp_ack = "%08x" % ack
		tcp_ack_txt =  "%c" % int(tmp_ack[0] + tmp_ack[1],16) 
		tcp_ack_txt += "%c" % int(tmp_ack[2] + tmp_ack[3],16)
		tcp_ack_txt += "%c" % int(tmp_ack[4] + tmp_ack[5],16) 
		tcp_ack_txt += "%c" % int(tmp_ack[6] + tmp_ack[7],16)
		tmp_timestamp = "%08x" % timestmp
		timestamp_txt =  "%c" % int(tmp_timestamp[6] + tmp_timestamp[7],16) 
		timestamp_txt += "%c" % int(tmp_timestamp[4] + tmp_timestamp[5],16)
		timestamp_txt += "%c" % int(tmp_timestamp[2] + tmp_timestamp[3],16) 
		timestamp_txt += "%c" % int(tmp_timestamp[0] + tmp_timestamp[1],16)
		pcap_packet_header =  "\xD4\x0E\xC5\x4F"		# pcap_pkt_ts_sec 
		pcap_packet_header += timestamp_txt 	# pcap_pkt_ts_usec
		pcap_packet_header += total_length_txt		# pcap_pkt_incl_len - length of packet
		pcap_packet_header += total_length_txt		# pcap_pkt_orig_len - length of packet
		pcap_ip_header 	= "\x45\x00"
		pcap_ip_header += ip_total_length_txt 	# two bytes
		pcap_ip_header += ip_id_txt
		pcap_ip_header += "\x40\x00\x80"
		if self.udp == True:
			pcap_ip_header += "\x11"		# UDP
		else:
			pcap_ip_header += "\x06"		# TCP
		pcap_ip_header += "\x00\x00"
		pcap_ip_header += ip_source_ipaddress_txt
		pcap_ip_header += ip_dest_ipaddress_txt
		pcap_tcp_header =  tcp_source_port_txt
		pcap_tcp_header += tcp_dest_port_txt
		pcap_tcp_header += tcp_seq_txt	#seq - incease by 1 for each packet 
		pcap_tcp_header += tcp_ack_txt	#ack - incease by 1 for each packet
		pcap_tcp_header += "\x50\x18"
		pcap_tcp_header += "\x40\x29"
		pcap_tcp_header += "\x00\x00"
		pcap_tcp_header += "\x00\x00"
		pcap_udp_header =  tcp_source_port_txt
		pcap_udp_header += tcp_dest_port_txt
		pcap_udp_header += udp_length_txt
		pcap_udp_header += "\x00\x00"
		pcap += pcap_packet_header
		pcap += pcap_ethernet_header
		pcap += pcap_ip_header
		if self.udp == True:
			pcap += pcap_udp_header
		else:
			pcap += pcap_tcp_header
		pcap += tcp_data 
		ack = seq + 1
		seq = ack
		timestmp += 100
		x+=1
	fpcap.write(pcap)
	fpcap.close()

    def	StartWireshark(self):
	path = self.wiresharkpath + " " + self.pcappath + "\n"	
	process = subprocess.Popen(path, shell=True, stdout=subprocess.PIPE)

    def	EnableWireshark(self, event):
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)
	if event.IsChecked() == 1:
		self.wireshark_enabled = True
		path = ""
		dir = "C:\\Program Files (x86)\\Wireshark\\"
		dlg = wx.FileDialog(
            		self, message="Choose a file", defaultDir=dir, 
            		defaultFile="wireshark", wildcard="*.exe", style=wx.OPEN | wx.MULTIPLE | wx.CHANGE_DIR
            		)
		dlg.SetFilterIndex(2)
		if dlg.ShowModal() == wx.ID_OK:
			path = dlg.GetPath()
			dlg.Destroy()
			if path == "":
				return 1
		if not os.path.exists(path):
			wx.MessageBox("File does not exist", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
			return 1
		self.wiresharkpath = "\"" + path + "\""
		self.tc_output.AppendText("Status: Wireshark integration enabled\n")
		self.tc_output.ShowPosition(self.tc_output.GetLastPosition()-1)
	else:
		self.wireshark_enabled = False
		self.wiresharkpath = ""
		self.tc_output.AppendText("Status: Wireshark integration disabled\n")
		self.tc_output.ShowPosition(self.tc_output.GetLastPosition()-1)
		return

#------------------------------------------------------------------------------------------------------------------------------------------
#--- VMware Control -----------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------------
# EnableVMware()
# CreateVMwareConfWindow()
# ConfigureVMware()
# SetVMwareMode()
# ConfVMwareOSUsername()
# ConfVMwareOSPassword()
# ConfVMwareOSProcessName()
# ConfVMwarePathToVM()
# ConfVMwarePathTovmrun()
# ConfVMwareProduct()
# ConfVMwareTimeout()
# OnOkVMwareConf()
# ControlVM()
#------------------------------------------------------------------------------------------------------------------------------------------

    def	EnableVMware(self,event):
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)
	if event.IsChecked() == 1:
		self.VMwareEnabled = True
		self.tc_output.AppendText("Status: VMware integration enabled\n")
		self.tc_output.ShowPosition(self.tc_output.GetLastPosition()-1)
	else:
		self.VMwareEnabled = False
		self.tc_output.AppendText("Status: VMware integration disabled\n")
		self.tc_output.ShowPosition(self.tc_output.GetLastPosition()-1)

    def CreateVMwareConfWindow (self):
	win = wx.Frame(self, -1, "VMware configuration",size=(300,300), style=wx.TAB_TRAVERSAL | wx.FRAME_FLOAT_ON_PARENT | wx.CAPTION | wx.FRAME_TOOL_WINDOW)
	win.Center()
	win.Show(True)
	win.SetBackgroundColour("White")
	path = self.workingdir
	path = path + "\\..\\images\\zulu_logo16x16.png"
 	image = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap() 
	icon = wx.EmptyIcon() 
	icon.CopyFromBitmap(image) 
	win.SetIcon(icon) 
	return win

    def	ConfigureVMware (self,evt):
	VMware_product_list = ["Workstation", "VMware Server 1", "VMware Server 2", "ESX", "vCenter Server"]
	timeout_list = ["1","2","3","4","5","6","7","8","9","10"]
	self.OkVMwareConf = False
	self.VMwareconfwin = self.CreateVMwareConfWindow()
	self.VMwareconfwin.SetFocus()
	vs = wx.BoxSizer( wx.VERTICAL )
	box1_title = wx.StaticBox( self.VMwareconfwin, -1, "Configue VMware settings" )
	box1 = wx.StaticBoxSizer( box1_title, wx.VERTICAL )
	grid1 = wx.FlexGridSizer( 0, 2, 0, 0 )
	self.conf_ctrls = []       
	self.cb_VM_system = wx.RadioButton(self.VMwareconfwin, -1, "OS control")
	self.cb_VM_process = wx.RadioButton(self.VMwareconfwin, -1, "Process control")
	self.text1 = wx.StaticText(self.VMwareconfwin, -1, "Username")
	self.text2 = wx.TextCtrl(self.VMwareconfwin, -1, self.VMware_OS_username)
	self.text3 = wx.StaticText(self.VMwareconfwin, -1, "Password")
	self.text4 = wx.TextCtrl(self.VMwareconfwin, -1, self.VMware_OS_password, style=wx.TE_PASSWORD)
	self.text5 = wx.StaticText(self.VMwareconfwin, -1, "Path to process")
	self.text6 = wx.TextCtrl(self.VMwareconfwin, -1, self.VMware_OS_process_name)
	self.text7 = wx.StaticText(self.VMwareconfwin, -1, "Path to VM")
	self.b_VM_path = wx.Button(self.VMwareconfwin, 10, "    Select path     ", (20, 20))
	self.text9 = wx.StaticText(self.VMwareconfwin, -1, "Path to vmrun.exe")
	self.b_vmrun_path = wx.Button(self.VMwareconfwin, 20, "    Select path     ", (20, 20))
	self.text11 = wx.StaticText(self.VMwareconfwin, -1, "VMware Product")
	self.cb_VM_product = wx.ComboBox(self.VMwareconfwin, 500, "Workstation", wx.DefaultPosition, wx.DefaultSize, VMware_product_list, wx.CB_DROPDOWN)
	self.text12 = wx.StaticText(self.VMwareconfwin, -1, "Restart time (min)")
	self.cb_VM_timeout = wx.ComboBox(self.VMwareconfwin, 600, "1", wx.DefaultPosition, wx.DefaultSize, timeout_list, wx.CB_DROPDOWN)
	grid1.Add( self.cb_VM_system, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( self.cb_VM_process, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( self.text1, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( self.text2, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( self.text3, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( self.text4, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( self.text5, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( self.text6, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( self.text7, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( self.b_VM_path, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( self.text9, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( self.b_vmrun_path, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( self.text11, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( self.cb_VM_product, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( self.text12, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( self.cb_VM_timeout, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	box1.Add( grid1, 0, wx.ALIGN_CENTRE|wx.ALL, 5 )
	vs.Add( box1, 0, wx.ALIGN_CENTRE|wx.ALL, 5 )
	button = wx.Button(self.VMwareconfwin, 1005, "OK")
	self.VMwareconfwin.Bind(wx.EVT_BUTTON, self.OnOkVMwareConf, button)
	vs.Add( button, 0, wx.ALIGN_CENTRE|wx.ALL, 5 )
	self.VMwareconfwin.Bind(wx.EVT_RADIOBUTTON, self.SetVMwareMode, self.cb_VM_system)
	self.VMwareconfwin.Bind(wx.EVT_RADIOBUTTON, self.SetVMwareMode, self.cb_VM_process)
	self.VMwareconfwin.Bind(wx.EVT_TEXT, self.ConfVMwareOSUsername, self.text2)
	self.VMwareconfwin.Bind(wx.EVT_TEXT, self.ConfVMwareOSPassword, self.text4)
	self.VMwareconfwin.Bind(wx.EVT_TEXT, self.ConfVMwareOSProcessName, self.text6)
	self.VMwareconfwin.Bind(wx.EVT_TEXT, self.ConfVMwarePathToVM, self.b_VM_path)
	self.VMwareconfwin.Bind(wx.EVT_TEXT, self.ConfVMwarePathTovmrun, self.b_vmrun_path)
	self.VMwareconfwin.Bind(wx.EVT_COMBOBOX, self.ConfVMwareProduct, self.cb_VM_product)
	self.VMwareconfwin.Bind(wx.EVT_COMBOBOX, self.ConfVMwareTimeout, self.cb_VM_timeout)
	self.VMwareconfwin.Bind(wx.EVT_BUTTON, self.ConfVMwarePathToVM, self.b_VM_path)
	self.VMwareconfwin.Bind(wx.EVT_BUTTON, self.ConfVMwarePathTovmrun, self.b_vmrun_path)
	if self.VMwareMode == "Process":
		self.cb_VM_process.SetValue(True)
	else:
		self.cb_VM_system.SetValue(True)
	if str(self.cb_VM_system.GetValue()) == "True":
		self.VMwareMode = "OS"
		self.text1.Enable(False)
		self.text2.Enable(False)
		self.text3.Enable(False)
		self.text4.Enable(False)
		self.text5.Enable(False)
		self.text6.Enable(False)
	else:
		self.VMwareMode = "Process"
		self.text1.Enable(True)
		self.text2.Enable(True)
		self.text3.Enable(True)
		self.text4.Enable(True)
		self.text5.Enable(True)
		self.text6.Enable(True)
	self.VMwareconfwin.SetSizer( vs )
	vs.Fit( self.VMwareconfwin )
	while self.OkVMwareConf == False:
		try:
			wx.Yield()
		except:
			pass

    def	SetVMwareMode (self, event):
	if str(self.cb_VM_system.GetValue()) == "True":
		self.VMwareMode = "OS"
		self.text1.Enable(False)
		self.text2.Enable(False)
		self.text3.Enable(False)
		self.text4.Enable(False)
		self.text5.Enable(False)
		self.text6.Enable(False)
	else:
		self.VMwareMode = "Process"
		self.text1.Enable(True)
		self.text2.Enable(True)
		self.text3.Enable(True)
		self.text4.Enable(True)
		self.text5.Enable(True)
		self.text6.Enable(True)

    def	ConfVMwareOSUsername (self, event):
	try:
		self.VMware_OS_username = event.GetString()	
		self.session_changed = True
		self.mb.Enable(self.ID_Save_Session, True)
		self.tb.EnableTool(self.ID_toolSaveFile, True)
	except:
		pass

    def ConfVMwareOSPassword (self, event):
	try:
		self.VMware_OS_password = event.GetString()
		self.session_changed = True
		self.mb.Enable(self.ID_Save_Session, True)
		self.tb.EnableTool(self.ID_toolSaveFile, True)
	except:
		pass

    def ConfVMwareOSProcessName (self, event):
	try:
		self.VMware_OS_process_name = event.GetString()
		self.session_changed = True
		self.mb.Enable(self.ID_Save_Session, True)
		self.tb.EnableTool(self.ID_toolSaveFile, True)
	except:
		pass

    def ConfVMwarePathToVM (self, event):
	path = ""
	dir = "C:\\users\\andy\\vm\\"

	dlg = wx.FileDialog(
        	self, message="Choose a file", defaultDir=dir, 
        	defaultFile="", wildcard="*.vmx", style=wx.OPEN | wx.MULTIPLE | wx.CHANGE_DIR
        	)
	dlg.SetFilterIndex(2)
	if dlg.ShowModal() == wx.ID_OK:
		path = dlg.GetPath()
		dlg.Destroy()
		if path == "":
			return 1
	if not os.path.exists(path):
		wx.MessageBox("File does not exist", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
		return 1
	self.VMware_VM_path = "\"" + path + "\""
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)

    def ConfVMwarePathTovmrun (self, event):
	path = ""
	dir = "C:\\Program Files (x86)\\VMware\\VMware VIX\\"
	dlg = wx.FileDialog(
        	self, message="Choose a file", defaultDir=dir, 
        	defaultFile="vmrun", wildcard="*.exe", style=wx.OPEN | wx.MULTIPLE | wx.CHANGE_DIR
        	)
	dlg.SetFilterIndex(2)
	if dlg.ShowModal() == wx.ID_OK:
		path = dlg.GetPath()
		dlg.Destroy()
		if path == "":
			return 1
	if not os.path.exists(path):
		wx.MessageBox("File does not exist", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
		return 1
	self.VMware_vmrun_path = "\"" + path + "\""
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)

    def ConfVMwareProduct (self, event):
	try:
		cb = event.GetEventObject()
		self.VMware_product = cb.GetClientData(event.GetSelection())
		self.session_changed = True
		self.mb.Enable(self.ID_Save_Session, True)
		self.tb.EnableTool(self.ID_toolSaveFile, True)
	except:
		pass

    def ConfVMwareTimeout (self,event):
	try:
		cb = event.GetEventObject()
		timeout = cb.GetClientData(event.GetSelection())
		self.VMware_timeout = int(timeout)
		self.session_changed = True
		self.mb.Enable(self.ID_Save_Session, True)
		self.tb.EnableTool(self.ID_toolSaveFile, True)
	except:
		pass

    def OnOkVMwareConf (self, event):
	self.OkVMwareConf = True
	self.VMwareconfwin.Close()

    def	ControlVM (self):
	vmtype = ""
	command = ""
	if self.VMware_product == "Workstation":
		vmtype = "ws"
	if self.VMware_product == "VMware Server 1":
		vmtype = "server1"
	if self.VMware_product == "VMware Server 2":
		vmtype = "server"
	if self.VMware_product == "ESX":
		vmtype = "esx"
	if self.VMware_product == "vCenter Server":
		vmtype = "vc"
	if self.VMware_VM_path == "":
		wx.MessageBox("No VMware VM path configured", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
		return 1
 	if self.VMware_vmrun_path == "":
		wx.MessageBox("No VMware vmrun.exe path configured", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
		return 1 
	if self.VMware_product == "":
		wx.MessageBox("No VMware product configured", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
		return 1 
	if self.VMwareMode == "Process":
		if self.VMware_OS_username == "":
			wx.MessageBox("No VMware OS username configured", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
			return 1
		if self.VMware_OS_password == "":
			wx.MessageBox("No VMware OS password configured", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
			return 1
		if self.VMware_OS_process_name == "":
			wx.MessageBox("No VMware OS process name configured", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
			return 1
		# do process restart
		output_list = []
		tmp_list = []
		pid = ""
		found = False
		command = self.VMware_vmrun_path + " -T " + vmtype + " -gu "+ self.VMware_OS_username + " -gp " + self.VMware_OS_password + " listProcessesInGuest " + self.VMware_VM_path
		process = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		output = process.stdout.read()
		output_list = output.split('\n')
		x = 1
		while x < len (output_list) -1:
			tmp_list = output_list[x].split(',')
			if tmp_list[2] == " cmd=" + self.VMware_OS_process_name + "\r":
				found = True
				break
			x+=1
		if found == True:
			pid = tmp_list[0]
			pid = pid[4:]
			command = self.VMware_vmrun_path + " -T " + vmtype + " -gu "+ self.VMware_OS_username + " -gp " + self.VMware_OS_password + " killProcessInGuest " + self.VMware_VM_path + " " + pid
			process = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
			self.tc_output.AppendText("Status: VM target process killed\n")
			self.tc_output.ShowPosition(self.tc_output.GetLastPosition()-1)
			self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
			self.fplog.write("\nStatus: VM target process killed")
			time.sleep(1)
		command = self.VMware_vmrun_path + " -T " + vmtype + " -gu "+ self.VMware_OS_username + " -gp " + self.VMware_OS_password + " runProgramInGuest " + self.VMware_VM_path + " " + self.VMware_OS_process_name
		process = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		self.tc_output.AppendText("Status: VM target process restarted\n")
		self.tc_output.ShowPosition(self.tc_output.GetLastPosition()-1)
		time.sleep(1)
		process.kill()
	else:
		command = self.VMware_vmrun_path + " -T " + vmtype + " reset " + self.VMware_VM_path
		self.tc_output.AppendText("Status: Resetting VM - please wait.")
		self.tc_output.ShowPosition(self.tc_output.GetLastPosition()-1)
		process = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		timeout_seconds = self.VMware_timeout * 60
		x = 0
		while x < timeout_seconds:
			try:
				wx.Yield()
			except:
				pass
			time.sleep(1)
			self.tc_output.AppendText(".")
			self.tc_output.ShowPosition(self.tc_output.GetLastPosition()-1)
			x+=1
		self.tc_output.AppendText("Status: VM now reset\n")
		self.tc_output.ShowPosition(self.tc_output.GetLastPosition()-1)
		self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
		self.fplog.write("\nStatus: VM now reset")

#------------------------------------------------------------------------------------------------------------------------------------------
#--- SMTP Control -------------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------------
# CreateSMTPConfWindow()
# ConfigureSMTP()
# ConfSMTPAddress()
# ConfSMTPUsername()
# ConfSMTPPassword()
# ConfSMTPFromAddress()
# ConfSMTPToAddress()
# SetTLSMode()
# OnOkSMTPConf()
# SendEmail()
#------------------------------------------------------------------------------------------------------------------------------------------

    def CreateSMTPConfWindow (self):
	win = wx.Frame(self, -1, "Email configuration",size=(300,300), style=wx.TAB_TRAVERSAL | wx.FRAME_FLOAT_ON_PARENT | wx.CAPTION | wx.FRAME_TOOL_WINDOW)
	win.Center()
	win.Show(True)
	win.SetBackgroundColour("White")
	path = self.workingdir
	path = path + "\\..\\images\\zulu_logo16x16.png"
 	image = wx.Image(path, wx.BITMAP_TYPE_PNG).ConvertToBitmap() 
	icon = wx.EmptyIcon() 
	icon.CopyFromBitmap(image) 
	win.SetIcon(icon) 
	return win

    def	ConfigureSMTP (self,evt):
	self.OkSMTPConf = False
	self.SMTPconfwin = self.CreateSMTPConfWindow()
	self.SMTPconfwin.SetFocus()
	vs = wx.BoxSizer( wx.VERTICAL )
	box1_title = wx.StaticBox( self.SMTPconfwin, -1, "Configue email settings" )
	box1 = wx.StaticBoxSizer( box1_title, wx.VERTICAL )
	grid1 = wx.FlexGridSizer( 0, 2, 0, 0 )
	self.conf_ctrls = []       
	text1 = wx.StaticText(self.SMTPconfwin, -1, "SMTP Server address:Port")	
	text2 = wx.TextCtrl( self.SMTPconfwin, -1, self.smtp_server)
	text3 = wx.StaticText(self.SMTPconfwin, -1, "SMTP Username:")	
	text4 = wx.TextCtrl( self.SMTPconfwin, -1, self.smtp_login)
	text5 = wx.StaticText(self.SMTPconfwin, -1, "SMTP password:")	
	text6 = wx.TextCtrl( self.SMTPconfwin, -1, self.smtp_password, style=wx.TE_PASSWORD)
	text7 = wx.StaticText(self.SMTPconfwin, -1, "SMTP From address:")	
	text8 = wx.TextCtrl( self.SMTPconfwin, -1, self.smtp_from)
	text9 = wx.StaticText(self.SMTPconfwin, -1, "SMTP To address:")	
	text10 = wx.TextCtrl( self.SMTPconfwin, -1, self.smtp_to)
	cb_TLS = wx.CheckBox(self.SMTPconfwin, -1, "Use TLS")
	if self.tls == True:
		cb_TLS.SetValue(True)
	grid1.Add( text1, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( text2, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( text3, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( text4, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( text5, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( text6, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( text7, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( text8, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( text9, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( text10, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	grid1.Add( cb_TLS, 0, wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
	box1.Add( grid1, 0, wx.ALIGN_CENTRE|wx.ALL, 5 )
	vs.Add( box1, 0, wx.ALIGN_CENTRE|wx.ALL, 5 )
	button = wx.Button(self.SMTPconfwin, 1005, "OK")
	self.SMTPconfwin.Bind(wx.EVT_BUTTON, self.OnOkSMTPConf, button)
	vs.Add( button, 0, wx.ALIGN_CENTRE|wx.ALL, 5 )
	self.SMTPconfwin.Bind(wx.EVT_TEXT, self.ConfSMTPAddress, text2)
	self.SMTPconfwin.Bind(wx.EVT_TEXT, self.ConfSMTPUsername, text4)
	self.SMTPconfwin.Bind(wx.EVT_TEXT, self.ConfSMTPPassword, text6)
	self.SMTPconfwin.Bind(wx.EVT_TEXT, self.ConfSMTPFromAddress, text8)
	self.SMTPconfwin.Bind(wx.EVT_TEXT, self.ConfSMTPToAddress, text10)
	self.SMTPconfwin.Bind(wx.EVT_CHECKBOX, self.SetTLSMode, cb_TLS)
	self.SMTPconfwin.SetSizer( vs )
	vs.Fit( self.SMTPconfwin )
	while self.OkSMTPConf == False:
		try:
			wx.Yield()
		except:
			pass

    def	ConfSMTPAddress (self, event):
	try:
		self.smtp_server = event.GetString()
		self.session_changed = True
		self.mb.Enable(self.ID_Save_Session, True)
		self.tb.EnableTool(self.ID_toolSaveFile, True)
	except:
		pass

    def ConfSMTPUsername (self, event):
	try:
		self.smtp_login = event.GetString()
		self.session_changed = True
		self.mb.Enable(self.ID_Save_Session, True)
		self.tb.EnableTool(self.ID_toolSaveFile, True)
	except:
		pass

    def ConfSMTPPassword (self, event):
	try:
		self.smtp_password = event.GetString()
		self.session_changed = True
		self.mb.Enable(self.ID_Save_Session, True)
		self.tb.EnableTool(self.ID_toolSaveFile, True)
	except:
		pass

    def ConfSMTPFromAddress (self, event):
	try:
		self.smtp_from = event.GetString()
		self.session_changed = True
		self.mb.Enable(self.ID_Save_Session, True)
		self.tb.EnableTool(self.ID_toolSaveFile, True)
	except:
		pass

    def ConfSMTPToAddress (self, event):
	try:
		self.smtp_to = event.GetString()
		self.session_changed = True
		self.mb.Enable(self.ID_Save_Session, True)
		self.tb.EnableTool(self.ID_toolSaveFile, True)
	except:
		pass

    def	SetTLSMode(self,event):
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)
	if event.IsChecked() == 1:
		self.tls = True
	else:
		self.tls = False

    def OnOkSMTPConf (self, event):
	self.OkSMTPConf = True
	self.SMTPconfwin.Close()

    def	SendEmail(self, name): 
	msg = MIMEMultipart('alternative') 
	s = smtplib.SMTP(self.smtp_server) 
	s.ehlo() 
	if self.tls == True:
		s.starttls()
	s.ehlo() 
	s.login(self.smtp_login, self.smtp_password) 
	msg['Subject'] = 'Fuzzer results: The target has crashed - a PoC is attached' 
	msg['From'] = "Zulu fuzzer" 
	body = 'message' 
	content = MIMEText(body, 'plain') 
	filename = self.PoC_filename 
	f = file(filename) 
	attachment = MIMEText(f.read()) 
	attachment.add_header('Content-Disposition', 'attachment', filename=name)            
	msg.attach(attachment)
	s.sendmail(self.smtp_from, self.smtp_to, msg.as_string()) 
	s.quit()

#------------------------------------------------------------------------------------------------------------------------------------------
#--- Session and Log Files ----------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------------
# ConfigureLogfile()
# SaveAsSession()
# SaveSession()
# OpenSession()
#------------------------------------------------------------------------------------------------------------------------------------------

    def ConfigureLogfile (self,event):
	path = ""
	dir = self.workingdir
	dir += "\\..\\logs\\"
	dlg = wx.FileDialog(self, message="Change log file location", defaultDir=dir ,defaultFile="Zulu_logfile", wildcard="*.log", style=wx.SAVE)
	dlg.SetFilterIndex(2)
	if dlg.ShowModal() == wx.ID_OK:
		path = dlg.GetPath()
		dlg.Destroy()
	if path == "":
		return 1
	path = path[:-4]	# remove .log
	self.fplog.close()
	newpath = path + time.strftime("_%Y-%m-%d_%H-%M-%S", time.localtime()) + ".log"
	self.fplog = file(newpath, 'a')	# open new logfile for writing
	self.fplog.write("\n\n**** Zulu Log file ****\n\n")
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)

    def SaveAsSession(self,event):
	self.sessionfile = ""
	self.SaveSession(1)

    def SaveSession(self, event):
	if not self.sessionfile:
		path = ""
		newdirectory = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
		dir = self.workingdir
		dir += "\\..\\sessions\\" + newdirectory + "\\"
		os.makedirs(dir)
		dlg = wx.FileDialog(
           	 self, message="Save file as ...", defaultDir=dir, 
            	defaultFile="session", wildcard="*.zulu", style=wx.SAVE
            	)
		dlg.SetFilterIndex(2)
		if dlg.ShowModal() == wx.ID_OK:
			path = dlg.GetPath()
			dlg.Destroy()
		if path == "":
			return 1
	else:
		path = self.sessionfile
	try:
		fp = file(path, 'w')	# open file for writing 
	except:
		wx.MessageBox("Error opening session file", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
	fp.write("PORT=%d\n" % self.port)
	fp.write("TARGETHOST=%s\n" % self.targethost)
	fp.write("TARGETPORT=%d\n" % self.targetport)
	fp.write("RECEIVEPACKETFIRST=%d\n" % int(self.receivepacketfirst))
	fp.write("LOGFILEPATH=%s\n" % self.logfilepath)
	fp.write("USEUDP=%d\n" % int(self.udp))
	fp.write("FUZZER=%s\n" % self.fuzzer)
	fp.write("CAPTURE=%s\n" % self.capture_type)
	
	fp.write("SMTP_SERVER=%s\n" % self.smtp_server)
	fp.write("SMTP_LOGIN=%s\n" % self.smtp_login)
	fp.write("SMTP_PASSWORD=%s\n" % self.smtp_password)
	fp.write("SMTP_FROM=%s\n" % self.smtp_from)
	fp.write("SMTP_TO=%s\n" % self.smtp_to)
	fp.write("SMTP_TLS=%d\n" % int(self.tls))

	fp.write("VMWARE_OS_USERNAME=%s\n" % self.VMware_OS_username)
	fp.write("VMWARE_OS_PASSWORD=%s\n" % self.VMware_OS_password)
	fp.write("VMWARE_OS_PROCESS_NAME=%s\n" % self.VMware_OS_process_name)
	fp.write("VMWARE_VM_PATH=%s\n" % self.VMware_VM_path)
	fp.write("VMWARE_VMRUN_PATH=%s\n" % self.VMware_vmrun_path)
	fp.write("VMWARE_PRODUCT=%s\n" % self.VMware_product)
	fp.write("VMWARE_MODE=%s\n" % self.VMwareMode)
	fp.write("VMWARE_ENABLED=%d\n" % int(self.VMwareEnabled))
	fp.write("VMWARE_TIMEOUT=%d\n" % self.VMware_timeout)

	fp.write("TCP_CONNECT_RETRIES=%d\n" % self.fuzz_retries)
	fp.write("RECEIVE_TIMEOUT=%.1f\n" % self.Receive_timeout)
	fp.write("FUZZCASE_DELAY=%.1f\n" % self.fuzz_delay)

	fp.write("PROCESS_TO_FUZZ=%s\n" % self.process_to_fuzz)
	fp.write("PROCESS_COMMAND_ARGS=%s\n" % self.process_command_args)
	fp.write("PROCESS_RUN_TIME=%.1f\n" % self.process_run_time)
	fp.write("PROCESS_TERMINATE_TYPE=%s\n" % self.process_termiate_type)

	fp.write("WIRESHARK_ENABLED=%d\n" % int(self.wireshark_enabled))
	fp.write("WIRESHARK_PATH=%s\n" % self.wiresharkpath)

	fp.write("ENABLE_ZULUSCRIPT=%d\n" % int(self.custom_script))

	fp.write("TESTCASE_BUFFER_OVERFLOW=%d\n" % int(self.buffer_overflow))
	fp.write("TESTCASE_FORMAT_STRING=%d\n" % int(self.formatstring))
	fp.write("TESTCASE_SINGLE_BYTE=%d\n" % int(self.singlebyte))
	fp.write("TESTCASE_DOUBLE_BYTE=%d\n" % int(self.doublebyte))
	fp.write("TESTCASE_QUAD_BYTE=%d\n" % int(self.quadbyte))
	fp.write("TESTCASE_NULL=%d\n" % int(self.nullcase))
	fp.write("TESTCASE_UNIX=%d\n" % int(self.unixcase))
	fp.write("TESTCASE_WINDOWS=%d\n" % int(self.windowscase))
	fp.write("TESTCASE_XML=%d\n" % int(self.xmlcase))
	fp.write("TESTCASE_USER_DEFINED=%d\n" % int(self.userdefined))
	fp.write("TESTCASE_CONTROL_CHARS=%d\n" % int(self.controlcase))
	fp.write("TESTCASE_EXTENDED_ASCII=%d\n" % int(self.extendedcase))
	fp.write("TESTCASE_BYTE_BITSWEEP=%d\n" % int(self.bitbyte))
	fp.write("TESTCASE_WORD_BITSWEEP=%d\n" % int(self.bitword))
	fp.write("TESTCASE_LONG_BITSWEEP=%d\n" % int(self.bitlong))
	fp.write("TESTCASE_BYTE_BITSWEEP_INV=%d\n" % int(self.bitbyteinv))
	fp.write("TESTCASE_WORD_BITSWEEP_INV=%d\n" % int(self.bitwordinv))
	fp.write("TESTCASE_LONG_BITSWEEP_INV=%d\n" % int(self.bitlonginv))

	fp.write("USB_GRAPHICUSB_PATH=%s\n" % self.GraphicUSB_path)
	fp.write("USB_TARGET_ADDRESS=%s\n" % self.usb_target_ip_address)
	fp.write("USB_TEMP_SCRIPT=%s\n" % self.usb_temp_gen_script)

	if (self.packets_to_send):
		x = 0
		while x < len(self.packets_to_send):
			packetnum = self.packets_to_send[x][0]
			start = self.packets_to_send[x][1][0]
			end = self.packets_to_send[x][1][1]
			fp.write("FUZZPOINT=")
			fp.write("%d,%d,%d" % (packetnum,start,end))
			fp.write("\n")
			x+=1
	if (self.LengthFields):
		x = 0
		while x < len(self.LengthFields):
			field_size = self.LengthFields[x][0]
			field_pos = self.LengthFields[x][1]
			start = self.LengthFields[x][2]
			end = self.LengthFields[x][3]
			packetnum = self.LengthFields[x][4]
			byte_order = self.LengthFields[x][5]
			fp.write("LENGTH=")
			fp.write("%d,%d,%d,%d,%d,%d" % (field_size,field_pos,start,end,packetnum,byte_order))
			fp.write("\n")
			x+=1
	x = 0	
	while x < len (self.packets):
		ip = self.packets[x][0][0]
		port = self.packets[x][0][1]
		data = self.packets[x][1]
		newpath = path + ".packet%d" % x
		try:
			fpp = file(newpath, 'wb')	# open file for writing 
		except:
			wx.MessageBox("Error opening packet file", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
		fpp.write(ip)
		fpp.write("\n")
		fpp.write("%d" % port)
		fpp.write("\n")
		fpp.write("%s" % data)
		fpp.close()
		x+=1
	self.session_changed = False
	self.mb.Enable(self.ID_Save_Session, False)
	self.tb.EnableTool(self.ID_toolSaveFile, False)
	self.sessionfile = path
	self.parent.Title = "Zulu - " + path
	fp.close()  

    def OpenSession(self, evt):
	if self.firstloaded == False:
		self.ResetEverything()
	datalist = []
	path = ""
	tmpcomment = []
	entries = []
	entries_item = []
	dir = self.workingdir
	if self.firstloaded == False:
		dir += "\\..\\sessions\\"
		dlg = wx.FileDialog(
            	self, message="Choose a file", defaultDir=dir, 
            	defaultFile="default", wildcard="*.zulu", style=wx.OPEN | wx.MULTIPLE | wx.CHANGE_DIR
            	)
		dlg.SetFilterIndex(2)
		if dlg.ShowModal() == wx.ID_OK:
			path = dlg.GetPath()
			dlg.Destroy()
			if path == "":
				return 1
	else:
		path = self.workingdir[:-4] + "\\conf\\default.conf"
	if not os.path.exists(path):
		wx.MessageBox("File does not exist", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
		return 1
	try:
		fp = file(path, 'r')	# open file for reading
	except:
		wx.MessageBox("Error opening file", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
	if self.firstloaded == False:
		self.sessionfile = path
	data = fp.read()
	datalist = data.split('\n')
	item = []
	x = 0
	while x < len(datalist):
		entries = []
		entries_item = []
		item = datalist[x].split('=')
		if item[0] == "PORT":
			self.port = int(item[1]) 
		if item[0] == "TARGETHOST":
			temptargethost = item[1]
		if item[0] == "TARGETPORT":
			temptargetport = int(item[1])
		if item[0] == "RECEIVEPACKETFIRST":
			self.receivepacketfirst = int(item[1])
		if item[0] == "LOGFILEPATH":
			self.logfilepath = item[1]
		if item[0] == "USEUDP":
			self.udp = int(item[1])
		if item[0] == "FUZZER":
			self.fuzzer = item[1]
		if item[0] == "CAPTURE":
			self.capture_type = item[1]
		if item[0] == "SMTP_SERVER":
			self.smtp_server = item[1]
		if item[0] == "SMTP_LOGIN":
			self.smtp_login = item[1]
		if item[0] == "SMTP_PASSWORD":
			self.smtp_password = item[1]
		if item[0] == "SMTP_FROM":
			self.smtp_from = item[1]
		if item[0] == "SMTP_TO":
			self.smtp_to = item[1]
		if item[0] == "SMTP_TLS":
			self.tls = int(item[1])

		if item[0] == "VMWARE_OS_USERNAME":
			self.VMware_OS_username = item[1]
		if item[0] == "VMWARE_OS_PASSWORD":
			self.VMware_OS_password = item[1]
		if item[0] == "VMWARE_OS_PROCESS_NAME":
			self.VMware_OS_process_name = item[1]
		if item[0] == "VMWARE_VM_PATH":
			self.VMware_VM_path = item[1]
		if item[0] == "VMWARE_VMRUN_PATH":
			self.VMware_vmrun_path = item[1]
		if item[0] == "VMWARE_PRODUCT":
			self.VMware_product = item[1]
		if item[0] == "VMWARE_MODE":
			self.VMwareMode = item[1]
		if item[0] == "VMWARE_ENABLED":
			self.VMwareEnabled = int(item[1])
		if item[0] == "VMWARE_TIMEOUT":
			self.VMware_timeout = int(item[1])

		if item[0] == "TCP_CONNECT_RETRIES":
			self.fuzz_retries = int(item[1])
		if item[0] == "RECEIVE_TIMEOUT":
			self.Receive_timeout = float(item[1])
		if item[0] == "FUZZCASE_DELAY":
			self.fuzz_delay = float(item[1])

		if item[0] == "PROCESS_TO_FUZZ":
			self.process_to_fuzz = item[1]
		if item[0] == "PROCESS_COMMAND_ARGS":
			self.process_command_args = item[1]
		if item[0] == "PROCESS_RUN_TIME":
			self.process_run_time = float(item[1])
		if item[0] == "PROCESS_TERMINATE_TYPE":
			self.process_termiate_type = item[1]

		if item[0] == "WIRESHARK_ENABLED":
			self.wireshark_enabled = int(item[1])
		if item[0] == "WIRESHARK_PATH":
			self.wiresharkpath = item[1]

		if item[0] == "ENABLE_ZULUSCRIPT":
			self.custom_script = int(item[1])

		if item[0] == "TESTCASE_BUFFER_OVERFLOW":
			self.buffer_overflow = int(item[1])
		if item[0] == "TESTCASE_FORMAT_STRING":
			self.formatstring = int(item[1])
		if item[0] == "TESTCASE_SINGLE_BYTE":
			self.singlebyte = int(item[1])
		if item[0] == "TESTCASE_DOUBLE_BYTE":
			self.doublebyte = int(item[1])
		if item[0] == "TESTCASE_QUAD_BYTE":
			self.quadbyte = int(item[1])
		if item[0] == "TESTCASE_NULL":
			self.nullcase = int(item[1])
		if item[0] == "TESTCASE_UNIX":
			self.unixcase = int(item[1])
		if item[0] == "TESTCASE_WINDOWS":
			self.windowscase = int(item[1])
		if item[0] == "TESTCASE_XML":
			self.xmlcase = int(item[1])
		if item[0] == "TESTCASE_USER_DEFINED":
			self.userdefined = int(item[1])
		if item[0] == "TESTCASE_CONTROL_CHARS":
			self.controlcase = int(item[1])
		if item[0] == "TESTCASE_EXTENDED_ASCII":
			self.extendedcase = int(item[1])
		if item[0] == "TESTCASE_BYTE_BITSWEEP":
			self.bitbyte = int(item[1])
		if item[0] == "TESTCASE_WORD_BITSWEEP":
			self.bitword = int(item[1])
		if item[0] == "TESTCASE_LONG_BITSWEEP":
			self.bitlong = int(item[1])
		if item[0] == "TESTCASE_BYTE_BITSWEEP_INV":
			self.bitbyteinv = int(item[1])
		if item[0] == "TESTCASE_WORD_BITSWEEP_INV":
			self.bitwordinv = int(item[1])
		if item[0] == "TESTCASE_LONG_BITSWEEP_INV":
			self.bitlonginv = int(item[1])

		if item[0] == "USB_GRAPHICUSB_PATH":
			self.GraphicUSB_path = item[1]
		if item[0] == "USB_TARGET_ADDRESS":
			self.usb_target_ip_address = item[1]
		if item[0] == "USB_TEMP_SCRIPT":
			self.usb_temp_gen_script = item[1]

		if item[0] == "FUZZPOINT":
			entries = item[1].split(',')
			entries[0] = int(entries[0])
			entries[1] = int(entries[1])
			entries[2] = int(entries[2])
			entries_item.append(entries[0])
			entries.pop(0)
			entries_item.append(entries)
			self.packets_to_send.append(entries_item)
			self.tb.EnableTool(self.ID_toolFuzzerStart, True)
			self.mb.Enable(self.ID_Start_Fuzzing, True)
			self.btn_ClearAllFuzzPoints.Enable(True)

		if item[0] == "LENGTH":
			entries = item[1].split(',')
			entries[0] = int(entries[0])
			entries[1] = int(entries[1])
			entries[2] = int(entries[2])
			entries[3] = int(entries[3])
			entries[4] = int(entries[4])
			entries[5] = int(entries[5])
			self.LengthFields.append(entries)
			self.btn_ClearAllFuzzPoints.Enable(True)	
		x+=1

	# update checkboxes
	self.EnableCheckboxes()

	# update fuzzpoints window
	self.UpdateDataModificationPoints()

	if self.firstloaded == True:
		fp.close()
		self.firstloaded = False
		self.targethost = temptargethost
		self.targetport = temptargetport
		return
	else:
		# load in packet data
		path = path[:-5]
		packetentrylist = []
		filenumber = 0
		while (1):
			pktfile = path + ".zulu.packet" + "%d" % filenumber
			try:
				fp = file(pktfile, 'r')	# open file for reading
			except:
				break
			data = fp.read()
			x = 0
			ip_address = ""
			port = ""
			realdata = ""
			tmplist = []
			tmplist2 = []
			while data[x] != "\x0a":
				ip_address += data[x]
				x+=1
			x+=1
			while data[x] != "\x0a":
				port += data[x]
				x+=1
			x+=1
			while x < len(data):
				realdata += data[x]
				x+=1
			tmplist.append(ip_address)
			tmplist.append(port)
			tmplist[1] = int(tmplist[1])
			tmplist2.append(tmplist)
			tmplist2.append(realdata)
			self.packets.append(tmplist2)
			filenumber +=1		
		self.targethost = temptargethost
		self.targetport = temptargetport
		self.process_input_data()
		self.parent.Title = "Zulu - " + path
		fp.close() 

#------------------------------------------------------------------------------------------------------------------------------------------
#--- Misc Networking ----------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------------------------------
# PacketTest()
# LaunchPoC()
# SetUDPMode()
# CreatePoc()
# ConnectionToClose()
# ping()
#------------------------------------------------------------------------------------------------------------------------------------------

    def	PacketTest(self,event):
	print "packet test"
	packet_data_list = []
	packet_data_list_in = []
	if self.udp == False:
		self.test_sock = socket(AF_INET, SOCK_STREAM)
	else:
		self.test_sock = socket(AF_INET, SOCK_DGRAM)
	self.test_sock.settimeout(self.Receive_timeout)
	try:
		self.test_sock.connect((self.targethost, self.targetport))
	except:
		message = "Packet test: Connect error - attempt\n"
		print "----------------------------------------------------"
		print message
		print "----------------------------------------------------"
 		self.tc_output.AppendText(message)
		self.tc_output.ShowPosition(self.tc_output.GetLastPosition()-1)
		self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
		self.fplog.write(message)
	x = 0
	while x < len(self.packets):
		tmplist = []
		if len(self.packets[x][1]) != 0:
			if self.packets[x][0][1] != self.targetport:
				tmplist.append(x)
				tmplist.append(self.packets[x][1])
				packet_data_list.append(tmplist)
			else:
				tmplist.append(x)
				tmplist.append(self.packets[x][1])
				packet_data_list_in.append(tmplist)
			
		x+=1
	x = 0
	while x < len (packet_data_list):
		data = packet_data_list[x][1]
		if self.receivepacketfirst == False:
			try:
				wx.Yield()
			except:
				pass
			packetnum = packet_data_list[x][0]
			recv_packetnum = packetnum + 1
			#----------------- send packet------------------------------
			out =  "Sending packet #%d" % packetnum
			print out
			self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
			self.fplog.write(out)
			self.fplog.write("\n")
			try:
				self.test_sock.send(data)
				print repr(data)
				self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
				self.fplog.write(repr(data))
				self.fplog.write("\n")
				print
			except:
		 		out =  "Error sending packet #%d" % packetnum
				print out
				self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
				self.fplog.write(out)
				self.fplog.write("\n")
				print
				break
			#----------------- receive packet---------------------------
			out =  "Receiving packet #%d" % recv_packetnum
			print out
			self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
			self.fplog.write(out)
			self.fplog.write("\n")
			try:
				buf = self.test_sock.recv(5000)
				print repr(buf)
				self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
				self.fplog.write(repr(buf))
				self.fplog.write("\n")
				print
			except:
		 		out =  "Error receiving packet #%d" % recv_packetnum
				print out
				self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
				self.fplog.write(out)
				self.fplog.write("\n")
				print
				break
		else:
			try:
				wx.Yield()
			except:
				pass
			recv_packetnum = packet_data_list[x][0]
			packetnum = recv_packetnum + 1
			#----------------- receive packet---------------------------
			out =  "Receiving packet #%d" % recv_packetnum
			print out
			self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
			self.fplog.write(out)
			self.fplog.write("\n")
			try:
				buf = self.test_sock.recv(5000)
				print repr(buf)
				self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
				self.fplog.write(repr(buf))
				self.fplog.write("\n")
				print
			except:
		 		out =  "Error receiving packet #%d" % recv_packetnum
				print out
				self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
				self.fplog.write(out)
				self.fplog.write("\n")
				print
				break
			#----------------- send packet------------------------------
				
			out =  "Sending packet #%d" % packetnum
			print out
			self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
			self.fplog.write(out)
			self.fplog.write("\n")
			try:
				self.test_sock.send(data)
				print repr(data)
				self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
				self.fplog.write(repr(data))
				self.fplog.write("\n")
				print
			except:
		 		out =  "Error sending packet #%d" % packetnum
				print out
				self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
				self.fplog.write(out)
				self.fplog.write("\n")
				print
				break
			#----------------- receive packet---------------------------
			out =  "Receiving packet #%d" % recv_packetnum
			print out
			self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
			self.fplog.write(out)
			self.fplog.write("\n")
			try:
				buf = self.test_sock.recv(5000)
				print repr(buf)
				self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
				self.fplog.write(repr(buf))
				self.fplog.write("\n")
				print
			except:
		 		out =  "Error receiving packet #%d" % recv_packetnum
				print out
				self.fplog.write(time.strftime("%H:%M:%S  ", time.localtime()))
				self.fplog.write(out)
				self.fplog.write("\n")
				print
				break
		x+=1

    def	LaunchPoC (self, event):
	if self.latest_PoC == "":
		return
	self.tc_output.AppendText("Status: Launching latest PoC\n")
	self.tc_output.ShowPosition(self.tc_output.GetLastPosition()-1)
	command = "python.exe " + self.latest_PoC + " " + self.targethost + " " + "%d" % self.targetport
	process = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	self.tc_output.AppendText("Status: Latest PoC executed\n")
	self.tc_output.ShowPosition(self.tc_output.GetLastPosition()-1)

    def	SetUDPMode(self,event):
	self.session_changed = True
	self.mb.Enable(self.ID_Save_Session, True)
	self.tb.EnableTool(self.ID_toolSaveFile, True)
	if event.IsChecked() == 1:
		self.udp = True
	else:
		self.udp = False

    def CreatePoc (self):
	path = self.workingdir
	path = path + "\\..\\templates\\Zulu_PoC.template.txt"
	try:
		fp = file(path, 'r')	# open file for reading 
	except:
		wx.MessageBox("Error opening PoC template file", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
	template = fp.read()
	insert = "%s" % repr(self.last_packet_data_list)
	newpoc = string.replace(template, "[DATA]", insert)
	fp.close
	newfile = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
	path = self.workingdir[:-3]
	path = path + "\\PoC\\PoC_" + newfile + "_PoC.py"
	self.PoC_filename = path
	self.latest_PoC = path
	self.tb.EnableTool(self.ID_toolExploit, True)
	try:
		fp = file(path, 'w')	# open file for writing 
	except:
		wx.MessageBox("Error opening PoC file", caption="Error", style=wx.OK|wx.ICON_ERROR, parent=self)
	fp.write(newpoc)
	fp.close()
	name = newfile + "_PoC.py"
	try:
		self.SendEmail(name)
	except:
		print time.strftime("%H:%M:%S  ", time.localtime()),
		print "Email send failure - please check SMTP settings"
		pass

    def ConnectionToClose(self):
	s = socket(AF_INET, SOCK_STREAM)
	s.connect(("127.0.0.1", self.port))
	s.close()

    def ping(self, host):
    	result = subprocess.call(["ping","-w","500","-n","1",host],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    	if result == 0:
        	return True
    	elif result == 1:
        	raise Exception('Host not found')
    	elif result == 2:
        	raise Exception('Ping timed out')

#------------------------------------------------------------------------------------------------------------------------------------------

app = wx.App(False)  
frame = wx.Frame(None, wx.ID_ANY, "Zulu - the interactive fuzzer", size=(1130,840), style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER ^ wx.MAXIMIZE_BOX ) 

win = MainPanel(frame)
frame.Show(True) 
frame.Center()   
app.MainLoop()
