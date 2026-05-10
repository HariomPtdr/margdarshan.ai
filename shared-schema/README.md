# grievance-schema

The UCO contract. Every service imports this package.

## Install (locally during development)

```bash
pip install -e ./shared-schema
```

In a service's `requirements.txt`:

```
grievance-schema @ file:///app/shared-schema
```

## Usage

```python
from grievance_schema import UCO, LocationData, ChatRequest, PipelineEvent
```

## Versioning

Bump version in `setup.py` for ANY breaking change. All services must update together.
