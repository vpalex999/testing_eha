"""Test Service EHA client - test_2_con1 -"""
# -*- coding: utf-8 -*-

import pytest
import allure


@pytest.fixture()
def maket3_test_2_con1(test_server_3_1, data_maket_mea1209_1211):
    return test_server_3_1(data_maket_mea1209_1211, data_maket_mea1209_1211["server_port1"], "test_2")


@allure.step("Test Checking connecting from another address from port1")
def test_3_con1(maket3_test_2_con1):
    """Checking connecting from another address from port1"""
    # print("test_3_con1")
    d = maket3_test_2_con1

    def сhecking_connecting_from_another_address(status):
        # print(status)
        stat, desc = status
        assert stat, desc

    d.addCallback(сhecking_connecting_from_another_address)
    return d

