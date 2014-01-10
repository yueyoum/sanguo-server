from django.test import TransactionTestCase


from utils import app_test_helper

from protomsg import GetServerListRequest



class ServerListTest(TransactionTestCase):
    fixtures = ['servers.json',]

    def test_get_server_list(self):
        req = GetServerListRequest()
        req.session = ""
        req.anonymous.device_token = "111111"

        data = app_test_helper.pack_data(req)
        res = app_test_helper.make_request("/world/server-list/", data)
        msgs = app_test_helper.unpack_data(res)