import pytest
import allure
import re
from pprint import pprint
import paramiko

from allure.constants import AttachmentType
from datetime import datetime

from twisted.internet.protocol import Protocol
from twisted.internet.protocol import Factory
from twisted.internet.protocol import ServerFactory
from twisted.internet.defer import Deferred
from twisted.internet.defer import maybeDeferred
from twisted.internet.defer import succeed


def date_time():
    nt = datetime.now()
    return "{}-{:02}-{:02} {:02}:{:02}:{:02}.{:3}".format(nt.year,\
                                                          nt.month,\
                                                          nt.day,\
                                                          nt.hour,\
                                                          nt.minute,\
                                                          nt.second,\
                                                          str(nt.microsecond)[:3])


class ServerProtocol(Protocol):

    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        print("\n{} Conn Made...{}".format(date_time(), self.transport.getPeer()))
        print("\nStatus_connect before: {}".format(self.factory.status_connect))
        self.factory.count_connect.append(self.transport.getPeer())
        if not self.factory.status_connect:
            self.factory.status_connect = "{}:{}:{}"\
                .format(date_time(),\
                        self.transport.getPeer().host,\
                        self.transport.getPeer().port)
            print("\nStatus_connect after: {}".format(self.factory.status_connect))
        else:
            if self.factory.status_connect:
                print("\n{} Conn Close...{}".format(date_time(), self.transport.getPeer()))
                self.transport.loseConnection()

    def connectionLost(self, reason):
        print("\nConnection lost {}\n{}".format(reason, self.transport.getPeer()))
        if re.search("Connection to the other side was lost", str(reason)):
            print("\nConnection to the other side was lost {}\n{}".format(reason, self.transport.getPeer()))
            self.factory.status_connect = False


@allure.step("class ServerEHAFactory(Factory)")
class ServerEHAFactory(Factory):
    protocol = ServerProtocol

    def __init__(self, deferred, timeout_connect):
        with pytest.allure.step("Init factory"):
            self.deferred = deferred
            self.timeout_connect = timeout_connect
            self.status_connect = False
            self.connection_lost = False
            self.connection_failed = False
            self.count_connect = []
            from twisted.internet import reactor
            reactor.callLater(self.timeout_connect, self.check_connect)
            allure.attach("Start reactor.callater",\
                          "{} Start check_connect with timeout {}sec: {}"\
                          .format(date_time(), self.timeout_connect, self.check_connect))
            # print("factory defer: {}".format(self.deferred))

    def buildProtocol(self, addr):
        self.protocol = ServerProtocol(self)
        return self.protocol

    def ConnectionLost(self):
        with pytest.allure.step("Detect clientConnLost"):
            # self.connection_lost = connector
            allure.attach("Lost connect from",\
                          "clientConnectionLost: {}")

    @allure.step("Factory check_connect")
    def check_connect(self):
        allure.attach("In check_connect",\
                      "Status connect from connector EHA:\n{}"\
                      .format(self.status_connect))
        allure.attach("In count_connected",\
                      "Count connected from server:\n{}"\
                      .format(self.count_connect))
        print("\nIn Count connected from server:{}".format(self.count_connect))

        if self.deferred is not None:
            d, self.deferred = self.deferred, None
        # Connected_OK, Other_Connect, Reconnect
        if self.status_connect:
            if len(self.count_connect) > 1:
                d.errback(self.count_connect)
            # allure.attach("Close connect", "{} Status connect  from connector EHA: {}"\
            #               .format(date_time(), self.status_connect))
            else:
                d.callback(self.status_connect)
        else:  # notConnect
            #if self.connection_lost:
            #    allure.attach("Detected loss of connection between {} seconds"\
            #                  .format(self.timeout_connect),\
            #                  "Status connect from connector EHA:{}.\n\
            #                  Start errback".format(self.status_connect))
            #    d.errback(self.connection_lost)
            #else:
            d.errback(self.count_connect)
            allure.attach("Out check_connect delay after {} seconds"\
                          .format(self.timeout_connect),\
                          "Status connect from connector EHA: {}.\n\
                          Start errback".format(self.status_connect))


# FIXTURES


