-- Seed data for roles, users, watchlists
INSERT INTO roles (id, name, permissions) VALUES
('role_operator', 'Operator', '["view_alerts", "view_cameras"]'::jsonb),
('role_investigator', 'Investigator', '["view_alerts", "view_cameras", "manage_cases", "run_queries"]'::jsonb),
('role_command', 'Command', '["view_all", "manage_users"]'::jsonb);

INSERT INTO users (id, username, password_hash, role_id, badge_number) VALUES
('user_1', 'op1', 'hash1', 'role_operator', 'B101'),
('user_2', 'inv1', 'hash2', 'role_investigator', 'B201'),
('user_3', 'cmd1', 'hash3', 'role_command', 'B301');

INSERT INTO watchlists (id, type, name, description) VALUES
('wl_1', 'vehicle', 'Stolen Vehicles', 'List of recently stolen vehicles'),
('wl_2', 'person', 'Wanted Persons', 'High profile wanted criminals');

INSERT INTO watchlist_items (id, watchlist_id, entity_id, entity_type, attributes, reason) VALUES
('wli_1', 'wl_1', NULL, 'vehicle', '{"license_plate": "GJ01XX0000"}'::jsonb, 'Stolen motorcycle reported on 2026-08-18');
