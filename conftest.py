import pytest
import allure
import re
import paramiko
from datetime import datetime
import time
from statistics import mean

from twisted.internet.protocol import Protocol
from twisted.internet.protocol import Factory
from twisted.internet.protocol import ServerFactory
from twisted.internet.defer import Deferred
from twisted.internet.defer import succeed

from sources.hdlc import hdlc_code

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
        return ''.join(["\n{}: {}".format(item[0], item[1]) for item in data.items()])
        #return ''.join(["\n{}: {}".format(item[0], item[1]) for item in data.items()])

    stend_data = print_data(data)
    print(stend_data)
    with pytest.allure.step("Stend configuration data"):
        allure.attach("Stend data", print_data(data))

    return data

@pytest.fixture()
def from_ok_3257():
    ok = [{"ocAddr":"3257", "Zones": [0,1,2,3]}]
    return ok



@pytest.fixture()
def create_ok(from_ok_3257):
    def return_ok(ok):
        # Data from parcer config file
        # data_from_config = [{"ocAddr":"3257", "Zones": [0,1,2,3]}]
        data_from_config = ok
        # OK for work
        system_data_ok = {}
        # Default DATA from OK
        default_data_ok = {
            "STATUS_OK": "SAFE",
            "Timer_status": False,
            "Start_timer": False,
            "LOOP_OK": False,
            "AREA_OK": False,
            "HUB_OK": False,
            "NUMBER_OK": False,
            "ADDRESS_OK": False,
            "Err_Count": 0,
            "count_a": 1,
            "count_b": 254,
            "ORDER_WORK": None,
            "ZONE_FROM_CNS": dict.fromkeys(range(36), 0),
            "ZONE_FOR_CNS": dict.fromkeys(range(36), 0),
            "CODE_ALARM": None,
            "DESC_ALARM": None,
            "TELEGRAMM_A": None,
            "TELEGRAMM_B": None,
            "RETURN_OK": 0,
            }

        def zone_for_cns(data_from_config, system_data_ok):
            telegrams = data_from_config

            for ok in system_data_ok:
                for tlg in telegrams:
                    if tlg['ocAddr'] == ok:
                        zone = tlg['Zones']
                        zone_dict = {x: zone[x] for x in range(len(zone))}
                        zone_from_cns = dict.fromkeys(range(36), 0)
                        zone_from_cns.update(zone_dict)
                        system_data_ok[ok]["ZONE_FROM_CNS"] = zone_from_cns

        def from_address_ok(address_ok, default_data_ok, reason=None):
            # print(type(address_ok))
            def_data = default_data_ok.copy()
            if type(address_ok) == int:
                address_ok = "{}".format(address_ok)

            def _code_address_ok(def_data, reason):
                address_ok = ""
                result = def_data["LOOP_OK"] << 4
                temp = def_data["AREA_OK"] << 1
                result = result | temp
                address_ok = address_ok + "{:02x}".format(int(hex(result), 16))
                result = 0
                temp = def_data["HUB_OK"] << 4
                result = result | temp
                temp = def_data["NUMBER_OK"] << 1
                temp = temp | 1
                result = result | temp
                address_ok = address_ok + "{:02x}".format(int(hex(result), 16))
                def_data["ADDRESS_OK"] = address_ok

            if len(address_ok) == 4:
                loop = int(address_ok[0], 16)
                area = int(address_ok[1], 16)
                hub = int(address_ok[2], 16)
                number = int(address_ok[3], 16)
                if area & 1 != 0:
                    reason = "Invalid configure AREA OK!"
                    print("Invalid configure AREA OK!")
                    return False, reason
                elif number & 1 != 1:
                    reason = "Invalid configure Number OK!"
                    print("Invalid configure Number OK!")
                    return False
                else:
                    area = area >> 1
                    number = number >> 1
                    def_data["LOOP_OK"], def_data["AREA_OK"], def_data["HUB_OK"], def_data[
                        "NUMBER_OK"] = loop, area, hub, number
                    _code_address_ok(def_data, reason)
                    diction = {}
                    diction[def_data["ADDRESS_OK"]] = def_data
                    return diction
            else:
                reason = "number of characters to be equal to 4"
                print("number of characters to be equal to 4")
                return False

        def create_ok(data_from_config, system_data_ok, default_data_ok, from_address_ok):

            addresses_ok = data_from_config
            try:
                for ok in addresses_ok:
                    system_data_ok.update(from_address_ok(ok['ocAddr'], default_data_ok))
                return True
            except:
                print("Wrong adress OK: '{}'".format(ok))
                return False

        if create_ok(data_from_config, system_data_ok, default_data_ok, from_address_ok):
            zone_for_cns(data_from_config, system_data_ok)
            return system_data_ok
    return return_ok(from_ok_3257)




