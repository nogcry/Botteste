# Controle de estado (ocioso, em posição)
import logging

logger = logging.getLogger(__name__)

class StateManager:
    def __init__(self):
        self._state = "IDLE"  # Estado inicial
        logger.info(f"StateManager iniciado no estado: {self._state}")

    @property
    def state(self):
        return self._state

    def set_in_position(self):
        """Define o estado para indicar que uma posição está aberta."""
        if self._state != "IN_POSITION":
            self._state = "IN_POSITION"
            logger.info("Estado alterado para: IN_POSITION")

    def set_idle(self):
        """Define o estado para ocioso, pronto para buscar novas entradas."""
        if self._state != "IDLE":
            self._state = "IDLE"
            logger.info("Estado alterado para: IDLE")