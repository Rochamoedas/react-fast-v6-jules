# src/domain/aggregates/financials.py
from pydantic import BaseModel
from src.domain.entities.production import Production
from src.domain.entities.oil_price import OilPrice
from src.domain.entities.exchange_rate import ExchangeRate

class Financials(BaseModel):
    """
    Represents financial calculations based on production, oil price, and exchange rates.
    """
    production: Production
    oil_price: OilPrice
    exchange_rate: ExchangeRate

    def calculate_oil_revenue_usd(self) -> float:
        """
        Calculates the oil revenue in USD.
        Revenue = Oil Production (barrels) * Oil Price (USD/barrel)
        """
        if self.production and self.oil_price:
            return self.production.oil_prod * self.oil_price.price
        return 0.0

    def calculate_oil_revenue_brl(self) -> float:
        """
        Calculates the oil revenue in BRL.
        Revenue = Oil Production (barrels) * Oil Price (USD/barrel) * Exchange Rate (BRL/USD)
        """
        if self.production and self.oil_price and self.exchange_rate:
            return self.production.oil_prod * self.oil_price.price * self.exchange_rate.rate
        return 0.0

    class Config:
        # Pydantic configuration
        arbitrary_types_allowed = True
