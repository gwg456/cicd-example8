# Database Schema Design

## Overview

The User Auth API uses a relational database design with SQLAlchemy ORM for Python. The schema is designed to support user authentication, role-based access control, and extensible permission management.

## Database Tables

### 1. Users Table

**Table Name:** `users`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTO_INCREMENT | Unique user identifier |
| username | VARCHAR(50) | UNIQUE, NOT NULL, INDEX | Unique username for login |
| email | VARCHAR(255) | UNIQUE, NOT NULL, INDEX | User's email address |
| full_name | VARCHAR(255) | NULLABLE | User's full display name |
| hashed_password | VARCHAR(255) | NOT NULL | Bcrypt hashed password |
| is_active | BOOLEAN | DEFAULT TRUE | Account activation status |
| is_superuser | BOOLEAN | DEFAULT FALSE | Superuser privileges flag |
| created_at | TIMESTAMP | DEFAULT NOW() | Account creation timestamp |
| updated_at | TIMESTAMP | ON UPDATE NOW() | Last update timestamp |

**Indexes:**
- Primary key index on `id`
- Unique index on `username`
- Unique index on `email`
- Index on `is_active` for filtering active users

**Constraints:**
- Username must be unique and not null
- Email must be unique, not null, and valid format
- Password must be hashed before storage
- created_at is set automatically on insertion
- updated_at is updated automatically on modification

### 2. Roles Table

**Table Name:** `roles`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTO_INCREMENT | Unique role identifier |
| name | VARCHAR(50) | UNIQUE, NOT NULL, INDEX | Role name (e.g., 'admin', 'user') |
| description | TEXT | NULLABLE | Role description |
| created_at | TIMESTAMP | DEFAULT NOW() | Role creation timestamp |

**Indexes:**
- Primary key index on `id`
- Unique index on `name`

**Constraints:**
- Role name must be unique and not null
- created_at is set automatically on insertion

### 3. Permissions Table

**Table Name:** `permissions`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTO_INCREMENT | Unique permission identifier |
| name | VARCHAR(100) | UNIQUE, NOT NULL, INDEX | Permission name (e.g., 'user:read') |
| description | TEXT | NULLABLE | Permission description |
| resource | VARCHAR(50) | NOT NULL | Resource type (e.g., 'user', 'role') |
| action | VARCHAR(50) | NOT NULL | Action type (e.g., 'read', 'write', 'delete') |
| created_at | TIMESTAMP | DEFAULT NOW() | Permission creation timestamp |

**Indexes:**
- Primary key index on `id`
- Unique index on `name`
- Composite index on (`resource`, `action`)

**Constraints:**
- Permission name must be unique and not null
- Resource and action are required fields
- created_at is set automatically on insertion

### 4. User-Roles Association Table

**Table Name:** `user_roles`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| user_id | INTEGER | FOREIGN KEY, NOT NULL | Reference to users.id |
| role_id | INTEGER | FOREIGN KEY, NOT NULL | Reference to roles.id |

**Indexes:**
- Composite primary key on (`user_id`, `role_id`)
- Index on `user_id`
- Index on `role_id`

**Constraints:**
- Foreign key constraint on `user_id` references `users(id)` ON DELETE CASCADE
- Foreign key constraint on `role_id` references `roles(id)` ON DELETE CASCADE
- Composite primary key ensures unique user-role combinations

### 5. Role-Permissions Association Table (Future Extension)

**Table Name:** `role_permissions`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| role_id | INTEGER | FOREIGN KEY, NOT NULL | Reference to roles.id |
| permission_id | INTEGER | FOREIGN KEY, NOT NULL | Reference to permissions.id |

**Indexes:**
- Composite primary key on (`role_id`, `permission_id`)
- Index on `role_id`
- Index on `permission_id`

**Constraints:**
- Foreign key constraint on `role_id` references `roles(id)` ON DELETE CASCADE
- Foreign key constraint on `permission_id` references `permissions(id)` ON DELETE CASCADE
- Composite primary key ensures unique role-permission combinations

## Relationships

### Many-to-Many: Users ↔ Roles

