import socket
import sys
from math import factorial, log, sqrt

import bitstring
from threading import Thread, Lock

from common.Datagram import Datagram
from common import utils
from common.values import Status, Mode, Operation, LOCAL_HOST, PORT, Error, DATAGRAM_SIZE
from typing import List


class Server(Thread):
    """ Implementation of server application """

    def __init__(self, host: str, port: int) -> None:
        """
        :param host: IP address to serve application on
        :param port: port number to serve application on
        """
        super().__init__(name='server')

        # initialize members
        self.host = host
        self.port = port
        self.on = True

        # create empty dict for storing open sessions and counter of session ids
        self.sessions = {}
        self.next_id = 1
        self.next_id_lock = Lock()

        # create empty dict for storing open sessions and counter of result ids
        self.results_storage = {}
        self.next_result_id = 1

    def run(self) -> None:
        """ Starts the server """
        self.listen()

    def stop(self) -> None:
        """ Starts the server

        Sets ON flag to FALSE, which stops listening for new connections. Then safely closes all open sessions.
        """
        self.on = False
        utils.log('stopping listening...')
        for session in self.sessions:
            # turn session off
            self.sessions[session] = False
            # wait for client to confirm disconnection
            session.join()

        utils.log('all sessions closed')

    def menu(self) -> None:
        """ Starts application CLI """

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
                    try:
                        int(command[1])
                    except ValueError:
                        print('invalid argument')
                    else:
                        if command[0] == Mode.QUERY_BY_SESSION_ID_CMD:
                            self.__query_by_session_id_cmd(int(command[1]))
                        elif command[0] == Mode.QUERY_BY_RESULT_ID_CMD:
                            self.__query_by_result_id_cmd(int(command[1]))
                else:
                    print('invalid command')

    def listen(self) -> None:
        """ Listens for incoming connections """

        # create socket for handling connections
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # set socket timeout [makes possible to safely break listening]
        s.settimeout(1)
        # bind socket with server address
        s.bind((self.host, self.port))
        # set maximal waiting queue
        s.listen(5)
        utils.log('listening on port ' + str(self.port))

        # listen util user turns server off
        while self.on:
            try:
                # accept connection
                connection, address = s.accept()
                utils.log('connected by ' + str(address))
                # create handler for new connection [see Handler definition below]
                handler = Handler(
                    name="handler_for_" + str(address),
                    server=self,
                    connection=connection,
                    address=address
                )
                # add new connection to sessions storage
                self.sessions[handler] = True
                # handle new session
                handler.start()
            except socket.timeout:
                pass

        utils.log('listening stopped')

    def handle_incoming_connection(self, connection: socket, address: tuple, handler: Thread) -> None:
        """
        Handles session

        :param connection: socket with established cconnection
        :param address: address of client
        :param handler: handler object
        """

        # create variable for storing id
        session_id = 0

        # handle requests
        while self.sessions[handler]:
            try:
                # receive data
                data = connection.recv(DATAGRAM_SIZE)
                answer: Datagram = None
                # noinspection PyBroadException
                try:
                    # decode data
                    datagram = Datagram.from_bytes(data)
                    # utils.log('received: ' + str(datagram))
                    answer: bytes
                    if datagram.mode == Mode.CONNECT:
                        answer, session_id = self.__connect(address)
                        self.results_storage[session_id] = {}
                    elif datagram.session_id == session_id:
                        if datagram.mode == Mode.IS_ALIVE:
                            answer = self.__is_alive(datagram.session_id, handler)
                        elif datagram.mode == Mode.DISCONNECT:
                            answer = self.__disconnect(datagram.session_id, address)
                            self.sessions[handler] = False
                        elif datagram.mode == Mode.OPERATION:
                            answer = self.__operation(datagram.session_id, datagram.operation, datagram.a, datagram.b)
                        elif datagram.mode == Mode.QUERY_BY_SESSION_ID:
                            answer = self.__query_by_session_id(session_id, datagram.session_id, connection)
                        elif datagram.mode == Mode.QUERY_BY_RESULT_ID:
                            answer = self.__query_by_result_id(session_id, datagram.session_id, datagram.result_id)
                    else:
                        # if authorization didn't succeed
                        answer = self.__error(Error.UNAUTHORISED)
                except (bitstring.ReadError, ValueError, TypeError) as e:
                    # if data was unreadable
                    utils.log("datagram exception: " + str(e), True)
                    answer = self.__error(Error.CANNOT_READ_DATAGRAM, Mode.ERROR, session_id)
                except Exception as e:
                    # if any other exception occurred
                    utils.log("exception: " + str(e), True)
                    answer = self.__error(Error.INTERNAL_SERVER_ERROR, Mode.ERROR, session_id)
                finally:
                    # send answer to the client
                    connection.sendall(answer)
            except (ConnectionAbortedError, ConnectionResetError):
                # if session was closed unsafely
                utils.log('breaking listening for session: ' + str(session_id))
                self.sessions[handler] = False

        # after closing session safely close connection
        connection.close()
        utils.log('session closed: ' + str(session_id))

    def __connect(self, address: tuple) -> (bytes, int):
        """
        Establish new session

        :param address: client address
        :return: (answer to the client , given session_id)
        """

        # get id
        self.next_id_lock.acquire()
        given_id = self.next_id
        self.next_id += 1
        self.next_id_lock.release()
        # prepare answer
        answer = Datagram(Status.OK, Mode.CONNECT, given_id)
        utils.log('new session: ' + str(given_id) + ' : ' + str(address[0]))
        return answer.get_bytes(), given_id

    @staticmethod
    def __disconnect(session_id: int, address: tuple) -> bytes:
        """
        Closes session

        :param session_id: id of session to close
        :param address: address of the client
        :return: answer for the client
        """
        answer = Datagram(Status.OK, Mode.DISCONNECT, session_id)
        utils.log('removed session: ' + str(session_id) + ' : ' + str(address))
        return answer.get_bytes()

    def __is_alive(self, session_id: int, handler: Thread) -> bytes:
        """
        Handles is alive request

        If session was closed on server, sends information about it to the client

        :param session_id: id of session to close
        :param handler: session handler
        :return: answer for the client
        """

        if self.sessions[handler]:
            answer = Datagram(Status.OK, Mode.IS_ALIVE, session_id)
        else:
            answer = Datagram(Status.REFUSED, Mode.IS_ALIVE, session_id)
        return answer.get_bytes()

    def __operation(self, session_id: int, operation: int, num_a: float, num_b: float) -> bytes:
        """
        Makes requested calculations

        :param session_id:
        :param operation: id of rewuested operation
        :param num_a: number a
        :param num_b: number b
        :return: answer for the client
        """

        utils.log('received call for ' + Operation.name_from_code(operation) + ' from session: ' + str(session_id))

        answer = Datagram(Status.OK, Mode.OPERATION, session_id, operation, num_a, num_b)
        answer.result_id = self.next_result_id
        result: float

        try:
            if operation == Operation.POWER:
                result = num_a**num_b
            elif operation == Operation.LOG:
                result = log(num_b)/log(num_a)
            elif operation == Operation.GEO_MEAN:
                if num_a*num_b < 0:
                    return self.__error(5, Mode.OPERATION, session_id, operation)
                result = sqrt(num_a*num_b)
            elif operation == Operation.BIN_COE:
                if num_b > num_a or num_a < 0 or num_b < 0:
                    return self.__error(5, Mode.OPERATION, session_id, operation)
                result = factorial(num_a)/(factorial(num_a-num_b)*factorial(num_b))
        except OverflowError:
            return self.__error(Error.MAX_VALUE_EXCEEDED, Mode.OPERATION, session_id, operation)

        if result == float('inf'):
            return self.__error(Error.MAX_VALUE_EXCEEDED, Mode.OPERATION, session_id, operation)

        self.results_storage[session_id][self.next_result_id] = \
            (operation, num_a, num_b, session_id, result, self.next_result_id)

        self.next_result_id += 1

        answer.result = result
        return answer.get_bytes()

    def __query_by_session_id(self, session_id: int, given_session_id: int, connection: socket) -> bytes:
        """
        Gets all results of session

        :param session_id: id of session to look for
        :param given_session_id: id of session requesting query
        :param connection: connection socket
        :return: answer for the client
        """
        utils.log('querying by session_id: ' + str(session_id) + ' for ' + str(given_session_id))

        if session_id != given_session_id:
            return self.__error(Error.UNAUTHORISED, Mode.QUERY_BY_SESSION_ID, session_id)

        if session_id not in self.results_storage:
            return self.__error(Error.NOT_EXISTING_DATA, Mode.QUERY_BY_SESSION_ID)

        if not self.results_storage[session_id]:
            return self.__error(Error.NOT_EXISTING_DATA, Mode.QUERY_BY_SESSION_ID)

        results = self.results_storage[session_id]
        answer: List[Datagram] = list()
        for result_id, result in results.items():
            answer.append(Datagram(
                Status.OK, Mode.QUERY_BY_SESSION_ID, session_id,
                operation=result[0],
                a=result[1],
                b=result[2],
                result=result[4],
                result_id=result_id,
                last=False
            ))

        # send all except last results to the client
        for i in range(0, len(answer) - 1):
            connection.sendall(answer[i].get_bytes())

        # return last result to send
        answer[len(answer) - 1].last = True
        return answer[len(answer) - 1].get_bytes()

    def __query_by_session_id_cmd(self, session_id: int) -> None:
        if session_id in self.results_storage:
            results = self.results_storage[session_id]
            for result_id, result in results.items():
                print('session_id = ' + str(session_id) + "\t" +
                      ' result id = ' + str(result[5]) + "\t" +
                      ' operation: ' + str(Operation.name_from_code(result[0])) + "\t" +
                      ' a = ' + str(result[1]) + "\t" +
                      ' b = ' + str(result[2]) + "\t" +
                      ' result = ' + str(result[4]))

        else:
            self.__error(Error.NOT_EXISTING_DATA, Mode.QUERY_BY_SESSION_ID)

    def __query_by_result_id(self, session_id: int, given_session_id: int, result_id: int) -> bytes:
        """
        Gets one result

        :param session_id: id of session to look for
        :param given_session_id: id of session requesting query
        :param result_id: id of result to look for
        :return: answer for the client
        """
        utils.log('querying by result id: ' + str(result_id) + 'for ' + str(given_session_id))

        if session_id != given_session_id:
            return self.__error(Error.UNAUTHORISED, Mode.QUERY_BY_SESSION_ID, session_id)

        if session_id not in self.results_storage:
            return self.__error(Error.NOT_EXISTING_DATA, Mode.QUERY_BY_SESSION_ID_CMD)

        session_results = self.results_storage[session_id]

        if result_id not in session_results:
            return self.__error(Error.UNAUTHORISED, Mode.QUERY_BY_RESULT_ID, session_id)

        answer = Datagram(
            Status.OK, Mode.QUERY_BY_RESULT_ID, session_id,
            operation=self.results_storage[session_id][result_id][0],
            a=self.results_storage[session_id][result_id][1],
            b=self.results_storage[session_id][result_id][2],
            result=self.results_storage[session_id][result_id][4],
            result_id=result_id,
        )

        return answer.get_bytes()

    def __query_by_result_id_cmd(self, result_id: int) -> None:
        result = None
        results = self.results_storage
        session_id = None

        for key, res in results.items():
            if result_id in res:
                result = res[result_id]
                session_id = key

        if result:
            print('session_id = ' + str(session_id) + "\t" +
                  ' result id = ' + str(result[5]) + "\t" +
                  ' operation: ' + str(Operation.name_from_code(result[0])) + "\t" +
                  ' a = ' + str(result[1]) + "\t" +
                  ' b = ' + str(result[2]) + "\t" +
                  ' result = ' + str(result[4]))

        else:
            self.__error(Error.NOT_EXISTING_DATA, Mode.QUERY_BY_RESULT_ID)

    @staticmethod
    def __error(code: int, mode: int = Mode.ERROR, session_id: int = 0, operation: int = 0) -> bytes:
        """
        Returns error answer

        :param code: error code
        :param mode: mode in which error occurred
        :param session_id: session id in which error occurred
        :param operation: operation in which error occurred
        :return: error answer for the client
        """
        utils.log(
            Error.name_from_code(code) + ' on session: ' + str(session_id) + ' mode: ' + Mode.name_from_code(mode),
            True
        )
        error = Datagram(Status.ERROR, mode, session_id, operation, a=code)
        return error.get_bytes()


class Handler(Thread):
    """ Handles session

    It's just a wrapper class, that runs asynchronously handle_incoming_connection method from Server class
    """

    def __init__(self, name: str, server: Server, address: tuple, connection: socket) -> None:
        super().__init__(name=name)
        self.server = server
        self.address = address
        self.connection = connection

    def run(self) -> None:
        self.server.handle_incoming_connection(self.connection, self.address, self)

    def stop(self) -> None:
        """ Safely finalizes session """

        self.server.sessions[self] = False
        self.connection.close()


def main():
    """ Starts the application """
    args = sys.argv
    host = args[1] if len(args) > 1 else LOCAL_HOST
    port = int(args[2]) if len(args) > 2 else PORT
    server = Server(host, port)
    server.start()
    server.menu()
    server.join()


if __name__ == '__main__':
    main()
