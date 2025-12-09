"""
Network operation tools
"""
import requests
import socket
from typing import List, Dict, Any
from tools.base_tool import BaseTool, ToolParameter, ToolResult


class HTTPRequestTool(BaseTool):
    """Make HTTP requests"""
    
    @property
    def name(self) -> str:
        return "http_request"
    
    @property
    def description(self) -> str:
        return "Make HTTP GET/POST requests"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter("url", "string", "URL to request", required=True),
            ToolParameter("method", "string", "HTTP method (GET/POST)", default="GET"),
            ToolParameter("headers", "dict", "Request headers", default=None),
            ToolParameter("data", "dict", "Request body data", default=None),
            ToolParameter("timeout", "integer", "Timeout in seconds", default=10)
        ]
    
    def execute(self, **kwargs) -> ToolResult:
        url = kwargs.get("url")
        method = kwargs.get("method", "GET").upper()
        headers = kwargs.get("headers", {})
        data = kwargs.get("data")
        timeout = kwargs.get("timeout", 10)
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=timeout)
            else:
                return ToolResult(success=False, output=None, error=f"Unsupported method: {method}")
            
            result = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content": response.text[:5000],  # Truncate large responses
                "url": response.url
            }
            
            return ToolResult(
                success=response.status_code < 400,
                output=result,
                metadata={"status_code": response.status_code, "method": method}
            )
            
        except requests.Timeout:
            return ToolResult(success=False, output=None, error=f"Request timed out after {timeout}s")
        except requests.RequestException as e:
            return ToolResult(success=False, output=None, error=str(e))
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))


class PortScanTool(BaseTool):
    """Scan network ports"""
    
    @property
    def name(self) -> str:
        return "port_scan"
    
    @property
    def description(self) -> str:
        return "Scan TCP ports on a host"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter("host", "string", "Target host", required=True),
            ToolParameter("ports", "list", "List of ports to scan", required=True),
            ToolParameter("timeout", "float", "Connection timeout", default=1.0)
        ]
    
    def execute(self, **kwargs) -> ToolResult:
        host = kwargs.get("host")
        ports = kwargs.get("ports", [])
        timeout = kwargs.get("timeout", 1.0)
        
        if not isinstance(ports, list):
            return ToolResult(success=False, output=None, error="Ports must be a list")
        
        open_ports = []
        closed_ports = []
        
        try:
            for port in ports:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(timeout)
                    result = sock.connect_ex((host, int(port)))
                    sock.close()
                    
                    if result == 0:
                        open_ports.append(port)
                    else:
                        closed_ports.append(port)
                        
                except Exception:
                    closed_ports.append(port)
            
            return ToolResult(
                success=True,
                output={
                    "host": host,
                    "open_ports": open_ports,
                    "closed_ports": closed_ports,
                    "total_scanned": len(ports)
                },
                metadata={"host": host, "open_count": len(open_ports)}
            )
            
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))


class DNSLookupTool(BaseTool):
    """DNS lookup tool"""
    
    @property
    def name(self) -> str:
        return "dns_lookup"
    
    @property
    def description(self) -> str:
        return "Resolve hostname to IP address"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter("hostname", "string", "Hostname to resolve", required=True)
        ]
    
    def execute(self, **kwargs) -> ToolResult:
        hostname = kwargs.get("hostname")
        
        try:
            ip_address = socket.gethostbyname(hostname)
            
            return ToolResult(
                success=True,
                output={
                    "hostname": hostname,
                    "ip_address": ip_address
                },
                metadata={"hostname": hostname, "ip": ip_address}
            )
            
        except socket.gaierror as e:
            return ToolResult(success=False, output=None, error=f"DNS lookup failed: {e}")
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))


class IPInfoTool(BaseTool):
    """Get IP information"""
    
    @property
    def name(self) -> str:
        return "ip_info"
    
    @property
    def description(self) -> str:
        return "Get information about an IP address"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter("ip", "string", "IP address to lookup", required=False)
        ]
    
    def execute(self, **kwargs) -> ToolResult:
        ip = kwargs.get("ip", "")
        
        try:
            # Use ipapi.co for IP information
            url = f"https://ipapi.co/{ip}/json/" if ip else "https://ipapi.co/json/"
            
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return ToolResult(success=True, output=data, metadata={"ip": data.get("ip")})
            else:
                return ToolResult(success=False, output=None, error=f"API returned {response.status_code}")
                
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))
