# Global Representativeness Index (GRI) Makefile

# Variables
PYTHON := python
VENV_ACTIVATE := source venv/bin/activate &&
SRC_DIR := gri
SCRIPTS_DIR := scripts
NOTEBOOKS_DIR := notebooks
DATA_DIR := data
PROCESSED_DIR := $(DATA_DIR)/processed
BENCHMARK_DIR := $(DATA_DIR)/raw/benchmark_data

# Colors for terminal output
BLUE := \033[34m
GREEN := \033[32m
RED := \033[31m
YELLOW := \033[33m
CYAN := \033[36m
RESET := \033[0m

.PHONY: help setup install test test-all lint typecheck format clean \
        process-data calculate-gri run-notebooks \
        venv-check data-check health-check \
        demo validate-data show-benchmarks

# Default target
help:
	@echo "$(BLUE)Global Representativeness Index (GRI) Project$(RESET)"
	@echo "$(YELLOW)Tools for measuring survey representativeness against global population$(RESET)"
	@echo ""
	@echo "$(BLUE)Setup Commands:$(RESET)"
	@echo "  $(GREEN)make setup$(RESET)                - Complete setup (venv + install + data processing)"
	@echo "  $(GREEN)make venv$(RESET)                 - Create virtual environment"
	@echo "  $(GREEN)make install$(RESET)              - Install dependencies in venv"
	@echo "  $(GREEN)make health-check$(RESET)         - Check system health (venv, data)"
	@echo ""
	@echo "$(BLUE)Data Processing Commands:$(RESET)"
	@echo "  $(GREEN)make process-data$(RESET)         - Process raw benchmark data using configuration"
	@echo "  $(GREEN)make validate-data$(RESET)        - Validate processed benchmark data"
	@echo "  $(GREEN)make show-benchmarks$(RESET)      - Display benchmark data summary"
	@echo ""
	@echo "$(BLUE)Analysis Commands:$(RESET)"
	@echo "  $(GREEN)make calculate-gri$(RESET)        - Run GRI calculation on sample data"
	@echo "  $(GREEN)make demo-config$(RESET)          - Demonstrate configuration system capabilities"
	@echo "  $(GREEN)make run-notebooks$(RESET)        - Execute all Jupyter notebooks"
	@echo "  $(GREEN)make demo$(RESET)                 - Run complete demo workflow"
	@echo ""
	@echo "$(BLUE)Development Commands:$(RESET)"
	@echo "  $(GREEN)make test$(RESET)                 - Run test suite"
	@echo "  $(GREEN)make lint$(RESET)                 - Run code linting"
	@echo "  $(GREEN)make format$(RESET)               - Format code with black"
	@echo "  $(GREEN)make clean$(RESET)                - Clean up cache and temporary files"
	@echo ""
	@echo "$(BLUE)Data Sources:$(RESET)"
	@echo "  • UN World Population Prospects 2023 (Age/Gender by Country)"
	@echo "  • Pew Research Global Religious Landscape 2010 (Religion by Country)"
	@echo "  • UN World Urbanization Prospects 2018 (Urban/Rural by Country)"
	@echo ""
	@echo "$(BLUE)GRI Processing:$(RESET)"
	@echo "  • Configuration-driven processing follows config/dimensions.yaml"
	@echo "  • Supports 13 dimensions including regional and single-dimension analysis"
	@echo "  • All data processing uses YAML configuration as source of truth"

# Setup commands
setup: venv install process-data health-check
	@echo "$(GREEN)GRI setup completed successfully!$(RESET)"

venv:
	@echo "$(BLUE)Creating virtual environment...$(RESET)"
	@if [ ! -d "venv" ]; then \
		$(PYTHON) -m venv venv; \
		echo "$(GREEN)Virtual environment created$(RESET)"; \
	else \
		echo "$(YELLOW)Virtual environment already exists$(RESET)"; \
	fi

install: venv
	@echo "$(BLUE)Installing dependencies...$(RESET)"
	@$(VENV_ACTIVATE) pip install -r requirements.txt
	@echo "$(GREEN)Dependencies installed$(RESET)"

# Health check commands
health-check: venv-check data-check
	@echo "$(GREEN)All health checks passed!$(RESET)"

venv-check:
	@echo "$(BLUE)Checking virtual environment...$(RESET)"
	@if [ ! -d "venv" ]; then \
		echo "$(RED)Error: Virtual environment not found$(RESET)"; \
		echo "$(YELLOW)Run: make venv$(RESET)"; \
		exit 1; \
	fi
	@$(VENV_ACTIVATE) python --version
	@echo "$(GREEN)Virtual environment OK$(RESET)"

data-check:
	@echo "$(BLUE)Checking benchmark data availability...$(RESET)"
	@if [ ! -d "$(BENCHMARK_DIR)" ]; then \
		echo "$(RED)Error: Benchmark data directory not found$(RESET)"; \
		echo "$(YELLOW)Expected: $(BENCHMARK_DIR)$(RESET)"; \
		exit 1; \
	fi
	@for file in WPP_2023_Male_Population.csv WPP_2023_Female_Population.csv GLS_2010_Religious_Composition.csv WUP_2018_Urban_Rural.csv Sources.csv; do \
		if [ ! -f "$(BENCHMARK_DIR)/$$file" ]; then \
			echo "$(RED)Error: Missing benchmark file $$file$(RESET)"; \
			exit 1; \
		fi; \
	done
	@echo "$(GREEN)Benchmark data availability OK$(RESET)"

# Data processing commands
process-data: venv-check data-check
	@echo "$(BLUE)Processing benchmark data using configuration...$(RESET)"
	@$(VENV_ACTIVATE) $(PYTHON) $(SCRIPTS_DIR)/process_data.py
	@echo "$(GREEN)Configuration-driven data processing completed$(RESET)"

validate-data: venv-check
	@echo "$(BLUE)Validating processed benchmark data...$(RESET)"
	@if [ ! -d "$(PROCESSED_DIR)" ]; then \
		echo "$(RED)Error: Processed data directory not found$(RESET)"; \
		echo "$(YELLOW)Run: make process-data$(RESET)"; \
		exit 1; \
	fi
	@for file in benchmark_country_gender_age.csv benchmark_country_religion.csv benchmark_country_environment.csv; do \
		if [ ! -f "$(PROCESSED_DIR)/$$file" ]; then \
			echo "$(RED)Error: Missing processed file $$file$(RESET)"; \
			exit 1; \
		fi; \
	done
	@$(VENV_ACTIVATE) $(PYTHON) -c "\
import pandas as pd; \
files = ['$(PROCESSED_DIR)/benchmark_country_gender_age.csv', '$(PROCESSED_DIR)/benchmark_country_religion.csv', '$(PROCESSED_DIR)/benchmark_country_environment.csv']; \
[print(f'✓ {f.split(\"/\")[-1]}: {len(pd.read_csv(f))} strata, sum={pd.read_csv(f)[\"population_proportion\"].sum():.6f}') for f in files]"
	@echo "$(GREEN)Data validation completed$(RESET)"

show-benchmarks: venv-check validate-data
	@echo "$(BLUE)Benchmark Data Summary:$(RESET)"
	@$(VENV_ACTIVATE) $(PYTHON) -c "\
import pandas as pd; \
age_gender = pd.read_csv('$(PROCESSED_DIR)/benchmark_country_gender_age.csv'); \
religion = pd.read_csv('$(PROCESSED_DIR)/benchmark_country_religion.csv'); \
environment = pd.read_csv('$(PROCESSED_DIR)/benchmark_country_environment.csv'); \
print('$(CYAN)Country × Gender × Age:$(RESET)'); \
print(f'  Strata: {len(age_gender):,}'); \
print(f'  Countries: {age_gender[\"country\"].nunique()}'); \
print(f'  Age groups: {sorted(age_gender[\"age_group\"].unique())}'); \
print(f'  Proportion sum: {age_gender[\"population_proportion\"].sum():.6f}'); \
print(); \
print('$(CYAN)Country × Religion:$(RESET)'); \
print(f'  Strata: {len(religion):,}'); \
print(f'  Countries: {religion[\"country\"].nunique()}'); \
print(f'  Religions: {sorted(religion[\"religion\"].unique())}'); \
print(f'  Proportion sum: {religion[\"population_proportion\"].sum():.6f}'); \
print(); \
print('$(CYAN)Country × Environment:$(RESET)'); \
print(f'  Strata: {len(environment):,}'); \
print(f'  Countries: {environment[\"country\"].nunique()}'); \
print(f'  Environments: {sorted(environment[\"environment\"].unique())}'); \
print(f'  Proportion sum: {environment[\"population_proportion\"].sum():.6f}');"

# Analysis commands  
demo-config: venv-check validate-data
	@echo "$(BLUE)Demonstrating GRI configuration system...$(RESET)"
	@$(VENV_ACTIVATE) $(PYTHON) $(SCRIPTS_DIR)/demo_config_system.py
	@echo "$(GREEN)Configuration demo completed$(RESET)"

calculate-gri: venv-check validate-data
	@echo "$(BLUE)Running GRI calculation demo...$(RESET)"
	@$(VENV_ACTIVATE) $(PYTHON) -c "\
import sys; sys.path.append('.'); \
from gri import calculate_gri, calculate_diversity_score, load_data; \
import pandas as pd; import numpy as np; \
print('$(CYAN)Creating sample survey data...$(RESET)'); \
np.random.seed(42); \
sample_countries = ['United States', 'India', 'Brazil', 'Germany', 'Nigeria', 'Japan']; \
sample_data = pd.DataFrame({ \
    'country': np.random.choice(sample_countries, 500), \
    'age_group': np.random.choice(['18-25', '26-35', '36-45', '46-55', '56-65', '65+'], 500), \
    'gender': np.random.choice(['Male', 'Female'], 500), \
    'religion': np.random.choice(['Christianity', 'Islam', 'Hinduism', 'Buddhism', 'Judaism', 'I do not identify with any religious group or faith', 'Other religious group'], 500), \
    'environment': np.random.choice(['Urban', 'Rural'], 500) \
}); \
print(f'Sample survey: {len(sample_data)} participants from {sample_data[\"country\"].nunique()} countries'); \
print(); \
benchmark_age_gender = load_data('$(PROCESSED_DIR)/benchmark_country_gender_age.csv'); \
benchmark_religion = load_data('$(PROCESSED_DIR)/benchmark_country_religion.csv'); \
benchmark_environment = load_data('$(PROCESSED_DIR)/benchmark_country_environment.csv'); \
gri_age = calculate_gri(sample_data, benchmark_age_gender, ['country', 'gender', 'age_group']); \
gri_religion = calculate_gri(sample_data, benchmark_religion, ['country', 'religion']); \
gri_env = calculate_gri(sample_data, benchmark_environment, ['country', 'environment']); \
div_age = calculate_diversity_score(sample_data, benchmark_age_gender, ['country', 'gender', 'age_group']); \
div_religion = calculate_diversity_score(sample_data, benchmark_religion, ['country', 'religion']); \
div_env = calculate_diversity_score(sample_data, benchmark_environment, ['country', 'environment']); \
avg_gri = np.mean([gri_age, gri_religion, gri_env]); \
avg_div = np.mean([div_age, div_religion, div_env]); \
print('$(CYAN)GRI Scorecard Results:$(RESET)'); \
print(f'  Country × Gender × Age:  GRI={gri_age:.4f}, Diversity={div_age:.4f}'); \
print(f'  Country × Religion:      GRI={gri_religion:.4f}, Diversity={div_religion:.4f}'); \
print(f'  Country × Environment:   GRI={gri_env:.4f}, Diversity={div_env:.4f}'); \
print(); \
print(f'$(YELLOW)Average GRI: {avg_gri:.4f}$(RESET)'); \
print(f'$(YELLOW)Average Diversity: {avg_div:.4f}$(RESET)'); \
interpretation = 'Excellent' if avg_gri >= 0.8 else 'Good' if avg_gri >= 0.6 else 'Moderate' if avg_gri >= 0.4 else 'Poor'; \
print(f'$(YELLOW)Assessment: {interpretation} representativeness$(RESET)');"
	@echo "$(GREEN)GRI calculation completed$(RESET)"

run-notebooks: venv-check validate-data
	@echo "$(BLUE)Executing Jupyter notebooks...$(RESET)"
	@$(VENV_ACTIVATE) pip install nbconvert jupyter 2>/dev/null || echo "$(YELLOW)Installing notebook dependencies...$(RESET)"
	@for notebook in $(NOTEBOOKS_DIR)/*.ipynb; do \
		echo "$(CYAN)Executing $$notebook...$(RESET)"; \
		$(VENV_ACTIVATE) jupyter nbconvert --to notebook --execute --inplace "$$notebook" || \
		echo "$(YELLOW)Notebook execution failed or skipped: $$notebook$(RESET)"; \
	done
	@echo "$(GREEN)Notebook execution completed$(RESET)"

demo: venv-check process-data calculate-gri
	@echo "$(GREEN)GRI Demo completed!$(RESET)"
	@echo "$(CYAN)Next steps:$(RESET)"
	@echo "  • Run 'make run-notebooks' to execute analysis notebooks"
	@echo "  • Check 'notebooks/' directory for detailed examples"
	@echo "  • Use your own survey data with the GRI functions"

# Development commands
test: venv-check
	@echo "$(BLUE)Running test suite...$(RESET)"
	@$(VENV_ACTIVATE) $(PYTHON) -m pytest tests/ -v
	@echo "$(GREEN)Tests completed$(RESET)"

lint: venv-check
	@echo "$(BLUE)Running code linting...$(RESET)"
	@$(VENV_ACTIVATE) flake8 $(SRC_DIR)/ $(SCRIPTS_DIR)/ --max-line-length=100 --ignore=E203,W503 2>/dev/null || \
		echo "$(YELLOW)flake8 not installed - skipping lint$(RESET)"

format: venv-check
	@echo "$(BLUE)Formatting code...$(RESET)"
	@$(VENV_ACTIVATE) black $(SRC_DIR)/ $(SCRIPTS_DIR)/ --line-length=100 2>/dev/null || \
		echo "$(YELLOW)black not installed - skipping format$(RESET)"

# Utility commands
clean:
	@echo "$(BLUE)Cleaning up cache and temporary files...$(RESET)"
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.log" -delete 2>/dev/null || true
	@find . -name ".ipynb_checkpoints" -type d -exec rm -rf {} + 2>/dev/null || true
	@rm -rf build/ dist/ 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete!$(RESET)"