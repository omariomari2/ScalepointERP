"""
Helper guide for using Cloud SQL Proxy to connect to PostgreSQL database
"""

print("""
To connect to the PostgreSQL database in Google Cloud SQL from your local machine,
you need to use the Cloud SQL Auth Proxy. Here are the steps:

1. Download the Cloud SQL Auth Proxy:
   - Windows: https://dl.google.com/cloudsql/cloud_sql_proxy_x64.exe
   - Mac/Linux: https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64

2. Make sure you're authenticated with Google Cloud:
   Run: gcloud auth login

3. Start the Cloud SQL Auth Proxy:
   Run: cloud_sql_proxy.exe -instances=erp-system-445701:us-central1:erp-database=tcp:5432

4. The proxy will create a local PostgreSQL port (5432) that forwards to your Cloud SQL instance

5. Use a database client like pgAdmin or DBeaver to connect to localhost:5432 with these credentials:
   - Host: localhost
   - Port: 5432
   - Database: erpsystem
   - Username: erpuser
   - Password: ERPuser2025!

6. Or run this command in a new terminal to access PostgreSQL directly:
   psql "host=localhost port=5432 dbname=erpsystem user=erpuser password=ERPuser2025!"

7. Once connected, you can run the following SQL to assign the Inventory Manager role to Raph:

   -- Find user ID for Raph
   SELECT id FROM "user" WHERE username = 'Raph';
   
   -- Find role ID for Inventory Manager
   SELECT id FROM role WHERE name ILIKE 'Inventory Manager';
   
   -- Assign role to user (replace user_id and role_id with values from above queries)
   INSERT INTO user_role (user_id, role_id) VALUES (user_id, role_id);
   
   -- Verify assignment
   SELECT u.username, r.name 
   FROM "user" u
   JOIN user_role ur ON u.id = ur.user_id
   JOIN role r ON ur.role_id = r.id
   WHERE u.username = 'Raph';
""") 