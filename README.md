# midisense
Using the Sense Hat of your Raspberry Pi to display connected MIDI devices

# Introduction

You have followed the instruction here https://neuma.studio/rpi-midi-complete.html to build a Raspberry Pi USB/Bluetooth MIDI host and now you wonder how you can display what is going on without having to buy a separate mini display? But you still have an unused Sense Hat lying around that is collecting dust. Well, then you are lucky!

Mount the Sense Hat on your Raspberry Pi and install this application!

# How it works

It will follow all connected devices and make the best use of the limited 8x8 pixel display to show what devices are connected. Each device is converted into a Pixel sequence based on its name. Upper case letters will be displayed as green pixels, lowercase in blue and numbers in red. Names that are longer than 8 characters will be scaled down as best as possible while maintaining important characters.

Examples:
- `iPad` will become
:large_blue_circle:
:green_circle:
:large_blue_circle:
:large_blue_circle:
- `Launchkey Mini` will become 
:green_circle:
:large_blue_circle:
:large_blue_circle:
:large_blue_circle:
:large_blue_circle:
:white_circle:
:green_circle:
:large_blue_circle:
- `OP-1` will become
:green_circle:
:green_circle:
:white_circle:
:red_circle:

Each line will represent one device. When a new device connects it will show its full name using the scrolling text feature in green colour. When the device disconnects it will show its name again using scrolling text in red colour.


# Prerequisites

- You have a Raspberry Pi 3 or 4
- You have installed a Sense Hat on your Raspberry Pi
- Alternatively you can use the Sense Hat Emulator to check out the program
- You have setup your Raspberry Pi as a USB/Bluetooth MIDI host as described in the excellent documentation at https://neuma.studio/rpi-midi-complete.html

# Installation

- Boot your Raspberry Pi
- Open a terminal
- Ensure git is installed

```
sudo apt install git
```
- Ensure sense-hat python bindings are installed (they should already be pre-installed)

```
sudo apt install sense-hat
```
- Clone this repository into your home directory
  
```
git clone https://github.com/cwacha/midisense.git
```
- Build a Debian package using the supplied script

```
cd midisense
cd pkg
./pkgmake.sh all
```

- Now you should have a Debian package in the current directory
  - `midisense_1.1.0-6_all.deb`
- Install the package using dpkg

```
sudo dpkg -i midisense_1.1.0-6_all.deb
```
- Done!

The package will configure `systemd` with a new service called midisense.service and start it automatically. It will also setup `udev` rules so that the midisense service is notified when new devices connect or disconnect. Your Sense Hat will immediately start to display connected devices. If no device is connected it will just display a red line in the middle of the screen.

# Removal
- To remove the package just run

```
sudo apt remove midisense
```

# Update
- In case I have a new version ready...
- Update your git repository

```  
cd ~/midisense
git pull
```
- Then just re-run the packaging process and install the new package on top of the old package. `dpkg` will handle the upgrade.

```
cd pkg
./pkgmake.sh all
sudo dpkg -i midisense*.deb
```

# Manual Execution

You can also run the application directly from the source directory

```
cd ~/midisense
cd src
./midisense.py

usage: midisense.py [-h] [--version] [-v] [--debug] [--run] [-D] [-u] [--quit] [--emu]

options:
  -h, --help     show this help message and exit
  --version      show program's version number and exit
  -v, --verbose  show INFO messages
  --debug        show DEBUG messages
  --run          run the service
  -D, --daemon   run as daemon in background. Must follow --run option
  -u, --update   trigger update on running service
  --quit         terminate running service
  --emu          Run display on Sense Hat Emulator
```

To run it normally in foreground with INFO messages. If you have installed the package previously make sure the installed service is stopped `sudo systemctl stop midisense`.

```
./midisense.py --run -v
```

It will scan for new devices automatically approx. once per minute. If you want to trigger an immediate update open a second terminal and run

```
cd ~/midisense
cd src
./midisense.py --update
```

Now you should see that the application updates immediately in the first terminal window.
To stop the app use Ctrl-C or call `./midisense.py --quit` from the second terminal window.

# Managing the systemd service

- You can start/stop the service temporarily

```
sudo systemctl start midisense
sudo systemctl stop midisense
```

- Or you can enable/disable the service permanently so that it always/never starts when you boot your Raspberry Pi

```
sudo systemctl enable midisense
sudo systemctl disable midisense
```

# Run midisense on the Sense Hat Emulator

Just add `--emu` to the main call

```
./midisense.py --run -v --emu
```

The app will tell you if the emulator packages are missing and how to install them.
