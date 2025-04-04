from struct import unpack, calcsize
import copy

from . import Cmd, CmdBoot, CmdHand, CmdPacket, OK


class Robot():
    def __init__(self, port, baud=600):
        self.cmd = Cmd()
        self.cmd_boot = CmdBoot(self.cmd)
        self.cmd_hand = CmdHand(self.cmd)

        self.port = port
        self.baud = baud

        self.is_enable = False

        if self.cmd.is_open:
            self.cmd.close()

    def __enter__(self):
        ret = self.cmd.open(self.port, self.baud)
        if ret is False:
            print("Uart Open Fail")
            print(f"  check: {self.port}")
            print(f"  run: sudo chmod 777 {self.port}")
            exit(-1)

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.is_enable:
            self.request_robot_enable(False)

        self.cmd.stop()
        self.cmd.close()

    def read_version(self):
        err_code, resp = self.cmd_boot.readVersion(100)
        if err_code == OK:
            print(
                "\n"
                "Boot Version Message\n"
                "\n"
                f"boot - version: {resp.boot.version_str}\n"
                "\n"
                f"boot - name_str: {resp.boot.name_str}\n"
                f"boot - firm_addr: {resp.boot.firm_addr}\n"
                "\n"
                f"firm - version: {resp.firm.version_str}\n"
                "\n"
                f"firm - name_str: {resp.firm.name_str}\n"
                f"firm - firm_addr: {resp.firm.firm_addr}\n"
                "\n"
                f"update - version: {resp.update.version_str}\n"
                "\n"
                f"update - name_str: {resp.update.name_str}\n"
                f"update - firm_addr: {resp.update.firm_addr}\n"
                "\n"
                )

    def request_robot_enable(self, enable):
        err_code, resp = self.cmd_hand.setEnable(enable)
        if err_code == OK:
            print(f"{'Enable' if enable else 'Disable'} OK")
            self.is_enable = True
        else:
            print("Err : " + str(hex(err_code)))

    def getSensorBypassPacket(self):
        cmd_packet = self.cmd.getPacket()
        if cmd_packet is None:
            return None, None

        packet = copy.deepcopy(cmd_packet)
        cmd_packet = None

        if packet.type == packet.PKT_TYPE_STATUS and packet.cmd == 0x000B:
            return self.processStatusSenorBypass(packet)

        return None, None

    def processStatusSenorBypass(self, packet: CmdPacket):
        str_fmt = "<3b"
        fmt_size = calcsize(str_fmt)

        sensor_bypass_id = packet.data[0]
        # sensor_bypass_type = packet.data[1]
        # sensor_bypass_length = packet.data[2]
        sensor_bypass_data = []
        for idx in range(0, 16):
            data = unpack(str_fmt, packet.data[3+(idx*fmt_size):3+(idx*fmt_size)+fmt_size])
            scaled_data = [v*2 for v in data]
            # print(f"{idx:02} : {scaled_data}")
            sensor_bypass_data.append(scaled_data)

        return sensor_bypass_id, sensor_bypass_data
