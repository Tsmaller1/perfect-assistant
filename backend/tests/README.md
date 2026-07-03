# Integration Tests — Perfect Assistant Backend

Comprehensive pytest suite validating all database-backed components with multi-tenant isolation, transaction safety, and error handling.

## Test Coverage

### Unit Test Files

| File | Component | Tests |
|------|-----------|-------|
| `test_appointments.py` | AppointmentManager | 9 tests |
| `test_conversation_memory.py` | ConversationMemory | 9 tests |
| `test_payment_handoff.py` | PaymentHandoffManager | 9 tests |
| `test_action_queue.py` | ActionQueueManager | 10 tests |
| `test_database_operations.py` | Database & Transactions | 11 tests |
| **Total** | **5 Components** | **48 tests** |

### What Each Test File Validates

#### `test_appointments.py` (9 tests)
- ✅ Create appointments
- ✅ Check availability and detect conflicts
- ✅ Retrieve appointments (all, by status)
- ✅ Cancel appointments
- ✅ Update status
- ✅ Get daily schedule
- ✅ **Multi-tenant isolation**
- ✅ **Cross-tenant access prevention**

#### `test_conversation_memory.py` (9 tests)
- ✅ Create conversations
- ✅ Add messages with entity extraction
- ✅ Retrieve conversation context
- ✅ Close conversations
- ✅ Get recent conversations
- ✅ Intent detection (ORDER, RESERVATION, etc.)
- ✅ **Multi-tenant isolation**
- ✅ **Cross-tenant access prevention**

#### `test_payment_handoff.py` (9 tests)
- ✅ Create leads with qualification scoring
- ✅ Calculate qualification scores based on order value
- ✅ Complete payment transfers
- ✅ Retrieve leads
- ✅ Filter by qualification score
- ✅ Update lead status
- ✅ **Multi-tenant isolation**
- ✅ **Cross-tenant access prevention**

#### `test_action_queue.py` (10 tests)
- ✅ Broadcast actions (ORDER, APPOINTMENT, LEAD, RESERVATION)
- ✅ Update action status (NEW → IN_PROGRESS → COMPLETED)
- ✅ Retrieve recent actions with limit
- ✅ Persist actions to database
- ✅ **Multi-tenant isolation**
- ✅ **Cross-tenant access prevention**

#### `test_database_operations.py` (11 tests)
- ✅ Database connection validation
- ✅ Transaction commit on success
- ✅ Transaction rollback on error
- ✅ Invalid data handling
- ✅ Duplicate handling
- ✅ JSONB field persistence (transcripts)
- ✅ Status transition validation
- ✅ Data isolation between sessions

## Running Tests

### Prerequisites

```bash
# Install dependencies
cd backend
pip install -r requirements.txt
```

### Run All Tests

```bash
# From backend directory
pytest tests/ -v

# With coverage report
pytest tests/ -v --cov=. --cov-report=html
```

### Run Specific Test File

```bash
# Test appointments only
pytest tests/test_appointments.py -v

# Test conversations only
pytest tests/test_conversation_memory.py -v

# Test payments only
pytest tests/test_payment_handoff.py -v

# Test actions only
pytest tests/test_action_queue.py -v

# Test database operations only
pytest tests/test_database_operations.py -v
```

### Run Specific Test

```bash
# Run single test
pytest tests/test_appointments.py::test_book_appointment -v

# Run tests matching pattern
pytest tests/ -k "multi_tenant" -v
```

### Run with Output

```bash
# Show print statements and logging
pytest tests/ -v -s

# Show all assertions
pytest tests/ -vv
```

## Test Database

- **Type**: SQLite in-memory (`:memory:`)
- **Auto-setup**: Tables created before each test
- **Auto-cleanup**: Tables dropped after each test
- **Isolation**: Each test gets fresh database
- **Speed**: In-memory operations (~10ms per test)

## Test Data

Each test has access to `test_data` fixture providing:

```python
{
    "tenant_1_id": "tenant-1",
    "tenant_2_id": "tenant-2",
    "business_1": Business(...),  # Pizza shop
    "business_2": Business(...),  # Coffee shop
}
```

### Pre-loaded Data (Tenant 1)
- 2 Appointments (July 10, 2pm & 3pm)
- 1 Conversation (with transcript & entities)
- 1 Lead (qualification score 0.85)
- 1 Action (ORDER)

### Empty Tenant 2
- No appointments, conversations, leads, or actions
- Used to test multi-tenant isolation

## Understanding Test Results

### Passing Test Output
```
test_appointments.py::test_book_appointment PASSED                     [  2%]
test_appointments.py::test_check_availability_no_conflict PASSED       [  4%]
test_appointments.py::test_multi_tenant_isolation PASSED               [  6%]
...
======================== 48 passed in 2.34s ========================
```

### Multi-Tenant Isolation Tests
Each component has tests that verify:
1. **Data Isolation**: Tenant A cannot see Tenant B's data
2. **Access Prevention**: Tenant B cannot update Tenant A's records
3. **Query Filtering**: All queries automatically filter by tenant_id

Example test:
```python
@pytest.mark.asyncio
async def test_multi_tenant_isolation(test_session, test_data):
    """Verify tenant 1 and 2 data are completely isolated."""
    manager = AppointmentManager(test_session)
    
    # Get appointments for tenant 2 (empty)
    appointments = await manager.get_appointments("tenant-2")
    assert len(appointments) == 0  # ✓ No data leakage
    
    # Get appointments for tenant 1 (has data)
    appointments = await manager.get_appointments("tenant-1")
    assert len(appointments) == 2  # ✓ Can access own data
```

## Troubleshooting

### Issue: Tests fail with "ModuleNotFoundError"

**Solution**: Run from `backend` directory:
```bash
cd backend
pytest tests/ -v
```

### Issue: Tests fail with "sqlalchemy.exc.OperationalError"

**Solution**: Make sure SQLAlchemy and aiosqlite are installed:
```bash
pip install sqlalchemy>=2.0.0 aiosqlite>=0.19.0
```

### Issue: Tests timeout

**Solution**: Tests should complete in ~2-5 seconds. If they timeout:
1. Check if database connection is slow
2. Verify aiosqlite is installed (not psycopg2)
3. Run single test to isolate: `pytest tests/test_appointments.py::test_book_appointment -v`

### Issue: "FAILED test_x FAILED: loop is closed" error

**Solution**: Delete pytest cache and reinstall pytest-asyncio:
```bash
rm -rf .pytest_cache __pycache__
pip install --force-reinstall pytest-asyncio
```

## Continuous Integration

Tests are designed to run in CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Run integration tests
  run: |
    cd backend
    pip install -r requirements.txt
    pytest tests/ -v --tb=short
```

## Performance

- **Total Duration**: ~2-5 seconds for all 48 tests
- **Database Setup**: ~50ms (create tables in memory)
- **Per Test**: ~20-50ms average
- **No External Dependencies**: Tests don't require Supabase

## Next Steps

After tests pass:

1. **Dashboard Integration** (2-3 hours)
   - Connect frontend to real API
   - Replace stub endpoints

2. **Docker Containerization** (2-3 hours)
   - Create Dockerfile
   - Create docker-compose.yml

3. **CI/CD Pipeline** (2-3 hours)
   - GitHub Actions workflow
   - Automated testing on push

4. **Production Deployment** (4-6 hours)
   - Azure Container Instances
   - Load balancing
   - Monitoring

---

**Phase 4.4 Status**: Integration Test Infrastructure Ready ✅
