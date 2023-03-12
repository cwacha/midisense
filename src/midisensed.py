#!/usr/bin/env python

from sense_hat import SenseHat
import re
import subprocess
import time
import signal
import os
import sys
import argparse

VERSION = "1.0.0"

sense = SenseHat()
known_devices = []
done = False
update_now = False
verbose = False

class Cursor:
	x = 0
	y = 0

cursor = Cursor()

black = (0, 0, 0)
green = (0, 255, 0)
blue = (0, 0, 255)
red = (255, 0, 0)

color_upper = green
color_lower = blue
color_number = red
color_special = black

# File mode creation mask of the daemon.
UMASK = 0

# Default working directory for the daemon.
WORKDIR = "/"

def logmsg(msg, level="INFO"):
	level = str.upper(level)
	
	if(level == "DEBUG" or level == "INFO"):
		if(verbose):
			print(f"{level}: {msg}")
	elif(level == "WARN" or level == "ERROR"):
		print(f"{level}: {msg}")
	else:
		print(f"{level}: {msg}")

def createDaemon():
	"""Detach a process from the controlling terminal and run it in the
	background as a daemon.
	"""

	try:
		pid = os.fork()
	except OSError as e:
		raise Exception("%s [%d]" % (e.strerror, e.errno))

	if (pid != 0):
		# parent
		os._exit(0)

	# first child.
	os.setsid()
	try:
		pid = os.fork()
	except OSError as e:
		raise Exception("%s [%d]" % (e.strerror, e.errno))

	if (pid != 0):
		# parent of first child
		os._exit(0)

	# second child
	os.chdir(WORKDIR)
	os.umask(UMASK)


def getLetterClass(letter):
	if letter == None:
		return 0

	if re.match("[a-z]", letter):
		return 1
	elif re.match("[A-Z]", letter):
		return 2
	elif re.match("[0-9]", letter):
		return 3
	else:
		return 4
	
def RenderMiniText(text):
	pixels = []

	text = text[:8]
	for letter in text:
		if getLetterClass(letter) == 1:
			pixels.append(color_lower)
		elif getLetterClass(letter) == 2:
			pixels.append(color_upper)
		elif getLetterClass(letter) == 3:
			pixels.append(color_number)
		else:
			pixels.append(color_special)

	return pixels

def RenderMiniText_plus(text):
	pixels = []
	
	tmp = [None] * 8
	
	f = 8 / len(text)
	if f > 1:
		f = 1
		
	#print("f=%f orig len=%d" % (f, len(text)))
	for i in range(len(text)):
		ti = round(f*i) 
		if(ti > 7):
			ti = 7
		#print("%s origin index=%d target index=%d" % (text[i], i, ti))
		c1 = getLetterClass(tmp[ti])
		c2 = getLetterClass(text[i])
		if(c1 < c2):
			tmp[ti] = text[i]
	
	while(tmp[-1] == None):
		tmp.pop()
		
	#print(tmp)
	text = "".join(tmp)

	return RenderMiniText(text)

def DrawMiniText(text):
	pixels = RenderMiniText_plus(text)
	
	for pixel in pixels:
		sense.set_pixel(cursor.x, cursor.y, pixel)
		MoveCursor()
	
	NewLine(True)

	
def ResetCursor():
	global cursor
	cursor.x = 0
	cursor.y = 0
	
def MoveCursor():
	global cursor
	cursor.x = cursor.x + 1
	
	if cursor.x > 7:
		cursor.x = 0
		cursor.y = cursor.y + 1
	if cursor.y > 7:
		cursor.y = 0

def NewLine(soft = False):
	global cursor
	
	if soft:
		if cursor.x == 0:
			return
			
	cursor.x = 0
	cursor.y = cursor.y + 1
	if cursor.y > 7:
		cursor.y = 0
		
def ClearScreen():
	ResetCursor()
	sense.clear(black)
	

