# main.py

import asyncio
import logging
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

# Importações dos Módulos e Configurações
from config import PLATFORM_PARAMS, STRATEGY_PARAMS
from handlers.data_handler import DataHandler
from handlers.execution_handler import ExecutionHandler
from handlers.risk_manager import RiskManager
from handlers.state_manager import StateManager

# Configuração do Logging Profissional
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)-7s [%(name)s] %(message)s",
    handlers=[
        logging.FileHandler("trading_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
console = Console()

def display_header():
    """Mostra um cabeçalho estilizado para o bot."""
    console.print(Panel(
        "[bold magenta]Quant Nexus Architect[/bold magenta] - Sistema de Negociação para Hyperliquid",
        title="[bold]Inicialização[/bold]",
        border_style="cyan"
    ))

def select_strategy():
    """Cria um menu dinâmico e permite que o usuário selecione uma estratégia."""
    console.print("\nSelecione a estratégia para executar:\n")
    
    # --- LÓGICA DINÂMICA ---
    # Converte as chaves do dicionário de estratégias em uma lista para seleção numérica
    strategy_keys = list(STRATEGY_PARAMS.keys())
    
    for i, key in enumerate(strategy_keys):
        strategy_name = STRATEGY_PARAMS[key].get('name', key.replace('_', ' ').title())
        console.print(f"{i + 1} - {strategy_name}")
    
    console.print() # Linha em branco para espaçamento
    
    choice = Prompt.ask(
        f"Escolha uma opção [1-{len(strategy_keys)}]",
        choices=[str(i + 1) for i in range(len(strategy_keys))],
        default="1"
    )
    
    # Retorna a chave de texto correspondente à escolha numérica (ex: 'triangular_arbitrage')
    return strategy_keys[int(choice) - 1]

async def main():
    """Função principal que orquestra a inicialização e execução do bot."""
    display_header()
    
    # 1. Seleção da Estratégia pelo Usuário
    chosen_strategy_key = select_strategy()
    strategy_config = STRATEGY_PARAMS[chosen_strategy_key]
    strategy_name = strategy_config['name']
    
    console.print(f"\nIniciando a estratégia: [bold green]{strategy_name}[/bold green]...\n")

    # 2. Inicialização dos Handlers (Módulos de Suporte)
    # A inicialização agora é feita dentro da classe BaseStrategy para evitar importações circulares.

    # 3. Conexão e Sincronização
    # A conexão será iniciada dentro da própria estratégia quando necessário.

    # 4. Instanciação da Estratégia Escolhida
    try:
        StrategyClass = strategy_config.get('class')
        if not StrategyClass:
            logger.critical(f"Classe de estratégia não definida para '{chosen_strategy_key}' no config.py.")
            return
            
        strategy_instance = StrategyClass(
            platform_params=PLATFORM_PARAMS,
            strategy_params=strategy_config['params']
        )
        
        # Inicializa a conexão DEPOIS de instanciar a estratégia
        await strategy_instance.execution_handler.initialize()

    except Exception as e:
        logger.critical(f"Erro ao instanciar a classe da estratégia: {e}", exc_info=True)
        return

    # 5. Loop Principal de Execução
    try:
        while True:
            await strategy_instance.process_tick()
            await asyncio.sleep(2)  # Pausa para não sobrecarregar a API
    except KeyboardInterrupt:
        logger.info("Desligamento solicitado pelo usuário.")
    except Exception as e:
        logger.critical(f"Erro fatal no loop principal: {e}", exc_info=True)
    finally:
        if 'strategy_instance' in locals() and strategy_instance.execution_handler:
            await strategy_instance.execution_handler.close_connection()
        console.print(Panel("[bold]Sistema encerrado.[/bold]", title="[bold]Shutdown[/bold]", border_style="red"))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass