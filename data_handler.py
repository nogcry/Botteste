import logging
import pandas as pd
from handlers.execution_handler import ExecutionHandler

logger = logging.getLogger(__name__)

class DataHandler:
    def __init__(self, platform_params):
        self.execution_handler = ExecutionHandler(platform_params)

    async def get_candles(self, symbol: str, timeframe: str = '1m', limit: int = 100) -> pd.DataFrame | None:
        """Busca dados históricos de velas (candles) de forma assíncrona."""
        try:
            ohlcv = await self.execution_handler.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            if not ohlcv:
                logger.warning(f"Não foram retornados dados de candles para {symbol}.")
                return None
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            logger.error(f"Erro ao buscar candles para {symbol}: {e}", exc_info=True)
            return None
            
    async def get_current_price(self, symbol: str) -> float | None:
        """
        Busca o preço de mercado mais recente calculando o mid-price do livro de ordens.
        Esta é a correção para o erro 'fetchTicker() not supported'.
        """
        try:
            # Busca o topo do livro de ordens (melhor compra e melhor venda)
            order_book = await self.execution_handler.exchange.fetch_order_book(symbol, limit=1)
            
            # Garante que o livro de ordens e os lances existem
            if order_book and order_book.get('bids') and order_book.get('asks'):
                best_bid = order_book['bids'][0][0]
                best_ask = order_book['asks'][0][0]
                
                # Calcula o mid-price e o retorna
                mid_price = (best_bid + best_ask) / 2
                return mid_price
                
            logger.warning(f"Não foi possível obter o livro de ordens para {symbol}.")
            return None
        except Exception as e:
            # Log do erro específico para diagnóstico
            logger.error(f"Erro ao buscar o preço atual de {symbol}: {e}", exc_info=True)
            return None