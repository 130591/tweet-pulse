#!/bin/bash
# Script para executar testes de integração do Tweet Pulse
# Uso: ./scripts/run_tests.sh [opções]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
VERBOSE=false
COVERAGE=false
PARALLEL=false
PATTERN=""
MARKERS=""
FAILFAST=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -v|--verbose)
      VERBOSE=true
      shift
      ;;
    -c|--coverage)
      COVERAGE=true
      shift
      ;;
    -p|--parallel)
      PARALLEL=true
      shift
      ;;
    -k|--pattern)
      PATTERN="$2"
      shift 2
      ;;
    -m|--markers)
      MARKERS="$2"
      shift 2
      ;;
    -x|--failfast)
      FAILFAST=true
      shift
      ;;
    -h|--help)
      echo "Uso: ./scripts/run_tests.sh [opções]"
      echo ""
      echo "Opções:"
      echo "  -v, --verbose      Saída verbose"
      echo "  -c, --coverage     Gerar relatório de cobertura"
      echo "  -p, --parallel     Executar testes em paralelo"
      echo "  -k, --pattern STR  Filtrar testes por padrão"
      echo "  -m, --markers STR  Filtrar testes por marker"
      echo "  -x, --failfast     Parar no primeiro erro"
      echo "  -h, --help         Mostrar esta mensagem"
      echo ""
      echo "Exemplos:"
      echo "  ./scripts/run_tests.sh -v -c"
      echo "  ./scripts/run_tests.sh -k storage -v"
      echo "  ./scripts/run_tests.sh -m asyncio -p"
      exit 0
      ;;
    *)
      echo -e "${RED}Opção desconhecida: $1${NC}"
      exit 1
      ;;
  esac
done

# Print header
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Tweet Pulse - Testes de Integração${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Build pytest command
PYTEST_CMD="pytest tests/test_integration/"

if [ "$VERBOSE" = true ]; then
  PYTEST_CMD="$PYTEST_CMD -vv"
else
  PYTEST_CMD="$PYTEST_CMD -v"
fi

if [ "$COVERAGE" = true ]; then
  PYTEST_CMD="$PYTEST_CMD --cov=tweetpulse.ingestion --cov-report=html --cov-report=term-missing"
fi

if [ "$PARALLEL" = true ]; then
  PYTEST_CMD="$PYTEST_CMD -n auto"
fi

if [ -n "$PATTERN" ]; then
  PYTEST_CMD="$PYTEST_CMD -k $PATTERN"
fi

if [ -n "$MARKERS" ]; then
  PYTEST_CMD="$PYTEST_CMD -m $MARKERS"
fi

if [ "$FAILFAST" = true ]; then
  PYTEST_CMD="$PYTEST_CMD -x"
fi

# Print command
echo -e "${YELLOW}Executando: $PYTEST_CMD${NC}"
echo ""

# Run tests
if eval $PYTEST_CMD; then
  echo ""
  echo -e "${GREEN}✓ Todos os testes passaram!${NC}"
  
  if [ "$COVERAGE" = true ]; then
    echo ""
    echo -e "${GREEN}Relatório de cobertura gerado em: htmlcov/index.html${NC}"
  fi
  
  exit 0
else
  echo ""
  echo -e "${RED}✗ Alguns testes falharam${NC}"
  exit 1
fi
