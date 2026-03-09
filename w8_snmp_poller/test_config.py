#import the unittest module which is used to write and run tests in Python
import unittest

#import the validate_config function from our main program (poller.py)
#this function checks if the configuration structure is valid
from poller import validate_config


#create a test class that inherits from unittest.TestCase
#all unit tests must be inside a class like this
class TestConfigValidation(unittest.TestCase):

    #this test checks that the program raises an error
    #if the "targets" field is missing in the config
    def test_missing_targets_raises_value_error(self):

        #create a configuration dictionary manually
        #here we intentionally leave out "targets"
        #to test if validate_config correctly detects the problem
        cfg = {
            "defaults": {
                "timeout_s": 2.5,           #timeout for each SNMP request
                "target_budget_s": 10,      #maximum time allowed per target
                "retries": 1,               #number of retry attempts
                "oids": ["sysUpTime.0"]     #list of OIDs to poll
            }
            #"targets" is missing here on purpose
        }

        #assertRaises checks that a specific exception occurs
        #validate_config should raise ValueError because
        #the required "targets" field is missing
        with self.assertRaises(ValueError):
            validate_config(cfg)


#this allows the test to run when the file is executed directly
#for example: python test_config.py
if __name__ == "__main__":
    unittest.main()