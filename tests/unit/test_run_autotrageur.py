import pytest

import autotrageur.run_autotrageur

def test_main(mocker):
    mock_autotrageur = mocker.Mock()
    mock_docopt = mocker.patch.object(autotrageur.run_autotrageur, 'docopt')
    mock_decimal_context = mocker.patch(
        'autotrageur.run_autotrageur.set_autotrageur_decimal_context')
    mock_FCFAutotrageur = mocker.patch(
        'autotrageur.run_autotrageur.FCFAutotrageur', return_value=mock_autotrageur)
    autotrageur.run_autotrageur.main()

    mock_decimal_context.assert_called_with()
    mock_FCFAutotrageur.assert_called_with()
    mock_autotrageur.run_autotrageur.assert_called_once()
    mock_autotrageur.logger.queue_listener.stop.assert_called_with()
    mock_docopt.assert_called_once()

