# MCP Inspector Setup Guide

MCP Inspector is a debugging and testing tool for MCP (Model Context Protocol) servers. Here's how to install and use it with your mcp-market-data-server.

## Installation Steps

### Option 1: Using npm (Recommended)

1. **Install MCP Inspector globally:**
```bash
npm install -g @modelcontextprotocol/inspector
```

2. **Verify installation:**
```bash
mcp-inspector --version
```

### Option 2: Using npx (No installation needed)

You can run MCP Inspector directly without installing:
```bash
npx @modelcontextprotocol/inspector
```

## Using MCP Inspector with Your Server

### 1. Start your MCP server

First, make sure your mcp-market-data-server is running:
```bash
cd /Users/sayantbh/PycharmProjects/mcp-market-data-server
python -m src.server
```

### 2. Launch MCP Inspector

In a new terminal, run:
```bash
mcp-inspector
```

This will open the MCP Inspector in your default browser (usually at http://localhost:5173).

### 3. Connect to Your Server

In the MCP Inspector interface:

1. Click on "Add Server"
2. Enter the connection details:
   - **Name**: Market Data Server
   - **Command**: `python`
   - **Arguments**: `-m src.server`
   - **Working Directory**: `/Users/sayantbh/PycharmProjects/mcp-market-data-server`

3. Click "Connect"

### 4. Test Your Tools

Once connected, you'll see your three tools:
- `financial_volume_profile`
- `financial_technical_analysis`
- `financial_technical_zones`

You can test each tool by:
1. Clicking on the tool name
2. Entering a stock symbol (e.g., "AAPL" or "SPY")
3. Clicking "Execute"

## Alternative: Using MCP CLI

You can also test your server using the MCP CLI:

```bash
# Install MCP CLI
npm install -g @modelcontextprotocol/cli

# Test a tool
mcp call python -m src.server financial_volume_profile '{"symbol": "AAPL"}'
```

## Troubleshooting

### If MCP Inspector doesn't connect:

1. **Check Python path**: Make sure `python` command works in your terminal
   ```bash
   which python
   ```

2. **Check server startup**: Run the server manually to see any errors
   ```bash
   cd /Users/sayantbh/PycharmProjects/mcp-market-data-server
   python -m src.server
   ```

3. **Check dependencies**: Ensure all requirements are installed
   ```bash
   pip install -r requirements.txt
   ```

### If you get API key errors:

Make sure your Twelve Data API key is properly set up:
```bash
# Check if the API key file exists
cat /etc/twelve_data_api_key.txt
```

If not, create it:
```bash
sudo echo "YOUR_API_KEY_HERE" > /etc/twelve_data_api_key.txt
sudo chmod 600 /etc/twelve_data_api_key.txt
```

## Example Test Cases

Here are some symbols you can test with:

1. **US Stocks**: AAPL, MSFT, GOOGL, AMZN
2. **ETFs**: SPY, QQQ, IWM
3. **Index Futures**: ES, NQ (if supported by your API plan)

## Additional Resources

- [MCP Documentation](https://modelcontextprotocol.org)
- [MCP Inspector GitHub](https://github.com/modelcontextprotocol/inspector)
- [FastMCP Documentation](https://github.com/modelcontextprotocol/fastmcp)