# tearUp/tearDown
# @pytest.yield_fixture()
# def test_server():
#     endpoint = None
# 
#     @allure.step("Create_test_server() from tearUp/tearDown")
#     def server(host, port, timeout_connect):
#         allure.attach("Create_test_server", "Create_test_server {}:{}:{}sec".format(host, port, timeout_connect))
#         d = Deferred()
#         allure.attach("Defer from factory", "Create deferred for Factory: {} ".format(d))
#         factory = ServerEHAFactory(d, timeout_connect)
#         nonlocal endpoint
#         assert endpoint is None
#         from twisted.internet import reactor
#         endpoint = reactor.listenTCP(port, factory, interface=host)
#         return d
#     yield server
#     with allure.step("Stop test server"):
#         if endpoint is not None:
#             allure.attach("Stop test server", "Stop test server:{}".format(endpoint))
#             endpoint.stopListening()


@pytest.fixture()
def data_maket_mea1209_1211():
    data = {
        "server_port1": 10000,
        "server_port2": 10001,
        "server_host": "192.168.10.168",
        "server_localhost": "127.0.0.1",
        "client_eha_side_1": "192.168.101.3",
        "client_eha_side_2": "192.168.101.4",
        "client_eha_float": "192.168.101.5",
        "double": True,
        "active_side": None,
        "remore_config_eha1": "Empty",
        "remore_config_eha2": "Empty",
        "timeout_connect": 3,
        "timeout_disconnect": 60,
        "user": 'root',
        "secret": 'iskratel',
        }

    data_new = {
        "server_port1": 10000,
        "server_port2": 10001,
        "server_host": "192.168.10.168",
        "server_localhost": "127.0.0.1",
        "double": True,
        "client_eha_side_1": {"ip": "192.168.101.3", "version": "Empty", "Other": ""},
        "client_eha_side_2": {"ip": "192.168.101.4", "version": "Empty"},
        "client_eha_float": {"ip": "192.168.101.5"},
        "active_side": "Empty",
        "timeout_connect": 3,
        "timeout_disconnect": 60,
        "user": 'root',
        "secret": 'iskratel',
        }

    def print_data(data):
        return ''.join(["\n{}: {}".format(item[0], item[1]) for item in data_new.items()])
        #return ''.join(["\n{}: {}".format(item[0], item[1]) for item in data.items()])

    stend_data = print_data(data_new)
    print(stend_data)
    with pytest.allure.step("Stend configuration data"):
        allure.attach("Stend data", print_data(data))

    return data_new


@pytest.fixture()
def from_port_1(test_server, data_maket_mea1209_1211):
    server = test_server(data_maket_mea1209_1211["server_host"],\
                         data_maket_mea1209_1211["server_port1"],\
                         data_maket_mea1209_1211["timeout_connect"])
    return {"defer": server, "data": data_maket_mea1209_1211}


@pytest.fixture()
def from_port_2(test_server, data_maket_mea1209_1211):
    server = test_server(data_maket_mea1209_1211["server_host"],\
                         data_maket_mea1209_1211["server_port2"],\
                         data_maket_mea1209_1211["timeout_connect"])
    return {"defer": server, "data": data_maket_mea1209_1211}


# FUXTURE 2


# class service_1(object):
# 
#     def __init__(self, data, server_port):
#         self.data = data
#         self.server_port = server_port
# 
#     def check_timeout_connected(self, status):
#         print("servicestatus1: {}".format((status)))
#         allure.attach("Check connected client from test server",\
#                       "Callback is return result connect for server {}:{} from: {}"\
#                       .format(self.data["server_host"], self.server_port, status))
# 
#         if self.data["double"]:
#             pass
#             # assert re.search(self.data["client_eha_side_1"], status) or re.search(self.data["client_eha_side_2"], status),\
#             #        "Detection connection to local port {} from an unexpected ip address: {}.\n\
#             #        The system waits for connection from the addreses: {} or {}\n"\
#             #        .format(self.server_port, status, self.data["client_eha_side_1"], self.data["client_eha_side_2"])
#             
#             print("End re double")
# 
#         else:
#             assert re.search(self.data["client_eha_float"], status),\
#                    "Detection connection to local port {} from an unexpected ip address: {}.\n\
#                    The system waits for connection from the addreses: {} or {}\n"\
#                    .format(self.server_port, status, self.data["client_eha_float"])
#         print("End re double2")
#         # return "return service"


class ServerServiceProtocol_2(Protocol):

    def prnt(self, status):
        print("prnt: {}".format(status))

    def connectionMade(self):
        print("\n{} Conn Made...{}".format(date_time(), self.transport.getPeer()))
        print("\nStatus_connect before: {}".format(self.factory.status_connect))
        self.factory.status_connect = "{}:{}:{}"\
            .format(date_time(),\
                    self.transport.getPeer().host,\
                    self.transport.getPeer().port)

        succeed(self.factory.service.check_timeout_connected(self.factory.status_connect))
        print("EEE: {}".format(self.factory.status_test))


