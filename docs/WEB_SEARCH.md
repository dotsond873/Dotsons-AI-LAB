# SerpApi web search

Set SERPAPI_API_KEY on the Render backend service, then redeploy. Never commit the actual key or put it in a VITE_ variable.

The checkbox sends web_search: true to POST /chat. Searches run only when selected, consume SerpApi quota, and send the message to SerpApi. Responses include sources and search_status. Existing clients default to ordinary chat. Search failures return a clear error. Uncheck search to continue ordinary chat.

Uses the existing httpx dependency and up to five Google organic result snippets, not full pages. Documentation: https://serpapi.com/search-api
