sql_for_create_roles = """
INSERT INTO roles (role_id, role) VALUES
(1, 'ADMIN'),
(2, 'STUDENT'),
(3, 'FACULTY');
"""

sql_for_create_admin = """
INSERT INTO users (
    id,
    first_name,
    last_name,
    email,
    phone,
    password,
    role_id,
    is_deleted,
    created_at,
    updated_at
)
VALUES (
    '7fa41ff5-d127-4d4a-b9b4-65f1b8b8b8b8'::uuid,
    'admin',
    'admin',
    'admin@admin.com',
    '+910000000000',
    '$2b$12$m08HRslO4jwlf04qRolf9eLsd.FLDHhjP5Dlen2WTQi6aJZkyeixa',
    1,
    false,
    now(),
    now()
);
"""
#the default password is "Admin@123" we need to change it based on hashing algorithm
