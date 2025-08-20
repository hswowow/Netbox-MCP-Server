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
git clone https://github.com/your-username/netbox-mcp.git
cd netbox-mcp
```

### 2. Set Up Python Environment

#### Option 1: Using uv (recommended - faster)
```bash
# Install uv if not already installed
# macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell):
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or using pip:
pip install uv

# Create virtual environment and install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows
```

#### Option 2: Using pip (traditional)
```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

#### ARM64 (Apple Silicon) Notes
On ARM64 systems (Apple Silicon Macs), you may need to use `python3` explicitly:
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment with explicit python3
uv sync --python python3

# Or with pip
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### Python Version Requirements
- **Minimum**: Python 3.10
- **Recommended**: Python 3.11 or 3.12
- **Tested**: Python 3.10, 3.11, 3.12

The project uses modern Python features and requires Python 3.10 or higher for optimal performance and compatibility.

### Package Management

This project supports both **uv** and **pip** for dependency management:

- **uv** (recommended): Faster installation, better dependency resolution, lock file support
- **pip**: Traditional Python package manager, works with `requirements.txt`

The project includes both `pyproject.toml` (for uv) and `requirements.txt` (for pip) for maximum compatibility.

### FastMCP Integration

The project uses **FastMCP** for MCP server management:
- **Installation**: `fastmcp install` - Install server for system-wide use
- **Development**: `fastmcp dev` - Run with auto-reload for development
- **Production**: `fastmcp run` - Run in production mode

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
```

### 4. Run the Server

#### Using fastmcp (recommended)
```bash
# Install and run the MCP server
fastmcp install
fastmcp run

# Or run directly without installation
fastmcp run src/main.py
```

#### Using uv
```bash
# Run with uv (automatically uses the virtual environment)
uv run fastmcp run src/main.py

# Or activate the environment first, then run
source .venv/bin/activate
fastmcp run src/main.py
```

#### Using pip
```bash
# Activate environment and run
source .venv/bin/activate
fastmcp run src/main.py
```

The server will start and be available for MCP connections.


## 🔧 Available Tools

### Device Management
- **`get_devices`**: Retrieve devices with filtering options
- **`get_device_by_name`**: Get specific device information
- **`get_device_interfaces`**: List device interfaces

### Site Management  
- **`get_sites`**: Retrieve all sites
- **`get_site_devices`**: Get devices at a specific site

### IP Address Management
- **`get_ip_addresses`**: Query IP addresses with filtering
- **`get_available_ips`**: Find available IPs in a prefix

### Interface Management
- **`get_interfaces`**: Query network interfaces
- **`get_interface_connections`**: Get interface cable connections

### Cable Tracing
- **`get_cable`**: Get detailed cable information
- **`trace_devices_connection`**: Bidirectional search between devices
- **`trace_from_interface`**: Tree search from specific interface

### Resource Access
- **`get_device_types`**: Available device types
- **`get_device_roles`**: Device role categories
- **`get_manufacturers`**: Equipment manufacturers
- **`get_sites_cached`**: Cached site information

## 💬 AI Prompts

The server includes pre-built prompts for common network operations:

- **Cable Tracing Guidance**: Instructions for using different cable tracing methods
- **Network Analysis**: Prompts for device and connectivity analysis
- **Troubleshooting**: Common network troubleshooting workflows

## 📋 Integration Examples

### MCP Client Integration

```python
import mcp

# Connect to the NetBox MCP server
client = mcp.Client("http://localhost:8000")

# Query devices
devices = await client.call_tool("get_devices", {
    "site": "headquarters",
    "role": "switch"
})

# Trace cable connections
path = await client.call_tool("trace_devices_connection", {
    "source_device": "switch-01",
    "target_device": "server-02"
})
```

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
| `NETBOX_RESOURCE_UPDATE_INTERVAL_HOURS` | Resource cache update interval (hours) | `24` |

### Logging

- Application logs: `netbox_mcp_server.log`
- Log level controlled by Python logging configuration
- Structured logging for debugging and monitoring

## 🔒 Security

- Environment variable configuration for sensitive data
- API token-based NetBox authentication
- Proper error handling and logging
- No sensitive data in logs

## 🚀 Advanced Usage

### Cable Tracing Algorithms

The server implements two advanced cable tracing algorithms:

1. **Bidirectional Search** (`trace_devices_connection`):
   - Searches from both source and target devices simultaneously
   - Optimal for finding shortest paths between specific devices
   - Time complexity: O(b^(d/2)) where b is branching factor, d is depth

2. **Tree Search** (`trace_from_interface`):
   - Recursive exploration from a starting interface
   - Maps complete network topology from a point
   - Handles patch panels and complex interconnections

### Resource Caching

The server automatically caches NetBox resources for improved performance:
- Device types, roles, and manufacturers
- Site information
- Time-based cache refresh (configurable via `NETBOX_RESOURCE_UPDATE_INTERVAL_HOURS`)
- Automatic cache management with update cycle tracking

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Set up development environment:
   ```bash
   # Using uv (recommended)
   uv sync
   uv run fastmcp install
   uv run pre-commit install  # Install pre-commit hooks
   
   # Or using pip
   pip install -r requirements.txt
   pip install -e ".[dev]"    # Install development dependencies
   fastmcp install
   ```
4. Make your changes and run tests:
   ```bash
   # Using uv
   uv run fastmcp dev
   uv run pytest
   
   # Or using pip
   fastmcp dev
   pytest
   ```
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastMCP](https://github.com/jlowin/fastmcp) - The MCP framework powering this server
- [pynetbox](https://github.com/netbox-community/pynetbox) - NetBox API client library
- [NetBox](https://netbox.dev/) - The network documentation and IPAM platform
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer and resolver

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/your-username/netbox-mcp/issues) section
2. Create a new issue with detailed information
3. Include relevant logs and configuration details

---

**Made with ❤️ for the NetBox and network automation community**