- A user can have multiple roles
- A role can be assigned to multiple users
- Relationship is managed through the `user_roles` association table
- SQLAlchemy relationship defined with `secondary` parameter

```python
# In User model
roles = relationship("Role", secondary=user_roles, back_populates="users")

# In Role model
users = relationship("User", secondary=user_roles, back_populates="roles")
```

### Many-to-Many: Roles ↔ Permissions (Future)

- A role can have multiple permissions
- A permission can belong to multiple roles
- Relationship managed through `role_permissions` association table

## Database Design Decisions

### 1. Password Security

- Passwords are never stored in plain text
- Using bcrypt hashing with salt for password storage
- Password validation enforced at application level (minimum 8 characters)

### 2. Soft Delete vs Hard Delete

- Currently implementing hard delete for simplicity
- Can be extended to soft delete by adding `deleted_at` column
- Soft delete recommended for production systems

### 3. Timestamp Management

- Using database-level timestamp defaults for consistency
- `created_at` set automatically on record creation
- `updated_at` updated automatically on record modification
- All timestamps stored in UTC for consistency

### 4. Indexing Strategy

- Primary keys are automatically indexed
- Unique constraints create implicit indexes
- Additional indexes on frequently queried columns:
  - `users.username` and `users.email` for login lookups
  - `users.is_active` for filtering active users
  - `roles.name` for role lookups
  - Composite indexes on association tables

### 5. Data Types

- Using appropriate data types for each field
- VARCHAR with defined lengths for better performance
- TEXT for longer content (descriptions)
- BOOLEAN for flags
- TIMESTAMP for time-related data

### 6. Referential Integrity

- Foreign key constraints ensure data consistency
- CASCADE delete on association tables
- Prevents orphaned records in junction tables

## Database Migrations

Using Alembic for database migrations:

```bash
# Generate migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Downgrade migrations
alembic downgrade -1
```

## Sample Data

### Default Roles

```sql
INSERT INTO roles (name, description) VALUES 
('admin', 'System administrator with full access'),
('manager', 'Manager with limited administrative access'),
('user', 'Regular user with basic access');
```

### Default Permissions

```sql
INSERT INTO permissions (name, description, resource, action) VALUES 
('user:read', 'Read user information', 'user', 'read'),
('user:write', 'Create and update users', 'user', 'write'),
('user:delete', 'Delete users', 'user', 'delete'),
('role:read', 'Read role information', 'role', 'read'),
('role:write', 'Create and update roles', 'role', 'write'),
('role:delete', 'Delete roles', 'role', 'delete');
```

## Performance Considerations

### 1. Query Optimization

- Use eager loading for relationships when needed
- Implement pagination for large datasets
- Use database indexes effectively

### 2. Connection Pooling

- Configure SQLAlchemy connection pool appropriately
- Monitor connection usage in production

### 3. Caching Strategy

- Consider caching frequently accessed user/role data
- Implement cache invalidation on user/role updates

## Security Considerations

### 1. Data Protection

- Sensitive data (passwords) are properly hashed
- Email addresses are validated at application level
- SQL injection prevention through ORM usage

### 2. Access Control

- Role-based access control implemented at API level
- Proper authentication required for all protected endpoints
- Superuser privileges clearly separated

### 3. Audit Trail (Future Enhancement)

- Consider adding audit tables for tracking changes
- Log important operations (login, role changes, etc.)
- Implement data retention policies

## Database Configuration

### Development

```python
SQLALCHEMY_DATABASE_URL = "sqlite:///./dev.db"
```

### Production

```python
SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost/dbname"
```

### Test

```python
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
```

## Backup and Recovery

### Backup Strategy

- Regular automated backups
- Point-in-time recovery capability
- Test backup restoration procedures

### Data Retention

- Define data retention policies
- Implement data archiving for old records
- Comply with data protection regulations (GDPR, etc.)

## Monitoring

### Database Health

- Monitor connection pool usage
- Track slow queries
- Monitor disk space usage

### Application Metrics

- User registration/login rates
- API response times
- Error rates by endpoint