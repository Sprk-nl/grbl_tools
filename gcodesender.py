#!/usr/bin/python
"""\
Simple g-code streaming script
https://github.com/bborncr/gcodesender.py/blob/master/gcodesender.py
"""

import serial
import time
import argparse
import re

PosCheck = re.compile(
'(?i)^[gG0-3]{1,3}(?:\s+x-?(?P<x>[0-9.]{1,15})|\s+y-?(?P<y>[0-9.]{1,15})|\s+z-?(?P<z>[0-9.]{1,15}))*$')


## degrees of pen state:
pen_up   = 60
pen_down = 100
pen_state_up = True
dicti = []

parser = argparse.ArgumentParser(description='This is a basic gcode sender. http://crcibernetica.com')
parser.add_argument('-p','--port',help='Input USB port', nargs="?", default="/dev/ttyUSB0")
parser.add_argument('file', help='Gcode file name')
args = parser.parse_args()

## show values ##
print ("USB Port: %s" % args.port )
print ("Gcode file: %s" % args.file )

def gcode_print(message):
    i = PosCheck.match(message)
    if i:
        print(i.groupdict())
    else:
        #print(position_response, '->', None)
        print(message)
        pass

def pen_check(z_position):
    global pen_up
    global pen_down
    global pen_state_up
    returndata = None
    if float(z_position) >= 1 and pen_state_up == False:
        print("Pen -> UP")
        pen_state_up = True
        returndata = "M3 S" + str(pen_up)
    if float(z_position) < 1 and pen_state_up == True:
        print("Pen -> Down")
        pen_state_up = False
        returndata = "M3 S" + str(pen_down)
    else:
        pass
    print("returning data: {}".format(returndata))
    return returndata


def pen_rewrite(message):
    i = PosCheck.match(message)
    returndata = None
    if i:
        dicti = i.groupdict()
        if "z" in dicti is not None:
            z_value = dicti.get('z')
            # print(z_value)
            try:
                z_value = float(z_value)
                # ("returning {}".format(z_value))
                returndata = pen_check(z_value)
            except:
                pass
        else:
            pass
    else:
        #print(position_response, '->', None)
        pass
    return returndata

def removeComment(string):
    if (string.find(';')==-1):
        return string
    else:
        return string[:string.index(';')]

# Open serial port
#s = serial.Serial('/dev/ttyACM0',115200)
s = serial.Serial(args.port,115200)
print ('Opening Serial Port')

# Open g-code file
#f = open('/media/UNTITLED/shoulder.g','r');
f = open(args.file,'r');
print ('Opening gcode file')

# Wake up
message = "\r\n\r\n" # Hit enter a few times to wake the Printrbot
s.write(message.encode()) # Send g-code block
time.sleep(2)   # Wait for Printrbot to initialize
s.flushInput()  # Flush startup text in serial input
print ('Keep in mind, the bot has a buffer of about 16 lines')
print ('Pen movements and rotations differ from screen buffer')
print ('Sending gcode')

# Stream g-code
for line in f:
    l = removeComment(line)
    l = l.strip() # Strip all EOL characters for streaming
    if  (l.isspace()==False and len(l)>0) :
        #print ('Sending: ' + l)
        message = (l + '\n')
        gcode_print(message)

        pen_message = pen_rewrite(message)
        if pen_message: # check if there is pen movement needed
            print("we need pen movement")
            s.write(pen_message.encode()) # Send pen g-code block

        s.write(message.encode()) # Send g-code block
        grbl_out = s.readline() # Wait for response with carriage return
        #print (' : ' + str(grbl_out).strip())

# Wait here until printing is finished to close serial port and file.
prompt_data = input('  Press <Enter> to exit.')
print (prompt_data)


# Close file and serial port
f.close()
s.close()
