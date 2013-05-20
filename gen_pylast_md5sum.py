from radioplayer import pylast
import getpass
password = getpass.getpass("Please enter your Last.FM or Libre.FM password: ")
md5sum = pylast.md5(password)
print "MD5 is: %s ... Please edit ~/.config/radioplayer.cfg accordingly." % md5sum

