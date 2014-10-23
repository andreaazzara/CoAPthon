import random

import sys
PY_COAP_PATH = '../'

sys.path.insert(0, PY_COAP_PATH)



from twisted.test import proto_helpers
from twisted.trial import unittest
from coapserver import CoAPServer
from coapthon2 import defines
from coapthon2.messages.message import Message
from coapthon2.messages.option import Option
from coapthon2.messages.request import Request
from coapthon2.messages.response import Response
from coapthon2.serializer import Serializer

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"


class Tests(unittest.TestCase):

    def setUp(self):
        self.proto = CoAPServer("[::1]", 5683)
        self.tr = proto_helpers.FakeDatagramTransport()
        self.proto.makeConnection(self.tr)
        self.current_mid = random.randint(1, 1000)

    def _test(self, message, expected):
        serializer = Serializer()
        datagram = serializer.serialize(message)
        self.proto.datagramReceived(datagram, ("127.0.0.1", 5632))
        datagram, source = self.tr.written[-1]
        host, port = source
        message = serializer.deserialize(datagram, host, port)
        self.assertEqual(message.type, expected.type)
        self.assertEqual(message.mid, expected.mid)
        self.assertEqual(message.code, expected.code)
        self.assertEqual(message.source, source)
        self.assertEqual(message.token, expected.token)
        self.assertEqual(message.payload, expected.payload)
        self.assertEqual(message.options, expected.options)

        self.tr.written = []

    def _test_separate(self, message, expected):
        serializer = Serializer()
        datagram = serializer.serialize(message)
        self.proto.datagramReceived(datagram, ("127.0.0.1", 5632))
        datagram, source = self.tr.written[0]
        host, port = source
        message = serializer.deserialize(datagram, host, port)

        self.assertEqual(message.type, defines.inv_types["ACK"])
        self.assertEqual(message.code, None)
        self.assertEqual(message.mid, self.current_mid)
        self.assertEqual(message.source, source)

        datagram, source = self.tr.written[1]
        host, port = source
        message = serializer.deserialize(datagram, host, port)

        self.assertEqual(message.type, expected.type)
        self.assertEqual(message.code, expected.code)
        self.assertEqual(message.source, source)
        self.assertEqual(message.token, expected.token)
        self.assertEqual(message.payload, expected.payload)
        self.assertEqual(message.options, expected.options)

        self.tr.written = []

        message = Message.new_ack(message)
        datagram = serializer.serialize(message)
        self.proto.datagramReceived(datagram, ("127.0.0.1", 5632))

    def tearDown(self):
        self.proto.stopProtocol()
        del self.proto
        del self.tr

    def test_get_storage(self):
        args = ("/storage",)
        kwargs = {}
        path = args[0]
        req = Request()
        for key in kwargs:
            o = Option()
            o.number = defines.inv_options[key]
            o.value = kwargs[key]
            req.add_option(o)

        req.code = defines.inv_codes['GET']
        req.uri_path = path
        req.type = defines.inv_types["CON"]
        req.mid = self.current_mid

        expected = Response()
        expected.type = defines.inv_types["ACK"]
        expected.mid = self.current_mid
        expected.code = defines.responses["CONTENT"]
        expected.token = None
        expected.payload = "Storage Resource for PUT, POST and DELETE"

        self._test(req, expected)

    def test_get_not_found(self):
        args = ("/not_found",)
        kwargs = {}
        path = args[0]
        req = Request()
        for key in kwargs:
            o = Option()
            o.number = defines.inv_options[key]
            o.value = kwargs[key]
            req.add_option(o)

        req.code = defines.inv_codes['GET']
        req.uri_path = path
        req.type = defines.inv_types["CON"]
        req.mid = self.current_mid

        expected = Response()
        expected.type = defines.inv_types["NON"]
        expected.mid = self.current_mid
        expected.code = defines.responses["NOT_FOUND"]
        expected.token = None
        expected.payload = None

        self._test(req, expected)

    def test_post_and_get_storage(self):
        args = ("/storage/data1",)
        kwargs = {}
        path = args[0]
        req = Request()
        for key in kwargs:
            o = Option()
            o.number = defines.inv_options[key]
            o.value = kwargs[key]
            req.add_option(o)

        req.code = defines.inv_codes['POST']
        req.uri_path = path
        req.type = defines.inv_types["CON"]
        req.mid = self.current_mid
        req.payload = "Created"

        expected = Response()
        expected.type = defines.inv_types["ACK"]
        expected.mid = self.current_mid
        expected.code = defines.responses["CREATED"]
        expected.token = None
        expected.payload = None
        option = Option()
        option.number = defines.inv_options["Location-Path"]
        option.value = "storage/data1"
        expected.add_option(option)

        self._test(req, expected)

        req = Request()
        for key in kwargs:
            o = Option()
            o.number = defines.inv_options[key]
            o.value = kwargs[key]
            req.add_option(o)

        req.code = defines.inv_codes['GET']
        req.uri_path = path
        req.type = defines.inv_types["CON"]
        req.mid = self.current_mid

        expected = Response()
        expected.type = defines.inv_types["ACK"]
        expected.mid = self.current_mid
        expected.code = defines.responses["CONTENT"]
        expected.token = None
        expected.payload = "Created"

    def test_get_separate(self):
        args = ("/separate",)
        kwargs = {}
        path = args[0]
        req = Request()
        for key in kwargs:
            o = Option()
            o.number = defines.inv_options[key]
            o.value = kwargs[key]
            req.add_option(o)

        req.code = defines.inv_codes['GET']
        req.uri_path = path
        req.type = defines.inv_types["CON"]
        req.mid = self.current_mid

        expected = Response()
        expected.type = defines.inv_types["CON"]
        expected.code = defines.responses["CONTENT"]
        expected.token = None
        expected.payload = "Separate"

        self._test_separate(req, expected)
