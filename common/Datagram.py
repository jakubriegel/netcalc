from bitstring import BitArray, ConstBitArray, ConstBitStream


class Datagram:
    """ Stores, prepares and retrieves data sent over network """

    def __init__(
            self,
            status: int, mode: int, session_id: int=0,
            operation: int=0, a: float=0, b: float=0,
            result: float=0, result_id: int=0, last: bool = True
    ) -> None:
        super().__init__()
        self.status = status
        self.mode = mode
        self.session_id = session_id
        self.operation = operation
        self.a = a
        self.b = b
        self.result = result
        self.result_id = result_id
        self.last = last

    @classmethod
    def from_bytes(cls, binary: bytes):
        """ Parses retrieved data into python object
        :param binary: data to parse
        """

        datagram = ConstBitStream(bytes=binary)
        operation = datagram.read('uint:2')
        a = datagram.read('float:64')
        b = datagram.read('float:64')
        status = datagram.read('uint:2')
        session_id = datagram.read('uint:16')
        mode = datagram.read('uint:3')
        result = datagram.read('float:64')
        result_id = datagram.read('uint:32')
        last = datagram.read("bool")

        return cls(status, mode, session_id, operation, a, b, result, result_id, last)

    def get_bytes(self) -> bytes:
        """ Parses data to binary format """

        datagram = BitArray()

        datagram.append(ConstBitArray(uint=self.operation, length=2))
        datagram.append(ConstBitArray(float=self.a, length=64))
        datagram.append(ConstBitArray(float=self.b, length=64))
        datagram.append(ConstBitArray(uint=self.status, length=2))
        datagram.append(ConstBitArray(uint=self.session_id, length=16))
        datagram.append(ConstBitArray(uint=self.mode, length=3))
        datagram.append(ConstBitArray(float=self.result, length=64))
        datagram.append(ConstBitArray(uint=self.result_id, length=32))
        datagram.append(ConstBitArray(bool=self.last))

        return datagram.tobytes()

    def __str__(self) -> str:
        return \
            "{" + \
            " status=" + str(self.status) + \
            " mode=" + str(self.mode) + \
            " session_id=" + str(self.session_id) + \
            " operation=" + str(self.operation) + \
            " a=" + str(self.a) + \
            " b=" + str(self.b) + \
            " result=" + str(self.result) + \
            " result_id=" + str(self.result_id) + \
            " }"
