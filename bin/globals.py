#!/usr/bin/env python
# -*- coding: utf-8 -*-

__VERSION__ = '1.0alpha'
DEFAULT_TITLE = 'Serial Data Capture' 

WELCOME_INFO = ''

#15000 mil seconds for autosave period
AUTOSAVE_PERIOD = 15000

#when unprintable is enabled, it will output 20 characters per line
OUTPUT_PERLINE = 35

# value of newline settings
CRLF = 0
CR = 1
LF = 2

#properties of serial.
S_PORT = 1
S_BAUDRATE = 9600
S_BYTESIZE = 7
S_STOPBITS = 1
S_PARITY = 'E'
S_RTSCTS = False
S_XONXOFF = False
    
#properties of display settings
D_ECHO = False
D_NEWLINE = CRLF
D_UNPRINTABLE = True
D_FOREGROUND_COLOR = '(255,255,0)'
D_BACKGROUND_COLOR = '(255,255,255)'
D_DEFAULT_FONT = 'Courier 10 Pitch-12'
#D_DEFAULT_FONT = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL, False, u'Courier 10 Pitch')

if __name__ == '__main__':
    print 'this file can\'t be executed.'
