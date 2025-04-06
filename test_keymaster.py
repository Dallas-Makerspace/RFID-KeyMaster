import unittest
from unittest.mock import patch, MagicMock
from KeyMaster import KeyMaster


class TestKeyMaster(unittest.TestCase):

    @patch('KeyMaster.Loader')  # Mock the Loader class
    @patch('KeyMaster.configparser.ConfigParser')  # Mock the ConfigParser
    def test_keymaster_init(self, mock_configparser, mock_loader):
        # Mock the ConfigParser behavior
        mock_config = MagicMock()
        mock_config.items.return_value = [('driver1', 'Driver1Module'), ('driver2', 'Driver2Module')]
        mock_configparser.return_value = mock_config

        # Mock the Loader behavior
        mock_loader_instance = MagicMock()
        mock_loader_instance.getDriver.side_effect = lambda name: MagicMock() if name == 'log' else None
        mock_loader_instance.getDrivers.return_value = [MagicMock()]
        mock_loader.return_value = mock_loader_instance

        # Run the KeyMaster.__init__ method
        km = KeyMaster("dummy_config.ini")

        # Assertions
        mock_configparser.assert_called_once()  # Verify the config parser was used
        mock_loader.assert_called_once()  # Verify the loader was initialized
        self.assertIsNotNone(km.log)  # Ensure the log driver was initialized

    @patch('KeyMaster.time.sleep')  # Mock the time.sleep to avoid delays
    @patch('KeyMaster.logging.info')  # Mock logging
    @patch('KeyMaster.os.utime')  # Mock the watchdog file updates
    def test_keymaster_watchdog(self, mock_utime, mock_logging_info, mock_sleep):
        # Mock ConfigParser and Loader (to avoid hardware interaction)
        with patch('KeyMaster.Loader'), patch('KeyMaster.configparser.ConfigParser'):
            km = KeyMaster("dummy_config.ini")

        # Mock the infinite loop to stop after one iteration
        def side_effect(*args, **kwargs):
            if not hasattr(side_effect, "called"):
                side_effect.called = True
            else:
                raise KeyboardInterrupt  # Stop the loop after the first iteration

        mock_sleep.side_effect = side_effect

        # Call the watchdog loop
        with self.assertRaises(KeyboardInterrupt):  # Expect the loop to terminate with KeyboardInterrupt
            km.touch = MagicMock()  # Mock the touch function for the file
            km.watchdog_active = True  # Attribute to simulate the loop
            while True:
                km.touch("dummy_watchdog_file")
                side_effect()

        # Assertions
        mock_utime.assert_called_once_with("dummy_watchdog_file", None)  # Verify touch was called
        mock_logging_info.assert_called()  # Ensure it logged the start of the watchdog

    @patch('KeyMaster.Loader')  # Mock the Loader class
    @patch('KeyMaster.configparser.ConfigParser')  # Mock the ConfigParser
    @patch('KeyMaster.os.walk')  # Mock the os.walk dictionary to simulate driver paths
    def test_driver_paths_setup(self, mock_os_walk, mock_configparser, mock_loader):
        # Mock os.walk to simulate driver directories
        mock_os_walk.return_value = [('drivers/driver1', (), ()),
                                     ('drivers/driver2', (), ()),
                                     ('drivers/__pycache__/', (), ())]

        # Mock ConfigParser and Loader behavior
        mock_config = MagicMock()
        mock_config.items.return_value = []
        mock_configparser.return_value = mock_config

        mock_loader_instance = MagicMock()
        mock_loader.return_value = mock_loader_instance

        # Run __init__ and observe path setup behavior
        km = KeyMaster("dummy_config.ini")

        # Assertions
        mock_os_walk.assert_called_once_with('drivers')  # Verify 'os.walk' was used to search for driver paths
        self.assertIn('drivers/driver1', km.__dict__.get('removed_paths', []))  # Check paths in sys.path


# Run the tests
if __name__ == '__main__':
    unittest.main()
