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
    IS_ALIVE = 6

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
        elif code == Mode.IS_ALIVE:
            return 'IS_ALIVE'
        else:
            return 'unknown method'


class Operation:
    POWER = 0
    POWER_CMD = 'power'

    LOG = 1
    LOG_CMD = 'log'

    GEO_MEAN = 2
    GEO_MEAN_CMD = 'GM'  # Geometric Mean

    BIN_COE = 3
    BIN_COE_CMD = 'aCb'  # Binomial coefficient

    @staticmethod
    def name_from_code(code: int) -> str:
        if code == Operation.POWER:
            return Operation.POWER_CMD
        elif code == Operation.LOG:
            return Operation.LOG_CMD
        elif code == Operation.GEO_MEAN:
            return Operation.GEO_MEAN_CMD
        elif code == Operation.BIN_COE:
            return Operation.BIN_COE_CMD


class Error:
    SESSION_ID_NOT_FOUND = 0
    UNAUTHORISED = 1
    CANNOT_READ_DATAGRAM = 2
    INTERNAL_SERVER_ERROR = 3
    NOT_EXISTING_DATA = 4
    INVALID_ARGUMENT = 5
    MAX_VALUE_EXCEEDED = 6

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
        elif code == Error.NOT_EXISTING_DATA:
            return 'NOT_EXISTING_DATA'
        elif code == Error.INVALID_ARGUMENT:
            return 'INVALID_ARGUMENT'
        elif code == Error.MAX_VALUE_EXCEEDED:
            return 'MAX_VALUE_EXCEEDED'
        else:
            return 'unknown error'

