#!/usr/bin/env python3
"""
Overleaf MCP Server Entrypoint
Supports SSE (for Claude Web / Remote connections) and stdio (for Claude Desktop).
"""

import argparse
import sys
import os
from config import SERVER_HOST, SERVER_PORT, TRANSPORT, HEADLESS

def main():
    parser = argparse.ArgumentParser(description="Overleaf MCP Server for Claude")
    parser.add_argument(
        "--transport",
        choices=["sse", "stdio", "streamable-http"],
        default=TRANSPORT,
        help="MCP Transport protocol: 'sse' (default, for web/remote) or 'stdio' (Claude Desktop)"
    )
    parser.add_argument(
        "--host",
        default=SERVER_HOST,
        help="Host address for SSE server (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=SERVER_PORT,
        help="Port number for SSE server (default: 8000)"
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Run browser in visible mode (default is headless)"
    )

    args = parser.parse_args()

    # Apply headless flag if specified
    if args.no_headless:
        os.environ["OVERLEAF_HEADLESS"] = "false"

    # Import server after env flags
    from server import mcp, browser

    if args.no_headless:
        browser.headless = False

    print("=" * 60)
    print("🚀 Overleaf MCP Server starting...")
    print(f"📦 Transport : {args.transport}")
    if args.transport in ("sse", "streamable-http"):
        print(f"🌐 Host      : {args.host}")
        print(f"🔌 Port      : {args.port}")
        print(f"📡 SSE URL   : http://{args.host}:{args.port}/sse")
        print(f"💬 Messages  : http://{args.host}:{args.port}/messages/")
    print(f"🖥️  Headless  : {browser.headless}")
    print("=" * 60)

    try:
        from mcp.server.transport_security import TransportSecuritySettings
        # Allow requests from Cloudflare tunnels, ngrok, and cloud domains
        security_settings = TransportSecuritySettings(enable_dns_rebinding_protection=False)

        if args.transport == "stdio":
            mcp.run("stdio")
        elif args.transport == "sse":
            mcp.run("sse", host=args.host, port=args.port, transport_security=security_settings)
        elif args.transport == "streamable-http":
            mcp.run("streamable-http", host=args.host, port=args.port, transport_security=security_settings)
    except KeyboardInterrupt:
        print("\nShutting down Overleaf MCP Server...")
        sys.exit(0)

if __name__ == "__main__":
    main()
