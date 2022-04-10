# Raspberry Pi Recorder

## Pinout and pins used

| Pin # | Pin                    | Used for        | Pin# | Pin              | Used For                  |
|:-----:|:----------------------:|:---------------:|:----:|:----------------:|:-------------------------:|
| 1     | 3V3 Power              | 3V3 ADC         | 2    | 5V Power         | 5V in-ADC                 |
| 3     | GPIO2 (SDA)            | SDA-ADC         | 4    | 5V Power         |                           |
| 5     | GPIO3 (SCL)            | SCL-ADC         | 6    | Ground           |                           |
| 7     | GPIO4 (GPCLK0, 1-wire) | ADC Shutdown    | 8    | GPIO14 (TXD)     |                           |
| 9     | Ground                 | GND-ADC         | 10   | GPIO15 (RXD)     |                           |
| 11    | GPIO17                 | IR Sensor in    | 12   | GPIO18 (PCM_CLK) | bclk-ADC                  |
| 13    | GPIO27                 | Temp 1-wire     | 14   | Ground           | Temp GND                  |
| 15    | GPIO22                 |                 | 16   | GPIO23           |                           |
| 17    | 3V3 Power              | Temp 3V3        | 18   | GPIO24           | Shutdown Switch           |
| 19    | GPIO10 (MOSI)          |                 | 20   | Ground           | Shutdown Switch           |
| 21    | GPIO9 (MISO)           |                 | 22   | GPIO25           | Low Batt signal (lt blue) |
| 23    | GPIO11 (SCLK)          |                 | 24   | GPIO8 (CE0)      |                           |
| 25    | Ground                 |                 | 26   | GPIO7 (CE1)      |                           |
| 27    | GPIO0 (ID_SD)          |                 | 28   | GPIO1 (ID_SC)    |                           |
| 29    | GPIO5                  |                 | 30   | Ground           |                           |
| 31    | GPIO6                  |                 | 32   | GPIO12 (PWM0)    |                           |
| 33    | GPIO13 (PWM1)          |                 | 34   | Ground           |                           |
| 35    | GPIO19 (PCM_FS)        | fsync-ADC       | 36   | GPIO16           |                           |
| 37    | GPIO26                 | poweroff output | 38   | GPIO20 (PCM_DIN) | dout-ADC                  |
| 39    | Ground                 |                 | 40   | GPIO21 (PCM_OUT) |                           |

* ADC board: Uses I2C1 interface, the PCM interface, and one gen purpose IO for ADC Shutdown.  Will this work the the RTC? Switch to I2C0 interface?

* One-wire temp sensors: GPIO4 was originally used as the shutdown pin, but it overlaps the one-wire interface.  So we need to change this if we want to use the default 1-wire pin.

* DS3231 Realtime Clock: Uses the SDA and SCL interface. (I2C1) Also 3.v3 power.

* BN-220 GPS or Neo6M: Uses UART.  Pins 14 and 15.  Will also need a switch to disable the power to the device.  Neo 6M is powered by 5v, but the TX output is 3 v.

* Power supply enable pin: Use a GPIO8 pin for this since it starts out with a high pullup at boot.

## Configuration

1. Get Raspberry Pi Buster

2. Image the card:
* Edit the `/etc/hostname` and `/etc/hosts` files to change the hostname to  `piaudio`

* SSH - add an empty file called ssh on the boot partition.
  
  `touch /media/filip/boot/ssh`
  
  basic WiFi - update the `/etc/wpa_supplicant/wpa_supplicant.conf`

* You can use `wpa_passphrase <<your_SSID>>` to get the hashed value for a plain text psk.
3. Add the device overlay
* Copy tlv320adcx140-overlay.dtbo to /boot/overlays 
  
      `sudo cp device-tree-overlays/tlv320adcx140-overlay.dtbo /media/filip/boot/overlays/``

Edit `/boot/config.txt` to set all the proper IO

```c
dtparam=i2c_arm=on
dtparam=i2s=on
#dtparam=spi=on
dtoverlay=tlv320adcx140-overlay
# turn on IR sensor input
dtoverlay=gpio-ir,gpio_pin=17

