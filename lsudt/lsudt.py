#!/usr/bin/python3
# Utility to list USB devices including associated Linux devices
#
# Copyright (c) 2022 Andrew Murray <amurray@thegoodpenguin.co.uk>
import argparse
import os
import re
import pathlib
import pyudev
import yaml


class USBDevice:
    """
    Representation of a USB device with links to its parent and children
    """

    def __init__(self, port_path):
        self.port_path = port_path
        self.id_vendor = None
        self.id_product = None
        self.device_class = None
        self.devices = []
        self.children = []
        self.parent = None


class LinuxDevice:
    """
    Representation of a Linux device
    """

    def __init__(self):
        self.devname = None
        self.devlinks = None
        self.id_path = None
        self.eth = None


def populate_usb_info(device: pyudev.Device, usb_device: USBDevice) -> None:
    """
    Obtains information about a USB device based on device path and populates
    a given USBDevice object, this approach appears quicker than using pyusb
    """

    # Ensure this is a USB device
    if "DEVTYPE" not in device or dict(device.properties)["DEVTYPE"] != "usb_device":
        return

    # Read from sysfs
    product_path = device.sys_path + "/idProduct"
    vendor_path = device.sys_path + "/idVendor"
    device_class_path = device.sys_path + "/bDeviceClass"
    if (
        not os.path.isfile(product_path)
        or not os.path.isfile(vendor_path)
        or not os.path.isfile(device_class_path)
    ):
        return
    with open(product_path, "r") as file:
        product_str = file.readline().rstrip()
    with open(vendor_path, "r") as file:
        vendor_str = file.readline().rstrip()
    with open(device_class_path, "r") as file:
        device_class_str = file.readline().rstrip()

    # Wrap in a USBInfo object
    usb_device.id_product = int(product_str, base=16)
    usb_device.id_vendor = int(vendor_str, base=16)
    usb_device.device_class = int(device_class_str, base=16)


def get_port_path_from_device_path(devpath: str) -> str:
    """
    Returns a USB topology port path (e.g. 1-10.3) from a udev device path (e.g.
    /devices/pci0000:00/0000:00:14.0/usb1/1-10/1-10.3/1-10.3:1.0/ttyUSB0/tty/ttyUSB0)
    """

    # Search for the root USB string (e.g. usb1/1-10) and capture the
    # bus number and first port
    ree = re.search("/usb[0-9]+/([0-9]+-[0-9+])", devpath)
    if ree is None:
        return None

    # Work up the path until we reach the USB tree, this will contain the
    # full USB path in one string, e.g. 1-10.3:1.0
    ports = devpath.split("/")
    for portpath in reversed(ports):
        if portpath.startswith(ree.group(1)):
            # We only care about the physical topology so lets drop everything
            # after the colon (e.g. the device config and interface)
            return portpath.split(":")[0]

    return None


def find_usb_device(port_path: str) -> USBDevice:
    """
    Given a port_path find the associated USB device
    """
    for usb_device in usb_devices_list:
        if usb_device.port_path == port_path:
            return usb_device
    return None


def add_usb_device(port_path: str, args) -> USBDevice:
    """
    Create, if needed, a USBDevice for the given port path and add to
    the existing USB tree. It will also create parent USBDevice's up
    to the root of the tree.
    """

    # If device already exists, let's return that
    usb_device = find_usb_device(port_path)
    if usb_device is not None:
        return usb_device

    # Create a new USB device and add it to the list
    usb_device = USBDevice(port_path)
    usb_devices_list.append(usb_device)

    # If we're filting by port path and we reach the given port path
    # then don't go any further up the tree
    if args.port_path is not None and port_path == args.port_path:
        return usb_device

    # Identify the parent of this device, e.g. 1-10.3.2's parent will be 1-10.3
    usb_tree = port_path.rsplit(".", 1)
    parent_port_path = usb_tree[0]

    # If there is a parent, then find or create it and create a parent/client
    # relationship
    if len(usb_tree) == 2:
        parent = find_usb_device(parent_port_path)
        if parent is None:
            parent = add_usb_device(parent_port_path, args)

        # Let them know they have each other
        parent.children.append(usb_device)
        usb_device.parent = parent

    return usb_device


def does_id_path_match(id_path: str, usb_device: USBDevice) -> bool:
    """
    Determine if the current device or any of its parents have a device path
    that matches the provided root
    """

    for linux_device in usb_device.devices:
        if linux_device.id_path is not None and linux_device.id_path.startswith(
            id_path
        ):
            return True
    if usb_device.parent is None:
        return False
    return does_id_path_match(id_path, usb_device.parent)


