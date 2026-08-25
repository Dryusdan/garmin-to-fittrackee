from garmin_to_fittrackee import main


def test_main_callback_verbose_enables_debug(mocker):
    set_log_level = mocker.patch.object(main, "set_log_level")
    main.main_callback(verbose=True)
    set_log_level.assert_called_once_with("DEBUG")


def test_main_callback_not_verbose_keeps_level(mocker):
    set_log_level = mocker.patch.object(main, "set_log_level")
    main.main_callback(verbose=False)
    set_log_level.assert_not_called()
