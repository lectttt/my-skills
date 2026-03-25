# Phase 3: Architecture and Structuring

## Objective

**STRUCTURE** the agent optimally: folders, files, responsibilities, cache, performance.

## Detailed Process

### Step 1: Define Agent Name

Based on domain and objective, create a descriptive kebab-case name per the Agent Skills Open Standard.

**Format**: `{domain}-{objective}` or `{action}-{object}`

**Examples**:
- US Agriculture → `nass-usda-agriculture`
- Stock analysis → `stock-technical-analysis`
- Global climate → `noaa-climate-analysis`
- Brazil CONAB → `conab-crop-yield-analysis`

**Rules**:
- 1-64 characters
- Lowercase letters, numbers, and hyphens only
- Must not start or end with a hyphen
- Must not contain consecutive hyphens
- Must match parent directory name
- Descriptive but concise

### Step 2: Directory Structure

**Decision**: How many levels of organization?

**Option A - Simple** (small agents):
```
skill-name/
├── SKILL.md               ← Primary file, spec-compliant frontmatter
├── scripts/
│   └── main.py
├── references/
│   └── guide.md
├── assets/
│   └── config.json
├── install.sh             ← Cross-platform installer
└── README.md              ← Multi-platform install instructions
```

**Option B - Organized** (medium agents):
```
skill-name/
├── SKILL.md               ← Primary file, spec-compliant frontmatter
├── scripts/
│   ├── fetch.py
│   ├── parse.py
│   ├── analyze.py
│   └── utils/
│       ├── cache.py
│       └── validators.py
├── references/
│   ├── api-guide.md
│   └── methodology.md
├── assets/
│   └── config.json
├── install.sh
└── README.md
```

**Option C - Complete** (complex agents):
```
skill-name/
├── SKILL.md               ← Primary file, spec-compliant frontmatter
├── scripts/
│   ├── core/
│   │   ├── fetch_[source].py
│   │   ├── parse_[source].py
│   │   └── analyze_[source].py
│   ├── models/
│   │   ├── forecasting.py
│   │   └── ml_models.py
│   └── utils/
│       ├── cache_manager.py
│       ├── rate_limiter.py
│       └── validators.py
├── references/
│   ├── api/
│   │   └── [api-name]-guide.md
│   ├── methods/
│   │   └── analysis-methods.md
│   └── troubleshooting.md
├── assets/
│   ├── config.json
│   └── metadata.json
├── install.sh
├── README.md
└── data/
    ├── raw/
    ├── processed/
    ├── cache/
    └── analysis/
```

**Note**: Simple skills do NOT need `.claude-plugin/marketplace.json`. For complex skill suites with multiple component skills, an optional `marketplace.json` with ONLY official fields may be added.

**Choose based on**:
- Number of scripts (1-2 → A, 3-5 → B, 6+ → C)
- Analysis complexity
- Prefer starting with B, expand to C if needed

### Step 3: Define Script Responsibilities

**Principle**: Separation of Concerns

**Typical scripts**:

**1. fetch_[source].py**
- **Responsibility**: API requests, authentication, rate limiting
- **Input**: Query parameters (commodity, year, etc)
- **Output**: Raw JSON from API
- **Does NOT**: Parse, transform, analyze
- **Size**: 200-300 lines

**2. parse_[source].py**
- **Responsibility**: Parsing, cleaning, validation
- **Input**: API JSON
- **Output**: Structured DataFrame
- **Does NOT**: Fetch, analyze
- **Size**: 150-200 lines

**3. analyze_[source].py**
- **Responsibility**: All analyses (YoY, ranking, etc)
- **Input**: Clean DataFrame
- **Output**: Dict with results
- **Does NOT**: Fetch, parse
- **Size**: 300-500 lines (all analyses)

**Typical utils**:

**cache_manager.py**:
- Manage response cache
- Differentiated TTL
- ~100-150 lines

**rate_limiter.py**:
- Control rate limit
- Persistent counter
- Alerts
- ~100-150 lines

**validators.py**:
- Data validations
- Consistency checks
- ~100-150 lines

**unit_converter.py** (if needed):
- Unit conversions
- ~50-100 lines

### Step 4: Plan References

**Typical files**:

