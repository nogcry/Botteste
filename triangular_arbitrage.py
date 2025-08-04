# strategies/triangular_arbitrage.py

import logging
import asyncio
from .base_strategy import BaseStrategy

logger = logging.getLogger("TriangularArbitrage")

class TriangularArbitrageStrategy(BaseStrategy):
    """
    Estratégia 1 (VERSÃO FINAL): Arbitragem Estatística com 3 Pares de Mercado.
    Configurada com uma lista explícita de 3 'market_pairs' para evitar símbolos inválidos.
    """
    def __init__(self, platform_params: dict, strategy_params: dict):
        super().__init__(platform_params, strategy_params)
        
        self.market_pairs = self.params.get('market_pairs')
        
        if not self.market_pairs or len(self.market_pairs) != 3:
            logger.critical("ERRO DE CONFIGURAÇÃO: A estratégia de arbitragem requer 'market_pairs' com 3 símbolos válidos.")
            raise ValueError("Configuração 'market_pairs' inválida para TriangularArbitrageStrategy.")
            
        logger.info(f"Estratégia de Arbitragem Estatística configurada para os pares: {self.market_pairs}")

    async def process_tick(self):
        """Verifica e atua em oportunidades de arbitragem triangular."""
        try:
            # 1. Obter os preços atuais para os 3 pares de forma concorrente
            tasks = [self.data_handler.get_current_price(pair) for pair in self.market_pairs]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            price_map = {}
            for i, res in enumerate(results):
                pair = self.market_pairs[i]
                if isinstance(res, Exception) or res is None:
                    logger.error(f"Não foi possível obter preço para {pair}: {res}. Pulando ciclo.")
                    return
                price_map[pair] = res

            # 2. Desestruturar os preços assumindo a ordem [A/C, B/C, A/B]
            # Ex: ['ETH/USDC:USDC', 'BTC/USDC:USDC', 'ETH/BTC:USDC']
            price_ac = price_map[self.market_pairs[0]]
            price_bc = price_map[self.market_pairs[1]]
            price_ab_market = price_map[self.market_pairs[2]]

            if price_bc == 0:
                logger.warning("Preço do par base (B/C) é zero, impossível calcular taxa implícita.")
                return

            # 3. Calcular a taxa de câmbio implícita para A/B
            # (A/C) / (B/C) => (ETH/USDC) / (BTC/USDC) = ETH/BTC
            price_ab_implied = price_ac / price_bc

            # 4. Calcular a margem de lucro potencial (diferença percentual)
            profit_margin = ((price_ab_market / price_ab_implied) - 1) * 100

            logger.info(
                f"Análise de Arbitragem: "
                f"Par Mercado ({self.market_pairs[2].split(':')[0]}) = {price_ab_market:.6f} | "
                f"Par Implícito = {price_ab_implied:.6f} | "
                f"Margem Potencial = {profit_margin:.4f}%"
            )

            # 5. Verificar se a oportunidade é lucrativa o suficiente para agir
            min_margin = self.params['min_profit_margin']
            if abs(profit_margin) > min_margin:
                
                if profit_margin > 0:
                    direction = "Comprar Implícito / Vender Mercado"
                else:
                    direction = "Comprar Mercado / Vender Implícito"

                logger.info(
                    f"OPORTUNIDADE DE ARBITRAGEM DETECTADA! "
                    f"Margem: {profit_margin:.4f}%, Direção: {direction}"
                )
                
                # A lógica de execução das ordens entraria aqui.

        except Exception as e:
            logger.error(f"Erro inesperado no ciclo da estratégia de arbitragem: {e}", exc_info=True)