class ServerServiceFactory_2(ServerFactory):
    protocol = ServerServiceProtocol_2

    def __init__(self, deferred, service):
        self.deferred = deferred
        self.service = service
        self.status_connect = False
        self.timeout_connect = self.service.data["timeout_connect"]
        print("\nInitial factory service: {}, deferred: {}, time_out: {}"\
              .format(self.service, self.deferred, self.timeout_connect))

    def return_result(self, status):
        print("return_result_ok: {}".format("status"))
        if self.deferred is not None:
            d, self.deferred = self.deferred, None
        # if status:
        d.callback("status")

    def print_result(self):
        print("print_result:")
        return


# ######################################################################

class ServerServiceProtocol_3(Protocol):

    def prnt(self, status):
        print("prnt: {}".format(status))

    @allure.step("connectionMade")
    def connectionMade(self):
        print("\n{} Conn Made...{}".format(date_time(), self.transport.getPeer()))
        print("\nStatus_connect before: {}".format(self.factory.status_connect))
        self.factory.status_connect = "{}:{}:{}"\
            .format(date_time(),\
                    self.transport.getPeer().host,\
                    self.transport.getPeer().port)
        allure.attach("In Connect",\
                      "source address: {}".format(self.factory.status_connect))
        print("\nStatus_connect after: {}".format(self.factory.status_connect))
        with pytest.allure.step("Start chk()"):
            self.factory.chk()
            print("start chk()")


class ServerServiceFactory_3(Factory):
    protocol = ServerServiceProtocol_3

    def __init__(self, server, deferred, data):
        self.server = server
        self.deferred = deferred
        # self.service = service
        self.status_connect = False
        self.timeout_connect = data["timeout_connect"]
        print("\nInitial factory deferred: {}, time_out: {}"\
              .format(self.deferred, self.timeout_connect))
        from twisted.internet import reactor
        reactor.callLater(self.timeout_connect, self.chk)

    def chk(self):
        print("In chk()")
        succeed(self.server.check_timeout_connected(self.status_connect))

    def return_result(self, status):
        print("return_result_ok: {}".format(status))
        if self.deferred is not None:
            d, self.deferred = self.deferred, None
        # if status:
        d.callback(status)

    def print_result(self):
        print("print_result!!!:")
        return


# ############################### TEST 2 ######################################

class ServerServiceProtocol_2_1(Protocol):

    @allure.step("connectionMade")
    def connectionMade(self):
        print("\n{} Conn Made...{}".format(date_time(), self.transport.getPeer()))
        print("\nStatus_connect before: {}".format(self.factory.status_connect))
        self.factory.count_connect.append(self.transport.getPeer())
        if not self.factory.status_connect:
            self.factory.status_connect = "{}:{}:{}"\
                .format(date_time(),\
                        self.transport.getPeer().host,\
                        self.transport.getPeer().port)
            allure.attach("In Connect",\
                          "source address: {}".format(self.factory.status_connect))
            print("\nStatus_connect after: {}".format(self.factory.status_connect))
            succeed(self.factory.server.checking_connecting_from_another_address(self.factory.status_connect))
        else:
            if self.factory.status_connect:
                print("\n{} Conn Close...{}".format(date_time(), self.transport.getPeer()))
                self.transport.loseConnection()

    def connectionLost(self, reason):
        print("\nConnection lost {}\n{}".format(reason, self.transport.getPeer()))
        if re.search("Connection was closed cleanly", str(reason)):
            succeed(self.factory.server.check_discon_after_connected(reason))


class ServerServiceFactory_2_1(Factory):
    protocol = ServerServiceProtocol_2_1

    def __init__(self, server, deferred, data):
        self.server = server
        self.deferred = deferred
        # self.service = service
        self.status_connect = False
        self.timeout_connect = data["timeout_connect"]
        self.timeout_disconnect = data["timeout_disconnect"]
        self.count_connect = []
        print("\nInitial factory deferred: {}, time_out: {}"\
              .format(self.deferred, self.timeout_connect))
        from twisted.internet import reactor
        reactor.callLater(self.timeout_connect, self.chk)

    def chk(self):
        print("{} In chk()".format(date_time()))
        succeed(self.server.check_timeout_connected(self.status_connect))

    def chk_timeout_disconnect(self):
        print("{} In chk_timeout_disconnect()".format(date_time()))
        succeed(self.server.check_discon_after_connected(self.status_connect))

    def return_result(self, status):
        print("return_result_ok: {}".format(status))
        if self.deferred is not None:
            d, self.deferred = self.deferred, None
        # if status:
        d.callback(status)

    def get_eha_data(self):
        with pytest.allure.step("Get config data from EHA"):
            allure.attach("Get config data from EHA", self.server.get_eha_data())
        # print(self.server.get_eha_data())


