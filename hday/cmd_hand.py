import time
import cmd
from struct import *
from hday.err_code import *
from hday.cmd import *



CAN_NORMAL    = 0
CAN_MONITOR   = 1
CAN_LOOPBACK  = 2

CAN_CLASSIC   = 0
CAN_FD_NO_BRS = 1
CAN_FD_BRS    = 2

CAN_STD       = 0
CAN_EXT       = 1

CAN_ID_MASK   = 0
CAN_ID_RANGE  = 1





class CmdHand:

  CMD_BLDC_GET        = 0x0200
  CMD_BLDC_SET        = 0x0201
  CMD_MAIN_GET_MODULE_CNT  = 0x0204
  CMD_MAIN_GET_MODULE_INFO = 0x0205
  CMD_MAIN_SEND_POSITION   = 0x020C
  CMD_MAIN_SEND_PING       = 0x020D


  def __init__(self, cmd: Cmd):
    self.cmd = cmd

  def __del__(self):
    pass

  def setEnable(self, enable, timeout=500):
    err_code = ERR_CMD_RX_TIMEOUT
    send_buf = pack("<BI", 0, enable)
    ret, packet = self.cmd.sendCmdRxResp(self.CMD_BLDC_SET, send_buf, len(send_buf), timeout)
    if ret == True:
      err_code = packet.err_code
    return err_code, None

  def getEnable(self, enable, timeout=500):
    err_code = ERR_CMD_RX_TIMEOUT
    send_buf = pack("B", 0)
    ret, packet = self.cmd.sendCmdRxResp(self.CMD_BLDC_GET, send_buf, len(send_buf), timeout)
    if ret == True:
      err_code = packet.err_code
      if packet.err_code == 0:
        str_fmt = "<BI"
        fmt_size = calcsize(str_fmt)
        data = unpack(str_fmt, packet.data[:fmt_size])
        enable = data[1]
    return err_code, None

  def setTorqueEnable(self, enable, timeout=500):
    err_code = ERR_CMD_RX_TIMEOUT
    send_buf = pack("<BBB", 1, 0xFF, enable)
    ret, packet = self.cmd.sendCmdRxResp(self.CMD_BLDC_SET, send_buf, len(send_buf), timeout)
    if ret == True:
      err_code = packet.err_code
    return err_code, None

  def getTorqueEnable(self, enable, timeout=500):
    err_code = ERR_CMD_RX_TIMEOUT
    send_buf = pack("B", 1)
    ret, packet = self.cmd.sendCmdRxResp(self.CMD_BLDC_GET, send_buf, len(send_buf), timeout)
    if ret == True:
      err_code = packet.err_code
      if packet.err_code == 0:
        str_fmt = "<BB"
        fmt_size = calcsize(str_fmt)
        data = unpack(str_fmt, packet.data[:fmt_size])
        enable = data[1]
    return err_code, None

  def sendPosition(self, id, position, velocity=5):
    send_buf = pack("<Bff", id, position, velocity)
    self.cmd.send(CmdPacket.PKT_TYPE_CTRL, self.CMD_MAIN_SEND_POSITION, 0, send_buf, len(send_buf))
    return OK, None

  def sendPing(self):
    self.cmd.send(CmdPacket.PKT_TYPE_CTRL, self.CMD_MAIN_SEND_PING, OK, None, 0)
    return OK, None

  def getModuleCount(self, timeout=500):
    if self.cmd.is_open == False:
      return ERR_CMD_NOT_OPEN, 0

    err_code = ERR_CMD_RX_TIMEOUT
    count = 0
    ret, packet = self.cmd.sendCmdRxResp(self.CMD_MAIN_GET_MODULE_CNT, None, 0, timeout)
    if ret == True:
      err_code = packet.err_code
      if packet.err_code == 0:
        str_fmt = "<B"
        fmt_size = calcsize(str_fmt)
        data = unpack(str_fmt, packet.data[:fmt_size])
        count = data[0]
    return err_code, count

  def getModuleInfo(self, index, timeout=500):
    if self.cmd.is_open == False:
      return ERR_CMD_NOT_OPEN, 0

    resp = None
    err_code = ERR_CMD_RX_TIMEOUT
    send_buf = pack("B", index)
    ret, packet = self.cmd.sendCmdRxResp(self.CMD_MAIN_GET_MODULE_INFO, send_buf, len(send_buf), timeout)
    if ret == True:
      err_code = packet.err_code
      if packet.err_code == 0:
        str_fmt = "<BB32s"
        fmt_size = calcsize(str_fmt)
        data = unpack(str_fmt, packet.data[:fmt_size])
        resp = data
    return err_code, resp
