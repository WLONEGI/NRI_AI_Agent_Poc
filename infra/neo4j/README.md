# Neo4j Docker Setup

## Quick Start

1. **Update credentials** in `docker-compose.yml`:
   ```yaml
   NEO4J_AUTH=neo4j/your-secure-password
   ```

2. **Start Neo4j**:
   ```bash
   cd infra/neo4j
   docker-compose up -d
   ```

3. **Verify health**:
   ```bash
   docker-compose ps
   docker-compose logs neo4j
   ```

4. **Access Neo4j Browser**:
   - URL: http://localhost:7474
   - Username: `neo4j`
   - Password: `your-secure-password` (from step 1)

5. **Initialize schema**:
   ```bash
   cd ../..
   source .venv/bin/activate
   python services/mcp-server/scripts/init_neo4j_schema.py
   ```

6. **Seed users/teams** (optional):
   ```bash
   # Copy example config
   cp infra/users_teams.example.yaml infra/users_teams.yaml

   # Edit with your data
   vi infra/users_teams.yaml

   # Run seeding
   python services/mcp-server/scripts/seed_users.py
   ```

## Configuration

### Environment Variables

Update your `.env` file with:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-secure-password
```

### Memory Settings

Default configuration:
- Heap: 512MB initial, 2GB max
- Page cache: 1GB

For production or large datasets, increase in `docker-compose.yml`:

```yaml
- NEO4J_server_memory_heap_max__size=4G
- NEO4J_server_memory_pagecache_size=2G
```

### Vector Index Support

Vector indexes are enabled by default:

```yaml
- NEO4J_db_index_vector_enabled=true
- NEO4J_db_index_vector_similarity__function=cosine
```

This requires Neo4j Enterprise Edition (license accepted in docker-compose.yml).

## Data Persistence

All data is persisted in named Docker volumes:

- `neo4j_data`: Database files
- `neo4j_logs`: Log files
- `neo4j_import`: CSV import directory
- `neo4j_plugins`: Plugin JARs

To reset the database:

```bash
docker-compose down -v  # Warning: deletes all data!
docker-compose up -d
```

## Troubleshooting

### Connection refused

```bash
# Check container status
docker-compose ps

# Check logs
docker-compose logs neo4j

# Verify port mapping
docker ps | grep neo4j
```

### Out of memory

Increase heap and page cache in `docker-compose.yml`.

### Vector index not working

Ensure Enterprise Edition is used and license accepted:

```yaml
image: neo4j:5.15-enterprise
NEO4J_ACCEPT_LICENSE_AGREEMENT=yes
```

## Stop and Cleanup

```bash
# Stop containers
docker-compose down

# Stop and remove volumes (data loss!)
docker-compose down -v

# View logs
docker-compose logs -f neo4j
```
