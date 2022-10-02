# lsudt
lsudt (list USB device tree) is a utility for listing USB devices as a tree
including associated dev nodes and other information from udev.

This makes it much easier to understand the topology of a USB tree and the
relationship between device nodes and the USB devices they originate from.

The utility provides filtering capabilities allowing you to filter by
device path, port path, udev tag and udev ID_PATH.

## Example Usage

```bash

# Filter by USB port path
$ lsudt -p 1-10
Port 1-10: Hub (2109:2813 / 1-10)
    Port 1: Hub (1a40:101 / 1-10.1)
        Port 1: Device (67b:2303 / 1-10.1.1)
           /dev/ttyUSB0

        Port 4: Device (bda:8152 / 1-10.1.4)
           Net: enx00e04c360033

    Port 4: Device (5e3:749 / 1-10.4)
       /dev/sda
       /dev/sda1
       /dev/sda2
       /dev/sda3
       /dev/sda4
       /dev/sda5
       /dev/sda6
       /dev/sda7
       /dev/sda8
       /dev/bsg/6:0:0:0
       /dev/sg0

# Filter by device path
$ lsudt -d /sys/devices/pci0000:00/0000:00:14.0/usb1/1-4 
Port 1-4: Device (46d:843 / 1-4)
   /dev/input/event5
   /dev/media0
   /dev/video0
   /dev/video1
   /dev/snd/pcmC1D0c
   /dev/snd/controlC1

# Filter by ID_PATH
$ lsudt -i pci-0000:00:14.0-usb-0:5
Port 1-5: Device (b0e:348 / 1-5)
   /dev/snd/pcmC3D0c
   /dev/snd/pcmC3D0p
   /dev/snd/controlC3
   /dev/hidraw2
   /dev/input/event22
   /dev/usb/hiddev1
 
# Filter by udev TAG
$ lsudt -t power-switch
Port 1-4: (1-4)
   /dev/input/event5

Port 1-5: (1-5)
   /dev/input/event22

Port 1-7: (1-7)
   /dev/input/event3

Port 1-9: (1-9)
   /dev/input/event7
   /dev/input/event9
   /dev/input/event8

# Show more information
$ lsudt -p 1-10.1 -u -s -e -l
Port 1: Hub (1a40:101 / 1-10.1)
   /dev/bus/usb/001/085 (pci-0000:00:14.0-usb-0:10.1)
    Port 1: Device (67b:2303 / 1-10.1.1)
       /dev/bus/usb/001/109 (pci-0000:00:14.0-usb-0:10.1.1)
       /dev/ttyUSB0 (pci-0000:00:14.0-usb-0:10.1.1:1.0)
       : /dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller-if00-port0
       : /dev/serial/by-path/pci-0000:00:14.0-usb-0:10.1.1:1.0-port0

    Port 4: Device (bda:8152 / 1-10.1.4)
       /dev/bus/usb/001/086 (pci-0000:00:14.0-usb-0:10.1.4)
       Net: enx00e04c360033 (pci-0000:00:14.0-usb-0:10.1.4:1.0)

# Show help
$ lsudt -h
usage: lsudt [-h] [--version] [--show-devusb] [--show-idpath] [--show-empty-hubs]
             [--show-device-links] [--device-path DEVICE_PATH] [--port-path PORT_PATH]
             [--udev-tag TAG] [--udev-idpath ID_PATH]

View connected USB devices and device nodes

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --show-devusb, -u     show /dev/usb/ device nodes
  --show-idpath, -s     show udev ID_PATH next to devices
  --show-empty-hubs, -e
                        show empty hubs
  --show-device-links, -l
                        show device links
  --device-path DEVICE_PATH, -d DEVICE_PATH
                        limit output to devices contained within a path starting with /sys/devices/
  --port-path PORT_PATH, -p PORT_PATH
                        limit output to devices downstream of a particular port path
  --udev-tag TAG, -t TAG
                        limit output to devices with udev tag
  --udev-idpath ID_PATH, -i ID_PATH
                        limit output to devices with a parent starting with given idpath
```
