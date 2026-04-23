# RetailLang

## Requirements

- Python 3.10 or higher
- pip

## Local setup

### 1. Clone the repository

```bash
git clone https://github.com/stjamessoto/CSC415-Final-Project.git
cd CSC415-Final-Project
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
pip install -e .
```

### 3. Verify the install

```bash
python main.py --version
```

## Running the project

### Web IDE (recommended)

Launches a Streamlit browser app with a command editor, output tabs, and live chart preview.

```bash
python main.py web
```

Open **http://localhost:8501** in your browser. Use the sidebar to load example commands or type your own.

Default login credentials:

| Username | Password   |
|----------|------------|
| admin    | retail123  |
| analyst  | analyst123 |
| demo     | demo       |

To disable the login screen for local development:

```bash
python main.py web --no-auth
```

### Command line

Run a single RetailLang command:

```bash
python main.py run "Load data/sales.csv and compute total revenue by region"
```

Run a `.rl` script file:

```bash
python main.py run examples/revenue_by_region.rl --file
```

Save output to a file:

```bash
# Save generated Python code
python main.py run "Load data/sales.csv and compute total revenue by region" --output result.py

# Save as SQL
python main.py run "Load data/sales.csv and compute total revenue by region" --output result.sql

# Save chart as HTML
python main.py run "Load data/sales.csv and generate a bar chart" --output chart.html
```

Translate a command to SQL:

```bash
python main.py sql "Load data/sales.csv and compute total revenue by region"
```

Show the token stream (debug):

```bash
python main.py tokens "Load data/sales.csv and compute total revenue by region"
```

Show the AST (debug):

```bash
python main.py parse "Load data/sales.csv and compute total revenue by region"
```

Validate a `.rl` file without executing it:

```bash
python main.py validate examples/revenue_by_region.rl
```

### Interactive REPL

```bash
python main.py repl
```

Type commands at the `retaillang>` prompt. Type `help` for available REPL commands, `examples` for sample queries, or `exit` to quit.

## Running the tests

```bash
python -m pytest tests/ -v
```

With coverage report:

```bash
python -m pytest tests/ --cov=retaillang --cov=generators --cov-report=term-missing
```

## Project structure

```
CSC415-Final-Project/
├── retaillang/          # Language core: lexer, parser, AST, executor
├── generators/          # Code generators: Pandas, SQL, chart, pivot, JSON
├── app/                 # Streamlit web IDE
├── tests/               # Test suite
├── data/                # Sample CSV datasets
├── examples/            # Example .rl script files
├── docs/                # Design documents and grammar spec
├── deploy/              # Docker and cloud deployment configs
├── main.py              # CLI entry point
└── requirements.txt
```

## Example commands

```
Load data/sales.csv and compute total revenue by region
Load data/sales.csv and compute average profit by product
Load data/sales.csv, filter by region = West, and compute total revenue by product
Load data/sales.csv and compute total revenue by region and sort by revenue descending
Load data/sales.csv, compute total revenue by region, and generate a bar chart
Load data/sales.csv, compute total revenue by region, and generate a line chart
Load data/sales.csv and create a pivot table by product and region
Load data/customers.csv and compute average total_spent by segment
```
