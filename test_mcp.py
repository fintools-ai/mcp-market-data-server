#!/usr/bin/env python3
"""
Simple MCP Server Test Script
"""

import asyncio
import json

async def test_mcp_server():
    """Test the MCP server by spawning it and calling tools"""

    print("🚀 Starting MCP server test...")

    # Start the server process
    try:
        process = await asyncio.create_subprocess_exec(
            "mcp-market-data-server",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            limit=100 * 1024 * 1024  # 100MB limit
        )
        print("✅ Server started")
    except FileNotFoundError:
        print("❌ mcp-market-data-server command not found")
        return

    try:
        # Initialize MCP connection
        print("🔗 Initializing connection...")

        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }

        # Send initialize request
        process.stdin.write((json.dumps(init_request) + "\n").encode())
        await process.stdin.drain()

        # Read response
        response = await process.stdout.readline()
        init_response = json.loads(response.decode().strip())

        if "result" in init_response:
            print("✅ Connection initialized")
        else:
            print(f"❌ Initialize failed: {init_response}")
            return

        # Send initialized notification
        init_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        process.stdin.write((json.dumps(init_notification) + "\n").encode())
        await process.stdin.drain()

        # List available tools
        print("📋 Getting available tools...")

        list_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }

        process.stdin.write((json.dumps(list_request) + "\n").encode())
        await process.stdin.drain()

        response = await process.stdout.readline()
        #print(response)
        tools_response = json.loads(response.decode().strip())

        if "result" in tools_response:
            tools = tools_response["result"]["tools"]
            print(f"✅ Found {len(tools)} tools:")
            for tool in tools:
                print(f"   - {tool['name']}: {tool.get('description', 'No description')[:60]}...")
        else:
            print(f"❌ Failed to list tools: {tools_response}")
            return

        # Test each tool with AAPL
        test_symbol = "SPY"
        print(f"\n🧪 Testing tools with {test_symbol}...")

        for i, tool in enumerate(tools):
            tool_name = tool["name"]
            print(f"\n📊 Testing {tool_name}...")

            # Call the tool
            tool_request = {
                "jsonrpc": "2.0",
                "id": 3 + i,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": {"symbol": test_symbol}
                }
            }

            process.stdin.write((json.dumps(tool_request) + "\n").encode())
            await process.stdin.drain()

            # Read response with timeout
            try:
                response = await asyncio.wait_for(process.stdout.readline(), timeout=30)
                tool_response = json.loads(response.decode().strip())

                print(tool_response)

            except asyncio.TimeoutError:
                print(f"   ⏰ {tool_name}: Timed out")
            except json.JSONDecodeError:
                print(f"   ❌ {tool_name}: Invalid JSON response")
            except Exception as e:
                print(f"   ❌ {tool_name}: Error - {e}")

        print(f"\n🎉 Test completed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")

    finally:
        # Clean shutdown
        try:
            process.stdin.close()
            await process.stdin.wait_closed()
            await asyncio.wait_for(process.wait(), timeout=5)
            print("✅ Server stopped")
        except:
            process.terminate()
            await process.wait()
            print("🛑 Server terminated")


if __name__ == "__main__":
    asyncio.run(test_mcp_server())