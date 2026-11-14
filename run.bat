@echo off
if "%~1"=="" (
  python -m src.main --package A --test-mode --repository tests\fixtures\acyclic.txt --ascii-tree --load-order
) else (
  python -m src.main %*
)
