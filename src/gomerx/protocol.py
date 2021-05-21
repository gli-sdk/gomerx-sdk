import binascii
import json
from typing import Dict

""" 协议格式示例
{"seq": 999, "code": 100, "hard": {"mode": 101 }}
"""

__all__ = ['Message']

SDK_FIRST_SEQ_ID = 10000
SDK_LAST_SEQ_ID = 20000

SDK_MSG_TYPE_REQ = 1
SDK_MSG_TYPE_RESP = 2


class ProtoData(object):
    _cmdtype = SDK_MSG_TYPE_REQ
    _cmdid = None
    _cmdprm = None

    def __init__(self, **kwargs):
        self._buf = None
        self._len = None

    @property
    def cmdid(self):
        return self._cmdid

    @cmdid.setter
    def cmdid(self, value):
        self._cmdid = value

    def pack_req(self):
        return dict()

    def unpack_req(self, buf):
        return True

    def pack_resp(self):
        pass

    def unpack_resp(self, buf):
        return True


class MessageBase(object):
    _next_seq_id = SDK_FIRST_SEQ_ID

    def __init__(self):
        pass


class Message(MessageBase):
    def __init__(self, proto=None):
        self._buf = None
        self._len = 0
        self._is_ack = False
        self._need_ack = 1  # 0 for no need, 1 for ack now, 2 for ack when finish
        if self.__class__._next_seq_id == SDK_LAST_SEQ_ID:
            self.__class__._next_seq_id = SDK_FIRST_SEQ_ID
        else:
            self.__class__._next_seq_id += 1
        self._seq_id = self._next_seq_id
        self._proto = proto

    def pack(self):
        if self._proto:
            data = self._proto.pack_req()
            data.update({"seq": self._seq_id, "msgtype": self._need_ack})
            data_buf = json.dumps(data)
        self._buf = data_buf
        return self._buf

    def unpack_protocol(self):
        if not self._proto.unpack_resp(self._buf):
            return False
        return True

    def get_proto(self):
        return self._proto

    def get_buf(self):
        return self._buf


def decode_msg(buff: str):
    msg = Message()
    msg._buf = buff.decode(encoding='utf-8')
    msg._len = len(msg._buf)
    msg_dict = json.loads(msg._buf)
    msg._is_ack = True
    msg._seq_id = msg_dict['seq']
    if 'hard' in msg_dict:
        msg._proto = ProtoGetHardInfo()
    elif 'item' in msg_dict:
        item = msg_dict['item']
        if item == 5000:
            msg._proto = ProtoChassisMove()
        elif item == 5010:
            msg._proto = ProtoArmControl()
        elif item == 5011:
            msg._proto = ProtoServoControl()
        elif item == 5020:
            msg._proto = ProtoGripperCtrl()
        elif item == 5300:
            msg._proto = ProtoSetLed()
    return msg

##########################################################


class ProtoGetHardInfo(ProtoData):
    _cmdid = 300

    def __init__(self):
        self._version = 'x.x.x'
        self._sn = ''
        self._battery = 0
        self._funckey = 'hard'
        self._cmdkey = 'call'

    def pack_req(self):
        data = {self._funckey: {self._cmdkey: self._cmdid}}
        return data

    def unpack_resp(self, buf):
        info = json.loads(buf)
        hard_info = info['hard']
        self._version = hard_info['ver']
        self._sn = hard_info['sn']
        self._battery = hard_info['bat']

        return True


class ProtoSetLed(ProtoData):

    _cmdid = 5300

    def __init__(self, color=(0, 0, 0)):
        self._r = color[0]
        self._g = color[1]
        self._b = color[2]

    def pack_req(self):
        self.__class__._cmdprm = [0xff, self._r, self._g, self._b]
        data = {'item': self._cmdid, 'param': self.__class__._cmdprm}
        return data

    def unpack_resp(self, buf):
        return True


class ProtoSetWheelSpeed(ProtoData):
    def __init__(self):
        self._lf = 0
        self._lb = 0
        self._rf = 0
        self._rb = 0

    def pack_req(self):
        return super().pack_req()

    def unpack_resp(self, buf):
        return super().unpack_resp(buf)


class ProtoChassisMove(ProtoData):
    _cmdid = 5000

    def __init__(self):
        self._action_id = 0
        self._x = 0
        self._y = 0
        self._a = 0

    def pack_req(self):
        self.__class__._cmdprm = [self._x, self._y]
        data = {'item': self._cmdid, 'param': self.__class__._cmdprm}
        return data

    def unpack_resp(self, buf):
        info = json.loads(buf)
        self._code = info['code']
        return True


class ProtoServoControl(ProtoData):
    _cmdid = 5011

    def __init__(self):
        self._action_id = 0
        self._id = 0
        self._value = 0

    def pack_req(self):
        if self._id == 0:
            self.__class__._cmdprm = [self._value, 0xff]
        elif self._id == 1:
            self.__class__._cmdprm = [0xff, self._value]
        data = {'item': self._cmdid, 'param': self.__class__._cmdprm}
        return data

    def unpack_resp(self, buf):
        info = json.loads(buf)
        self._code = info['code']
        return True


class ProtoServoGetAngle(ProtoData):
    def __init__(self):
        self._id = 0
        self._angle = 0

    def pack_req(self):
        return super().pack_req()

    def unpack_resp(self, buf):
        return super().unpack_resp(buf)


class ProtoArmControl(ProtoData):
    _cmdid = 5010

    def __init__(self):
        self._action_id = 0
        self._x = 0
        self._y = 0

    def pack_req(self):
        self.__class__._cmdprm = [self._x, self._y]
        data = {'item': self._cmdid, 'param': self.__class__._cmdprm}
        return data

    def unpack_resp(self, buf):
        info = json.loads(buf)
        self._code = info['code']
        return True


class ProtoGripperCtrl(ProtoData):
    _cmdid = 5020

    def __init__(self):
        self._action_id = 0
        self._value = 0

    def pack_req(self):
        self.__class__._cmdprm = [self._value]
        data = {'item': self._cmdid, 'param': self.__class__._cmdprm}
        return data

    def unpack_resp(self, buf):
        info = json.loads(buf)
        self._code = info['code']
        return True


class ProtoGripperStatus(ProtoData):
    def __init__(self):
        self._status = 0

    def pack_req(self):
        return super().pack_req()

    def unpack_resp(self, buf):
        return super().unpack_resp(buf)


class ProtoVisionDetectInfo(ProtoData):

    def __init__(self):
        self._info = []

    def pack_req(self):
        return super().pack_req()

    def unpack_req(self, buf):
        return super().unpack_req(buf)


class ProtoVisionDetectEnable(ProtoData):
    pass


class ProtoPushPeriodMsg(ProtoData):

    def __init__(self):
        self._sub_mode = 0
        self._data_buf = None

    def pack_req(self):
        return super().pack_req()

    def unpack_req(self, buf):
        return super().unpack_req(buf)
