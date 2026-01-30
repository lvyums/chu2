# AGENTS.md - Agentic Coding Guidelines for chu2

This file provides guidance for AI coding agents operating in this repository.

## Essential Commands

### Development Server
```bash
python app.py
```
Access at http://127.0.0.1:5000

### Database Operations
| Command | Description |
|---------|-------------|
| `python migrate.py init` | Initialize database schema |
| `python migrate.py migrate` | Migrate data from JSON to database |
| `python migrate.py validate` | Validate coordinate ranges and year constraints |
| `python migrate.py all` | Initialize schema and migrate data |

### Testing
```bash
python test.py                      # Run all test cases
python test.py TestClass.test_method  # Run specific test
```
**Note**: Currently no test.py exists. Tests should be added when implementing new features.

### Docker Deployment
```bash
docker-compose up -d --build        # Build and start containers
docker-compose exec web python migrate.py init     # Init DB in container
docker-compose exec web python migrate.py migrate  # Migrate data in container
```

---

## Code Style Guidelines

### Python (Flask) Conventions

**Imports** (standard library → third-party → local):
```python
import json
import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import database
from database import db, Model
```

**Naming**:
- Functions/variables: `snake_case` (e.g., `load_sites_data`, `db_url`)
- Classes: `PascalCase` (e.g., `ArchaeologicalSite`, `QuizQuestion`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `BASE_DIR`, `API_BASE_URL`)

**Type Hints**: Minimal usage; only when beneficial:
```python
def init_app(app: Flask) -> None:
    ...
```

**Error Handling**: Try-except with descriptive print statements:
```python
try:
    with app.app_context():
        sites = ArchaeologicalSite.query.all()
except Exception as e:
    print(f"数据库查询失败: {e}")
    return jsonify({"error": "Database query failed"}), 500
```

**Documentation**:
- Module-level docstrings in Chinese
- Function docstrings for public APIs:
```python
def get_map_data():
    """获取所有遗址数据"""
    ...
```

**Model Patterns**:
- Use SQLAlchemy `db.Model` base class
- Define `__tablename__` explicitly
- Include `to_dict()` method for serialization
- Use `db.CheckConstraint` for validation:
```python
__table_args__ = (
    db.CheckConstraint('year BETWEEN -770 AND -221', name='valid_year_range'),
)
```

### JavaScript Conventions

**Module Structure**:
- One module per feature (e.g., `mapModule.js`, `gameModule.js`)
- Named exports for functions:
```javascript
export async function initMap() { ... }
```

**Async Patterns**:
```javascript
try {
    const response = await fetch(`${API_BASE_URL}/sites`);
    const data = await response.json();
    // handle data
} catch (error) {
    console.error("地图数据加载失败", error);
}
```

**Event Handling**: Traditional handlers (onclick attributes in HTML):
```javascript
btn.onclick = () => this.checkAnswer(index, btn);
```

**Naming**: camelCase for variables/functions, UPPER_SNAKE for constants

### HTML Templates (Jinja2)
- Located in `templates/` directory
- Rendered by Flask routes using `render_template()`
- Static assets served from `static/` folder

---

## Critical Constraints

### Data Validation
- Year values: **-770 to -221** (enforced by CheckConstraint)
- Coordinates: **WGS84 decimal degrees** (73.0°-135.0°E, 15.0°-54.0°N)
- Quiz answers: **integers 0-3** (CheckConstraint enforced)

### Database Schema
- Artifacts data: still maintained in JSON (`artifacts.json`)
- Quiz questions/sites: migrated to SQLite/PostgreSQL via `migrate.py`
- Always run `migrate.py migrate` after modifying JSON data files

### Frontend Initialization
- Map functionality depends on `mapModule.js` initialization sequence
- Game module auto-initializes and loads from `quiz_questions.json`
- Coordinate validation fails for non-WGS84 systems (GCJ-02 prohibited)

---

## Project Structure

```
chu2/
├── app.py              # Flask application entry point
├── database.py         # SQLAlchemy models and init
├── migrate.py          # Database migration utility
├── sites.json          # Archaeological sites data
├── quiz_questions.json # Quiz question bank
├── artifacts.json      # Artifact data (JSON-only)
├── requirements.txt    # Python dependencies
├── static/
│   └── js/
│       ├── mapModule.js      # Map visualization
│       ├── gameModule.js     # Quiz game logic
│       └── galleryModule.js  # Gallery functionality
└── templates/
    └── *.html         # Jinja2 templates
```

---

## Development Workflow

1. **Modify JSON data** → run `python migrate.py migrate`
2. **Add new API endpoint** → add route in `app.py`, use `db.Model`
3. **Add new model** → define in `database.py`, run `migrate.py init`
4. **Frontend changes** → edit corresponding JS module in `static/js/`

## No-Go Areas

- Never use `as any`, `@ts-ignore`, or suppress type errors
- Never commit without explicit user request
- Never delete or modify `.json_history/` backup files
- Never leave code in broken state after failures
