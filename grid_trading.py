import logging
import asyncio
from .base_strategy import BaseStrategy

logger = logging.getLogger("GridTradingStrategy")

class GridTradingStrategy(BaseStrategy):
    """Estratégia 7: Grid Trading Alavancado."""
    
    def __init__(self, platform_params: dict, strategy_params: dict):
        super().__init__(platform_params, strategy_params)
        self.grid_orders_placed = False # Controle para setup inicial da grade

    async def setup_grid(self, current_price):
        """Cria a grade inicial de ordens de compra e venda."""
        logger.info(f"Configurando a grade em torno do preço {current_price:.2f}")
        
        # Parâmetros
        symbol = self.platform_params['target_symbol']
        leverage = self.platform_params['leverage']
        num_levels = self.params['grid_levels']
        step = self.params['grid_step_percentage'] * current_price
        amount_per_level = self.params['amount_per_level_usd'] / current_price
        
        # ETAPA 1: Configurar a alavancagem para o par UMA VEZ
        await self.execution_handler.setup_trading_environment(symbol, leverage)
        
        tasks = []
        # Cria as tarefas para posicionar as ordens
        for i in range(1, num_levels + 1):
            buy_price = current_price - i * step
            sell_price = current_price + i * step
            
            # CORREÇÃO: Chamada correta da função place_order.
            # O tipo da ordem é 'limit'.
            # O preço é passado como o argumento 'price' (um float).
            # 'params' está vazio (None) pois a alavancagem já foi definida.
            tasks.append(self.execution_handler.place_order(symbol=symbol, side='buy', amount=amount_per_level, order_type='limit', price=buy_price))
            tasks.append(self.execution_handler.place_order(symbol=symbol, side='sell', amount=amount_per_level, order_type='limit', price=sell_price))
        
        # ETAPA 2: Executa todas as tarefas de criação de ordem em paralelo
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful_orders = [res for res in results if res and not isinstance(res, Exception)]
        
        if successful_orders:
             logger.info(f"{len(successful_orders)} ordens da grade posicionadas com sucesso.")
             self.grid_orders_placed = True
        else:
            logger.error("Nenhuma ordem da grade pôde ser posicionada. Verifique os logs de erro acima.")


    async def process_tick(self):
        """Verifica se a grade precisa ser criada."""
        # A lógica só executa uma vez para configurar a grade inicial.
        if not self.grid_orders_placed:
             current_price = await self.data_handler.get_current_price(self.platform_params['target_symbol'])
             if current_price:
                 await self.setup_grid(current_price)