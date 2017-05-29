"""Test Service EHA client - test_3_con2 -"""
# -*- coding: utf-8 -*-

import pytest
import allure


@pytest.fixture()
def maket3_test_3_con2(test_server_3_1, data_maket_mea1209_1211):
    # print("maket3_test_3_con2")
    return test_server_3_1(data_maket_mea1209_1211, data_maket_mea1209_1211["server_port2"], "test_3")


@allure.step("Test Checking the disconnection after connection from port2")
def test_3_con2(maket3_test_3_con2):
    """Test Checking the disconnection after connection from port2"""
    # print("test_3_con1")
    d = maket3_test_3_con2

    def check_disconnect_after_connect(status):
        # print(status)
        stat, desc = status
        assert stat, desc

    d.addCallback(check_disconnect_after_connect)
    return d

