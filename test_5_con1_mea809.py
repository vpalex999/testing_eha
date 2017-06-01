"""Test Service EHA client"""
# -*- coding: utf-8 -*-

import pytest
import allure





@pytest.fixture()
def maket3_test_5_con1(test_server_5_1, check_side_mea809, data_maket_mea809, ):
    return test_server_5_1(data_maket_mea809, data_maket_mea809["server_port1"], "test_5")


@allure.step("Test connect_from EHA_port1")
def test_5_con1(maket3_test_5_con1):
    """Test Service connect client EHA to test server for port1"""
    d = maket3_test_5_con1

    def check_connect(status):

        stat, desc = status

        with pytest.allure.step("Result test"):
            allure.attach("Show statistics data from test",\
                          "\n{}\nInfo: {}".format(stat, desc))

        assert stat == None, desc
        print("\ncheck_connect test status: {}\nInfo: {}".format(stat, desc))

    d.addCallback(check_connect)

    return d


