# MCP Usage Notes for Job Search

## Correct MCP Integration Pattern

Apify actors are exposed via MCP servers in Hermes. The correct workflow is:

1. **Configure the MCP server** in `~/.hermes/config.yaml`:
   ```yaml
   mcp:
     servers:
       apify:
         url: https://api.apify.com/v2/acts
         auth_header: "Bearer <YOUR_APIFY_TOKEN>"
   ```

2. **Discover available tools** (if needed):
   ```bash
   hermes mcp picker  # Interactive catalog
   hermes mcp install apify/indeed-scraper  # Example from catalog
   ```

3. **Use the skill's abstraction** - The `job-search` skill handles the MCP calls internally via:
   - Indeed: `sheshinmcfly/indeed-jobs-scraper` actor via MCP
   - LinkedIn: `apify/agent-data` actor via MCP

**Common Mistake**: Attempting to use `hermes mcp call` - this command does not exist. MCP tool invocation is handled through skills or direct agent tool calls once the server is configured.

## Credits Tracking

The Indeed scraper on Apify costs approximately $0.06 per 1,000 results, fitting within the $5/month free tier for ~83k jobs.