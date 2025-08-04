# strategies/statistical_arbitrage.py

import logging
import asyncio
import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy

logger = logging.getLogger("StatisticalArbitrage")

class StatisticalArbitrageStrategy(BaseStrategy):
    """
    Estratégia de Arbitragem Estatística (Pairs Trading) baseada em Z-score.
    Opera em um par de ativos que se espera que sejam co-integrados.
    """
    def __init__(self, platform_params: dict, strategy_params: dict):
        super().__init__(platform_params, strategy_params)
        self.pair = self.params['pair']
        self.lookback_period = self.params['lookback_period']
        self.z_score_threshold = self.params['z_score_threshold']
        self.exit_z_score = self.params['exit_z_score']
        self.historical_data = {self.pair[0]: pd.DataFrame(), self.pair[1]: pd.DataFrame()}

        logger.info(f"Estratégia de Arbitragem Estatística iniciada para o par: {self.pair}")

    async def fetch_historical_data(self):
        """Busca e armazena dados históricos para ambos os ativos do par."""
        tasks = [
            self.data_handler.get_candles(self.pair[0], '1m', self.lookback_period),
            self.data_handler.get_candles(self.pair[1], '1m', self.lookback_period)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, res in enumerate(results):
            asset = self.pair[i]
            if isinstance(res, Exception) or res is None or res.empty:
                logger.error(f"Não foi possível obter dados históricos para {asset}. A estratégia não pode continuar.")
                return False
            self.historical_data[asset] = res
        return True

    def calculate_spread(self) -> pd.Series:
        """Calcula o spread de preços entre os dois ativos."""
        close_a = self.historical_data[self.pair[0]]['close']
        close_b = self.historical_data[self.pair[1]]['close']
        # O spread é a razão entre os preços, uma abordagem comum para ativos de cripto
        spread = close_a / close_b
        return spread

    async def process_tick(self):
        """Analisa o Z-score do spread e gera sinais de negociação."""
        # 1. Garantir que temos dados históricos suficientes
        if len(self.historical_data[self.pair[0]]) < self.lookback_period:
            if not await self.fetch_historical_data():
                return # Aguarda o próximo ciclo se os dados não puderem ser carregados

        # 2. Calcular o spread e o Z-score
        spread = self.calculate_spread()
        mean_spread = spread.rolling(window=self.lookback_period).mean().iloc[-1]
        std_spread = spread.rolling(window=self.lookback_period).std().iloc[-1]

        if std_spread == 0:
            logger.warning("Desvio padrão do spread é zero. Impossível calcular Z-score.")
            return

        current_spread = spread.iloc[-1]
        z_score = (current_spread - mean_spread) / std_spread

        logger.info(
            f"Análise de Pares ({self.pair[0]} / {self.pair[1]}): "
            f"Spread Atual = {current_spread:.6f} | "
            f"Média = {mean_spread:.6f} | "
            f"Z-score = {z_score:.4f}"
        )

        # 3. Lógica de Geração de Sinais
        # Se não estivermos em posição, procuramos por uma entrada
        if self.state_manager.state == "IDLE":
            # Z-score alto: Spread está caro. Vender o spread (Vender A, Comprar B)
            if z_score > self.z_score_threshold:
                logger.info(f"SINAL DE VENDA (SHORT SPREAD): Z-score ({z_score:.4f}) > Limiar ({self.z_score_threshold})")
                # Lógica de execução de ordem de venda aqui
                # self.state_manager.set_in_position("SHORT_SPREAD")

            # Z-score baixo: Spread está barato. Comprar o spread (Comprar A, Vender B)
            elif z_score < -self.z_score_threshold:
                logger.info(f"SINAL DE COMPRA (LONG SPREAD): Z-score ({z_score:.4f}) < Limiar (-{self.z_score_threshold})")
                # Lógica de execução de ordem de compra aqui
                # self.state_manager.set_in_position("LONG_SPREAD")

        # Se estivermos em posição, procuramos por uma saída (retorno à média)
        elif self.state_manager.state == "SHORT_SPREAD" and z_score < self.exit_z_score:
            logger.info(f"SINAL DE FECHAMENTO (SHORT SPREAD): Z-score ({z_score:.4f}) cruzou o limiar de saída ({self.exit_z_score})")
            # Lógica para fechar a posição vendida aqui
            # self.state_manager.set_idle()
        
        elif self.state_manager.state == "LONG_SPREAD" and z_score > -self.exit_z_score:
            logger.info(f"SINAL DE FECHAMENTO (LONG SPREAD): Z-score ({z_score:.4f}) cruzou o limiar de saída (-{self.exit_z_score})")
            # Lógica para fechar a posição comprada aqui
            # self.state_manager.set_idle()
