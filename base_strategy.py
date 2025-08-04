# Classe base abstrata para todas as estratégias
from abc import ABC, abstractmethod
from handlers.data_handler import DataHandler
from handlers.execution_handler import ExecutionHandler
from handlers.risk_manager import RiskManager
from handlers.state_manager import StateManager

class BaseStrategy(ABC):
    """Classe base para todas as estratégias de negociação."""
    def __init__(self, platform_params: dict, strategy_params: dict):
        self.platform_params = platform_params  # Armazena a configuração da plataforma
        self.data_handler = DataHandler(platform_params)
        self.execution_handler = self.data_handler.execution_handler
        self.risk_manager = RiskManager(self.execution_handler, platform_params)
        self.state_manager = StateManager()
        self.params = strategy_params

    @abstractmethod
    async def process_tick(self):
        """
        Método principal chamado a cada "tick" do loop do bot.
        A lógica de verificar sinais e tomar decisões deve estar aqui.
        """
        raise NotImplementedError