@pytest.fixture()
def data_maket_mea809(create_ok):
    data = {
            "server_port1": 10000,
            "server_port2": 10001,
            "server_host": "192.168.10.168",
            "server_localhost": "127.0.0.1",
            "double": False,
            "client_eha_side_1": {"ip": "192.168.121.119", "version": "Empty", "Other": ""},
            "client_eha_side_2": {"ip": "192.168.101.4", "version": "Empty", "Other": ""},
            "client_eha_float": {"ip": "192.168.101.5"},
            "active_side": "Empty",
            "timeout_connect": 3,
            "timeout_disconnect": 60,
            "user": 'root',
            "secret": 'iskratel',
            "statistics": {
                "stat_orders": {"count_send_orders": 0, "min_delta": 0, "max_delta": 0, "average": 0},
                "stat_status": {"count_received_status": 0, "min_delta": 0, "max_delta": 0, "average": 0}
            },
            "system_data": {
                "start_time": time.time(),
                "hdlc": bytearray(),
                "time_delta": "",
                "System_Status": "SAFE",
                "Lost_Connect": False,
                "FIRST_START": True,
                "Count_A": 1,
                "Count_B": 254,
                "Err_Count": 0,
                "Timer_status": False,
                "Start_timer": False,
                "ORDER_Count_A": 1,
                "ORDER_Count_B": 254,
                "ORDER_CODE_ALARM": None,
                "ORDER_DESC_ALARM": None,
                "ORDER": None,
                "ORDER_STATUS": None,
                "HDLC_SEND_STATUS": None,
                "OK": create_ok,
                "WORK_OK": {},
                "Timer_OK": {},
            }
        }
    return data



@pytest.fixture()
def chk_active_side_eha():

    def check_side_eha(data):

        def show_status_stend(data):
            def print_data(data):
                return ''.join(["\n{}: {}".format(item[0], item[1]) for item in data.items()])

            # print(print_data(data))
            with pytest.allure.step("Stend configuration data"):
                allure.attach("Stend data", print_data(data))

        def chk_side(eha, user, passwd, data):

            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ip = data[eha]["ip"]
                # pprint("eha: {}".format(eha))
                # pprint("data: {}".format(data))
                client.connect(ip, username=user, password=passwd, timeout=2)
                stdin, stdout, stderr = client.exec_command('ls -l /opt/jboss-as/standalone/deployments/eha*')
                version = stdout.read() + stderr.read()
                version_eha = version.decode('utf-8').splitlines()
                data[eha]["version"] = ''.join(["{}\n".format(ver) for ver in version_eha])
                # pprint("version: {}".format(data[eha]["version"]))
                stdin, stdout, stderr = client.exec_command('cat /proc/drbd')
                status = stdout.read() + stderr.read()
                status_eha = status.decode('utf-8').splitlines()
                for active in status_eha:
                    if re.search("Primary/Secondary", active):
                        data["active_side"] = data[eha]
                        data[eha]["Other"] = "Primary/Secondary"
                        print("Checking EHA is double side!!!")
                        return True
                        break

                    if re.search("Secondary/Primary", active):
                        # print("active: {}".format(active))
                        # print("Other: {}".format(data[eha]["Other"]))
                        data[eha]["Other"] = "SecondaryPrimary"
                        return True
                        break

                    if re.search("No such file or directory", active):
                        data["active_side"] = data[eha]
                        data[eha]["Other"] = "No such file or directory"
                        print("checking EHA is standalone side!!!")
                        return True


                client.close()
            except paramiko.ssh_exception.AuthenticationException:
                data[eha]["Other"] = "Authentication failed."
                return False
            except:
                data[eha]["Other"] = "TimeoutError"
                return False

        assert chk_side("client_eha_side_1", data["user"], data["secret"], data),\
            "{}\n{}".format(data["client_eha_side_1"]["Other"], show_status_stend(data))
        if data["double"]:
            if not chk_side("client_eha_side_2", data["user"], data["secret"], data):
                show_status_stend(data)
                raise (data["client_eha_side_1"]["Other"])

        show_status_stend(data)
        return ''.join(["\n{}: {}".format(item[0], item[1]) for item in data.items()])

    return check_side_eha




