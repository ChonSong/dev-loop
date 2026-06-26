---
name: secure-private-chat-instance
description: Building isolated, authenticated chat environments for private messaging with Hermes
category: privacy-security
tags: [security, isolation, authentication, docker, hermes-web-ui]
---

# Secure Private Chat Instance

This skill documents the complete pattern for creating isolated, authenticated chat environments where users can interact with Hermes privately. This is essential for providing separate, secure spaces for different users or purposes while maintaining system integrity.

## Scope

Creates completely isolated chat instances with:
- Unique authentication (username/password)
- Separate Docker container deployment
- Independent configuration space
- No shared memory or state with other instances
- Configurable access controls

## Prerequisites

- Docker installed and running
- Administrative access to host system
- Basic understanding of Docker networking
- Sufficient system resources for each container

## Implementation Steps

1. **Container Isolation Setup**
   - Create dedicated Docker network for private instances
   - Configure separate volumes for each instance's data
   - Set up dedicated configuration directories

2. **Authentication Configuration**
   - Implement credential vault using secure storage
   - Set up password hashing and verification
   - Configure authentication middleware

3. **Instance Provisioning**
   - Deploy base Hermes Web UI image
   - Apply instance-specific environment variables
   - Configure routing and access controls

4. **Security Hardening**
   - Apply network isolation rules
   - Set up process containment policies
   - Implement audit logging

## Verification

After setup:
- Verify container isolation through network diagnostics
- Test authentication flow with test credentials
- Confirm no cross-instance state leakage
- Validate audit logs show proper access attempts

## Maintenance

- Monitor resource usage per instance
- Rotate credentials periodically
- Update isolation policies quarterly
- Audit access logs weekly

## Related Skills

- `hermes-web-ui` - Base web interface
- `docker-container-management` - Container lifecycle
- `credential-vault` - Secure credential storage
- `network-isolation` - Network security patterns