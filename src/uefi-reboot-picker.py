#!/usr/bin/env python3
import gi
import re
import subprocess

gi.require_version("Gtk", "3.0")
gi.require_version("AppIndicator3", "0.1")
from gi.repository import Gtk, AppIndicator3

# Set to True for development mode, which will not reboot the system after selecting a boot entry.
DEVELOPMENT_MODE = False

icon_name = "system-reboot"


def get_all_boot_entries():
    """
    Build a dictionary of entries from the output of `efibootmgr`.
    """
    lines = (
        subprocess.run("efibootmgr", stdout=subprocess.PIPE)
        .stdout.decode("utf-8")
        .splitlines()
    )

    boot_current_pattern = re.compile("^BootCurrent: ([0-9a-fA-F]+)")
    boot_pattern = re.compile("^Boot([0-9a-fA-F]+)\\* (.*)\\t.*$")

    boot_current = None
    boot_entries = {}

    for line in lines:
        boot_current_match = boot_current_pattern.match(line)
        boot_match = boot_pattern.match(line)


        if boot_current_match:
            boot_current = boot_current_match.group(1)
        elif boot_match:
            boot_number = boot_match.group(1)
            boot_entries[boot_number] = (
                f"{boot_match.group(2)} {"(Currently booted)" if boot_number == boot_current else ""}"
            )

    return boot_entries


def build_menu():
    menu = Gtk.Menu()

    boot_entries = get_all_boot_entries()

    print(boot_entries)

    for boot_number, boot_title in boot_entries.items():
        menuitem = Gtk.MenuItem(label=boot_title)
        menuitem.connect("activate", do_reboot, boot_number)

        menu.append(menuitem)

    exittray = Gtk.MenuItem(label="Exit Tray")
    exittray.connect("activate", quit)
    menu.append(Gtk.SeparatorMenuItem())
    
    firmware_item = Gtk.MenuItem(label="Firmware Setup")
    firmware_item.connect("activate", do_reboot, "firmware_setup")
    menu.append(firmware_item)

    menu.append(Gtk.SeparatorMenuItem())
   
    menu.append(exittray)

    menu.show_all()
    return menu


def do_reboot(menuitem, uefi_boot_number):
    if uefi_boot_number == "firmware_setup":
        subprocess.run("pkexec systemctl reboot --firmware-setup".split())
    else:
        subprocess.run(f"pkexec efibootmgr --bootnext {uefi_boot_number}".split())

        if not DEVELOPMENT_MODE:
            subprocess.run("pkexec reboot".split())


def quit(_):
    Gtk.main_quit()


indicator = AppIndicator3.Indicator.new(
    "customtray", icon_name, AppIndicator3.IndicatorCategory.APPLICATION_STATUS
)
indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
indicator.set_menu(build_menu())


Gtk.main()