@pytest.fixture()
def check_side_mea809(chk_active_side_eha, data_maket_mea809):
    return chk_active_side_eha(data_maket_mea809)



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


# ############################### TEST 5 #############################################

class ServerServiceProtocol_5_1(Protocol):

    def prnt(self, status):
        print("prnt: {}".format(status))

    @allure.step("connectionMade")
    def connectionMade(self):
        print("\n{} Conn Made...{}".format(date_time(), self.transport.getPeer()))
        print("\nStatus_connect before: {}".format(self.factory.status_connect))
        self.factory.count_connect.append(self.transport.getPeer())
        if not self.factory.status_connect:
            self.factory.start_time = time.time()
            self.factory.status_connect = "{}:{}:{}"\
                .format(date_time(),\
                        self.transport.getPeer().host,\
                        self.transport.getPeer().port)
            allure.attach("In Connect",\
                          "source address: {}".format(self.factory.status_connect))
            print("\nStatus_connect after: {}".format(self.factory.status_connect))
            succeed(self.factory.server.checking_connecting_from_another_address(self.factory.status_connect))
            self.timer_600()
        else:
            # if self.factory.status_connect:
            print("\n{} Conn Close...{}".format(date_time(), self.transport.getPeer()))
            succeed(self.factory.server.check_attempted_reconnection_in_active_state(str(self.transport.getPeer())))
            self.transport.loseConnection()

    def connectionLost(self, reason):
        print("\n{} Connection lost {}\n{}".format(date_time(), reason, self.transport.getPeer()))
        if re.search("Connection was closed cleanly", str(reason)):
            succeed(self.factory.server.check_discon_after_connected(str(reason) + str(self.transport.getPeer())))

    def dataReceived(self, data):
        delta_time = time.time() - self.factory.start_time
        self.factory.delta_status.append(time.time() - self.factory.start_time)
        self.factory.stat_status["count_received_status"] += 1

        print("{} {:0.3f} receive status: {}".format(date_time(), delta_time, data))

    def dataSend(self, status):
        # own 3257
        order = "00 01 02 00 00 00 1C 00 04 FB 00 0E 32 57 74 04 C1 81 2F 32 57 76 FB 3E 7E F5 60 2D"
        hdlc_order = hdlc_code(order)
        hdlc_b = b'\x10\x02\x00\x01\x02\x00\x00\x00*\x00\xeb\x14\x00\x1c2W\xe4\xeb\xe4\x1b\xe4\x1b\xe4\x1b\xe4\x1b@\xad2W\xe6\x14\x1b\xe4\x1b\xe4\x1b\xe4\x1b\xe4\xbf(\xe6\x10\x10\x10\x83'
        delta_time = time.time() - self.factory.start_time
        self.factory.delta_orders.append(time.time() - self.factory.start_time)
        self.transport.write(hdlc_b)
        self.factory.start_time = time.time()
        print("{} {:0.3f} send data: {}".format(date_time(), delta_time, hdlc_b))
        self.factory.stat_orders["count_send_orders"] += 1
        self.timer_600()

    # Автомат генерирует накачку каждые 600мс от начала соединения
    def timer_600(self):
        # print("timer_600")
        from twisted.internet import reactor
        reactor.callLater(0.6, self.dataSend, "status")




class ServerServiceFactory_5_1(Factory):
    protocol = ServerServiceProtocol_5_1

    def __init__(self, server, deferred, data):
        self.start_time = time.time()
        self.server = server
        self.deferred = deferred
        # self.service = service
        self.status_connect = False
        self.timeout_connect = data["timeout_connect"]
        self.timeout_disconnect = data["timeout_disconnect"]
        self.count_connect = []

        self.delta_orders = []
        self.delta_status = []
        self.stat_orders = data["statistics"]["stat_orders"]
        self.stat_status = data["statistics"]["stat_status"]
        print(self.stat_orders)
        print(self.stat_status)
        # self.stat_orders = {"count_send_orders": 0, "min_delta": 0, "max_delta": 0, "average": 0}
        # self.stat_status = {"count_received_status": 0, "min_delta": 0, "max_delta": 0, "average": 0}
        self.timeout_work_test = 10  # seconds
        print("\nInitial factory deferred: {}, protocol: {}, time_out: {}"\
              .format(self.deferred, self.protocol,  self.timeout_connect))
        from twisted.internet import reactor
        reactor.callLater(self.timeout_connect, self.chk_connect)
        reactor.callLater(self.timeout_work_test, self.stop_test)



    def chk_connect(self):
        print("{} In chk()".format(date_time()))
        succeed(self.server.check_timeout_connected(self.status_connect))

    def chk_timeout_disconnect(self):
        print("{} In chk_timeout_disconnect()".format(date_time()))
        succeed(self.server.check_discon_after_connected(self.status_connect))

    def return_result(self, status):
        print("return_result_ok: {}".format(status))
        if status[0]:
            return
        else:
            if self.deferred is not None:
                d, self.deferred = self.deferred, None
            d.callback(status)

    def stop_test(self):
        succeed(self.average(self.delta_orders, self.stat_orders))
        succeed(self.average(self.delta_status, self.stat_status))
        self.return_result((None, "\nStatistics data:\nSend orders{}\nReceived status: {}"\
                           .format(self.stat_orders, self.stat_status)))

    def get_eha_data(self):
        with pytest.allure.step("Get config data from EHA"):
            allure.attach("Get config data from EHA", self.server.get_eha_data())
        # print(self.server.get_eha_data())

    def average(self, delta, dict):
        dict["min_delta"] = float('{:.3f}'.format(min(delta)))
        dict["max_delta"] = float('{:.3f}'.format(max(delta)))
        dict["average"] = float('{:.3f}'.format(mean(delta)))


