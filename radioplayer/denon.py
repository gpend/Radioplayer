
import ConfigParser
import telnetlib
import time

class DenonRemote:

    def __init__(self, config):
        try:
            self.address = config.get("denon", "address")
        except ConfigParser.NoSectionError:
            self.address = None

    @property
    def enabled(self):
        return self.address != None

    def _connect(self):
        try:
            server = telnetlib.Telnet(self.address)
        except socket.error:
            server = None
        return server

    def send_command(self, cmd, server=None):
        do_close = False
        if not server:
            server = self._connect()
            do_close = True
        if not server:
            return

        server.write("%s\r" % cmd)
        time.sleep(1)
        result = server.read_eager()

        if do_close:
            server.close()
        return result

    def power_on(self, server=None):
        self.send_command("PWON", server=server)

    def power_off(self, server=None):
        self.send_command("PWSTANDBY", server=server)

    def toggle_power(self):
        server = self._connect()
        if not server:
            return False

        status = self.send_command("PW?", server)
        if status.startswith("PWON"):
            self.power_off(server)
            powered = False
        else:
            self.power_on(server)
            powered = True

        server.close()
        return powered