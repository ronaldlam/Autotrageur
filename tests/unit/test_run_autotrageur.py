import pytest

import run_autotrageur

def test_main(mocker):
    bg_logger = mocker.Mock()
    autotrageur = mocker.Mock()
    arguments = mocker.Mock()
    mock_decimal_context = mocker.patch(
        'run_autotrageur.set_autotrageur_decimal_context')
    mock_setup_background_logger = mocker.patch(
        'fp_libs.logging.bot_logging.setup_background_logger',
        return_value=bg_logger)
    mock_FCFAutotrageur = mocker.patch(
        'run_autotrageur.FCFAutotrageur', return_value=autotrageur)
    run_autotrageur.main(arguments)

    mock_decimal_context.assert_called_with()
    mock_setup_background_logger.assert_called_with()
    mock_FCFAutotrageur.assert_called_with(bg_logger)
    autotrageur.logger.queue_listener.start.assert_called_with()
    autotrageur.run_autotrageur.assert_called_with(arguments)
    autotrageur.logger.queue_listener.stop.assert_called_with()

