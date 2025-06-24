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
        process-data calculate-gri scorecard run-notebooks \
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
	@echo "  $(GREEN)make calculate-gri$(RESET)        - Run GRI calculation on Global Dialogues data"
	@echo "  $(GREEN)make calculate-gri GD=<N>$(RESET) - Run GRI calculation on specific GD dataset (e.g., GD=3)"
	@echo "  $(GREEN)make scorecard$(RESET)            - Generate comprehensive scorecards for all GD surveys"
	@echo "  $(GREEN)make scorecard GD=<N>$(RESET)     - Generate scorecard for specific GD (e.g., GD=3)"
	@echo "  $(GREEN)make scorecard SIMPLIFIED=1$(RESET) - Use simplified country benchmarks for conservative VWRS"
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
	@echo "$(BLUE)Validating processed benchmark data using configuration...$(RESET)"
	@$(VENV_ACTIVATE) $(PYTHON) $(SCRIPTS_DIR)/validate_data_config.py
	@echo "$(GREEN)Configuration-driven data validation completed$(RESET)"

show-benchmarks: venv-check validate-data
	@$(VENV_ACTIVATE) $(PYTHON) $(SCRIPTS_DIR)/show_benchmarks_config.py

# Analysis commands

calculate-gri: venv-check validate-data
	@echo "$(BLUE)Running configuration-driven GRI calculation demo...$(RESET)"
	@if [ -n "$(GD)" ]; then \
		$(VENV_ACTIVATE) $(PYTHON) $(SCRIPTS_DIR)/calculate_gri_config.py --gd $(GD); \
	else \
		$(VENV_ACTIVATE) $(PYTHON) $(SCRIPTS_DIR)/calculate_gri_config.py; \
	fi
	@echo "$(GREEN)Configuration-driven GRI calculation completed$(RESET)"

scorecard: venv-check validate-data
	@echo "$(BLUE)Generating comprehensive GRI scorecards...$(RESET)"
	@if [ -n "$(GD)" ]; then \
		echo "  Generating scorecard for GD$(GD)"; \
		if [ "$(SIMPLIFIED)" = "1" ]; then \
			echo "  Using simplified country benchmarks (31 major countries)"; \
			$(VENV_ACTIVATE) $(PYTHON) $(SCRIPTS_DIR)/generate_gd_scorecards.py --gd $(GD) --simplified; \
		else \
			$(VENV_ACTIVATE) $(PYTHON) $(SCRIPTS_DIR)/generate_gd_scorecards.py --gd $(GD); \
		fi \
	else \
		echo "  Generating scorecards for all GD surveys"; \
		if [ "$(SIMPLIFIED)" = "1" ]; then \
			echo "  Using simplified country benchmarks (31 major countries)"; \
			$(VENV_ACTIVATE) $(PYTHON) $(SCRIPTS_DIR)/generate_gd_scorecards.py --simplified; \
		else \
			$(VENV_ACTIVATE) $(PYTHON) $(SCRIPTS_DIR)/generate_gd_scorecards.py; \
		fi \
	fi
	@echo "$(GREEN)Scorecard generation complete!$(RESET)"
	@echo "  Scorecards saved to: analysis_output/scorecards/"

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