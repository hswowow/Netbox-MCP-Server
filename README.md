# NetBox MCP Server

A Model Context Protocol (MCP) server that provides seamless access to NetBox DCIM and IPAM data through a standardized interface. This server enables AI models and applications to interact with NetBox infrastructure data using natural language queries and structured API calls.

## 🌟 Features

- **🔧 Comprehensive Tools**: Query devices, sites, IP addresses, interfaces, and cables
- **🔌 Advanced Cable Tracing**: Bidirectional search and tree-based network topology discovery
- **📚 Cached Resources**: Fast access to device types, roles, manufacturers, and sites
- **💬 AI Prompts**: Pre-built prompts for network analysis and troubleshooting
- **🔒 Secure**: Environment variable configuration and proper error handling
- **📊 Monitoring**: Comprehensive logging and resource caching

## 🚀 Quick Start

### Prerequisites

- Python 3.10+ (3.10, 3.11, or 3.12)
- NetBox instance with API access
- Virtual environment (recommended)
- uv package manager (recommended for faster installation)

### 1. Clone the Repository

```bash
git clone https://github.com/hswowow/Netbox-MCP-Server
cd Netbox-MCP-Server
```

### 2. Set Up Python Environment

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh

uv sync
```

### 3. Configure Environment

Create a `.env` file with your NetBox credentials:

```bash
# NetBox Configuration
NETBOX_URL=https://your-netbox-instance.com
NETBOX_API_TOKEN=your_netbox_api_token_here

# MCP Server Configuration (optional)
MCP_TRANSPORT=streamable-http
MCP_HOST=localhost
MCP_PORT=8000

NETBOX_RESOURCE_UPDATE_INTERVAL_HOURS=24
```

### 4. Run the Server

#### Installing in Claude-Desktop/Cursor (STDIO)
```bash
"netbox-mcp": {
      "command": "/path/to/uv",
      "args": [
        "run",
        "--directory", "/path/to/Netbox-MCP-Server",
        "--with",
        "fastmcp",
        "fastmcp",
        "run",
        "/path/to/src/main.py"
      ],
      "env": {
        "NETBOX_URL": "https://your-netbox.com/",
        "NETBOX_TOKEN": "API_TOKEN",
        "NETBOX_RESOURCE_UPDATE_INTERVAL_HOURS": "24"
      },
      "transport": "stdio",
      "type": null,
      "cwd": null,
      "timeout": null,
      "description": null,
      "icon": null,
      "authentication": null,
      "capabilities": {
        "prompts": {
          "listChanged": true
        }
      }
    }
```

#### Dev
```bash
uv run fastmcp dev src/main.py 
```

#### Run
```bash
uv run fastmcp run src/main.py 
```

The server will start and be available for MCP connections.


## 🔧 Available Tools

### Device Management
- **`get_devices`**: Retrieve devices with filtering options

### Site Management  
- **`get_sites`**: Retrieve all sites

### IP Address Management
- **`get_ip_addresses`**: Query IP addresses with filtering
- **`get_ip_prefixes`**: Query IP prefixes with filtering
- **`get_ip_ranges`**: Query IP ranges with filtering
- **`get_vrfs`**: Query VRFs (Virtual Routing and Forwarding)
- **`get_vlans`**: Query VLANs with filtering

### Interface Management
- **`get_interfaces`**: Query network interfaces
- **`get_interfaces_by_vlan`**: Filter interfaces by PVID (untagged VLAN) across all devices or a specific device
- **`get_front_ports`**: Query front ports from patch panels and modular devices
- **`get_rear_ports`**: Query rear ports from patch panels and modular devices

### Cable Tracing
- **`get_cable`**: Get detailed cable information
- **`trace_devices_connection`**: Bidirectional search between devices
- **`trace_from_interface`**: Tree search from specific interface

### Cached Resources & Tools
- **`get_cached_resources`**: Access cached NetBox resources (sites, device types, roles, manufacturers)
- **`get_resource_summary`**: Get summary of cached resources
- **`get_available_prompts`**: Get available AI prompts for network analysis

### AI Prompts
- **`TraceNetworkPath`**: Comprehensive network path tracing between devices
- **`DeviceInterfaces`**: Device interface analysis and connectivity assessment
- **`SiteNetworkInfrastructure`**: Site-based network infrastructure analysis
- **`PatchPanelAnalysis`**: Patch panel and cable management analysis

### Static Resources
- **`netbox://sites`**: Cached site information
- **`netbox://device-types`**: Cached device type information
- **`netbox://device-roles`**: Cached device role information
- **`netbox://manufacturers`**: Cached manufacturer information


## 📁 Project Structure

```
netbox-mcp/
├── src/
│   ├── main.py              # MCP server entry point
│   ├── tools/               # MCP tool implementations
│   │   ├── cables.py        # Cable tracing tools
│   │   ├── devices.py       # Device management tools
│   │   ├── interfaces.py    # Interface tools
│   │   ├── ipam.py          # IP address management
│   │   └── sites.py         # Site management tools
│   └── prompts/
│       └── prompts.py       # AI prompts and guidance
├── resources/               # Cached NetBox resources
├── requirements.txt         # Python dependencies (pip)
├── pyproject.toml          # Project configuration (uv/pip)
├── uv.lock                 # Lock file for uv
├── .env.example            # Environment configuration template
└── README.md               # This file
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NETBOX_URL` | NetBox instance URL | Required |
| `NETBOX_API_TOKEN` | NetBox API token | Required |
| `MCP_TRANSPORT` | MCP transport protocol | `streamable-http` |
| `MCP_HOST` | Server host binding | `localhost` |
| `MCP_PORT` | Server port | `8000` |
| `NETBOX_RESOURCE_UPDATE_INTERVAL_HOURS` | Resource cache update interval (hours) for recurring updates | `24` |

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastMCP](https://github.com/jlowin/fastmcp) - The MCP framework powering this server
- [pynetbox](https://github.com/netbox-community/pynetbox) - NetBox API client library
- [NetBox](https://netbox.dev/) - The network documentation and IPAM platform
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer and resolver

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/hswowow/Netbox-MCP-Server/issues) section
2. Create a new issue with detailed information
3. Include relevant logs and configuration details

---

**Made with ❤️ for the NetBox and network automation community**
