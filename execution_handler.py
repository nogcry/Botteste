import logging
import ccxt.async_support as ccxt

logger = logging.getLogger(__name__)

class ExecutionHandler:
    def __init__(self, platform_params):
        self.exchange = None
        self.wallet_address = platform_params["wallet_address"]
        self.private_key = platform_params["private_key"]

    async def initialize(self):
        """Inicializa a conexão seguindo o padrão comprovado."""
        if not self.wallet_address or not self.private_key:
            raise ValueError("Credenciais da carteira não configuradas no arquivo .env.")
        try:
            self.exchange = ccxt.hyperliquid({
                "walletAddress": self.wallet_address,
                "privateKey": self.private_key,
                "enableRateLimit": True,
                "options": {'adjustForTimeDifference': True}
            })
            await self.exchange.load_markets()
            logger.info("Handler de Execução conectado e sincronizado.")
        except Exception as e:
            logger.error(f"Falha ao inicializar o ExecutionHandler: {e}", exc_info=True)
            raise

    async def setup_trading_environment(self, symbol: str, leverage: int):
        """Define a alavancagem para um símbolo, como exigido pela API."""
        try:
            # O modo de margem na Hyperliquid é 'isolated' por padrão e não pode ser alterado por par
            await self.exchange.set_leverage(leverage, symbol)
            logger.info(f"Alavancagem de {leverage}x definida para {symbol}.")
        except Exception as e:
            logger.warning(f"Aviso durante a configuração de ambiente para {symbol}: {e}")

    async def place_order(self, symbol: str, side: str, amount: float, order_type: str = 'market', price: float = None, params: dict = None):
        """Envia uma ordem para a exchange com a estrutura de parâmetros correta."""
        try:
            logger.info(f"Enviando ordem: {side} {amount} {symbol} @ {price} com params: {params}")
            order = await self.exchange.create_order(symbol, order_type, side, amount, price, params)
            logger.info(f"Ordem enviada com sucesso: ID {order.get('id')}")
            return order
        except Exception as e:
            logger.error(f"Erro ao enviar ordem para {symbol}: {e}", exc_info=True)
            return None

    async def get_balance_usd(self) -> float:
        """Busca o balanço total em USDC."""
        try:
            balance = await self.exchange.fetch_balance()
            # A estrutura de balanço do CCXT para Hyperliquid pode variar
            return float(balance.get('USDC', {}).get('total', 0.0))
        except Exception as e:
            logger.error(f"Erro ao buscar balanço: {e}")
            return 0.0

    async def get_open_positions(self):
        """Busca posições abertas."""
        try:
            positions = await self.exchange.fetch_positions()
            return [p for p in positions if float(p.get('contracts', 0)) != 0]
        except Exception as e:
            logger.error(f"Erro ao buscar posições: {e}")
            return []

    async def close_connection(self):
        """Encerra a conexão com a exchange de forma limpa."""
        if self.exchange:
            await self.exchange.close()
            logger.info("Conexão com a exchange encerrada.")