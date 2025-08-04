# config.py

import os
from dotenv import load_dotenv

# Importações das classes de estratégia que serão utilizadas
from strategies.trend_following import TrendFollowingStrategy
# A classe StatisticalArbitrageStrategy será criada no próximo passo
from strategies.statistical_arbitrage import StatisticalArbitrageStrategy

load_dotenv()

# ==============================================================================
# PARÂMETROS GLOBAIS DA PLATAFORMA E RISCO
# ==============================================================================
PLATFORM_PARAMS = {
    "wallet_address": os.getenv("HYPERLIQUID_WALLET_ADDRESS"),
    "private_key": os.getenv("HYPERLIQUID_PRIVATE_KEY"),
    "slippage_max": 0.05,       # 5% de slippage máximo permitido para ordens a mercado
    "min_entry_value_usd": 10.0, # Valor mínimo de entrada em USD, conforme documentação
    "leverage": 10,             # Alavancagem padrão para as estratégias
}

# ==============================================================================
# ESTRATÉGIA 1: ORQUESTRADOR DE PORTFÓLIO (SEGUIDOR DE TENDÊNCIA)
# ==============================================================================
# Lista de 26 ativos de alto volume para a estratégia de seguidor de tendência.
# O orquestrador irá lançar uma instância da estratégia para cada um destes ativos.
PORTFOLIO_ASSETS = [
    'BTC/USDC:USDC', 'ETH/USDC:USDC', 'HYPE/USDC:USDC', 'SOL/USDC:USDC',
    'XRP/USDC:USDC', 'PUMP/USDC:USDC', 'DOGE/USDC:USDC', 'SUI/USDC:USDC',
    'AAVE/USDC:USDC', 'BNB/USDC:USDC', 'TRUMP/USDC:USDC', 'LINK/USDC:USDC',
    'PENDLE/USDC:USDC', 'VIRTUAL/USDC:USDC', 'OP/USDC:USDC', 'FARTCOIN/USDC:USDC',
    'ENA/USDC:USDC', 'kBONK/USDC:USDC', 'kPEPE/USDC:USDC', 'PENGU/USDC:USDC',
    'LTC/USDC:USDC', 'CRV/USDC:USDC', 'TON/USDC:USDC', 'LAUNCHCOIN/USDC:USDC',
    'AVAX/USDC:USDC', 'ADA/USDC:USDC'
]

# ==============================================================================
# CONFIGURAÇÃO DAS ESTRATÉGIAS A SEREM EXECUTADAS
# ==============================================================================
# Dicionário principal que define quais estratégias o bot irá carregar e executar.
STRATEGY_CONFIG = {
    
    # Estratégia de Pairs Trading (Arbitragem Estatística)
    'statistical_arbitrage': {
        'enabled': True,
        'class': StatisticalArbitrageStrategy, # Descomentar quando a classe for criada
        'params': {
            'pair': ['BTC/USDC:USDC', 'ETH/USDC:USDC'], # O par para negociar
            'lookback_period': 120,       # Período para calcular a média e o desvio padrão do spread
            'z_score_threshold': 2.0,     # Limiar de Z-score para abrir uma posição
            'exit_z_score': 0.5,          # Limiar de Z-score para fechar a posição (retorno à média)
            'risk_per_trade': 0.01,       # Risco de 1% do capital total por operação
        }
    },

    # Estratégia de Seguidor de Tendência para o Portfólio
    'trend_following': {
        'enabled': True,
        'class': TrendFollowingStrategy,
        'params': {
            "ema_fast": 10,
            "ema_slow": 30,
            "risk_per_trade": 0.01,
            "stop_loss_atr_multiplier": 2.0,
            "take_profit_atr_multiplier": 4.0
        }
    }
}
