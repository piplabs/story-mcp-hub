from mcp.server.fastmcp import FastMCP
import httpx

mcp = FastMCP("Story Search")

@mcp.tool()
async def search_copyright_infringement(query: str) -> str:
    """Search the web for potential copyright infringement before IP registration."""
    async with httpx.AsyncClient() as client:
        # 物理调用 DuckDuckGo API
        url = f"https://api.duckduckgo.com/?q={query}&format=json"
        response = await client.get(url)
        return response.text

if __name__ == "__main__":
    mcp.run()
