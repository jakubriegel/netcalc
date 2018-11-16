import calendar
import socket
import sys
import time
from math import factorial, log, sqrt

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
        self.next_id = 1
        self.next_id_lock = Lock()

        self.next_result_id = 1
        self.results_storage = {}

    def run(self) -> None:
        self.listen()

    def stop(self) -> None:
        self.on = False
        utils.log('stopping listening...')
        for session in self.sessions:
            self.sessions[session] = False
            session.join()
        utils.log('all sessions closed')

    def menu(self):
        print('You can now use netcalc server')
        print(Mode.QUERY_BY_SESSION_ID_CMD + ' id\t: get all calculations of given session')
        print(Mode.QUERY_BY_RESULT_ID_CMD + ' id\t: get calculation by its id')
        print('exit\t\t: turn off and exit netcalc server')
        while True:
            command = input()
            if command == 'exit':
                self.stop()
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
                handler = Handler(
                    name="handler_for_" + str(address),
                    server=self,
                    connection=connection,
                    address=address
                )
                self.sessions[handler] = True
                handler.start()
            except socket.timeout:
                pass

        utils.log('listening stopped')

    def handle_incoming_connection(self, connection: socket, address: tuple, handler) -> None:
        session_id = 1
        while self.sessions[handler]:
            try:
                data = connection.recv(MAX_DATAGRAM_SIZE)
                answer: Datagram = None
                # noinspection PyBroadException
                try:
                    datagram = Datagram.from_bytes(data)
                    # utils.log('received: ' + str(datagram))
                    answer: bytes
                    if datagram.mode == Mode.CONNECT:
                        answer, session_id = self.__connect(address)
                    elif datagram.session_id == session_id:
                        if datagram.mode == Mode.IS_ALIVE:
                            answer = self.__is_alive(datagram.session_id, handler)
                        elif datagram.mode == Mode.DISCONNECT:
                            answer = self.__disconnect(datagram.session_id, address)
                            self.sessions[handler] = False
                        elif datagram.mode == Mode.OPERATION:
                            answer = self.__operation(datagram.session_id, datagram.operation, datagram.a, datagram.b)
                        elif datagram.mode == Mode.QUERY_BY_SESSION_ID:
                            answer = self.__query_by_session_id(datagram.session_id)
                        elif datagram.mode == Mode.QUERY_BY_RESULT_ID:
                            answer = self.__query_by_result_id(datagram.session_id, datagram.a)
                    else:
                        answer = self.__error(Error.UNAUTHORISED)
                except (bitstring.ReadError, ValueError, TypeError):
                    answer = self.__error(Error.CANNOT_READ_DATAGRAM, Mode.ERROR)
                except Exception as e:
                    print(e)
                except:
                    answer = self.__error(Error.INTERNAL_SERVER_ERROR, Mode.ERROR)
                finally:
                    connection.sendall(answer)
            except (ConnectionAbortedError, ConnectionResetError):
                utils.log('breaking listening for session: ' + str(session_id))
                self.sessions[handler] = False

        connection.close()
        utils.log('session closed: ' + str(session_id))

    def __connect(self, address: tuple) -> (bytes, int):
        self.next_id_lock.acquire()
        given_id = self.next_id
        self.next_id += 1
        self.next_id_lock.release()
        answer = Datagram(Status.OK, Mode.CONNECT, given_id)
        utils.log('new session: ' + str(given_id) + ' : ' + str(address[0]))
        return answer.get_bytes(), given_id

    @staticmethod
    def __disconnect(session_id: int, address: tuple) -> bytes:
        answer = Datagram(Status.OK, Mode.DISCONNECT, session_id)
        utils.log('removed session: ' + str(session_id) + ' : ' + str(address))
        return answer.get_bytes()

    def __is_alive(self, session_id: int, handler: Thread):
        if self.sessions[handler]:
            answer = Datagram(Status.OK, Mode.IS_ALIVE, session_id)
        else:
            answer = Datagram(Status.REFUSED, Mode.IS_ALIVE, session_id)
        return answer.get_bytes()

    def __operation(self, session_id: int, operation: int, num_a: float, num_b: float) -> bytes:
        utils.log('received call for ' + Operation.name_from_code(operation) + ' from session: ' + str(session_id))
        answer = Datagram(Status.OK, Mode.OPERATION, session_id, operation, num_a, num_b)
        answer.result_id = self.next_result_id
        self.next_result_id += 1
        result = 0

        if operation == Operation.POWER:
            result = num_a**num_b
        elif operation == Operation.LOG:
            result = log(num_b)/log(num_a)
        elif operation == Operation.OP_3:
            result = sqrt(num_a*num_b)
        elif operation == Operation.OP_4:
            result = factorial(num_a)/(factorial(num_a-num_b)*factorial(num_b))

        answer.result = result
        return answer.get_bytes()

    def __query_by_session_id(self, session_id: int) -> bytes:
        # TODO: [Artur] implement querying by session id
        utils.log('querying by session_id: ' + str(session_id))
        answer = Datagram.from_result_list(
            Status.OK, Mode.QUERY_BY_SESSION_ID, session_id, self.results_storage[session_id])

        return answer.get_bytes()

    def __query_by_session_id_cmd(self, session_id: int) -> None:
        # TODO: [Artur] implement querying by session id from terminal
        results = self.results_storage[session_id]
        for result in results:
            print('session_id = ' + str(result[1]) +
                  ' result id = ' + str(result[6]) +
                  ' operation: ' + str(Operation.name_from_code(result[2])) +
                  ' a = ' + str(result[3]) +
                  ' b = ' + str(result[4]) +
                  ' result = ' + str(result[5]))

    def __query_by_result_id(self, session_id: int, result_id: int) -> bytes:
        # TODO: [Artur] implement querying by result id
        answer = Datagram(
            Status.OK, Mode.QUERY_BY_RESULT_ID, self.results_storage[session_id][result_id],
            calendar.timegm(time.gmtime())
        )
        print(answer)
        return answer.get_bytes()

    def __query_by_result_id_cmd(self, result_id: int) -> None:
        # TODO: [Artur] implement querying by result id from terminal
        result = None

        for i in range(0, self.next_id):
            if self.results_storage[i][result_id]:
                result = self.results_storage[i][result_id]

        if result:
            print('session_id = ' + str(result[1]) +
                  ' result id = ' + str(result[6]) +
                  ' operation: ' + str(Operation.name_from_code(result[2])) +
                  ' a = ' + str(result[3]) +
                  ' b = ' + str(result[4]) +
                  ' result = ' + str(result[5]))

        else:
            print(self.__error(Error.NOT_EXISTING_DATA))

    @staticmethod
    def __error(code: int, mode: int = Mode.ERROR, session_id: int = 0, operation: int = 0) -> bytes:
        utils.log(Error.name_from_code(code) + ' on session: ' + str(session_id), True)
        error = Datagram(Status.ERROR, mode, session_id, operation, a=code)
        return error.get_bytes()


class Handler(Thread):

    def __init__(self, name: str, server: Server, address: tuple, connection: socket) -> None:
        super().__init__(name=name)
        self.server = server
        self.address = address
        self.connection = connection

    def run(self) -> None:
        self.server.handle_incoming_connection(self.connection, self.address, self)

    def stop(self):
        self.server.sessions[self] = False
        self.connection.close()


def main():
    args = sys.argv
    host = args[1] if len(args) > 1 else LOCAL_HOST
    port = int(args[2]) if len(args) > 2 else PORT
    server = Server(host, port)
    server.start()
    server.menu()
    server.join()


if __name__ == '__main__':
    main()
