import socket
import bitstring
from common import utils
from common.values import Status, Mode, Operation, LOCAL_HOST, PORT, MAX_DATAGRAM_SIZE, Error
from common.Datagram import Datagram


class Client:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.session_id = 0

    def start(self):
        if self.__connect():
            self.menu()

    def menu(self):
        print('You can now use netcalc')
        print(Operation.POWER_CMD + ' a b\t: raise a to the power of b')
        print(Operation.LOG_CMD + ' a b\t\t: get the logarithm of a of the base of b')
        print(Operation.OP_3_CMD + ' a b\t\t: tba')
        print(Operation.OP_4_CMD + ' a b\t\t: tba')
        print(Mode.QUERY_BY_SESSION_ID_CMD + '\t\t: get all calculations')
        print(Mode.QUERY_BY_RESULT_ID_CMD + ' id\t: get calculation by its id')
        print('exit\t\t: exit netcalc')

        while True:
            print('>', end=' ')
            command = input()
            if command == 'exit':
                self.__disconnect()
                break
            else:
                command = command.split()

                if command[0] == Mode.QUERY_BY_SESSION_ID_CMD and len(command) == 1:
                    self.__query_by_session_id()
                elif command[0] == Mode.QUERY_BY_RESULT_ID_CMD and len(command) == 2:
                    self.__query_by_result_id(int(command[1]))
                elif len(command) == 3:
                    operation: int
                    if command[0] == Operation.POWER_CMD:
                        operation = Operation.POWER
                    elif command[0] == Operation.LOG_CMD:
                        operation = Operation.LOG
                    elif command[0] == Operation.OP_3_CMD:
                        operation = Operation.OP_3
                    elif command[0] == Operation.OP_4_CMD:
                        operation = Operation.OP_4

                    a = float(command[1])
                    b = float(command[2])

                    self.__operation(operation, a, b)
                else:
                    print('invalid command')

    def __send_datagram(self, datagram: Datagram, session_query: bool = False) -> Datagram:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        s.sendall(datagram.get_bytes())
        answer_bin = s.recv(MAX_DATAGRAM_SIZE)
        try:
            answer = Datagram.from_bytes(answer_bin)
        except (bitstring.ReadError, ValueError, TypeError):
            print('error reading datagram')
        else:
            if answer.status == Status.ERROR:
                print(
                    'error on server: ' + Mode.name_from_code(answer.mode) + ' - ' + Error.name_from_code(answer.a)
                )
            if answer.status == Status.REFUSED:
                print(
                    'server refused to ' + Mode.name_from_code(datagram.mode) + ' reason: ' + Error.name_from_code(answer.a)
                )
            return answer if not session_query else Datagram.results_from_bytes(answer_bin)

    def __connect(self) -> bool:
        utils.log('connecting to : ' + self.host + ':' + str(self.port))
        datagram = Datagram(Status.NEW, Mode.CONNECT)
        answer = self.__send_datagram(datagram)
        utils.log('connected to : ' + self.host + ':' + str(self.port))
        self.session_id = answer.session_id
        if answer.status == Status.OK:
            return True
        else:
            utils.log(self.host + ':' + str(self.port) + ' refused to connect')
            return False

    def __disconnect(self) -> bool:
        utils.log('disconnecting from : ' + self.host + ':' + str(self.port))
        datagram = Datagram(Status.NEW, Mode.DISCONNECT, self.session_id)
        answer = self.__send_datagram(datagram)
        if answer.status == Status.OK:
            utils.log('disconnected from : ' + self.host + ':' + str(self.port))
            self.session_id = answer.session_id
            return True
        else:
            utils.log(
                'cannot disconnect from : ' + self.host + ':' + str(self.port) + ' error code: ' + str(answer.a),
                True
            )
            return False

    def __operation(self, operation: int, a: float, b: float):
        datagram = Datagram(Status.NEW, Mode.OPERATION, self.session_id, operation, a, b)
        answer = self.__send_datagram(datagram)
        if answer.status == Status.OK:
            print(str(answer.result) + '\t:' + str(answer.result_id))

    def __query_by_session_id(self):
        datagram = Datagram(Status.NEW, Mode.QUERY_BY_SESSION_ID, self.session_id)
        answer = self.__send_datagram(datagram, True)
        if answer.status == Status.OK:
            for result in answer.results:
                # TODO: [Artur] improve presentation of results [maybe method in utils used both by client and server?]
                print(Operation.name_from_code(result[1]) + ' ' + str(result[2]) + ' ' + str(result[3]) + ' -> ' + str(result[4]))

    def __query_by_result_id(self, result_id: int):
        datagram = Datagram(Status.NEW, Mode.QUERY_BY_RESULT_ID, self.session_id, a=result_id)
        answer = self.__send_datagram(datagram)
        if answer.status == Status.OK:
            # TODO: [Artur] improve presentation of result
            print(answer)
            print(Operation.name_from_code(answer.operation) + ' ' + str(answer.a) + ' ' + str(answer.b) + ' -> ' + str(answer.result))


if __name__ == '__main__':
    client = Client(LOCAL_HOST, PORT)
    client.start()