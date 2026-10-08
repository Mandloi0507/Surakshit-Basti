"""create_core_domain_tables

Revision ID: 8fc2b09eb97c
Revises: c7c1fc0ebe42
Create Date: 2026-10-08 00:29:24.866357

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = '8fc2b09eb97c'
down_revision: Union[str, Sequence[str], None] = 'c7c1fc0ebe42'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('audit_log',
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('user_name', sa.String(length=100), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', sa.String(length=100), nullable=True),
        sa.Column('before_state_json', sa.JSON(), nullable=True),
        sa.Column('after_state_json', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('capacity_norms',
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('norm_type', sa.String(length=50), nullable=False),
        sa.Column('tier', sa.String(length=50), nullable=False),
        sa.Column('resource_name', sa.String(length=50), nullable=False),
        sa.Column('norm_value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=50), nullable=False),
        sa.Column('source_citation', sa.String(length=255), nullable=False),
        sa.Column('is_placeholder', sa.Boolean(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('districts',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('state', sa.String(length=100), nullable=False),
        sa.Column('bbox_json', sa.JSON(), nullable=False),
        sa.Column('geometry', geoalchemy2.types.Geometry(geometry_type='MULTIPOLYGON', srid=4326, dimension=2, from_text='ST_GeomFromEWKT', name='geometry', spatial_index=True), nullable=True),
        sa.Column('projected_crs', sa.String(length=20), nullable=False),
        sa.Column('grid_resolution_m', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('cells',
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('district_id', sa.String(length=50), nullable=False),
        sa.Column('geometry', geoalchemy2.types.Geometry(geometry_type='POLYGON', srid=4326, dimension=2, from_text='ST_GeomFromEWKT', name='geometry', spatial_index=True), nullable=False),
        sa.Column('slope_deg', sa.Float(), nullable=True),
        sa.Column('aspect_deg', sa.Float(), nullable=True),
        sa.Column('curvature', sa.Float(), nullable=True),
        sa.Column('flow_accum', sa.Float(), nullable=True),
        sa.Column('wetness_index', sa.Float(), nullable=True),
        sa.Column('hand_m', sa.Float(), nullable=True),
        sa.Column('dist_drainage_m', sa.Float(), nullable=True),
        sa.Column('dist_road_m', sa.Float(), nullable=True),
        sa.Column('lulc_class', sa.String(length=50), nullable=True),
        sa.Column('lulc_code', sa.Integer(), nullable=True),
        sa.Column('landslide_score', sa.Float(), nullable=False),
        sa.Column('flood_score', sa.Float(), nullable=False),
        sa.Column('flash_flood_score', sa.Float(), nullable=False),
        sa.Column('coastal_score', sa.Float(), nullable=False),
        sa.Column('combined_hazard', sa.Float(), nullable=False),
        sa.Column('hazard_class', sa.String(length=20), nullable=False),
        sa.Column('factor_contributions_json', sa.JSON(), nullable=False),
        sa.Column('data_origin', sa.String(length=30), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['district_id'], ['districts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cells_combined_hazard'), 'cells', ['combined_hazard'], unique=False)
    op.create_index(op.f('ix_cells_district_id'), 'cells', ['district_id'], unique=False)
    op.create_index(op.f('ix_cells_hazard_class'), 'cells', ['hazard_class'], unique=False)

    op.create_table('datasets',
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('district_id', sa.String(length=50), nullable=False),
        sa.Column('dataset_name', sa.String(length=100), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=True),
        sa.Column('license', sa.String(length=100), nullable=True),
        sa.Column('access_date', sa.String(length=20), nullable=True),
        sa.Column('data_origin', sa.String(length=30), nullable=False),
        sa.Column('checksum', sa.String(length=128), nullable=True),
        sa.Column('processing_status', sa.String(length=50), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['district_id'], ['districts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_datasets_district_id'), 'datasets', ['district_id'], unique=False)

    op.create_table('events',
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('district_id', sa.String(length=50), nullable=False),
        sa.Column('event_name', sa.String(length=150), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('event_date', sa.String(length=20), nullable=False),
        sa.Column('geometry', geoalchemy2.types.Geometry(srid=4326, dimension=2, from_text='ST_GeomFromEWKT', name='geometry', spatial_index=True), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('data_origin', sa.String(length=30), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['district_id'], ['districts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_events_district_id'), 'events', ['district_id'], unique=False)

    op.create_table('rainfall_observations',
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('district_id', sa.String(length=50), nullable=False),
        sa.Column('observation_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('valid_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('rainfall_mm', sa.Float(), nullable=False),
        sa.Column('rainfall_grid_json', sa.JSON(), nullable=True),
        sa.Column('data_origin', sa.String(length=30), nullable=False),
        sa.Column('retrieved_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['district_id'], ['districts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rainfall_observations_district_id'), 'rainfall_observations', ['district_id'], unique=False)

    op.create_table('scenarios',
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('district_id', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('rainfall_multiplier', sa.Float(), nullable=False),
        sa.Column('weight_overrides_json', sa.JSON(), nullable=False),
        sa.Column('site_adjustments_json', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['district_id'], ['districts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scenarios_district_id'), 'scenarios', ['district_id'], unique=False)

    op.create_table('sites',
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('district_id', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('geometry', geoalchemy2.types.Geometry(srid=4326, dimension=2, from_text='ST_GeomFromEWKT', name='geometry', spatial_index=True), nullable=False),
        sa.Column('tier', sa.String(length=50), nullable=False),
        sa.Column('area_sqm', sa.Float(), nullable=False),
        sa.Column('slope_deg', sa.Float(), nullable=False),
        sa.Column('dist_road_m', sa.Float(), nullable=False),
        sa.Column('dist_water_m', sa.Float(), nullable=False),
        sa.Column('cap_land', sa.Integer(), nullable=False),
        sa.Column('cap_water', sa.Integer(), nullable=False),
        sa.Column('cap_sanitation', sa.Integer(), nullable=False),
        sa.Column('cap_road', sa.Integer(), nullable=False),
        sa.Column('cap_services', sa.Integer(), nullable=False),
        sa.Column('final_capacity', sa.Integer(), nullable=False),
        sa.Column('limiting_factor', sa.String(length=50), nullable=False),
        sa.Column('allocated_population', sa.Integer(), nullable=False),
        sa.Column('remaining_capacity', sa.Integer(), nullable=False),
        sa.Column('confidence_level', sa.String(length=20), nullable=False),
        sa.Column('screening_reasons_json', sa.JSON(), nullable=False),
        sa.Column('data_origin', sa.String(length=30), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['district_id'], ['districts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sites_district_id'), 'sites', ['district_id'], unique=False)
    op.create_index(op.f('ix_sites_final_capacity'), 'sites', ['final_capacity'], unique=False)

    op.create_table('habitations',
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('district_id', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('geometry', geoalchemy2.types.Geometry(srid=4326, dimension=2, from_text='ST_GeomFromEWKT', name='geometry', spatial_index=True), nullable=False),
        sa.Column('population', sa.Integer(), nullable=False),
        sa.Column('households', sa.Integer(), nullable=False),
        sa.Column('vuln_children_u6', sa.Float(), nullable=False),
        sa.Column('vuln_elderly_60p', sa.Float(), nullable=False),
        sa.Column('vuln_disabled', sa.Float(), nullable=False),
        sa.Column('vuln_female_head', sa.Float(), nullable=False),
        sa.Column('vuln_kutcha', sa.Float(), nullable=False),
        sa.Column('vuln_dist_health_m', sa.Float(), nullable=False),
        sa.Column('vulnerability_index', sa.Float(), nullable=False),
        sa.Column('hazard_score', sa.Float(), nullable=False),
        sa.Column('urgency_score', sa.Float(), nullable=False),
        sa.Column('bucket', sa.String(length=30), nullable=False),
        sa.Column('assigned_site_id', sa.String(length=100), nullable=True),
        sa.Column('unassigned_reason', sa.Text(), nullable=True),
        sa.Column('decision_reasons_json', sa.JSON(), nullable=False),
        sa.Column('data_origin', sa.String(length=30), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['assigned_site_id'], ['sites.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['district_id'], ['districts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_habitations_assigned_site_id'), 'habitations', ['assigned_site_id'], unique=False)
    op.create_index(op.f('ix_habitations_bucket'), 'habitations', ['bucket'], unique=False)
    op.create_index(op.f('ix_habitations_district_id'), 'habitations', ['district_id'], unique=False)
    op.create_index(op.f('ix_habitations_urgency_score'), 'habitations', ['urgency_score'], unique=False)

    op.create_table('ingestion_runs',
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('dataset_id', sa.String(length=100), nullable=False),
        sa.Column('district_id', sa.String(length=50), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('data_origin', sa.String(length=30), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('row_count', sa.Integer(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['district_id'], ['districts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ingestion_runs_dataset_id'), 'ingestion_runs', ['dataset_id'], unique=False)
    op.create_index(op.f('ix_ingestion_runs_district_id'), 'ingestion_runs', ['district_id'], unique=False)

    op.create_table('assignments',
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('scenario_id', sa.String(length=100), nullable=False),
        sa.Column('habitation_id', sa.String(length=100), nullable=False),
        sa.Column('site_id', sa.String(length=100), nullable=True),
        sa.Column('assigned_population', sa.Integer(), nullable=False),
        sa.Column('distance_km', sa.Float(), nullable=False),
        sa.Column('routing_method', sa.String(length=50), nullable=False),
        sa.Column('decision_rank', sa.Integer(), nullable=False),
        sa.Column('reasons_json', sa.JSON(), nullable=False),
        sa.Column('unassigned_reason', sa.Text(), nullable=True),
        sa.Column('solver_method', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['habitation_id'], ['habitations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['scenario_id'], ['scenarios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['site_id'], ['sites.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_assignments_habitation_id'), 'assignments', ['habitation_id'], unique=False)
    op.create_index(op.f('ix_assignments_scenario_id'), 'assignments', ['scenario_id'], unique=False)
    op.create_index(op.f('ix_assignments_site_id'), 'assignments', ['site_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_assignments_site_id'), table_name='assignments')
    op.drop_index(op.f('ix_assignments_scenario_id'), table_name='assignments')
    op.drop_index(op.f('ix_assignments_habitation_id'), table_name='assignments')
    op.drop_table('assignments')

    op.drop_index(op.f('ix_ingestion_runs_district_id'), table_name='ingestion_runs')
    op.drop_index(op.f('ix_ingestion_runs_dataset_id'), table_name='ingestion_runs')
    op.drop_table('ingestion_runs')

    op.drop_index(op.f('ix_habitations_urgency_score'), table_name='habitations')
    op.drop_index(op.f('ix_habitations_district_id'), table_name='habitations')
    op.drop_index(op.f('ix_habitations_bucket'), table_name='habitations')
    op.drop_index(op.f('ix_habitations_assigned_site_id'), table_name='habitations')
    op.drop_table('habitations')

    op.drop_index(op.f('ix_sites_final_capacity'), table_name='sites')
    op.drop_index(op.f('ix_sites_district_id'), table_name='sites')
    op.drop_table('sites')

    op.drop_index(op.f('ix_scenarios_district_id'), table_name='scenarios')
    op.drop_table('scenarios')

    op.drop_index(op.f('ix_rainfall_observations_district_id'), table_name='rainfall_observations')
    op.drop_table('rainfall_observations')

    op.drop_index(op.f('ix_events_district_id'), table_name='events')
    op.drop_table('events')

    op.drop_index(op.f('ix_datasets_district_id'), table_name='datasets')
    op.drop_table('datasets')

    op.drop_index(op.f('ix_cells_hazard_class'), table_name='cells')
    op.drop_index(op.f('ix_cells_district_id'), table_name='cells')
    op.drop_index(op.f('ix_cells_combined_hazard'), table_name='cells')
    op.drop_table('cells')

    op.drop_table('districts')
    op.drop_table('capacity_norms')
    op.drop_table('audit_log')