# ############################### TEST 3 #############################################

class ServerServiceProtocol_3_1(Protocol):

    def prnt(self, status):
        print("prnt: {}".format(status))

    @allure.step("connectionMade")
    def connectionMade(self):
        print("\n{} Conn Made...{}".format(date_time(), self.transport.getPeer()))
        print("\nStatus_connect before: {}".format(self.factory.status_connect))
        self.factory.count_connect.append(self.transport.getPeer())
        if not self.factory.status_connect:
            self.factory.status_connect = "{}:{}:{}"\
                .format(date_time(),\
                        self.transport.getPeer().host,\
                        self.transport.getPeer().port)
            allure.attach("In Connect",\
                          "source address: {}".format(self.factory.status_connect))
            print("\nStatus_connect after: {}".format(self.factory.status_connect))
        else:
            if self.factory.status_connect:
                print("\n{} Conn Close...{}".format(date_time(), self.transport.getPeer()))
                self.transport.loseConnection()

    def connectionLost(self, reason):
        print("\nConnection lost {}\n{}".format(reason, self.transport.getPeer()))
        if re.search("Connection was closed cleanly", str(reason)):
            succeed(self.factory.server.check_discon_after_connected(reason))


class ServerServiceFactory_3_1(Factory):
    protocol = ServerServiceProtocol_3_1

    def __init__(self, server, deferred, data):
        self.server = server
        self.deferred = deferred
        # self.service = service
        self.status_connect = False
        self.timeout_disconnect = data["timeout_disconnect"]
        self.count_connect = []
        print("\nInitial factory deferred: {}, time_out: {}"\
              .format(self.deferred, self.timeout_disconnect))
        from twisted.internet import reactor
        reactor.callLater(self.timeout_disconnect, self.chk_timeout_disconnect)
        # reactor.callLater(0, self.get_eha_data)

    def chk(self):
        print("{} In chk()".format(date_time()))
        succeed(self.server.check_timeout_connected(self.status_connect))

    def chk_timeout_disconnect(self):
        print("{} In chk_timeout_disconnect()".format(date_time()))
        succeed(self.server.check_discon_after_connected(self.status_connect))

    def return_result(self, status):
        print("return_result_ok: {}".format(status))
        if self.deferred is not None:
            d, self.deferred = self.deferred, None
        # if status:
        d.callback(status)

    def get_eha_data(self):
        with pytest.allure.step("Get config data from EHA"):
            allure.attach("Get config data from EHA", self.server.get_eha_data())
        # print(self.server.get_eha_data())


# tearUp/tearDown
@pytest.yield_fixture()
def test_server_3_1():
    endpoint = None
    ss = None

    @allure.step("Create test_server3() from tearUp/tearDown")
    # def server(host, port, timeout_connect, data):
    def server(data, port, test=None):
        d = Deferred()
        host = data["server_host"]
        timeout_connect = data["timeout_connect"]
        # allure.attach("Defer from factory", "Create deferred for Factory: {} ".format(d))
        # service = service_1(data, port)
        allure.attach("Create_test_server", "Create_test_server: {}:{}".format(host, port))
        nonlocal endpoint
        assert endpoint is None
        nonlocal ss
        assert ss is None
        if test is None:
            ss = Server_Test3(host, port, timeout_connect, data, d)
        elif re.search("test_2", test):
            ss = Server_Test3.from_test_2(host, port, timeout_connect, data, d)
        elif re.search("test_3", test):
            ss = Server_Test3.from_test_3(host, port, timeout_connect, data, d)
        ss.chk_eha_config()

        from twisted.internet import reactor
        endpoint = reactor.listenTCP(port, ss.factory, interface=host)
        return d
    yield server
    with allure.step("Stop test server"):
        if endpoint is not None:
            allure.attach("Stop test server", "Stop test server:{}".format(endpoint))
            endpoint.stopListening()


# ############################################################################

