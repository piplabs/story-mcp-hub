from mcp.server.fastmcp import FastMCP
from duckduckgo_search import DDGS

# Initialize FastMCP server
mcp = FastMCP("story-search-mcp")

@mcp.tool()
async def search_copyright_infringement(query: str):
    """
    Search the web for potential copyright infringement of a given text or IP metadata.
    """
    with DDGS() as ddgs:
        results = [r for r in ddgs.text(query, max_results=5)]
        return {"results": results}

if __name__ == "__main__":
    mcp.run()
