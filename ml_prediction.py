import logging
import random
from .base_strategy import BaseStrategy

logger = logging.getLogger("MLPredictionStrategy")

class MLPredictionStrategy(BaseStrategy):
    """Estratégia 8: Previsão Direcional com Machine Learning (Simulado)."""

    def __init__(self, platform_params: dict, strategy_params: dict):
        super().__init__(platform_params, strategy_params)
        logger.info("Estratégia de ML inicializada (Modo de Simulação).")

    async def get_ml_prediction(self, data):
        """SIMULAÇÃO de uma previsão de modelo de ML."""
        prediction = random.choice([1, -1, 0])
        confidence = random.uniform(0.6, 0.99)
        logger.info(f"Previsão do Modelo ML: {'COMPRA' if prediction == 1 else 'VENDA' if prediction == -1 else 'MANTER'} (Confiança: {confidence:.2f})")
        return prediction, confidence

    async def process_tick(self):
        """Executa uma negociação com base na previsão simulada do modelo."""
        if self.state_manager.state == "IN_POSITION":
            return

        symbol = self.platform_params['target_symbol']
        
        features = await self.data_handler.get_candles(symbol, '1m', 20)
        if features is None:
            return

        prediction, confidence = await self.get_ml_prediction(features)
        
        if prediction != 0 and confidence > self.params['min_confidence_threshold']:
            side = 'buy' if prediction == 1 else 'sell'
            logger.info(f"Executando ordem baseada em ML: {side.upper()}")
            
            current_price = await self.data_handler.get_current_price(symbol)
            if not current_price: return

            stop_loss_price = current_price * (1 - 0.01) if side == 'buy' else current_price * (1 + 0.01)
            take_profit_price = current_price * (1 + 0.02) if side == 'buy' else current_price * (1 - 0.02)

            size = await self.risk_manager.calculate_position_size(
                risk_per_trade=self.params['risk_per_trade'],
                entry_price=current_price,
                stop_loss_price=stop_loss_price
            )

            if size:
                # ETAPA 1: Configurar o ambiente de negociação (alavancagem)
                await self.execution_handler.setup_trading_environment(symbol, self.platform_params['leverage'])
                
                # ETAPA 2: Criar o dicionário de parâmetros com os nomes corretos
                order_params = {
                    'stopLossPrice': stop_loss_price,
                    'takeProfitPrice': take_profit_price
                }
                
                # ETAPA 3: Enviar a ordem
                await self.execution_handler.place_order(
                    symbol, 
                    side, 
                    size, 
                    'market', 
                    current_price, 
                    params=order_params
                )
                self.state_manager.set_in_position()