def sanitise_device_path(device_path: str) -> str:
    """
    A user may provide a device path without a /sys, or /sys/devices
    prefix, let's sanitise it so that we can accept a variety of inputs
    """

    # pyudev requires a path from /sys/devices/ but without the /sys
    # prefix, so let's remove it if there
    if device_path.startswith("/sys"):
        device_path = device_path[len("/sys") :]

    # If the path doesn't start with /devices let's assume their path
    # starts after the /devices prefix thus let's remove it
    if not device_path.startswith("/devices"):
        device_path = f"/devices/{device_path}"

    return device_path


def populate_device_info(linux_device: pyudev.Device) -> LinuxDevice:
    """
    Create a LinuxDevice and populate it with information from the
    udev device
    """
    device = LinuxDevice()

    if "DEVNAME" in linux_device:
        device.devname = dict(linux_device.properties)["DEVNAME"]
    if "DEVLINKS" in linux_device:
        device.devlinks = dict(linux_device.properties)["DEVLINKS"]
    if "ID_PATH" in linux_device:
        device.id_path = dict(linux_device.properties)["ID_PATH"]

    if (
        "SUBSYSTEM" in linux_device
        and dict(linux_device.properties)["SUBSYSTEM"] == "net"
    ):
        device.eth = dict(linux_device.properties)["INTERFACE"]

    # Only return the device if it has something we can display
    if device.devname is None and device.eth is None:
        return None

    return device


def scan_usb_tree(args) -> None:
    """
    Enumerate devices from udev and construct a USB tree
    """

    root_device_path = "/"

    if args.device_path is not None:
        root_device_path = sanitise_device_path(args.device_path)

    # Get all the devices from udev
    context = pyudev.Context()
    linux_devices = context.list_devices(tag=args.tag)

    for linux_device in linux_devices:
        devpath = dict(linux_device.properties)["DEVPATH"]

        # If we are filtering by device path, ignore anything outside of filter
        if not devpath.startswith(root_device_path):
            continue

        # Identify the port path (physical USB topology) for this device based
        # on it's devicepath, we use this to derive topology
        port_path = get_port_path_from_device_path(devpath)
        if port_path is None or len(port_path) == 0:
            continue

        # If we are filtering by port path, ignore naything outside this filter
        if args.port_path is not None and not port_path.startswith(args.port_path):
            continue

        # We have a device with a port path so let's represent this as a USB
        # device
        usb_device = add_usb_device(port_path, args)

        # Obtain USB device information, even though the udev device is on the
        # USB bus, this particular devpath may not be a usb device (e.g. could
        # be scsi, network, etc)
        populate_usb_info(linux_device, usb_device)

        linux_device = populate_device_info(linux_device)
        if linux_device:
            usb_device.devices.append(linux_device)


def showtree(usb_devices, space, args) -> None:
    """
    Display the USB tree for the given list of USB devices
    """
    for usb_device in usb_devices:
        show(usb_device, space, args)


def parse_one_configuration_file(path: str):
    """
    Read a yml config files and obtain segments and mappings
    """
    try:
        with open(path, "r") as config_file:
            i = yaml.safe_load(config_file)
            if i is None:
                return
            if i.get("mappings"):
                for mapping in i["mappings"]:
                    if (
                        mapping.get("identifier") is not None
                        and mapping.get("port") is not None
                    ):
                        mappings[mapping["identifier"]] = mapping["port"]
            if i.get("segments"):
                for mapping in i["segments"]:
                    segments.append(mapping)
    except (OSError, yaml.scanner.ScannerError):
        print(f"Unable to parse {path}")


def read_configuration():
    """
    Read yml config files to obtain segments and mappings
    """
    # Find home path for configuration
    home = pathlib.Path.home()
    settings_path = os.path.join(home, ".lsudt")

    if not os.path.isdir(settings_path):
        return

    for config in os.listdir(settings_path):
        if config.endswith(".yml"):
            parse_one_configuration_file(f"{settings_path}/{config}")


def load_port_labels():
    """
    Use the users segments and mappings to construct a map between port paths and user friendly
    labels
    """
    read_configuration()

    # Extract labels and port paths from lsudt files
    for segment in segments:
        # The segment is part of a USB topology, let's lookup the mappings
        # to find where in the USB tree it lives
        root_path = mappings.get(segment.get("identifier"))
        if root_path is None:
            continue

        # Add port label for the segment
        if segment.get("label") is not None:
            port_labels[root_path] = segment["label"]

        # Add port labels for the ports
        for port in segment["ports"]:
            if port.get("port") is not None and port.get("label") is not None:
                port_path = f"{root_path}.{port['port']}"
                port_labels[port_path] = port["label"]


