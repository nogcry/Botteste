import logging
import asyncio
from .base_strategy import BaseStrategy

logger = logging.getLogger("MarketMakingStrategy")

class MarketMakingStrategy(BaseStrategy):
    """Estratégia 2: Market Making de Spread Fixo (VERSÃO CORRIGIDA)."""

    async def process_tick(self):
        """Posiciona e gerencia ordens de compra e venda."""
        symbol = self.platform_params['target_symbol']
        
        # Em uma implementação real, o bot gerenciaria/cancelaria ordens existentes.
        # Por simplicidade, esta versão foca em posicionar um novo par de ordens.
        
        mid_price = await self.data_handler.get_current_price(symbol)
        if mid_price is None:
            return

        # Calcular os preços de compra (bid) e venda (ask)
        spread = self.params['spread_percentage'] * mid_price
        bid_price = mid_price - spread / 2
        ask_price = mid_price + spread / 2
        
        order_size = self.params['order_amount_usd'] / mid_price
        
        try:
            # ETAPA 1: Configurar ambiente de negociação
            await self.execution_handler.setup_trading_environment(symbol, self.platform_params['leverage'])
            
            logger.info(f"Posicionando ordens: COMPRA @ {bid_price:.2f}, VENDA @ {ask_price:.2f}")

            # ETAPA 2: Posicionar ordens com a chamada de API correta
            await asyncio.gather(
                self.execution_handler.place_order(symbol, 'buy', order_size, 'limit', price=bid_price),
                self.execution_handler.place_order(symbol, 'sell', order_size, 'limit', price=ask_price)
            )
        except Exception as e:
            logger.error(f"Erro ao posicionar ordens de market making: {e}")