def GetMidiInputs():
	inputs = []
	
	lines = subprocess.check_output("aconnect -i -l", shell=True).decode().split('\n')
	for line in lines:
		if not re.match("^client", line):
			continue
		if re.match("^client 0", line):
			continue
		if re.match(".*Midi Through", line):
			continue
		name_search = re.search(".*'(.*)'", line)
		if not name_search:
			continue
		
		name = name_search.group(1)
			
		inputs.append(name)

	return inputs

def DrawDeviceScreen(devices):
	ClearScreen()
	for devicename in devices:
		DrawMiniText(devicename)
	
	if len(devices) == 0:
		sense.show_letter("-", text_colour=red)

def UpdateKnownDevices(devices):
	global known_devices
	modified = False
	
	for device in devices:
		if not device in known_devices:
			# add device
			known_devices.append(device)
			logmsg("added %s" % device)
			sense.show_message(device, scroll_speed = 0.05, text_colour=green)
			modified = True
	
	known_devices_temp = known_devices
	for known_device in known_devices_temp:
		if not known_device in devices:
			# remove device
			known_devices.remove(known_device)
			logmsg("removed %s" % known_device)
			sense.show_message(known_device, scroll_speed = 0.05, text_colour=red)
			modified = True
	
	return modified
		
def sigterm_handler(signum, frame):
	global done
	done = True
	logmsg("Quitting...")

def sighup_handler(signum, frame):
	global update_now
	update_now = True
	logmsg("Triggering update on HUP signal")

signal.signal(signal.SIGINT, sigterm_handler)
signal.signal(signal.SIGTERM, sigterm_handler)
signal.signal(signal.SIGHUP, sighup_handler)

def findRunProcess():
	prog = os.path.basename(sys.argv[0])
	try:
		lines = subprocess.check_output(["/usr/bin/pgrep", "-f", f"{prog} --run"]).decode().split('\n')
	except subprocess.CalledProcessError as err:
		# not found
		logmsg("Run process not running.", level="ERROR")
		return None
		
	service_pid = lines[0]
	return service_pid

def sendSignaltoPID(pid, signal):
	if pid == None:
		logmsg(f"Failed to send {signal} signal. No PID provided", level="ERROR")
		return
	subprocess.run(["/usr/bin/kill", f"-{signal}", pid])

def mainLoop():
	global update_now
	
	update_now = True
	updated = True
	i = 0
	while not done:
		i = i + 1
		if i >= 60:
			logmsg("Triggering update on timer")
			update_now = True
			i = 0
		
		if update_now:
			update_now = False
			logmsg("Updating")
			inputs = GetMidiInputs()
			updated = UpdateKnownDevices(inputs)
		
		if updated:
			DrawDeviceScreen(known_devices)
			
		time.sleep(1)

	ClearScreen()
	logmsg("Good Bye!")
	sense.show_message("Bye", scroll_speed = 0.05, text_colour=red)
	


def main(argv):
	global verbose
	
	parser = argparse.ArgumentParser()
	parser.add_argument("--version", action="version", version="%(prog)s, Version " + VERSION)
	parser.add_argument("-v", "--verbose", dest="verbose", action="store_true")
	parser.add_argument("-D", "--daemon", dest="daemon", action="store_true", help="run as daemon in background")
	parser.add_argument("-u", "--update", dest="update", action="store_true")
	parser.add_argument("--quit", dest="terminate", action="store_true")
	parser.add_argument("--run", dest="run", action="store_true")
	
	options = parser.parse_args(argv)
		
	if options.verbose:
		verbose = True
		
	if options.update:
		pid = findRunProcess()
		sendSignaltoPID(pid, "HUP")
		sys.exit(0)
	
	if options.terminate:
		pid = findRunProcess()
		sendSignaltoPID(pid, "TERM")
		sys.exit(0)

	if options.daemon:
		createDaemon()		

	if options.run:
		mainLoop()
		
	
	#m = []
	#m.append("Launchkey Mini")
	#m.append("Lauchpad Mini mkII")
	#m.append("iPhone of Mickey")
	#m.append("OP-1")
	#DrawDeviceScreen(m)
	

if __name__ == "__main__":
	sys.exit(main(sys.argv[1:]))
			