# tearUp/tearDown
# @pytest.yield_fixture()
# def test_server_2():
#     endpoint = None
# 
#     @allure.step("Create test_server2() from tearUp/tearDown")
#     def server(host, port, timeout_connect, data):
#         allure.attach("Create_test_server", "Create_test_server {}:{}:{}sec".format(host, port, timeout_connect))
#         d = Deferred()
#         allure.attach("Defer from factory", "Create deferred for Factory: {} ".format(d))
#         service1 = service_1(data, port)
#         factory = ServerServiceFactory_2(d, service1)
#         nonlocal endpoint
#         assert endpoint is None
#         from twisted.internet import reactor
#         endpoint = reactor.listenTCP(port, factory, interface=host)
#         return d
#     yield server
#     with allure.step("Stop test server"):
#         if endpoint is not None:
#             allure.attach("Stop test server", "Stop test server:{}".format(endpoint))
#             endpoint.stopListening()


@pytest.fixture()
def maket_test1_port1(test_server_2, data_maket_mea1209_1211):
    server = test_server_2(data_maket_mea1209_1211["server_host"],\
                           data_maket_mea1209_1211["server_port1"],\
                           data_maket_mea1209_1211["timeout_connect"],\
                           data_maket_mea1209_1211)
    return server


# tearUp/tearDown
@pytest.yield_fixture()
def test_server_3():
    endpoint = None

    @allure.step("Create test_server3() from tearUp/tearDown")
    # def server(host, port, timeout_connect, data):
    def server(data, port):
        d = Deferred()
        host = data["server_host"]
        timeout_connect = data["timeout_connect"]
        # allure.attach("Defer from factory", "Create deferred for Factory: {} ".format(d))
        # service = service_1(data, port)
        allure.attach("Create_test_server", "Create_test_server {}:{}:{}sec".format(host, port, timeout_connect))
        nonlocal endpoint
        assert endpoint is None
        ss = Server_Test3(host, port, timeout_connect, data, d)
        from twisted.internet import reactor
        endpoint = reactor.listenTCP(port, ss.factory, interface=host)
        return d
    yield server
    with allure.step("Stop test server"):
        if endpoint is not None:
            allure.attach("Stop test server", "Stop test server:{}".format(endpoint))
            endpoint.stopListening()


