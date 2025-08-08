"""MCP Integration Layer for Story Protocol Specialized Agents

Loads MCP tools from Story SDK server and provides them as LangChain-compatible tools
following the exact pattern from the working ai-playground-backend implementation.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools

from .tool_lists import SPECIALIST_TOOL_MAPPING

logger = logging.getLogger(__name__)


class StoryMCPIntegration:
    """Handles MCP tool loading and distribution to specialists"""
    
    def __init__(self):
        self.all_mcp_tools: List[Any] = []
        self.tools_by_name: Dict[str, Any] = {}
        self.tools_by_specialist: Dict[str, Dict[str, List[Any]]] = {}
        self._initialized = False
    
    async def initialize(self):
        """Load all MCP tools from Story SDK server"""
        if self._initialized:
            logger.info("📦 MCP tools already initialized")
            return
            
        logger.info("🔄 Loading MCP tools from Story SDK server...")
        
        try:
            # Load tools from our Story SDK MCP server
            server_path = self._get_story_sdk_server_path()
            self.all_mcp_tools = await self._load_story_sdk_tools(server_path)
            
            # Create name mapping for quick lookup
            self.tools_by_name = {tool.name: tool for tool in self.all_mcp_tools}
            
            # Organize tools by specialist
            self._organize_tools_by_specialist()
            
            logger.info(f"✅ Successfully loaded {len(self.all_mcp_tools)} MCP tools")
            self._log_tool_summary()
            
            self._initialized = True
            
        except Exception as e:
            logger.error(f"❌ Error loading MCP tools: {str(e)}")
            raise
    
    async def _load_story_sdk_tools(self, server_path: str) -> List[Any]:
        """Load tools from Story SDK MCP server using the proven pattern"""
        if not os.path.exists(server_path):
            raise FileNotFoundError(f"Story SDK server not found at {server_path}")
        
        server_params = StdioServerParameters(
            command="python3",
            args=[server_path],
        )
        
        logger.info(f"🔧 Loading Story SDK tools from {server_path}")
        
        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await load_mcp_tools(session)  # The magic conversion!
                    logger.info(f"✅ Loaded {len(tools)} Story SDK tools")
                    return tools
        except Exception as e:
            logger.error(f"❌ Error loading Story SDK tools: {str(e)}")
            raise
    
    def _get_story_sdk_server_path(self) -> str:
        """Get the path to Story SDK MCP server"""
        # Get current file's directory (specialized-agent/)
        current_dir = Path(__file__).parent
        # Go up one level to story-sdk-mcp/ and get server.py
        server_path = current_dir.parent / "server.py"
        
        if server_path.exists():
            return str(server_path)
        
        # Fallback: try environment variable
        env_path = os.getenv("SDK_MCP_SERVER_PATH")
        if env_path and os.path.exists(env_path):
            return env_path
        
        raise FileNotFoundError(
            f"Story SDK server not found at {server_path}. "
            f"Set SDK_MCP_SERVER_PATH environment variable or ensure server.py exists."
        )
    
    def _organize_tools_by_specialist(self):
        """Organize loaded tools by specialist using our tool mapping"""
        logger.info("📊 Organizing tools by specialist...")
        
        # Initialize specialist tool containers
        for specialist, mapping in SPECIALIST_TOOL_MAPPING.items():
            self.tools_by_specialist[specialist] = {
                "safe": [],
                "sensitive": []
            }
            
            # Get safe tools for this specialist
            for tool_name in mapping["safe_tools"]:
                if tool_name in self.tools_by_name:
                    self.tools_by_specialist[specialist]["safe"].append(
                        self.tools_by_name[tool_name]
                    )
                else:
                    logger.warning(f"⚠️ Safe tool '{tool_name}' not found in MCP tools")
            
            # Get sensitive tools for this specialist
            for tool_name in mapping["sensitive_tools"]:
                if tool_name in self.tools_by_name:
                    self.tools_by_specialist[specialist]["sensitive"].append(
                        self.tools_by_name[tool_name]
                    )
                else:
                    logger.warning(f"⚠️ Sensitive tool '{tool_name}' not found in MCP tools")
    
    def _log_tool_summary(self):
        """Log summary of loaded tools"""
        logger.info("📊 Tool Summary by Specialist:")
        
        for specialist, tools in self.tools_by_specialist.items():
            safe_count = len(tools["safe"])
            sensitive_count = len(tools["sensitive"])
            total = safe_count + sensitive_count
            
            logger.info(
                f"  {specialist}: {total} tools ({safe_count} safe, {sensitive_count} sensitive)"
            )
            
            # Log individual tool names for debugging
            if tools["safe"]:
                safe_names = [t.name for t in tools["safe"]]
                logger.debug(f"    Safe: {', '.join(safe_names)}")
            if tools["sensitive"]:
                sensitive_names = [t.name for t in tools["sensitive"]]
                logger.debug(f"    Sensitive: {', '.join(sensitive_names)}")
    
    def get_specialist_tools(self, specialist: str) -> Dict[str, List[Any]]:
        """Get all tools for a specific specialist"""
        if not self._initialized:
            raise RuntimeError("MCP integration not initialized. Call initialize() first.")
        
        if specialist not in self.tools_by_specialist:
            raise ValueError(f"Unknown specialist: {specialist}")
        
        return self.tools_by_specialist[specialist]
    
    def get_safe_tools(self, specialist: str) -> List[Any]:
        """Get safe tools for a specialist"""
        tools = self.get_specialist_tools(specialist)
        return tools["safe"]
    
    def get_sensitive_tools(self, specialist: str) -> List[Any]:
        """Get sensitive tools for a specialist"""
        tools = self.get_specialist_tools(specialist)
        return tools["sensitive"]
    
    def get_all_tools_for_specialist(self, specialist: str) -> List[Any]:
        """Get all tools (safe + sensitive) for a specialist"""
        tools = self.get_specialist_tools(specialist)
        return tools["safe"] + tools["sensitive"]
    
    def get_all_sensitive_tool_names(self) -> List[str]:
        """Get names of all sensitive tools for interrupt_before configuration"""
        sensitive_names = []
        for specialist_tools in self.tools_by_specialist.values():
            for tool in specialist_tools["sensitive"]:
                sensitive_names.append(tool.name)
        return sensitive_names


# Global singleton instance
_mcp_integration: Optional[StoryMCPIntegration] = None


async def initialize_mcp_integration() -> StoryMCPIntegration:
    """Initialize the global MCP integration singleton"""
    global _mcp_integration
    
    if _mcp_integration is None:
        _mcp_integration = StoryMCPIntegration()
        await _mcp_integration.initialize()
    
    return _mcp_integration


def get_mcp_integration() -> StoryMCPIntegration:
    """Get the initialized MCP integration instance"""
    global _mcp_integration
    
    if _mcp_integration is None:
        raise RuntimeError(
            "MCP integration not initialized. Call initialize_mcp_integration() first."
        )
    
    return _mcp_integration


# Convenience functions for specialists
def get_specialist_tools(specialist: str) -> Dict[str, List[Any]]:
    """Get tools for a specialist (safe and sensitive separately)"""
    return get_mcp_integration().get_specialist_tools(specialist)


def get_specialist_safe_tools(specialist: str) -> List[Any]:
    """Get safe tools for a specialist"""
    return get_mcp_integration().get_safe_tools(specialist)


def get_specialist_sensitive_tools(specialist: str) -> List[Any]:
    """Get sensitive tools for a specialist"""
    return get_mcp_integration().get_sensitive_tools(specialist)


def get_all_specialist_tools(specialist: str) -> List[Any]:
    """Get all tools for a specialist"""
    return get_mcp_integration().get_all_tools_for_specialist(specialist)