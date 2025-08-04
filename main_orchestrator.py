# main_orchestrator.py

import asyncio
import logging
import random
from rich.console import Console
from rich.panel import Panel

# Importações dos Módulos e Configurações
from config import PLATFORM_PARAMS, STRATEGY_CONFIG, PORTFOLIO_ASSETS
from strategies.statistical_arbitrage import StatisticalArbitrageStrategy
from strategies.trend_following import TrendFollowingStrategy

# Configuração do Logging Profissional
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)-8s [%(name)s] %(message)s",
    handlers=[
        logging.FileHandler("trading_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Orchestrator")
console = Console()

def display_header():
    """Mostra um cabeçalho estilizado para o bot."""
    console.print(Panel(
        "[bold magenta]Quant Nexus Architect[/bold magenta] - Sistema Multi-Estratégia para Hyperliquid",
        title="[bold]Inicialização[/bold]",
        border_style="cyan"
    ))

async def run_strategy(strategy_class, platform_params, strategy_params, symbol=None):
    """Função wrapper para inicializar e executar uma única instância de estratégia."""
    instance = None  # Garantir que a variável exista no escopo
    try:
        # --- CONTROLE DE RATE LIMIT ---
        # Adiciona um atraso aleatório de até 5 segundos antes de iniciar cada estratégia
        # para evitar que todas as requisições à API aconteçam ao mesmo tempo.
        initial_delay = random.uniform(1, 15)
        logger.info(f"Aguardando {initial_delay:.2f}s antes de iniciar a estratégia para {symbol or 'Pairs Trading'}...")
        await asyncio.sleep(initial_delay)

        # Adapta a inicialização para a TrendFollowingStrategy que requer um símbolo
        if symbol:
            instance = strategy_class(platform_params, strategy_params, symbol)
        else:
            instance = strategy_class(platform_params, strategy_params)
        
        await instance.execution_handler.initialize()

        while True:
            await instance.process_tick()
            # Aumenta a pausa para reduzir a carga geral na API
            await asyncio.sleep(30)
            
    except Exception as e:
        strategy_name = strategy_class.__name__
        asset_info = f" para o ativo {symbol}" if symbol else ""
        logger.critical(f"Erro fatal na {strategy_name}{asset_info}: {e}", exc_info=True)
    finally:
        if instance and instance.execution_handler:
            await instance.execution_handler.close_connection()

async def main():
    """Função principal que orquestra a inicialização e execução de todas as estratégias."""
    display_header()
    tasks = []
    active_strategies = []

    # --- Carregar Estratégia de Arbitragem Estatística ---
    if STRATEGY_CONFIG['statistical_arbitrage']['enabled']:
        config = STRATEGY_CONFIG['statistical_arbitrage']
        # A classe ainda não foi importada, então usamos o nome por enquanto
        # Quando o arquivo for criado, a importação no topo será descomentada
        config['class'] = StatisticalArbitrageStrategy
        tasks.append(run_strategy(
            strategy_class=config['class'],
            platform_params=PLATFORM_PARAMS,
            strategy_params=config['params']
        ))
        active_strategies.append("Arbitragem Estatística (Pairs Trading)")

    # --- Carregar Estratégia de Seguidor de Tendência para o Portfólio ---
    if STRATEGY_CONFIG['trend_following']['enabled']:
        config = STRATEGY_CONFIG['trend_following']
        for asset in PORTFOLIO_ASSETS:
            tasks.append(run_strategy(
                strategy_class=config['class'],
                platform_params=PLATFORM_PARAMS,
                strategy_params=config['params'],
                symbol=asset
            ))
        active_strategies.append(f"Seguidor de Tendência ({len(PORTFOLIO_ASSETS)} ativos)")

    if not tasks:
        logger.error("Nenhuma estratégia foi habilitada no config.py. Encerrando.")
        return

    console.print(f"Iniciando as seguintes estratégias: [bold green]{', '.join(active_strategies)}[/bold green]...\n")

    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        logger.info("Desligamento solicitado pelo usuário.")
    finally:
        logger.info("Encerrando todas as conexões...")
        # O encerramento agora é tratado dentro de cada task `run_strategy`
        console.print(Panel("[bold]Sistema encerrado.[/bold]", title="[bold]Shutdown[/bold]", border_style="red"))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