# input pin to start the shut down sequence
dtoverlay=gpio-shutdown,gpio_pin=24,active_low=1,gpio_pull=up

# output pin to enable power source
dtoverlay=gpio-poweroff,gpiopin=26,active_low=1

#Shut off bluetooth to save power
dtoverlay=disable-bt

# Turn on 1-wire for temp sensors
dtoverlay=w1-gpio,gpiopin=27

#reduce GPU mem
gpu_mem=32

sudo systemctl disable hciuart # if disabling bluetooth do this too
```

Power up the RPI and log in to do the remaining items:

* Change the password with passwd

* Check that the new ADC is recognized:
  
  `arecord -L`

* Install the following packages
  
  ```shell
  sudo apt update
  sudo apt upgrade
  sudo apt install opus-tools
  sudo apt install vorbis-tools
  sudo apt install flac
  sudo apt install portaudio19-dev
  pip3 install mutagen
  pip3 install PyAudio
  pip3 install numpy
  ```
  
  Try 
  
  ```shell
  arecord -D plughw:1 -c1 -r 48000 -f S32_LE -t wav -V mono -v file.wav
  ```

## Slow Mouse issue

If you plan on using the graphical interface and your mouse lags, you can fix it by 
`sudo nano /boot/cmdline.txt`
and add the following to this long line of text : ` usbhid.mousepoll=0`

## Adding temp sensors

Setting the sensor bits to 11 and saving in eeprom

```shell
pi@piaudio:~/code $ sudo su
root@piaudio:/home/pi/code# echo 11 > /sys/bus/w1/devices/28-00000bf3fc08/resolution
root@piaudio:/home/pi/code# echo 11 > /sys/bus/w1/devices/28-00000bf3efa6/resolution
root@piaudio:/home/pi/code# echo save > /sys/bus/w1/devices/28-00000bf3fc08/eeprom
root@piaudio:/home/pi/code# echo save > /sys/bus/w1/devices/28-00000bf3efa6/eeprom
```

Need to identify which one is inside and outside

# Startup and Shutdown

We will want a job to continue to run after we log out.  Configure system so that a user manager is spawned for the user at boot and kept around after logouts.  This way user processes and sessions don't get killed if the user is not logged in:

```shell
sudo loginctl enable-linger $USER
```

# Adding a real time clock

We will add the DS3231 real time clock module.

See [Set RTC Time | Adding a Real Time Clock to Raspberry Pi | Adafruit Learning System](https://learn.adafruit.com/adding-a-real-time-clock-to-raspberry-pi/set-rtc-time)

First check the status of the time without the DS3231 set up

```shell
pi@piaudio:~ $ timedatectl status
               Local time: Sat 2022-01-22 17:59:23 CST
           Universal time: Sat 2022-01-22 23:59:23 UTC
                 RTC time: n/a
                Time zone: America/Chicago (CST, -0600)
System clock synchronized: yes
              NTP service: active
          RTC in local TZ: no
```

Edit the /boot/config.txt to add the dtoverlay for the device:

```shell
sudo nano /boot/config.txt

dtoverlay=i2c-rtc,ds3231
```

Reboot and check `sudo i2cdetect -y 1` for addressing.

Disable the 'fake hwclock'

```shell
sudo apt-get -y remove fake-hwclock
sudo update-rc.d -f fake-hwclock remove
sudo systemctl disable fake-hwclock
```

Update the time servers in `/etc/systemd/timesyncd.conf`

```shell
NTP=time.nist.gov
FallbackNTP=0.debian.pool.ntp.org 1.debian.pool.ntp.org 2.debian.pool.ntp.org 3.debian.pool.ntp.org
```

Check the status of the time

```shell
pi@piaudio:~ $ timedatectl status
               Local time: Sat 2022-01-22 18:20:23 CST
           Universal time: Sun 2022-01-23 00:20:23 UTC
                 RTC time: Sun 2022-01-23 00:20:23
                Time zone: America/Chicago (CST, -0600)
System clock synchronized: yes
              NTP service: active
          RTC in local TZ: no
