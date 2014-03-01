
This mini-howto explains how to setup the player as a small daemon on
a Raspberry Pi running Raspbian.

Basic steps
===========

1. Install the player as explained in the README.rst
2. Make sure GStreamer 1.x works:

   ::

      $ gst-launch-1.0 playbin uri=http://....

3. Install daemontools

   ::

      $ sudo apt-get install daemontools

4. Setup the radio startup script in /etc/service/radio/run (should be executable)

   ::

      #!/bin/bash
      export LANG='en_US.UTF-8'
      export LC_ALL='en_US.UTF-8'
      export HOME=/home/pi
      export PYTHONIOENCODING=utf-8
      setuidgid pi python -u /usr/local/bin/radioplayer -x /home/pi/.config/radioplayer.cfg

5. Manually startup the daemon. At next boot daemontools should do it automatically.

   ::

      $ sudo svc -u /etc/service/radio

   In case of problems, stop the daemon and debug :)

   ::

      $ sudo svc -d /etc/service/radio

LIRC
====

The player provides a LIRC config file for the Streamzap remote but it
should be easy to adapt for other remotes supported by LIRC.

Here I use the devinput driver that connects to the device driver
file created by the streamzap kernel module.

::

  # /etc/lirc/hardware.conf
  #
  # Arguments which will be used when launching lircd
  LIRCD_ARGS=""

  #Don't start lircmd even if there seems to be a good config file
  #START_LIRCMD=false

  #Don't start irexec, even if a good config file seems to exist.
  #START_IREXEC=false

  #Try to load appropriate kernel modules
  LOAD_MODULES=true

  # Run "lircd --driver=help" for a list of supported drivers.
  DRIVER="devinput"
  # usually /dev/lirc0 is the correct setting for systems using udev 
  DEVICE="/dev/input/by-id/usb-Streamzap__Inc._Streamzap_Remote_Control-event-if00"
  MODULES=""

  # Default configuration files for your hardware if any
  LIRCD_CONF=""
  LIRCMD_CONF=""

::

  # /etc/lirc/lircd.conf
  include "/usr/share/lirc/remotes/devinput/lircd.conf.devinput"

Once lircd is running check the input events are correctly handled by
running irw and pressing some buttons of the remote.

Finally make sure the radioplayer.cfg file references the right keymap
file.

Growl
=====

If you want notifications delivered to your Mac via the network:

1. Install Growl on your Mac
2. Setup a password in the preferences
3. Make sure the Mac is reachable from the RPi by hostname
4. Install python-gntp on the RPi (no debian package, AFAIk. Use the
   source)
5. Update hostname/password options in radioplayer.cfg
