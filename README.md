# MCP Market Data Server

<div align="center">

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastMCP](https://img.shields.io/badge/FastMCP-Compatible-green.svg)](https://github.com/jlowin/fastmcp)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Twelve Data](https://img.shields.io/badge/API-Twelve%20Data-blue.svg)](https://twelvedata.com/)

*A powerful FastMCP server providing comprehensive financial market data analysis tools for LLM agents and trading applications.*

[🚀 Quick Start](#quick-start) • [📊 Features](#features) • [🛠️ Installation](#installation) • [📖 Documentation](#documentation) • [🤝 Contributing](#contributing)

</div>

---

## 🎯 Overview

The **MCP Market Data Server** is a production-ready financial analysis server implementing the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/). It provides four powerful analysis tools that deliver institutional-grade market insights:

- **🎚️ Volume Profile Analysis** - Identify key support/resistance levels based on volume distribution
- **📈 Technical Analysis** - Access 15+ standard indicators with multi-timeframe analysis
- **🎯 Technical Zones** - Calculate high-probability price zones for precise entry/exit decisions
- **📊 ORB Analysis** - Opening Range Breakout levels with multi-period analysis for intraday/0DTE trading

Perfect for algorithmic trading, quantitative analysis, and AI-powered trading agents.

## ✨ Features

### 📊 **Multi-Timeframe Analysis**
- ⏱️ **1-minute**: Scalping and micro-movements
- ⏱️ **5-minute**: Intraday swing trading
- ⏱️ **1-day**: Position trading and trend analysis

### 📈 **Volume Profile Intelligence**
- 🎯 Point of Control (POC) identification
- 📊 Value Area High/Low (VAH/VAL) calculations
- 🔥 High/Low Volume Node detection
- 💹 Volume dynamics and momentum analysis
- 📈 Upside probability assessment

### 🔧 **Technical Indicators Suite**
- **Moving Averages**: SMA (20, 50, 200), EMA (20), VWAP
- **Momentum**: RSI, MACD, Stochastic Oscillator
- **Volatility**: ATR (Average True Range)
- **Volume**: OBV, CMF, Volume Rate of Change
- **Advanced**: Ichimoku Cloud, Trend Strength Analysis
- **Patterns**: Divergence Detection

### 🎯 **Smart Zone Analysis**
- 📐 Fibonacci retracement/extension levels
- 📅 Previous day high/low levels
- 📊 ATR-based volatility zones
- 🎚️ Volume Profile derived zones
- 🎨 Zone strength classification

### 📊 **Opening Range Breakout (ORB)**
- ⏱️ Multi-period analysis (5, 15, 30 minutes)
- 🎯 Breakout confirmation with volume
- 📈 Extension targets (0.5x, 1x, 1.5x, 2x)
- 🔍 ORB squeeze detection
- 📡 Trading bias analysis

### 🚀 **Enterprise Features**
- ⚡ Async/await architecture for high performance
- 🔒 Secure API key management
- 🏗️ Modular, extensible design
- 📝 Comprehensive logging and error handling
- 🧪 Full test coverage
- 📋 Type hints throughout



---

## 📖 API Reference

### 🎚️ `financial_volume_profile`

Analyzes volume distribution across price levels to identify key trading zones.

**Request:**
```json
{
  "tool": "financial_volume_profile", 
  "symbol": "AAPL"
}
```

**Response:**
```json
{
  "symbol": "AAPL",
  "status": "success",
  "timeframe_volume_profile": {
    "5m": {
      "volume_profile_structure": {
        "point_of_control": 150.25,
        "value_area_high": 151.80,
        "value_area_low": 149.10,
        "high_volume_nodes": [...],
        "low_volume_nodes": [...]
      },
      "volume_dynamics": {
        "supports_continued_upside": true,
        "volume_supports_upside_probability": 75.5,
        "volume_trend": "increasing",
        "volume_bias": "bullish"
      }
    }
  },
  "consolidated_analysis": {
    "supports_continued_upside": true,
    "confidence": "high"
  }
}
```

### 📈 `financial_technical_analysis`

Provides comprehensive technical indicators across multiple timeframes.

**Request:**
```json
{
  "tool": "financial_technical_analysis",
  "symbol": "MSFT"
}
```

**Response:**
```json
{
  "symbol": "MSFT", 
  "status": "success",
  "timeframe_indicators": {
    "1d": {
      "indicators": {
        "current_price": 380.50,
        "sma_20": 375.20,
        "sma_50": 370.15,
        "rsi": 65.2,
        "macd": {
          "macd": 2.34,
          "signal": 1.98,
          "histogram": 0.36
        },
        "atr": 8.45,
        "vwap": 379.80
      },
      "trend_analysis": {
        "trend": "uptrend",
        "strength": "moderate"
      }
    }
  }
}
```

### 🎯 `financial_technical_zones`

Identifies precise support/resistance zones using multiple methodologies.

**Request:**
```json
{
  "tool": "financial_technical_zones",
  "symbol": "GOOGL"  
}
```

**Response:**
```json
{
  "symbol": "GOOGL",
  "status": "success", 
  "timeframe_zones": {
    "5m": {
      "zones": [
        {
          "type": "SUPPORT",
          "level": 142.50,
          "strength": "strong",
          "source": "Volume Profile POC",
          "confidence": 85
        },
        {
          "type": "RESISTANCE", 
          "level": 145.80,
          "strength": "moderate",
          "source": "Previous Day High",
          "confidence": 70
        }
      ]
    }
  }
}
```

### 📊 `analyze_open_interest`

Analyzes Opening Range Breakout patterns for intraday and 0DTE trading strategies.

**Request:**
```json
{
  "tool": "analyze_open_interest",
  "symbol": "SPY"
}
```

**Response:**
```json
{
  "symbol": "SPY",
  "status": "success",
  "timestamp": "2024-03-15T14:30:00Z",
  "market_session": "regular_hours",
  "current_price": 425.50,
  "orb_analysis": {
    "5min": {
      "orb_high": 424.75,
      "orb_low": 424.25,
      "orb_range": 0.50,
      "position": "above_range",
      "breakout_confirmed": true,
      "breakout_type": "bullish",
      "volume_analysis": {
        "volume_ratio_vs_day_avg": 1.35,
        "high_volume": true
      },
      "targets": {
        "bull_1x": 425.25,
        "bear_1x": 423.75
      },
      "targets_hit": ["bull_0.5x", "bull_1x"]
    }
  },
  "trading_bias": {
    "bias": "bullish",
    "confidence": "high",
    "strength_factors": [
      "5min bullish breakout confirmed",
      "5min high volume above range"
    ]
  },
  "orb_squeeze": {
    "squeeze_detected": false,
    "compression_ratio": 0.95
  }
}
```

---

## 🎯 Usage Examples

### Basic Analysis
```python
# Query: "Show me AAPL volume profile analysis"
# Response: Complete volume distribution with POC at $150.25
```

### Multi-Tool Analysis
```python
# Query: "Analyze TSLA using all technical tools and provide trading recommendation"
# Response: Comprehensive analysis with volume profile, indicators, and key zones
```

### Specific Scenarios
```python
# Scalping Setup
# Query: "Find 1-minute support levels for SPY for quick trades"

# Swing Trading
# Query: "Identify 5-minute resistance zones for NVDA breakout trading"

# Position Trading  
# Query: "Show daily technical analysis for QQQ trend confirmation"

# 0DTE Trading
# Query: "Analyze SPY ORB for 0DTE entry - is breakout confirmed?"
```

---
