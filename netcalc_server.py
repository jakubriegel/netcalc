import calendar
import socket
import time
import bitstring
from threading import Thread, Lock
from common.Datagram import Datagram
from common import utils
from common.values import Status, Mode, Operation, LOCAL_HOST, PORT, Error, MAX_DATAGRAM_SIZE


class Server(Thread):
    def __init__(self, host: str, port: int) -> None:
        super().__init__(name='server')
        self.host = host
        self.port = port
        self.on = True

        self.sessions = {}
        self.sessions_lock = Lock()
        self.next_id = 1

    def run(self) -> None:
        self.listen()

    def stop(self) -> None:
        self.on = False
        utils.log('stopping listening...')

    def menu(self):
        print('You can now use netcalc server')
        print(Mode.QUERY_BY_SESSION_ID_CMD + ' id\t: get all calculations of given session')
        print(Mode.QUERY_BY_RESULT_ID_CMD + ' id\t: get calculation by its id')
        print('exit\t\t: turn off and exit netcalc server')
        while True:
            command = input()
            if command == 'exit':
                server.stop()
                break
            else:
                command = command.split()
                if len(command) == 2:
                    if command[0] == Mode.QUERY_BY_SESSION_ID_CMD:
                        self.__query_by_session_id_cmd(int(command[1]))
                    elif command[0] == Mode.QUERY_BY_RESULT_ID_CMD:
                        self.__query_by_result_id_cmd(int(command[1]))
                else:
                    print('invalid command')

    def listen(self) -> None:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.bind((self.host, self.port))
        s.listen(5)
        utils.log('listening on port ' + str(self.port))
        while self.on:
            try:
                connection, address = s.accept()
                utils.log('connected by ' + str(address))
                handler = Thread(
                    name="handler_for_" + str(address),
                    target=self.handle_incoming_connection,
                    args=(connection, address)
                )
                handler.start()
            except socket.timeout:
                pass

        utils.log('listening stopped')

    def handle_incoming_connection(self, connection: socket, address: tuple) -> None:
        data = connection.recv(MAX_DATAGRAM_SIZE)
        answer: Datagram = None
        # noinspection PyBroadException
        try:
            datagram = Datagram.from_bytes(data)

            utils.log('received: ' + str(datagram))
            answer: bytes
            if datagram.mode == Mode.CONNECT:
                answer = self.connect(address)
            elif datagram.session_id in self.sessions and self.sessions[datagram.session_id] == address[0]:
                if datagram.mode == Mode.DISCONNECT:
                    answer = self.disconnect(datagram.session_id, address)
                elif datagram.mode == Mode.OPERATION:
                    answer = self.__operation(datagram.session_id, datagram.operation, datagram.a, datagram.b)
                elif datagram.mode == Mode.QUERY_BY_SESSION_ID:
                    answer = self.__query_by_session_id(datagram.session_id)
                elif datagram.mode == Mode.QUERY_BY_RESULT_ID:
                    answer = self.__query_by_result_id(datagram.session_id, datagram.a)
                elif datagram.mode == Mode.OPERATION:
                    answer = self.__query_by_result_id(datagram.session_id, datagram.a)
            else:
                answer = Datagram(Status.REFUSED, datagram.mode, datagram.session_id).get_bytes()
        except (bitstring.ReadError, ValueError, TypeError):
            answer = self.error(Error.CANNOT_READ_DATAGRAM, Mode.ERROR)
        except:
            answer = self.error(Error.INTERNAL_SERVER_ERROR, Mode.ERROR)
        finally:
            connection.sendall(answer)
            connection.close()

    def connect(self, address: tuple) -> bytes:
        given_id = self.next_id
        self.next_id += 1
        self.sessions[given_id] = address[0]
        answer = Datagram(Status.OK, Mode.CONNECT, given_id)
        utils.log('new session: ' + str(given_id) + ' : ' + str(address[0]))
        return answer.get_bytes()

    def disconnect(self, session_id: int, address: tuple) -> bytes:
        del self.sessions[session_id]
        answer = Datagram(Status.OK, Mode.DISCONNECT, session_id)
        utils.log('removed session: ' + str(session_id) + ' : ' + str(address))
        return answer.get_bytes()

    @staticmethod
    def __operation(session_id: int, operation: int, num_a: float, num_b: float) -> bytes:
        utils.log('received call for ' + Operation.name_from_code(operation) + ' from session: ' + str(session_id))
        answer = Datagram(Status.OK, Mode.OPERATION, session_id, operation, num_a, num_b, result_id=1)  # TODO: [Artur] implement result_id
        # TODO: [Artur] implement operations and results storage
        if operation == Operation.POWER:
            result = num_a + num_b
            answer.result = result
        elif operation == Operation.LOG:
            print('log not yet implemented')
        elif operation == Operation.OP_3:
            print('op3 not yet implemented')
        elif operation == Operation.OP_4:
            print('op4 not yet implemented')

        return answer.get_bytes()

    def __query_by_session_id(self, session_id: int) -> bytes:
        # TODO: [Artur] implement querying by session id
        utils.log('querying by session_id: ' + str(session_id))
        answer = Datagram.from_result_list(
            Status.OK, Mode.QUERY_BY_SESSION_ID, session_id,
            [
                (98765, 0, 2.5, 2, 6.25, 98778987),
                (98766, 0, 3, 2, 9, 98778997),
                (98767, 0, 2.5, 2, 6.25, 98779087),
                (98768, 0, 2.5, 2, 6.25, 98779097),
                (98769, 0, 2.5, 2, 6.25, 98779807),
                (98770, 0, 2.5, 2, 6.25, 98780007),
                (98771, 0, 2.5, 2, 6.25, 98780017)
            ]
        )

        return answer.get_bytes()

    def __query_by_session_id_cmd(self, session_id: int) -> None:
        # TODO: [Artur] implement querying by session id from terminal
        results = [
                (98765, 0, 2.5, 2, 6.25, 98778987),
                (98766, 0, 3, 2, 9, 98778997),
                (98767, 0, 2.5, 2, 6.25, 98779087),
                (98768, 0, 2.5, 2, 6.25, 98779097),
                (98769, 0, 2.5, 2, 6.25, 98779807),
                (98770, 0, 2.5, 2, 6.25, 98780007),
                (98771, 0, 2.5, 2, 6.25, 98780017)
            ]
        for result in results:
            print(Operation.name_from_code(result[1]) + ' ' + str(result[2]) + ' ' + str(result[3]) + ' -> ' + str(result[4]))

    def __query_by_result_id(self, session_id: int, result_id: int) -> bytes:
        # TODO: [Artur] implement querying by result id
        answer = Datagram(
            Status.OK, Mode.QUERY_BY_RESULT_ID, session_id, Operation.POWER, 2, 3, 8, result_id, calendar.timegm(time.gmtime())
        )
        print(answer)
        return answer.get_bytes()

    def __query_by_result_id_cmd(self, result_id: int) -> None:
        # TODO: [Artur] implement querying by result id from terminal
        print(str(result_id) + ': ' + Operation.name_from_code(Operation.POWER) + ' ' + str(2) + ' ' + str(3) + ' -> ' + str(8))

    @staticmethod
    def error(code: int, mode: int = Mode.ERROR, session_id: int = 0, operation: int = 0) -> bytes:
        utils.log(Error.name_from_code(code) + ' on session: ' + str(session_id), True)
        error = Datagram(Status.ERROR, mode, session_id, operation, a=code)
        return error.get_bytes()


if __name__ == '__main__':
    server = Server(LOCAL_HOST, PORT)
    server.start()
    server.menu()
    server.join()
