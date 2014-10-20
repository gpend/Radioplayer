
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

    def send_command(self, cmd, server=None):
        do_close = False
        if not server:
            server = telnetlib.Telnet(self.address)
            do_close = True

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
        server = telnetlib.Telnet(self.address)
        status = self.send_command("PW?", server)
        if status.startswith("PWON"):
            self.power_off(server)
        else:
            self.power_on(server)

        server.close()