# tearUp/tearDown
@pytest.yield_fixture()
def test_server_5_1():
    endpoint = None
    ss = None

    @allure.step("Create test_server3() from tearUp/tearDown")
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
        elif re.search("test_5", test):
            ss = Server_Test3.from_test_5(host, port, timeout_connect, data, d)

        from twisted.internet import reactor
        endpoint = reactor.listenTCP(port, ss.factory, interface=host)
        return d
    yield server
    with allure.step("Stop test server"):
        if endpoint is not None:
            ss.chk_eha_config()
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

        elif test == "test_5":
            self.factory = ServerServiceFactory_5_1(self, self.d, self.data)

        else:
            self.factory = ServerServiceFactory_3(self, self.d, self.data)

    @classmethod
    def from_test_3(cls, host, port, timeout_connect, data, d):
        return cls(host, port, timeout_connect, data, d, "test_3")

    @classmethod
    def from_test_2(cls, host, port, timeout_connect, data, d):
        return cls(host, port, timeout_connect, data, d, "test_2")

    @classmethod
    def from_test_5(cls, host, port, timeout_connect, data, d):
        print("create server from test 5")
        return cls(host, port, timeout_connect, data, d, "test_5")

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

        elif re.search("Connection was closed cleanly", str(status)) and\
                re.search(str(self.data["active_side"]["ip"]), str(status)):
            print("\nConnection was closed cleanly {}".format(status))
            self.factory.status_connect = False
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

        elif re.search(str(self.data["active_side"]["ip"]), str(status)):
            print("\nChecking active side succes {}".format(status))
            return self.factory.return_result((True, "Checking connect EHA client from active side succes {}".format(status)))
        else:
            return self.factory.return_result((False, "Connecting from another address to server: {}".format(status)))

    @allure.step("Call Checking connecting from another address()")
    def check_attempted_reconnection_in_active_state(self, getpeer):
        if re.search(str(self.data["active_side"]["ip"]), getpeer):
            return self.factory.return_result((False, "Detected attempted reconnection from own side EHA in active state: {}".format(getpeer)))
        else:
            return self.factory.return_result((False,
                                              "Detected attempted reconnection from other side in active state: {}".format(getpeer)))

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
                    if re.search("Primary/Secondary", active):
                        data["active_side"] = data[eha]
                        data[eha]["Other"] = "Primary/Secondary"
                        print("Checking EHA is double side!!!")
                        return True
                        break

                    if re.search("Secondary/Primary", active):
                        # print("active: {}".format(active))
                        # print("Other: {}".format(data[eha]["Other"]))
                        data[eha]["Other"] = "SecondaryPrimary"
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

        if chk_side("client_eha_side_1", self.data["user"], self.data["secret"], self.data):
                chk_side("client_eha_side_2", self.data["user"], self.data["secret"],self.data)


        tt = ''.join(["\n{}: {}".format(item[0], item[1]) for item in self.data.items()])
        print("tt: {}".format(tt))
        print("Active side: {}".format(self.data["active_side"]))
        return  ''.join(["\n{}: {}".format(item[0], item[1]) for item in self.data.items()])



    def chk_eha_config(self):
        with pytest.allure.step("Get data from EHA"):
            # allure.attach("Get version EHA", self.get_eha_version())
            allure.attach("Get version EHA", self.chk_active_side_eha())


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