class Server_Test3(object):

    def __init__(self, host, port, timeout_connect, data, d, test=None):
        self.d = d
        self.host = host
        self.port = port
        self.timeout_connect = timeout_connect
        self.timeout_disconnect = data["timeout_disconnect"]
        self.data = data
        if test == "test_2":
            self.factory = ServerServiceFactory_2_1(self, self.d, self.data)
        elif test == "test_3":
            self.factory = ServerServiceFactory_3_1(self, self.d, self.data)
        else:
            self.factory = ServerServiceFactory_3(self, self.d, self.data)

    @classmethod
    def from_test_3(cls, host, port, timeout_connect, data, d):
        return cls(host, port, timeout_connect, data, d, "test_3")

    @classmethod
    def from_test_2(cls, host, port, timeout_connect, data, d):
        return cls(host, port, timeout_connect, data, d, "test_2")

    @allure.step("Call check_timeout_connected()")
    def check_timeout_connected(self, status):
        print("check_timeout_connected: {}".format((status)))
        allure.attach("Check connected client from test server",\
                      "Callback is return result connect for server {}:{} from: {}"\
                      .format(self.data["server_host"], self.port, status))

        if not status:
            self.factory.return_result((status, "Delay {} seconds connection to local port {} from EHA"\
                                       .format(self.timeout_connect, self.port)))
        else:
            return self.factory.return_result((status, "Connect OK"))

    @allure.step("Call check_discon_after_connected()")
    def check_discon_after_connected(self, status):
        print("{} Check_timeout_disconnect: {}".format(date_time(), (status)))
        allure.attach("Check check_timeout_disconnect to server",\
                      "Callback is return result timeout disconnect for server {}:{} from: {}"\
                      .format(date_time(), self.data["server_host"], self.port, status))

        if not status:
            self.factory.return_result((status, "Delay {} seconds connection to local port {} from EHA"\
                                       .format(self.timeout_disconnect, self.port)))

        elif re.search("Connection was closed cleanly", str(status)):
            print("\nConnection was closed cleanly {}".format(status))
            return self.factory.return_result((False, "\n{} Connection was closed cleanly {}".format(date_time(), status)))
        else:
            return self.factory.return_result((True, status))

    @allure.step("Call Checking connecting from another address()")
    def checking_connecting_from_another_address(self, status):
    
        print("{} Checking connecting from another address: {}".format(date_time(), (status)))
        allure.attach("Checking connecting from another address to server",\
                      "Callback is return result connect for server {}:{} from: {}"\
                      .format(date_time(), self.data["server_host"], self.port, status))

        
        # act_side = self.chk_active_side_eha()
        print("act side: {}".format(self.data["active_side"]))
                  
        if not status:
            self.factory.return_result((status, "Delay {} seconds connection to local port {} from EHA"\
                                       .format(self.timeout_disconnect, self.port)))

        elif re.search(self.data["active_side"], str(status)):
            print("\nChecking active side succes {}".format(status))
            return self.factory.return_result((True, "Checking connect EHA client from active side succes {}".format(status)))
        else:
            return self.factory.return_result((False, "Connecting from another address to server: {}".format(status)))



    def chk_active_side_eha(self):

        def chk_side(eha, user, passwd, data):
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ip = data[eha]["ip"]
                # pprint("eha: {}".format(eha))
                # pprint("data: {}".format(data))
                client.connect(ip, username=user, password=passwd)
                stdin, stdout, stderr = client.exec_command('ls -l /opt/jboss-as/standalone/deployments/eha*')
                version = stdout.read() + stderr.read()
                version_eha = version.decode('utf-8').splitlines()
                data[eha]["version"] = ''.join(["{}\n".format(ver) for ver in version_eha])
                # pprint("version: {}".format(data[eha]["version"]))
                stdin, stdout, stderr = client.exec_command('cat /proc/drbd')
                status = stdout.read() + stderr.read()
                status_eha = status.decode('utf-8').splitlines()
                for active in status_eha:
                    if re.search("Secondary/Primary", active):
                        # print("active: {}".format(active))
                        # print("Other: {}".format(data[eha]["Other"]))
                        data[eha]["Other"] = "SecondaryPrimary"
                        return False
                        break
                    if re.search("Primary/Secondary", active):
                        data["active_side"] = data[eha]
                        data[eha]["Other"] = "Primary/Secondary"
                        print("Checking EHA is double side!!!")
                        return True
                        break
                    if re.search("No such file or directory", active):
                        data["active_side"] = data[eha]
                        data[eha]["Other"] = "No such file or directory"
                        print("checking EHA is standalone side!!!")
                        return False

                client.close()
            except paramiko.ssh_exception.AuthenticationException:
                return("Authentication failed.")
            except TimeoutError:
                return("TimeoutError")

        #if self.data["double"]:
        chk_side("client_eha_side_1", self.data["user"], self.data["secret"], self.data)
                # self.data["active_side"] = self.data["client_eha_side_1"]
        chk_side("client_eha_side_2", self.data["user"], self.data["secret"],self.data)
                    # self.data["active_side"] = self.data["client_eha_side_2"]
        tt = ''.join(["\n{}: {}".format(item[0], item[1]) for item in self.data.items()])
        print("tt: {}".format(tt))
        print("Active side: {}".format(self.data["active_side"]))
        return  ''.join(["\n{}: {}".format(item[0], item[1]) for item in self.data.items()])


            




    def chk_eha_config(self):
        with pytest.allure.step("Get data from EHA"):
            # allure.attach("Get version EHA", self.get_eha_version())
            allure.attach("Get version EHA", self.chk_active_side_eha())
            
            # allure.attach("Get ha status EHA", self.data["active_side"])
        # print(self.get_eha_version())
        # print("act_side: {}".format(self.data["active_side"]))

    def get_eha_version(self):
        return_data = []
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self.data["client_eha_side_1"],\
                           username=self.data["user"],\
                           password=self.data["secret"],\
                           timeout=1.5)
            stdin, stdout, stderr = client.exec_command('uptime')
            data = stdout.read() + stderr.read()
            uptime = data.decode('utf-8').splitlines()
            return_data.append(''.join(["{}\n".format(x) for x in uptime]))

            stdin, stdout, stderr = client.exec_command('ls -l /opt/jboss-as/standalone/deployments/eha*')
            data = stdout.read() + stderr.read()
            status_eha = data.decode('utf-8').splitlines()
            return_data.append(''.join(["{}\n".format(x) for x in status_eha]))


            client.close()
            return ''.join(["{}\n".format(x) for x in return_data])

        except paramiko.ssh_exception.AuthenticationException:
            return("Authentication failed.")
        except TimeoutError:
            return("TimeoutError: {}".format())
        except:
            raise("Uncknoun failed.")
