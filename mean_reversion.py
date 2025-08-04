# strategies/mean_reversion.py

import logging
import pandas_ta as ta
from .base_strategy import BaseStrategy

logger = logging.getLogger("MeanReversionStrategy")

class MeanReversionStrategy(BaseStrategy):
    """Estratégia 4: Reversão à Média com Bandas de Bollinger e IFR (VERSÃO COM LOGS MELHORADOS)."""

    async def process_tick(self):
        symbol = self.platform_params["target_symbol"]
        
        if self.state_manager.state == "IN_POSITION":
            # Adicionado log para clareza quando já estiver em uma posição
            logger.info("Já em posição. Aguardando saída antes de avaliar novas entradas.")
            return

        candles = await self.data_handler.get_candles(symbol, '5m', 100)
        if candles is None or len(candles) < self.params['bollinger_length']:
            logger.warning("Dados de candles insuficientes para calcular indicadores.")
            return

        # Calcular indicadores
        candles.ta.bbands(length=self.params['bollinger_length'], std=self.params['bollinger_std'], append=True)
        candles.ta.rsi(length=self.params['rsi_length'], append=True)
        candles.ta.atr(length=14, append=True)

        last_candle = candles.iloc[-1]
        current_price = await self.data_handler.get_current_price(symbol)
        
        if current_price is None:
            return

        # --- MELHORIA DE LOGGING ---
        # Extrair valores dos indicadores para logar
        lower_band = last_candle[f'BBL_{self.params["bollinger_length"]}_{self.params["bollinger_std"]}']
        middle_band = last_candle[f'BBM_{self.params["bollinger_length"]}_{self.params["bollinger_std"]}']
        upper_band = last_candle[f'BBU_{self.params["bollinger_length"]}_{self.params["bollinger_std"]}']
        rsi = last_candle[f'RSI_{self.params["rsi_length"]}']

        # Logar o estado atual do mercado a cada ciclo
        logger.info(
            f"Analisando {symbol}: Preço={current_price:.2f} | "
            f"Banda Inf.={lower_band:.2f} | Banda Sup.={upper_band:.2f} | RSI={rsi:.2f}"
        )
        
        signal = 0
        # Sinal de COMPRA (Preço abaixo da banda inferior + RSI sobrevendido)
        if current_price < lower_band and rsi < self.params['rsi_oversold']:
            signal = 1
            logger.info(f"SINAL DE COMPRA (Reversão) DETECTADO para {symbol}")
        
        # Sinal de VENDA (Preço acima da banda superior + RSI sobrecomprado)
        elif current_price > upper_band and rsi > self.params['rsi_overbought']:
            signal = -1
            logger.info(f"SINAL DE VENDA (Reversão) DETECTADO para {symbol}")
        
        else:
            # Log quando nenhuma condição for atendida
            logger.info("Condições de entrada não atendidas. Aguardando...")

        if signal != 0:
            side = 'buy' if signal == 1 else 'sell'
            atr = last_candle['ATRr_14']
            stop_loss_price = current_price - (atr * self.params['stop_loss_atr_multiplier']) if side == 'buy' else current_price + (atr * self.params['stop_loss_atr_multiplier'])
            take_profit_price = middle_band # Alvo na média

            size = await self.risk_manager.calculate_position_size(
                self.params['risk_per_trade'], current_price, stop_loss_price
            )

            if size:
                await self.execution_handler.setup_trading_environment(symbol, self.platform_params['leverage'])
                order_params = {'stopLoss': {'triggerPrice': stop_loss_price}, 'takeProfit': {'triggerPrice': take_profit_price}}
                await self.execution_handler.place_order(symbol, 'market', side, size, params=order_params)
                self.state_manager.set_in_position()