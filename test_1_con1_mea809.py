"""Test Service EHA client"""
# -*- coding: utf-8 -*-

import pytest
import allure


#@pytest.fixture()
#def maket3_test_1_con1(test_server_3_1, data_maket_mea809):
#    return test_server_3_1(data_maket_mea809, data_maket_mea809["server_port1"])


@allure.step("Test connect_from EHA_port1")
def test_1_con1(check_side_mea809):
    """Test Service connect client EHA to test server for port1"""
    #d = maket3_test_1_con1

    #def check_connect(status):
    #    print(status)
    #    stat, desc = status
    #    assert stat, desc

    #d.addCallback(check_connect)
    #return d

    print("\nCheck connect EHA side: {}".format(check_side_mea809))