def show(usb_device, space, args) -> None:
    """
    Display the USB tree for the given USB device
    """

    # Only show empty hubs if required
    if not args.show_empty_hubs:
        if len(usb_device.children) == 0 and len(usb_device.devices) == 0:
            return

    # When filtering by id_path, ignore anything that doesn't match
    if args.id_path is not None:
        if not does_id_path_match(args.id_path, usb_device):
            return

    # Determine the port number from the port path
    ports = usb_device.port_path.rsplit(".", 1)
    port = next(reversed(ports))

    # Create labels
    device_type = "Hub" if usb_device.device_class == 9 else "Device"
    usb_info = (
        ""
        if usb_device.id_vendor is None
        else f"{usb_device.id_vendor:x}:{usb_device.id_product:x}"
    )

    # Display device info
    if usb_device.port_path in port_labels:
        device_type = port_labels[usb_device.port_path]
    if usb_device.id_vendor is not None:
        print(
            f"{space}Port {port}: {device_type} ({usb_info} / {usb_device.port_path})"
        )
    else:
        print(f"{space}Port {port}: ({usb_device.port_path})")

    space_added = False

    # Iterate through the devices associated with this USB device
    for device in usb_device.devices:
        # Filter out /dev/bus/usb devices if needed
        if (
            not args.show_devusb
            and device.devname is not None
            and device.devname.startswith("/dev/bus/usb")
        ):
            continue
        id_path = (
            ""
            if device.id_path is None or args.show_idpath is False
            else f" ({device.id_path})"
        )
        devname = device.devname if device.devname is not None else f"Net: {device.eth}"
        print(f"{space}   {devname}{id_path}")
        if args.show_device_links:
            if device.devlinks is not None:
                device_links = device.devlinks.split(" ")
                for link in device_links:
                    print(f"{space}   : {link}")
                print("")
                space_added = True
    if len(usb_device.children) != 0:
        showtree(usb_device.children, space + "    ", args)
    elif space_added is False:
        print("")


def init_argparse() -> argparse.ArgumentParser:
    """
    Set up argument parser
    """
    parser = argparse.ArgumentParser(
        description="View connected USB devices and device nodes"
    )
    parser.add_argument("--version", action="version", version="%(prog)s 0.2.1")
    parser.add_argument(
        "--show-devusb",
        "-u",
        action="store_true",
        dest="show_devusb",
        help="show /dev/usb/ device nodes",
    )

    parser.add_argument(
        "--show-idpath",
        "-s",
        action="store_true",
        dest="show_idpath",
        help="show udev ID_PATH next to devices",
    )

    parser.add_argument(
        "--show-empty-hubs",
        "-e",
        action="store_true",
        dest="show_empty_hubs",
        help="show empty hubs",
    )

    parser.add_argument(
        "--show-device-links",
        "-l",
        action="store_true",
        dest="show_device_links",
        help="show device links",
    )

    parser.add_argument(
        "--device-path",
        "-d",
        action="store",
        dest="device_path",
        help="limit output to devices contained within a path starting with /sys/devices/",
    )
    parser.add_argument(
        "--port-path",
        "-p",
        action="store",
        dest="port_path",
        help="limit output to devices downstream of a particular port path",
    )
    parser.add_argument(
        "--label",
        "-b",
        action="store",
        dest="label",
        help="limit output to devices downstream of a particular label",
    )
    parser.add_argument(
        "--udev-tag",
        "-t",
        action="store",
        dest="tag",
        help="limit output to devices with udev tag",
    )
    parser.add_argument(
        "--udev-idpath",
        "-i",
        action="store",
        dest="id_path",
        help="limit output to devices with a parent starting with given idpath",
    )

    return parser


# Flat list of all USB devices discovered
usb_devices_list = []

# Map between ports and their labels
port_labels = {}

# List of 'segment' objects representing a labelled section of USB tree
segments = []

# Mappings between segments and their port path
mappings = {}


def main() -> None:
    """
    Entry point
    """
    parser = init_argparse()
    args = parser.parse_args()

    # Read port labels from configuration files
    load_port_labels()

    # Limit by label instead of port path
    if args.label is not None:
        port_path = mappings.get(args.label)
        if port_path is not None:
            args.port_path = port_path

    # Scan for devices and construct a tree
    scan_usb_tree(args)

    # Dislay the tree
    for device in usb_devices_list:

        # Render from roots
        if device.parent is None:
            show(device, "", args)


if __name__ == "__main__":
    main()
