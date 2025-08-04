# strategies/trend_following.py

import logging
import pandas as pd
import pandas_ta as ta
import joblib
from pathlib import Path
from .base_strategy import BaseStrategy

logger = logging.getLogger("MetaLabeledTrendStrategy")

# --- Caminho do Modelo de ML ---
# O script irá procurar pelo nosso modelo treinado na pasta de backtesting.
MODELS_PATH = Path(__file__).resolve().parent.parent / "backtesting/models"
MODEL_FILE = MODELS_PATH / "meta_label_filter.pkl"

class TrendFollowingStrategy(BaseStrategy):
    """
    Estratégia 3 (Final): Seguidor de Tendência com Filtro de Meta-Labeling de ML.
    """
    
    def __init__(self, platform_params: dict, strategy_params: dict, symbol: str):
        super().__init__(platform_params, strategy_params)
        self.symbol = symbol  # Ativo específico que esta instância irá operar
        # self.model = None
        # self.load_model()
        logger.info(f"Instância de TrendFollowingStrategy criada para o símbolo: {self.symbol}")

    def load_model(self):
        """Carrega o modelo de ML treinado no início."""
        try:
            self.model = joblib.load(MODEL_FILE)
            logger.info(f"Filtro de Machine Learning '{MODEL_FILE.name}' carregado com sucesso.")
        except FileNotFoundError:
            logger.error(f"ERRO CRÍTICO: Modelo '{MODEL_FILE}' não encontrado. A estratégia não pode funcionar sem o filtro.")
            self.model = None

    def get_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcula as mesmas features usadas para treinar o modelo."""
        # Feature 1: Volatilidade (ATR)
        df['volatility'] = df.ta.atr(length=14)
        
        # Feature 2: Momentum (RSI)
        df['momentum_rsi'] = df.ta.rsi(length=14)
        
        # Feature 3: Diferenciação Fracionária (requer a função)
        # Por simplicidade na execução ao vivo, vamos omitir a diferenciação fracionária
        # que é computacionalmente intensiva, e usar as outras duas features.
        # Em um sistema de produção avançado, essa função seria portada para cá.
        
        return df[['volatility', 'momentum_rsi']].dropna()


    async def process_tick(self):
        """Verifica sinais de tendência e os filtra com o modelo de ML."""
        if self.state_manager.state == "IN_POSITION": # or not self.model:
            return

        # O símbolo agora é um atributo da classe, definido no construtor
        symbol = self.symbol
        
        # 1. Obter dados e calcular sinais do modelo primário
        candles = await self.data_handler.get_candles(symbol, '5m', 150) # Pegamos mais candles para os cálculos
        if candles is None or len(candles) < self.params['ema_slow']:
            return

        candles.ta.ema(length=self.params['ema_fast'], append=True)
        candles.ta.ema(length=self.params['ema_slow'], append=True)

        last_candle = candles.iloc[-1]
        prev_candle = candles.iloc[-2]
        
        signal = 0
        if prev_candle[f'EMA_{self.params["ema_fast"]}'] < prev_candle[f'EMA_{self.params["ema_slow"]}'] and \
           last_candle[f'EMA_{self.params["ema_fast"]}'] > last_candle[f'EMA_{self.params["ema_slow"]}']:
            signal = 1
        elif prev_candle[f'EMA_{self.params["ema_fast"]}'] > prev_candle[f'EMA_{self.params["ema_slow"]}'] and \
             last_candle[f'EMA_{self.params["ema_fast"]}'] < last_candle[f'EMA_{self.params["ema_slow"]}']:
            signal = -1

        # 2. Se houver um sinal, executar o trade diretamente (filtro de ML desativado)
        if signal != 0:
            logger.info(f"Sinal de Cruzamento de Médias para {self.symbol}: {'COMPRA' if signal == 1 else 'VENDA'}")
            
            side = 'buy' if signal == 1 else 'sell'
            
            current_price = await self.data_handler.get_current_price(symbol)
            if not current_price: return

            # Usa ATR para definir stop loss e take profit dinâmicos
            candles.ta.atr(length=14, append=True)
            atr = candles.iloc[-1]['ATRr_14']
            
            stop_loss_price = current_price - (atr * self.params['stop_loss_atr_multiplier']) if side == 'buy' else current_price + (atr * self.params['stop_loss_atr_multiplier'])
            take_profit_price = current_price + (atr * self.params['take_profit_atr_multiplier']) if side == 'buy' else current_price - (atr * self.params['take_profit_atr_multiplier'])

            size = await self.risk_manager.calculate_position_size(
                self.params['risk_per_trade'], current_price, stop_loss_price
            )
            
            if size:
                await self.execution_handler.setup_trading_environment(symbol, self.platform_params['leverage'])
                order_params = {'stopLoss': {'triggerPrice': stop_loss_price}, 'takeProfit': {'triggerPrice': take_profit_price}}
                await self.execution_handler.place_order(symbol, 'market', side, size, params=order_params)
                self.state_manager.set_in_position()
