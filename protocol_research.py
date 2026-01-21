#!/usr/bin/env python3
"""
Protocol Research Utility – Instant A825 / GM320
------------------------------------------------
WARNING:
This script is for *USB HID protocol observation and experimentation only*.

• Does NOT flash firmware
• Does NOT modify VID/PID
• Does NOT bypass hardware locks
• Does NOT write to permanent storage

It sends benign HID Feature Reports to test whether a device
accepts or ignores configuration commands.

USE AT YOUR OWN RISK.
"""

import usb.core
import usb.util
import time

VID = 0x30fa
PID = 0x7f7f

def test_feature_reports():
    dev = usb.core.find(idVendor=VID, idProduct=PID)
    if dev is None:
        print("Device not found.")
        return

    print("Device found. Testing feature report acceptance...")

    try:
        if dev.is_kernel_driver_active(1):
            dev.detach_kernel_driver(1)

        # Benign feature report (NO FLASH / NO ID CHANGE)
        test_pkt = [0x07, 0x11, 0x00] + [0x00]*61

        dev.ctrl_transfer(
            bmRequestType=0x21,   # Host → Device | Class | Interface
            bRequest=0x09,        # SET_REPORT
            wValue=0x0307,        # Feature Report ID 7
            wIndex=1,             # Interface 1
            data_or_wLength=test_pkt
        )

        print("Feature report sent.")
        print("If device behavior does not change, firmware likely ignores writes.")

    except usb.core.USBError as e:
        print(f"USB error: {e}")

if __name__ == "__main__":
    test_feature_reports()

