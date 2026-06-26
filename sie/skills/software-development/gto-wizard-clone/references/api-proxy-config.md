# API Proxy Configuration (Next.js → FastAPI)

## Problem

Frontend makes API calls with relative URLs like `/api/v1/equity/calculate`. These hit Next.js (port 8555), but the FastAPI backend is on port 8002. Without proxy rewrites, the browser gets 404/empty responses.

## Solution: Next.js Rewrites

In `apps/web/next.config.ts`:

```typescript
async rewrites() {
  return [
    { source: '/api/:path*', destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002'}/api/:path*` },
    { source: '/icm/:path*', destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002'}/icm/:path*` },
    { source: '/plo4/:path*', destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002'}/plo4/:path*` },
    { source: '/double-board/:path*', destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002'}/double-board/:path*` },
    { source: '/bomb-pot/:path*', destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002'}/bomb-pot/:path*` },
    { source: '/ws/:path*', destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002'}/ws/:path*` },
  ]
}
```

## Router Prefix Mapping

The FastAPI backend uses non-standard prefixes for some routers (not under `/api/v1/`):
- Equity: `/api/v1/equity` (standard)
- ICM: `/icm` (NOT `/api/v1/icm`)
- PLO4: `/plo4/equity`
- Double Board: `/double-board`
- Bomb Pot: `/bomb-pot`
- Spots: `/api/v1/spots`
- Courses: `/api/v1/courses`

Each prefix needs its own rewrite rule.
