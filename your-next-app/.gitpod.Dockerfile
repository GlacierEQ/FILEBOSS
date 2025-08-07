FROM gitpod/workspace-full:latest
RUN npm i -g pnpm && \
  pnpm add -g @browserbasehq/mcp-browserbase exa @wonderwhy-er/desktop-commander @upstash/context7-mcp @big-omega/mem0-mcp @knowall-ai/mcp-neo4j-agent-memory @microsoft/playwright-mcp @supabase-community/supabase-mcp @xinzhongyouhai/mcp-sequentialthinking-tools @luminati-io/brightdata-mcp @qodo/code-interpreter-mcp @mcp/dependency-graph @shielded/sentinel-mcp @sciphi/datasci-mcp @spec-driven/architect-mcp
