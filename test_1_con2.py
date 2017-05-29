"""Test Service EHA client"""
# -*- coding: utf-8 -*-

import pytest
import allure


@pytest.fixture()
def maket3_test_1_con2(test_server_3_1, data_maket_mea1209_1211):
    return test_server_3_1(data_maket_mea1209_1211, data_maket_mea1209_1211["server_port2"])


@allure.step("Test connect_from EHA_port2")
def test_1_con2(maket3_test_1_con2):
    """Test Service connect client EHA to test server for port2"""
    d = maket3_test_1_con2

    def check_connect(status):
        print(status)
        stat, desc = status
        assert stat, desc

    d.addCallback(check_connect)
    return d



