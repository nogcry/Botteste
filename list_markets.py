
import asyncio
import ccxt.async_support as ccxt
import os
from dotenv import load_dotenv

async def main():
    """
    Conecta-se à Hyperliquid e lista todos os mercados disponíveis para encontrar
    símbolos válidos para as estratégias.
    """
    load_dotenv()
    
    wallet_address = os.getenv("HYPERLIQUID_WALLET_ADDRESS")
    private_key = os.getenv("HYPERLIQUID_PRIVATE_KEY")

    if not wallet_address or not private_key:
        print("Erro: As variáveis de ambiente HYPERLIQUID_WALLET_ADDRESS e HYPERLIQUID_PRIVATE_KEY não estão definidas.")
        print("Por favor, configure-as no arquivo .env")
        return

    exchange = ccxt.hyperliquid({
        "walletAddress": wallet_address,
        "privateKey": private_key,
    })

    try:
        # Carrega os mercados da exchange
        markets = await exchange.load_markets()
        
        print("==================================================")
        print("Mercados Disponíveis na Hyperliquid (via CCXT)")
        print("==================================================")
        
        # Imprime os símbolos de cada mercado
        for symbol in markets:
            print(symbol)
            
        print("\nTotal de mercados encontrados:", len(markets))

    except Exception as e:
        print(f"Ocorreu um erro ao buscar os mercados: {e}")
    finally:
        # É crucial fechar a conexão
        await exchange.close()

if __name__ == "__main__":
    asyncio.run(main())
