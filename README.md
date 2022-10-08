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
  --label LABEL, -b LABEL
                        limit output to devices downstream of a particular label
  --udev-tag TAG, -t TAG
                        limit output to devices with udev tag
  --udev-idpath ID_PATH, -i ID_PATH
                        limit output to devices with a parent starting with given idpath
```
## Installation

The easiest way to install lsudt is to use pip, as follows:

```bash
$ pip3 install lsudt
```

Alternatively you can clone the Github repo and install it as follows:

```bash
$ git clone https://github.com/The-Good-Penguin/lsudt.git
$ cd lsudt
$ pip3 install .
```

## Labels

The USB tree can be better visualised by using labels. A user may create a
configuration file that assigns text labels to specific devices.

For example consider the following USB tree:

```bash
$ lsudt -p 1-10
Port 1-10: Hub (2109:2813 / 1-10)
    Port 2: Hub (45b:209 / 1-10.2)
        Port 3: Device (67b:2303 / 1-10.2.3)
           /dev/ttyUSB0

        Port 4: Hub (1a40:101 / 1-10.2.4)
            Port 3: Device (67b:2303 / 1-10.2.4.3)
               /dev/ttyUSB1

            Port 4: Device (bda:8152 / 1-10.2.4.4)
               Net: enx00e04c360033
```

The same tree can be better visualised when using labels:

```bash
$ ./lsudt.py -p 1-10
Port 1-10: Hub (2109:2813 / 1-10)
    Port 2: Hub used for Raspberry Pi (45b:209 / 1-10.2)
        Port 3: Raspberry Pi UART (67b:2303 / 1-10.2.3)
           /dev/ttyUSB0

        Port 4: Additional hub (1a40:101 / 1-10.2.4)
            Port 3: USB relay (Pi power control) (67b:2303 / 1-10.2.4.3)
               /dev/ttyUSB1

            Port 4: Hub built in Ethernet (connected to Pi) (bda:8152 / 1-10.2.4.4)
               Net: enx00e04c360033
```

The configuration file for these labels is shown below:

```bash
segments:
  -
    identifier: raspberry_pi
    label: Hub used for Raspberry Pi
    ports:
      - port: 1
        label: UART
      - port: 3
        label: Raspberry Pi UART
      - port: 4
        label: Additional hub
      - port: 4.3
        label: USB relay (Pi power control)
      - port: 4.4
        label: Hub built in Ethernet (connected to Pi)

mappings:
  -
    identifier: raspberry_pi
    port: 1-10.2
```

A segment represents a fixed portion of the USB topology and consists
of an identifier, label and set of labels for child ports.

The segment is accompanied with a mapping that describes where the
segment lives in the overall USB tree. In this way, the port path of
the ports in a segment are relative to the port path in the mapping.

This is useful as the segment can represent a fixed set of devices
(e.g. a board in a board farm) and the mapping describes where it is
(e.g. making it easier to move a board in a board farm).

The configuration can be split across any number of files. lsudt will
scan for any files ending with the .yml suffix in the ~/.lsudt/ directory.

Finally a segment identifier can be used to filter the output of lsudt,
e.g.

```bash
$ ./lsudt.py -b raspberry_pi
Port 2: Hub used for Raspberry Pi (45b:209 / 1-10.2)
    Port 3: Raspberry Pi UART (67b:2303 / 1-10.2.3)
       /dev/ttyUSB0

    Port 4: Additional hub (1a40:101 / 1-10.2.4)
        Port 3: USB relay (Pi power control) (67b:2303 / 1-10.2.4.3)
           /dev/ttyUSB1

        Port 4: Hub built in Ethernet (connected to Pi) (bda:8152 / 1-10.2.4.4)
           Net: enx00e04c360033

```
