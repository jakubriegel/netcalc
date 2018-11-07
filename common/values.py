# utils
LOCAL_HOST = '127.0.0.1'
PORT = 1500

MAX_DATAGRAM_SIZE = 4096
RESULT_ENTRY_SIZE = 322


class Status:
    NEW = 0
    OK = 1
    REFUSED = 2
    ERROR = 3


class Mode:
    CONNECT = 0
    DISCONNECT = 1
    OPERATION = 2
    QUERY_BY_SESSION_ID = 3
    QUERY_BY_RESULT_ID = 4
    ERROR = 5

    QUERY_BY_SESSION_ID_CMD = 'session'
    QUERY_BY_RESULT_ID_CMD = 'result'

    @staticmethod
    def name_from_code(code: int) -> str:
        if code == Mode.CONNECT:
            return 'CONNECT'
        elif code == Mode.DISCONNECT:
            return 'DISCONNECT'
        elif code == Mode.OPERATION:
            return 'OPERATION'
        elif code == Mode.QUERY_BY_SESSION_ID:
            return 'QUERY_BY_SESSION_ID'
        elif code == Mode.QUERY_BY_RESULT_ID:
            return 'QUERY_BY_RESULT_ID'
        elif code == Mode.ERROR:
            return 'ERROR'
        else:
            return 'unknown method'


class Operation:
    POWER = 0
    POWER_CMD = 'power'

    LOG = 1
    LOG_CMD = 'log'

    OP_3 = 2  # TODO: [Artur] add OP_3 and OP_4
    OP_3_CMD = 'op3'

    OP_4 = 3
    OP_4_CMD = 'op4'

    @staticmethod
    def name_from_code(code: int) -> str:
        if code == Operation.POWER:
            return Operation.POWER_CMD
        elif code == Operation.LOG:
            return Operation.LOG_CMD
        elif code == Operation.OP_3:
            return Operation.OP_3_CMD
        elif code == Operation.OP_4:
            return Operation.OP_4_CMD


class Error:
    SESSION_ID_NOT_FOUND = 0
    UNAUTHORISED = 1
    CANNOT_READ_DATAGRAM = 2
    INTERNAL_SERVER_ERROR = 3

    @staticmethod
    def name_from_code(code: int) -> str:
        if code == Error.SESSION_ID_NOT_FOUND:
            return 'SESSION_ID_NOT_FOUND'
        elif code == Error.UNAUTHORISED:
            return 'UNAUTHORISED'
        elif code == Error.CANNOT_READ_DATAGRAM:
            return 'CANNOT_READ_DATAGRAM'
        elif code == Error.INTERNAL_SERVER_ERROR:
            return 'INTERNAL_SERVER_ERROR'
        else:
            return 'unknown error'

