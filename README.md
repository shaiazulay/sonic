Arista platform support for SONiC
=================================

Copyright (C) 2016 Arista Networks, Inc.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

## License

All linux kernel code is licensed under the GPLv2. All other code is
licensed under the GPLv3. Please see the LICENSE file for copies of
both licenses.

## Purpose

This package provides open source hardware support for Arista devices.
It is mainly targeted at SONiC OS (debian based) but should work on any system.
For more details visit the [SONiC website](https://azure.github.io/SONiC/)

In normal operations, the platform is initialized at boot time via a set of systemd
services. These services run commands using the `arista` tool.

This tool detects on which platform it is running before loading the appropriate
kernel drivers. Once the initialization is complete, the system exposes various
components through the sysfs such as fans, leds, xcvrs, ...

## Supported platforms

The following platforms are currently supported,

 - DCS-7050QX-32
 - DCS-7050QX-32S
 - DCS-7050CX3-32S
 - DCS-7060CX-32
 - DCS-7060CX2-32
 - DCS-7060PX4-32 and DCS-7060DX4-32
 - DCS-7170-32C
 - DCS-7170-32CD
 - DCS-7170-64C
 - DCS-7260CX3-64
 - DCS-7280CR3-32P4 and DCS-7280CR3-32D4

Some variants were omitted but might be supported see `arista platforms` for a
detailed list of supported SKUs.

Some platforms might require custom kernel patches and configs.
A working configuration is maintained under the [SONiC kernel repository](https://github.com/Azure/sonic-linux-kernel).

## Packaging

The current debian packaging mechanism creates 4 packages.
 - sonic-platform-arista : system configuration files
 - drivers-sonic-platform-arista : kernel modules and drivers
 - python2-sonic-platform-arista : python2 library to manage the hardware
 - python3-sonic-platform-arista : python3 library to manage the hardware

## Usage

At boot time the systemd services under `systemd/` are loaded. When runnable they
will perform the platform initialization.

The central piece of the platform support is the `arista` entry point.
It is a python script that load the arista platform library to perform actions.
This library is python2/python3 compatible.

For more details on the available commands see the help message
```
arista --help
```

The arista python library also possess other entry points for APIs.
SONiC uses a few like `sonic_platform`, `sfputil`, `sonic_eeprom`, ...

## Drivers

The kernel drivers in this repository are mostly running on a 4.9 kernel.
They are also compatible with 4.19 and potentially higher kernel versions.

### scd-hwmon

The `scd-hwmon` is the current implementation for the `scd` and is being used on all
platforms.

When the `scd-hwmon` driver is loaded, the various gpios and resets can be set
and unset by writing into the sysfs file.
The meaning of `0` or `1` should be deduced based on the name of the sysfs entry.

```
cd /sys/module/scd/drivers/pci:scd/<pciAddr>/
# put the switch chip in reset
echo 1 > switch_chip_reset
```

## Components

This section describes how to interact with the various components exposed by
the kernel drivers.
In order to see them, the platform must be successfully initialized.

The following sections describe how to manually interact with the components.
Examples shown may differ across platforms but the logic stays the same.

### LEDs

LED objects can be found under `/sys/class/leds`.The brightness field is used to
toggle between off and different colors.
The brightness to LED color mapping is as follows (0 maps to off for all LEDs):

```
status, fan_status, psu1, psu2:
  0 => off
  1 => green
  2 => red

beacon:
  1+ => blue

qsfp:
  1 => green
  2 => yellow

fan:
  1 => green
  2 => red
  3 => yellow
```

Given that this repository is primarily aimed at running on SONiC, an
implementation of the `led_control` plugin is available under
`arista.utils.sonic_leds`. It requires access to the `port_config.ini` file to
translate from `interface name` to `front panel port`.

### Fans

Fans are exposed under `/sys/class/hwmon/*` and respect the
[sysfs-interface](https://www.kernel.org/doc/Documentation/hwmon/sysfs-interface)
guidelines.

This repository provides the kernel modules to handle the fans.

### Temperature sensors

Temperature sensors are exposed under `/sys/class/hwmon/*` and also respect
the [sysfs-interface](https://www.kernel.org/doc/Documentation/hwmon/sysfs-interface).

They are all managed by linux standard modules like `lm73` and `max6658`.

### Power supplies

Power supplies and power controllers can be managed by the kernel's
generic `pmbus` module. Assuming the pmbus module was compiled into the
kernel.

Some power supplies may need kernel patches against the `pmbus` driver.

### System EEPROM

The system eeprom contains platform specific information like the `SKU`, the
`serial number` and the `base mac address`.

The location of the eeprom that contains this information vary from one product to
another. The most reliable way to get this information is to run `arista syseeprom`

The library implements the SONiC eeprom plugin under `arista.utils.sonic_eeprom`.

### Transceivers - QSFPs / SFPs

Currently only platforms with QSFP+, SFP+, OSFP and QSFPDD ports are supported.
All transceivers provide 2 kinds of information.

#### Pins

The first piece of information is obtained from the transceiver physical pins.
 - OSFP: present, reset, low power mode, interrupt, module select
 - QSFP: present, reset, low power mode, interrupt, module select
 - SFP: present, rxlos, txfault, txdisable

These knobs are accessible under `/sys/module/scd/drivers/pci:scd/.../`
The name of the entries follow this naming `<type><id>_<pin>`
For example `qsfp2_reset` or `sfp66_txdisable`.

See [this section](#scd-hwmon) on how to use them.

#### Eeproms

The second piece of information provided by a transceiver is the content of its
`eeprom`. It is accessible via `SMBus` at the fixed address `0x50`. Some
transceivers also exist at other `SMBus` addresses like `0x51` and `0x56`.

On linux, an unoffical module called `optoe` manages such devices.
This library implements the spfutil plugin for SONiC to manage xcvrs.

Before being read, the QSFP+, OSFP and QSFPDD modules must be taken out of reset and
have their module select signals asserted. This can be done through the GPIO
interface. The library does it at boot time.

### QSFP - SFP multiplexing

On the `DCS-7050QX-32S`, the first QSFP port and the 4 SFP ports are multiplexed.
To choose between one or the other, write into the sysfs file located under
`/sys/modules/scd/drivers/pci:scd/.../mux_sfp_qsfp`

### GPIOs and resets

Most of the GPIOs of the system are exposed by the `scd-hwmon` driver.
They should be available under `/sys/module/scd/drivers/pci:scd/.../`.
