# MCP Market Data Server

A FastMCP server providing financial market data analysis tools for LLM agents. This server offers three main tools for technical analysis:

1. **Volume Profile Analysis** - Identifies key support/resistance levels based on volume distribution
2. **Technical Analysis** - Provides standard indicators (SMA, RSI, MACD, ATR, VWAP, Ichimoku)
3. **Technical Zones** - Calculates high-probability price zones for entry/exit decisions

## Features

- Multi-timeframe analysis (1m, 5m, 1d)
- Volume dynamics and momentum indicators
- Fibonacci retracement/extension levels
- Previous day high/low levels
- ATR-based volatility zones
- Trend strength analysis
- Divergence detection

## Prerequisites

- Python 3.8+
- Twelve Data API key (free tier available at https://twelvedata.com)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd mcp-market-data-server
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your Twelve Data API key:
```bash
# Create the API key file
sudo echo "YOUR_TWELVE_DATA_API_KEY" > /etc/twelve_data_api_key.txt
sudo chmod 600 /etc/twelve_data_api_key.txt
```

## Running the Server

Start the MCP server:
```bash
python -m src.server
```

The server will be available for MCP client connections.

## Available Tools

### 1. financial_volume_profile

Retrieves Volume Profile structure for multiple timeframes.

**Parameters:**
- `symbol` (string): Stock ticker symbol (e.g., "AAPL", "SPY")

**Returns:**
- Point of Control (POC)
- Value Area High (VAH) and Low (VAL)
- High Volume Nodes (HVN) and Low Volume Nodes (LVN)
- Volume dynamics analysis

### 2. financial_technical_analysis

Retrieves standard technical indicators across timeframes.

**Parameters:**
- `symbol` (string): Stock ticker symbol

**Returns:**
- Moving averages (SMA 50, EMA 20)
- Oscillators (RSI, Stochastic, MACD)
- Volatility (ATR)
- VWAP
- Ichimoku Cloud
- Volume indicators (OBV, CMF)
- Trend strength analysis
- Divergence detection

### 3. financial_technical_zones

Identifies support/resistance zones using multiple methodologies.


**Parameters:**
- `symbol` (string): Stock ticker symbol

**Returns:**
- Volume Profile zones (POC, VAH, VAL)
- Fibonacci levels
- ATR-based targets
- Previous day high/low
- Zone classifications (SUPPORT, RESISTANCE, NEUTRAL, TARGET)


