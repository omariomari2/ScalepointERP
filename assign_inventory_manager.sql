-- SQL Script to assign Inventory Manager role to Raph
-- First, make sure the Inventory Manager role exists
DO $$
DECLARE
    role_id INTEGER;
    user_id INTEGER;
BEGIN
    -- Check if Inventory Manager role exists
    SELECT id INTO role_id FROM role WHERE name ILIKE 'Inventory Manager';
    
    -- Create the role if it doesn't exist
    IF role_id IS NULL THEN
        INSERT INTO role (name, description) 
        VALUES ('Inventory Manager', 'Manages inventory transfers and stock movements')
        RETURNING id INTO role_id;
        RAISE NOTICE 'Created Inventory Manager role with ID: %', role_id;
    ELSE
        RAISE NOTICE 'Found existing Inventory Manager role with ID: %', role_id;
    END IF;
    
    -- Find Raph's user ID
    SELECT id INTO user_id FROM "user" WHERE username = 'Raph';
    
    IF user_id IS NULL THEN
        RAISE EXCEPTION 'User Raph not found in database';
    ELSE
        RAISE NOTICE 'Found user Raph with ID: %', user_id;
    END IF;
    
    -- Check if the role is already assigned
    IF EXISTS (SELECT 1 FROM user_role WHERE user_id = user_id AND role_id = role_id) THEN
        RAISE NOTICE 'User Raph already has the Inventory Manager role';
    ELSE
        -- Assign the role
        INSERT INTO user_role (user_id, role_id) VALUES (user_id, role_id);
        RAISE NOTICE 'Successfully assigned Inventory Manager role to user Raph';
    END IF;
END $$;

-- Verify the assignment
SELECT u.username, r.name as role_name
FROM "user" u
JOIN user_role ur ON u.id = ur.user_id
JOIN role r ON ur.role_id = r.id
WHERE u.username = 'Raph';

-- List all users and their roles
SELECT u.username, r.name as role_name
FROM "user" u
LEFT JOIN user_role ur ON u.id = ur.user_id
LEFT JOIN role r ON ur.role_id = r.id
ORDER BY u.username, r.name; 