# Dashboard Guide

The Akasha Dashboard is a React SPA embedded directly in the server binary. No separate deployment needed.

## Accessing the Dashboard

```
https://localhost:7771/dashboard/
```

> Accept the self-signed certificate warning on first access.

## Authentication

### Auth Enabled (`auth.enabled = true`)

You'll see a login page. Use:
- **Username**: `akasha` (or your custom user)
- **Password**: `akasha` (change immediately)

### Auth Disabled (`auth.enabled = false`)

The dashboard auto-logs in as an anonymous admin. No login required.

## Pages

### 1. Cluster Dashboard

The main operational view showing:

| Section | What it shows |
|---------|--------------|
| **Stats Grid** | Total Records, Connected Agents, Total Writes, Cluster Nodes (X/Y), Pending Deltas, Uptime |
| **Node Topology** | Card per node with status dot (green=alive, red=dead), LEADER badge, address, version, last seen |
| **Memory Fabric** | Visual bars for each cognitive layer (Working, Episodic, Semantic, Procedural) with counts |
| **Cluster Health** | Status, Version, Raft Term/Role, Commit Index, Nidra Leader, Last Cycle |

**Auto-refresh**: Data updates every 5 seconds.

### 2. Explorer

Three tabs for browsing all data:

| Tab | What it shows |
|-----|--------------|
| **Records** | Glob search (default `**`) with JSON inspector. Click any record to see its full value |
| **Memory** | Visual cards per cognitive layer with counts and descriptions |
| **Pheromones** | Active pheromone trails table with signal type, emitter, intensity bars, and half-life |

### 3. Administration

| Tab | What it shows |
|-----|--------------|
| **Users** | User table with role badges, Edit/Delete actions, "+ New User" form |
| **API Keys** | Key table with role, namespaces, revoke action. New key creation with one-time display |

**Security banner**: If the default `akasha` user exists, a warning reminds you to change the password.

## Profile Modal

Click your **username in the sidebar** (bottom-left) to open the profile modal:

- View your username and role
- Change your password (current + new + confirm)

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Click sidebar user | Open profile modal |
| Enter (in search) | Execute record search |
| Escape | Close profile modal |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Dashboard shows blank page | Clear browser cache, check `/api/v1/health` is reachable |
| "0/3 Cluster Nodes" | API returns lowercase `alive` — this was fixed in v1.0.0 |
| Login fails with 401 | Check `auth.enabled` in config, verify credentials |
| Uptime shows "—" | Upgrade to v1.0.0 (uptime metric added) |
| Can't change password | Click your username in the sidebar, not the Admin page |
