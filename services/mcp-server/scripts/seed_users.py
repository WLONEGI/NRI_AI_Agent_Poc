#!/usr/bin/env python3
"""
User and Team Seeding Script

Loads user and team data from YAML configuration and seeds Neo4j database.

Usage:
    python scripts/seed_users.py [--yaml-path PATH] [--dry-run]

Arguments:
    --yaml-path: Path to YAML file (default: infra/users_teams.yaml)
    --dry-run: Print operations without executing them

Requirements:
    - Neo4j connection configured via environment variables
    - YAML file with users and teams structure
"""

import sys
import argparse
from pathlib import Path
from typing import List, Dict

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from infra.neo4j_client import Neo4jClient
from config.settings import settings
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_yaml_config(yaml_path: Path) -> Dict:
    """Load and validate YAML configuration."""
    if not yaml_path.exists():
        raise FileNotFoundError(f"YAML file not found: {yaml_path}")

    with open(yaml_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # Validate structure
    if 'users' not in config or 'teams' not in config:
        raise ValueError("YAML must contain 'users' and 'teams' keys")

    if not isinstance(config['users'], list):
        raise ValueError("'users' must be a list")

    if not isinstance(config['teams'], list):
        raise ValueError("'teams' must be a list")

    return config


def seed_teams(driver, teams: List[Dict], dry_run: bool = False) -> int:
    """Seed team nodes in Neo4j."""
    query = """
    MERGE (t:Team {id: $id})
    SET t.name = $name,
        t.created_at = coalesce(t.created_at, datetime()),
        t.updated_at = datetime()
    RETURN t.id AS team_id
    """

    count = 0
    with driver.session() as session:
        for team in teams:
            team_id = team.get('id')
            team_name = team.get('name')

            if not team_id or not team_name:
                logger.warning(f"Skipping invalid team: {team}")
                continue

            if dry_run:
                logger.info(f"[DRY-RUN] Would create/update team: {team_id} ({team_name})")
            else:
                try:
                    result = session.run(query, id=team_id, name=team_name)
                    record = result.single()
                    logger.info(f"✓ Team created/updated: {record['team_id']}")
                    count += 1
                except Exception as e:
                    logger.error(f"✗ Failed to seed team {team_id}: {e}")

    return count


def seed_users(driver, users: List[Dict], dry_run: bool = False) -> int:
    """Seed user nodes and relationships in Neo4j."""
    query = """
    MERGE (u:User {id: $id})
    SET u.name = $name,
        u.team_id = $team_id,
        u.created_at = coalesce(u.created_at, datetime()),
        u.updated_at = datetime()
    WITH u
    MATCH (t:Team {id: $team_id})
    MERGE (u)-[:BELONGS_TO]->(t)
    RETURN u.id AS user_id, t.id AS team_id
    """

    count = 0
    with driver.session() as session:
        for user in users:
            user_id = user.get('id')
            user_name = user.get('name')
            team_id = user.get('team')

            if not user_id or not user_name or not team_id:
                logger.warning(f"Skipping invalid user: {user}")
                continue

            if dry_run:
                logger.info(
                    f"[DRY-RUN] Would create/update user: {user_id} ({user_name}) → {team_id}"
                )
            else:
                try:
                    result = session.run(
                        query, id=user_id, name=user_name, team_id=team_id
                    )
                    record = result.single()
                    logger.info(
                        f"✓ User created/updated: {record['user_id']} → {record['team_id']}"
                    )
                    count += 1
                except Exception as e:
                    logger.error(f"✗ Failed to seed user {user_id}: {e}")

    return count


def main():
    """Main seeding workflow."""
    parser = argparse.ArgumentParser(description='Seed Neo4j with users and teams from YAML')
    parser.add_argument(
        '--yaml-path',
        type=Path,
        default=Path('infra/users_teams.yaml'),
        help='Path to YAML configuration file (default: infra/users_teams.yaml)',
    )
    parser.add_argument(
        '--dry-run', action='store_true', help='Print operations without executing'
    )

    args = parser.parse_args()

    logger.info("=== User/Team Seeding ===")
    logger.info(f"YAML Config: {args.yaml_path}")
    logger.info(f"Neo4j URI: {settings.NEO4J_URI}")

    if args.dry_run:
        logger.info("MODE: DRY-RUN (no database changes)")

    try:
        # Load configuration
        logger.info("\n--- Loading YAML Configuration ---")
        config = load_yaml_config(args.yaml_path)
        logger.info(f"✓ Loaded {len(config['teams'])} teams, {len(config['users'])} users")

        # Connect to Neo4j
        if not args.dry_run:
            client = Neo4jClient()
            if not client.health_check():
                logger.error("✗ Neo4j health check failed")
                sys.exit(1)
            logger.info("✓ Connected to Neo4j")
        else:
            client = None

        # Seed teams first (required for user relationships)
        logger.info("\n--- Seeding Teams ---")
        if args.dry_run:
            team_count = seed_teams(None, config['teams'], dry_run=True)
        else:
            team_count = seed_teams(client.driver, config['teams'])

        # Seed users
        logger.info("\n--- Seeding Users ---")
        if args.dry_run:
            user_count = seed_users(None, config['users'], dry_run=True)
        else:
            user_count = seed_users(client.driver, config['users'])

        # Summary
        logger.info("\n=== Seeding Complete ===")
        if not args.dry_run:
            logger.info(f"✓ {team_count} teams processed")
            logger.info(f"✓ {user_count} users processed")
            client.close()
        else:
            logger.info(f"[DRY-RUN] Would process {len(config['teams'])} teams")
            logger.info(f"[DRY-RUN] Would process {len(config['users'])} users")

    except Exception as e:
        logger.error(f"\n✗ Seeding failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
