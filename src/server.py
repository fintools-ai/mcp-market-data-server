from fastmcp import FastMCP
import os, sys
import logging
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))

# Import tool implementations
from src.services.tools.volume_profile_tool import financial_volume_profile
from src.services.tools.technical_analysis_tool import financial_technical_analysis
from src.services.tools.technical_zones_tool import financial_technical_zones
from src.services.tools.orb_tool import financial_orb_analysis

logging.basicConfig(
    level=getattr(logging, "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

# Create MCP server instance
mcp = FastMCP("mcp-market-data-server")

# Register tools with MCP server
@mcp.tool()
async def financial_volume_profile_tool(symbol: str):
    """
    Retrieves Volume Profile structure (POC, VAH, VAL, Nodes) for default granular timeframes (1m, 5m).
    Useful for identifying key support and resistance levels based on volume distribution.
    """
    try:
        return await financial_volume_profile(symbol)
    except Exception as err:
        logger.error("failed to start financial_volume_profile_tool, error :", err )
        return None


@mcp.tool()
async def financial_technical_analysis_tool(symbol: str):
    """
    Retrieves standard Technical Analysis indicator values (e.g., SMA, RSI, MACD, ATR, VWAP) for default granular timeframes (1m, 5m, 1d).
    Useful for assessing trend, momentum, and volatility.
    """
    return await financial_technical_analysis(symbol)

@mcp.tool()
async def financial_technical_zones_tool(symbol: str):
    """
    Retrieves calculated high-probability support and resistance price zones derived from methods like Volume Profile and volatility extensions for default granular timeframes (1m, 5m).
    Useful for identifying precise entry, exit, and stop-loss levels.
    """
    return await financial_technical_zones(symbol)

@mcp.tool()
async def financial_orb_analysis(symbol: str):
    """
    Analyzes Opening Range Breakout (ORB) levels for multiple timeframes (5, 15, 30 minutes).
    Provides ORB high/low, breakout confirmation, volume analysis, and extension targets.
    Essential for 0DTE and intraday trading strategies.
    """
    return await financial_orb_analysis(symbol)


def main():
    mcp.run()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        sys.exit(1)
