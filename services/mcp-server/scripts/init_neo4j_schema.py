#!/usr/bin/env python3
"""
Neo4j Schema Initialization Script

Creates vector indexes, constraints, and other schema elements required for
the Crystal Intelligence knowledge integration PoC.

Usage:
    python scripts/init_neo4j_schema.py

Requirements:
    - Neo4j 5.x with vector plugin
    - Environment variables: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from infra.neo4j_client import Neo4jClient
from config.settings import settings
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_vector_index(driver):
    """Create vector index on Knowledge.embedding for similarity search."""
    query = """
    CREATE VECTOR INDEX knowledge_embedding IF NOT EXISTS
    FOR (k:Knowledge)
    ON (k.embedding)
    OPTIONS {
        indexConfig: {
            `vector.dimensions`: 1536,
            `vector.similarity_function`: 'cosine'
        }
    }
    """
    try:
        with driver.session() as session:
            session.run(query)
        logger.info("✓ Vector index 'knowledge_embedding' created/verified")
    except Exception as e:
        logger.error(f"✗ Failed to create vector index: {e}")
        raise


def create_constraints(driver):
    """Create uniqueness constraints on entity IDs."""
    constraints = [
        (
            "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
            "User.id uniqueness constraint",
        ),
        (
            "CREATE CONSTRAINT team_id_unique IF NOT EXISTS FOR (t:Team) REQUIRE t.id IS UNIQUE",
            "Team.id uniqueness constraint",
        ),
        (
            "CREATE CONSTRAINT query_id_unique IF NOT EXISTS FOR (q:Query) REQUIRE q.id IS UNIQUE",
            "Query.id uniqueness constraint",
        ),
        (
            "CREATE CONSTRAINT knowledge_id_unique IF NOT EXISTS FOR (k:Knowledge) REQUIRE k.id IS UNIQUE",
            "Knowledge.id uniqueness constraint",
        ),
        (
            "CREATE CONSTRAINT agent_execution_id_unique IF NOT EXISTS FOR (a:AgentExecution) REQUIRE a.id IS UNIQUE",
            "AgentExecution.id uniqueness constraint",
        ),
        (
            "CREATE CONSTRAINT data_source_id_unique IF NOT EXISTS FOR (d:DataSource) REQUIRE d.id IS UNIQUE",
            "DataSource.id uniqueness constraint",
        ),
        (
            "CREATE CONSTRAINT tool_execution_id_unique IF NOT EXISTS FOR (t:ToolExecution) REQUIRE t.id IS UNIQUE",
            "ToolExecution.id uniqueness constraint",
        ),
        (
            "CREATE CONSTRAINT extracted_content_id_unique IF NOT EXISTS FOR (e:ExtractedContent) REQUIRE e.id IS UNIQUE",
            "ExtractedContent.id uniqueness constraint",
        ),
    ]

    with driver.session() as session:
        for query, description in constraints:
            try:
                session.run(query)
                logger.info(f"✓ {description} created/verified")
            except Exception as e:
                logger.error(f"✗ Failed to create {description}: {e}")
                raise


def create_indexes(driver):
    """Create performance indexes on commonly queried fields."""
    indexes = [
        (
            "CREATE INDEX knowledge_hierarchy_level IF NOT EXISTS FOR (k:Knowledge) ON (k.hierarchy_level)",
            "Knowledge.hierarchy_level index",
        ),
        (
            "CREATE INDEX knowledge_owner_id IF NOT EXISTS FOR (k:Knowledge) ON (k.owner_id)",
            "Knowledge.owner_id index",
        ),
        (
            "CREATE INDEX query_user_id IF NOT EXISTS FOR (q:Query) ON (q.user_id)",
            "Query.user_id index",
        ),
        (
            "CREATE INDEX query_timestamp IF NOT EXISTS FOR (q:Query) ON (q.timestamp)",
            "Query.timestamp index",
        ),
        (
            "CREATE INDEX user_team_id IF NOT EXISTS FOR (u:User) ON (u.team_id)",
            "User.team_id index",
        ),
    ]

    with driver.session() as session:
        for query, description in indexes:
            try:
                session.run(query)
                logger.info(f"✓ {description} created/verified")
            except Exception as e:
                logger.warning(f"⚠ Could not create {description}: {e}")
                # Don't raise - indexes are performance optimizations, not critical


def verify_schema(driver):
    """Verify that all schema elements were created successfully."""
    with driver.session() as session:
        # Check constraints
        result = session.run("SHOW CONSTRAINTS")
        constraints = [record['name'] for record in result]
        logger.info(f"✓ Total constraints: {len(constraints)}")

        # Check indexes
        result = session.run("SHOW INDEXES")
        indexes = [record['name'] for record in result]
        logger.info(f"✓ Total indexes: {len(indexes)}")

        # Verify vector index specifically
        result = session.run(
            "SHOW INDEXES WHERE name = 'knowledge_embedding' AND type = 'VECTOR'"
        )
        vector_indexes = list(result)
        if vector_indexes:
            logger.info("✓ Vector index 'knowledge_embedding' verified")
        else:
            logger.error("✗ Vector index 'knowledge_embedding' not found!")
            raise RuntimeError("Vector index creation failed")


def main():
    """Initialize Neo4j schema."""
    logger.info("=== Neo4j Schema Initialization ===")
    logger.info(f"Connecting to: {settings.NEO4J_URI}")

    try:
        # Initialize client
        client = Neo4jClient()

        # Verify connection
        if not client.health_check():
            logger.error("✗ Neo4j health check failed")
            sys.exit(1)

        logger.info("✓ Connected to Neo4j successfully")

        # Create schema elements
        logger.info("\n--- Creating Constraints ---")
        create_constraints(client.driver)

        logger.info("\n--- Creating Vector Index ---")
        create_vector_index(client.driver)

        logger.info("\n--- Creating Performance Indexes ---")
        create_indexes(client.driver)

        logger.info("\n--- Verifying Schema ---")
        verify_schema(client.driver)

        logger.info("\n=== Schema Initialization Complete ===")

        # Close connection
        client.close()

    except Exception as e:
        logger.error(f"\n✗ Schema initialization failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