```

Check status of time sync

```shell
pi@piaudio:~ $ timedatectl timesync-status
       Server: 2601:603:b7f:fec0::bad:beef (2.debian.pool.ntp.org)
Poll interval: 8min 32s (min: 32s; max 34min 8s)
         Leap: normal
      Version: 4
      Stratum: 2
    Reference: 7F43715C
    Precision: 1us (-24)
Root distance: 20.300ms (max: 5s)
       Offset: -30.708ms
        Delay: 110.577ms
       Jitter: 32.769ms
 Packet count: 5
    Frequency: -12.796ppm
```

Check for errors in time sync

```shell
journalctl --unit=systemd-timesyncd.service
```

## Creating a service for the INA219 or INA226 voltage and current monitoring

1. Create a program (monitorINA)that returns voltage and current data via a pipe to the main program.  program also shuts down pi iif battery is too low.

2. Set up to run at start

Create a new systemd service:

```shell
cd  /etc/systemd/system
sudo touch battery-monitor.service
```

Then put in the following text into the file

```shell
[Unit]
Description=Monitors battery voltage and shuts down Pi if low
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=1
User=pi
ExecStart=/usr/bin/python3 /home/pi/code/monitor.py

[Install]
WantedBy=multi-user.target
```

Start the service

```shell
sudo systemctl start battery-monitor
sudo systemctl status battery-monitor
sudo systemctl stop battery-monitor
sudo systemctl restart battery-monitor
```

Enable the service to have it start at boot

```shell
sudo systemctl enable battery-monitor
```

## Installing the IR sensor for a remote control

The easiest way to make this work is to use a universal remote that can be programmed to the rc6_mce protocol.  Buster out of the box will recognize this protocol, convert it to keypresses, and let you trigger scripts.  This is a Microsoft protocol.  A Philips universal remote will have codes for Microsoft.

[Raspberry Pi IR Receiver Gordon Turner](https://blog.gordonturner.com/2020/05/31/raspberry-pi-ir-receiver/)

Need to change the config.txt file to enable the ir input:

```shell
sudo nano /boot/config.txt

Uncomment this to enable infrared communication.
dtoverlay=gpio-ir,gpio_pin=17
```

The latest Raspberry Pi OS (Buster) has IR built into the kernel so no need for installing lirc.  Next install a linux program to read the remote keycodes.  

```shell
sudo apt-get install ir-keytable -y
```

Run to see current status

```shell
pi@piaudio:~/code $ ir-keytable
Found /sys/class/rc/rc0/ (/dev/input/event0) with:
    Name: gpio_ir_recv
    Driver: gpio_ir_recv, table: rc-rc6-mce
    LIRC device: /dev/lirc0
    Attached BPF protocols: Operation not permitted
    Supported kernel protocols: lirc rc-5 rc-5-sz jvc sony nec sanyo mce_kbd rc-6 sharp xmp imon 
    Enabled kernel protocols: lirc rc-5 rc-5-sz jvc sony nec sanyo mce_kbd rc-6 sharp xmp imon 
    bus: 25, vendor/product: 0001:0001, version: 0x0100
    Repeat delay = 500 ms, repeat period = 125 ms