**api-guide.md** (~1500 words):
- How to get API key
- Main endpoints with examples
- Important parameters
- Response format
- Limitations and quirks
- API troubleshooting

**analysis-methods.md** (~2000 words):
- Each analysis explained
- Mathematical formulas
- Interpretations
- Validations
- Concrete examples

**troubleshooting.md** (~1000 words):
- Common problems
- Step-by-step solutions
- FAQs

**domain-context.md** (optional, ~1000 words):
- Domain context
- Terminology
- Important concepts
- Benchmarks

### Step 5: Plan Assets

**config.json**:
- API settings (URL, rate limits, timeouts)
- Cache settings (TTLs, directories)
- Analysis defaults
- Validation thresholds

**Typical structure**:
```json
{
  "api": {
    "base_url": "...",
    "api_key_env": "VAR_NAME",
    "rate_limit_per_day": 1000,
    "timeout_seconds": 30
  },
  "cache": {
    "enabled": true,
    "dir": "data/cache",
    "ttl_historical_days": 365,
    "ttl_current_days": 7
  },
  "defaults": {
    "param1": "value1"
  },
  "validation": {
    "threshold1": 0.01
  }
}
```

**metadata.json** (if needed):
- Domain-specific metadata
- Mappings (aliases)
- Conversions (units)
- Groupings (regions)

**Example**:
```json
{
  "commodities": {
    "CORN": {
      "aliases": ["corn", "maize"],
      "unit": "BU",
      "conversion_to_mt": 0.0254
    }
  },
  "regions": {
    "MIDWEST": ["IA", "IL", "IN", "OH"]
  }
}
```

### Step 6: Cache Strategy

**Decision**: What to cache and for how long?

**General rule**:
- **Historical data** (year < current): Permanent cache (365+ days)
- **Current year data**: Short cache (7 days - may be revised)
- **Metadata** (commodity lists, states): Permanent cache

**Implementation**:
- Cache by key (parameter hash)
- Check age before using
- Fallback to expired cache if API fails

**Example**:
```python
def get_cache_ttl(year: int) -> timedelta:
    """Determine cache TTL based on year"""
    current_year = datetime.now().year

    if year < current_year:
        # Historical: cache for 1 year (effectively permanent)
        return timedelta(days=365)
    else:
        # Current year: cache for 7 days (may be revised)
        return timedelta(days=7)
```

### Step 7: Rate Limiting Strategy

**Decision**: How to control rate limits?

**Components**:
1. **Persistent counter** (file/DB)
2. **Pre-request verification**
3. **Alerts** (when near limit)
4. **Blocking** (when limit reached)

**Implementation**:
```python
class RateLimiter:
    def __init__(self, max_requests: int, period_seconds: int):
        self.max_requests = max_requests
        self.period = period_seconds
        self.counter_file = Path("data/cache/rate_limit_counter.json")

    def allow_request(self) -> bool:
        """Check if request is allowed"""
        count = self._get_current_count()

        if count >= self.max_requests:
            return False

        # Warn when near limit
        if count > self.max_requests * 0.9:
            print(f"⚠️ Rate limit: {count}/{self.max_requests} requests used")

        return True

    def record_request(self):
        """Record that request was made"""
        count = self._get_current_count()
        self._save_count(count + 1)
```

### Step 8: Document Architecture

Create section in DECISIONS.md:

```markdown
## Phase 3: Architecture

### Chosen Structure

```
[Directory tree]
```

**Justification**:
- Separate scripts for modularity
- Utils for reusable code
- References for progressive disclosure
- Data/ to separate raw vs processed

### Defined Scripts

**fetch_[source].py** (280 lines estimated):
- Responsibility: [...]
- Input/Output: [...]

[For each script...]

### Cache Strategy

- Historical: Permanent cache
- Current: 7 day cache
- Justification: [historical data doesn't change]

### Rate Limiting

- Method: [persistent counter]
- Limits: [1000/day]
- Alerts: [>90% usage]
```

## Phase 3 Checklist

- [ ] Agent name defined
- [ ] Directory structure chosen (A/B/C)
- [ ] Responsibilities of each script defined
- [ ] References planned (which files, content)
- [ ] Assets planned (which configs, structure)
- [ ] Cache strategy defined (what, TTL)
- [ ] Rate limiting strategy defined
- [ ] Architecture documented in DECISIONS.md
