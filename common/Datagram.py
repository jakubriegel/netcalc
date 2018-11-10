from bitstring import BitArray, ConstBitArray, ConstBitStream


class Datagram:
    def __init__(
            self,
            status: int, mode: int, session_id: int=None,
            operation: int=None, a: float=None, b: float=None,
            result: float=None, result_id: int=None, timestamp: int=None,
            results: list = None
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
        self.timestamp = timestamp
        self.results = results

    @classmethod
    def from_bytes(cls, binary: bytes):
        datagram = ConstBitStream(bytes=binary)

        status = datagram.read('uint:2')
        mode = datagram.read('uint:3')
        session_id = datagram.read('uint:16') if datagram.length >= 21 else None
        operation = datagram.read('uint:2') if datagram.length >= 23 else None
        a = datagram.read('float:64') if datagram.length >= 87 else None
        b = datagram.read('float:64') if datagram.length >= 151 else None
        result = datagram.read('float:64') if datagram.length >= 215 else None
        result_id = datagram.read('uint:32') if datagram.length >= 247 else None
        timestamp = datagram.read('uint:64') if datagram.length >= 311 else None

        return cls(status, mode, session_id, operation, a, b, result, result_id, timestamp)

    @classmethod
    def results_from_bytes(cls, binary: bytes):
        datagram = ConstBitStream(bytes=binary)

        status = datagram.read('uint:2')
        mode = datagram.read('uint:3')
        session_id = datagram.read('uint:16') if datagram.length >= 21 else None
        results = []
        while datagram.pos + 322 < datagram.length:
            results.append((
                datagram.read('uint:64'),   # result_id
                datagram.read('uint:2'),    # operation
                datagram.read('float:64'),  # a
                datagram.read('float:64'),  # b
                datagram.read('float:64'),  # result
                datagram.read('uint:64')    # timestamp
            ))

        return cls.from_result_list(status, mode, session_id, results)

    @classmethod
    def from_result_list(cls, status: int, mode: int, session_id: int, results: list):
        return cls(status, mode, session_id, results=results)

    def get_bytes(self) -> bytes:
        datagram = BitArray()
        datagram.append(ConstBitArray(uint=self.status, length=2))
        datagram.append(ConstBitArray(uint=self.mode, length=3))
        if self.session_id is not None:
            datagram.append(ConstBitArray(uint=self.session_id, length=16))
            if self.results is not None:
                for result in self.results:  # 322
                    datagram.append(ConstBitStream(uint=result[0], length=64))   # result_id
                    datagram.append(ConstBitStream(uint=result[1], length=2))    # operation
                    datagram.append(ConstBitStream(float=result[2], length=64))  # a
                    datagram.append(ConstBitStream(float=result[3], length=64))  # b
                    datagram.append(ConstBitStream(float=result[4], length=64))  # result
                    datagram.append(ConstBitStream(uint=result[5], length=64))   # timestamp

            elif self.operation is not None:
                datagram.append(ConstBitArray(uint=self.operation, length=2))
                if self.a is not None:
                    datagram.append(ConstBitArray(float=self.a, length=64))
                    if self.b is not None:
                        datagram.append(ConstBitArray(float=self.b, length=64))
                        if self.result is not None:
                            datagram.append(ConstBitArray(float=self.result, length=64))
                            if self.result_id is not None:
                                datagram.append(ConstBitArray(uint=self.result_id, length=32))
                                if self.timestamp is not None:
                                    datagram.append(ConstBitArray(float=self.timestamp, length=64))

        return datagram.tobytes()

    def __str__(self) -> str:
        data = "{" + \
            " status=" + str(self.status) + \
            " mode=" + str(self.mode) + \
            " session_id=" + str(self.session_id)

        if self.operation is not None:
            data += " operation=" + str(self.operation)
        if self.a is not None:
            data += " a=" + str(self.a)
        if self.b is not None:
            data += " b=" + str(self.b)
        if self.result is not None:
            data += " result=" + str(self.result)
        if self.result_id is not None:
            data += " result_id=" + str(self.result_id)
        if self.timestamp is not None:
            data += " timestamp=" + str(self.timestamp)
        if self.results is not None:
            data += " results=" + str(self.results)

        data += ' }'
        return data
