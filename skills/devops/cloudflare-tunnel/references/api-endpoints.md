# Cloudflare Tunnel API Endpoints

## Account & Zone

```
GET  /client/v4/accounts                              # List accounts
GET  /client/v4/zones?name=DOMAIN                      # Get zone ID
```

## Tunnel CRUD

```
POST   /client/v4/accounts/{id}/cfd_tunnel              # Create tunnel
GET    /client/v4/accounts/{id}/cfd_tunnel               # List tunnels
GET    /client/v4/accounts/{id}/cfd_tunnel/{id}          # Get tunnel details
PATCH  /client/v4/accounts/{id}/cfd_tunnel/{id}          # Update tunnel (triggers reload)
DELETE /client/v4/accounts/{id}/cfd_tunnel/{id}          # Delete tunnel
```

## Tunnel Configuration

```
GET  /client/v4/accounts/{id}/cfd_tunnel/{id}/configurations   # Get ingress config
PUT  /client/v4/accounts/{id}/cfd_tunnel/{id}/configurations   # Set ingress config
GET  /client/v4/accounts/{id}/cfd_tunnel/{id}/token            # Get tunnel token
```

## DNS Records

```
GET    /client/v4/zones/{id}/dns_records?name=FQDN    # Lookup DNS record
POST   /client/v4/zones/{id}/dns_records               # Create DNS record
PATCH  /client/v4/zones/{id}/dns_records/{id}          # Update DNS record
DELETE /client/v4/zones/{id}/dns_records/{id}          # Delete DNS record
```

## Identity Providers

```json
GET  /client/v4/accounts/{id}/access/identity_providers        # List IDPs (find email OTP provider UUID)
```

## Cloudflare Access Applications

**Account-level** (requires account ID from `/accounts`):
```json
GET    /client/v4/accounts/{id}/access/apps                    # List access apps
POST   /client/v4/accounts/{id}/access/apps                    # Create app (with optional inline policies)
GET    /client/v4/accounts/{id}/access/apps/{id}               # Get app details
PUT    /client/v4/accounts/{id}/access/apps/{id}               # Update app
DELETE /client/v4/accounts/{id}/access/apps/{id}               # Delete app
```

**Zone-level** (simpler when you already have the zone ID — scopes to one zone):
```json
GET    /client/v4/zones/{zone_id}/access/apps                  # List access apps for zone
POST   /client/v4/zones/{zone_id}/access/apps                  # Create app
GET    /client/v4/zones/{zone_id}/access/apps/{id}             # Get app details
PUT    /client/v4/zones/{zone_id}/access/apps/{id}             # Update app
DELETE /client/v4/zones/{zone_id}/access/apps/{id}             # Delete app
```

## Cloudflare Access Policies

```json
GET    /client/v4/accounts/{id}/access/apps/{id}/policies      # List policies for an app
POST   /client/v4/accounts/{id}/access/apps/{id}/policies      # Create policy
PUT    /client/v4/accounts/{id}/access/apps/{id}/policies/{id}  # Update policy
DELETE /client/v4/accounts/{id}/access/apps/{id}/policies/{id}  # Delete policy
```

Note: You can skip the separate POST for policies by including a `policies` array directly in the app creation POST body — this creates both atomically in one call.
```
**Notable**: The `/token` endpoint returns `result` as a raw string (the JWT token), NOT an object:
```json
{"success": true, "result": "eyJhIj...0ifQ=="}
```

## Create Tunnel Request Body

```json
{
  "name": "tunnel-name",
  "tunnel_secret": "base64-encoded-32-byte-secret"
}
```

## Ingress Config (PUT)

```json
{
  "config": {
    "ingress": [
      {"hostname": "app.example.com", "service": "http://localhost:8080"},
      {"service": "http_status:404"}
    ],
    "warp-routing": {},
    "__configuration_flags": {"no-autoupdate": "true"}
  }
}
```

## DNS CNAME Record

```json
{
  "type": "CNAME",
  "name": "subdomain",
  "content": "TUNNEL_ID.cfargotunnel.com",
  "ttl": 1,
  "proxied": true
}
```