```

Set to all protocols for now, so that we can test with any remote.

```shell
sudo ir-keytable -p all
```

Run this and press  keys on the remote.  Will show key codes, the protocol, and variant from device rc0.

```shell
ir-keytable -t -s rc0
```

Now, you will want to program your universal remote to use a Microsoft code.  Specifically rc6_mce which you may need to find by trial and error.

Select only the protocol that matches your remote, to avoid spurious input.

```shell
sudo ir-keytable -p rc6
```

Run `ir-keytable -t -s rc0` again and try the keys to see the keynames you will get.  If desired, you can update the keytable so that different key names are mapped to the keys.  This ways the key names can better match the actual buttons on your remote, or reflect your application.  For example, I changed the the POWER button keyname from "KEY_SLEEP" to "KEY_POWER" and this now triggers the Pi to shut down.  I also changed the INPUT button  "KEY_PVR" to "KEY_WLAN" to make it clearer that this key turns on wifi.  I will use the EXIT button "KEY_EXIT" as it is to shut off the wifi.

You will find sample keytables here:

```shell
ls /lib/udev/rc_keymaps/
```

Copy the file `rc6_mce.toml` to your home directory.  Then you can edit the keys names.  Key names need to match the ones in here: [linux/input-event-codes.h at d2d1ac07330bfb8e896bd58a6ac3a950d1d96fde · raspberrypi/linux · GitHub](https://github.com/raspberrypi/linux/blob/d2d1ac07330bfb8e896bd58a6ac3a950d1d96fde/include/uapi/linux/input-event-codes.h)

Put the modified keytable file `rc6_mce.toml`_in the directory `/etc/rc_keymaps/`

```shell
sudo cp rc6_mce.toml /etc/rc_keymaps/
```

To test, reload the keytable manually

```shell
sudo ir-keytable -c -w /etc/rc_keymaps/rc6_0.toml
```

You can also reload the whole configuration normally done at boot.  You will get an error message if something is wrong with your edited keymap

```shell
sudo  ir-keytable -a /etc/rc_maps.cfg
```

Then try this to see if keys are recognized

```shell
ir-keytable -t -s rc0
```

And try this to see if triggerhappy will recognize the keys being pressed:

```shell
thd --dump /dev/input/event*
```

You should see this type of output when pressing keys

```
EV_KEY    KEY_OK    1    /dev/input/event0
# KEY_OK    1    command
EV_KEY    KEY_OK    0    /dev/input/event0
# KEY_OK    0    command
EV_KEY    KEY_OK    1    /dev/input/event0
# KEY_OK    1    command
EV_KEY    KEY_OK    0    /dev/input/event0
# KEY_OK    0    command
EV_KEY    KEY_NUMERIC_STAR    1    /dev/input/event0
# KEY_NUMERIC_STAR    1    command
EV_KEY    KEY_NUMERIC_STAR    0    /dev/input/event0
# KEY_NUMERIC_STAR    0    command
EV_KEY    KEY_NUMERIC_STAR    1    /dev/input/event0
```

The following keys seem to control the Pi:

KEY_POWER - powers the Pi down

KEY_LEFT, KEY_RIGHT,KEY_UP,KEY_DOWN - moves the cursor

KEY_MUTE - mutes or unmutes the Pi sound

KEY_VOLUMEUP, KEYVOLUMEDOWN - raises or lowers the volume

#### Create triggerhappy scripts for these keys:

KEY_WLAN - Turn on Wifi

KEY_EXIT - Turn off WiFi

[GitHub - wertarbyte/triggerhappy: A lightweight hotkey daemon](https://github.com/wertarbyte/triggerhappy)

Create a new triggerhappy configuration

```shell
sudo nano /etc/triggerhappy/triggers.d/remote-WLAN_CONTROL.conf
```

Add the following lines to turn on and off wifi

```
KEY_WLAN     1   /usr/bin/sudo  /usr/sbin/ifconfig wlan0 up
KEY_EXIT     1   /usr/bin/sudo  /usr/sbin/ifconfig wlan0 down
```

Restart the triggerhappy daemon

```shell
sudo systemctl restart triggerhappy
```

Triggerhappy uses the user `nobody` so we need to give this user permission to use `usr/sbin/ifconfig` without a password for sudo

```shell
sudo visudo


# ADDED
nobody ALL =NOPASSWD: /usr/sbin/ifconfig*
```

Check the status to see if any errors while executing

```shell
systemctl status triggerhappy
```

# Installing the ADC and recording firmware

First install some dependencies onto the raspberry pi

```shell
sudo apt install opus-tools
sudo apt install vorbis-tools
sudo apt-get install flac
pip3 install mutagen
pip3 install PyAudio
pip3 install numpy
```





# Running the recorder script

## Command line

Since we ensured that user jobs are not cancelled when the user logs out, we can start them like this.

* Direct errors to an error file: `autorecordt.py 2> errors.txt &`

* Direct output and errors to two files: `autorecordt.py > out.txt 2> err.txt &`
