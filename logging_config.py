# Configuração do sistema de logs
import logging
import sys
from rich.logging import RichHandler

def setup_logging():
    """Configura o sistema de logging para usar o Rich para uma saída bonita."""
    logging.basicConfig(
        level="INFO",
        format="%(asctime)s [%(name)s] %(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )
    # Silencia logs muito verbosos de outras bibliotecas se necessário
    logging.getLogger("ccxt").setLevel(logging.WARNING)