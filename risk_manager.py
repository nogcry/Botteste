# Cálculo de risco e tamanho de posição
import logging

logger = logging.getLogger(__name__)

class RiskManager:
    def __init__(self, execution_handler, platform_params):
        self.execution_handler = execution_handler
        self.platform_params = platform_params

    async def calculate_position_size(self, risk_per_trade: float, entry_price: float, stop_loss_price: float) -> float | None:
        """Calcula o tamanho da posição com base no risco por trade (López de Prado)."""
        balance = await self.execution_handler.get_balance_usd()
        if balance <= 0:
            logger.warning("Balanço insuficiente para calcular o tamanho da posição.")
            return None

        risk_amount_usd = balance * risk_per_trade
        price_risk_per_unit = abs(entry_price - stop_loss_price)

        if price_risk_per_unit == 0:
            logger.warning("Risco por unidade é zero. Não é possível calcular o tamanho da posição.")
            return None

        position_size_asset = risk_amount_usd / price_risk_per_unit
        
        # Validação contra o valor mínimo de entrada da plataforma
        position_value_usd = position_size_asset * entry_price
        if position_value_usd < self.platform_params["min_entry_value_usd"]:
            logger.warning(f"Tamanho da posição calculado ({position_value_usd:.2f} USD) é menor que o mínimo de {self.platform_params['min_entry_value_usd']} USD.")
            return None
            
        logger.info(f"Cálculo de Posição: Balanço={balance:.2f} USD, Risco={risk_per_trade*100}%, Tamanho={position_size_asset:.4f} Ativo")
        return position_size_asset