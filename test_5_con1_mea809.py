"""Test Service EHA client"""
# -*- coding: utf-8 -*-

import pytest
import allure


@pytest.fixture()
def maket3_test_5_con1(test_server_5_1, data_maket_mea809, check_side_mea809):
    return test_server_5_1(data_maket_mea809, data_maket_mea809["server_port1"], "test_5")


@allure.step("Test connect_from EHA_port1")
def test_5_con1(maket3_test_5_con1):
    """Test Service connect client EHA to test server for port1"""
    d = maket3_test_5_con1
    print("\ncheck_connect test: {}")
    def check_connect(status):
        print("\ncheck_connect test: {}".format(status))
        stat, desc = status
        assert stat == None, desc

    d.addCallback(check_connect)

    return d


