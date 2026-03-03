# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

YDT 2721 is a satellite link budget calculation software implementing the Chinese telecommunications industry standard YD/T 2721-2014 "Link Budget Calculation Methods for Geostationary Satellite Fixed Services". It calculates complete satellite communication link budgets including clear-sky and rain-fade scenarios.

## Development Commands

### Installation
```bash
pip install -e .
```

### Running Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test module
python -m pytest tests/test_satellite.py -v

# Run with coverage
python -m pytest tests/ --cov=src/ydt2721
```

### Running Examples
```bash
# Basic demo
python examples/demo.py

# Full integration test
python examples/test_all.py
```

### CLI Usage
```bash
# Generate parameter template
python cli.py template --output config.json

# Execute calculation with config file
python cli.py calculate --config config.json --output report --format all

# Validate parameters
python cli.py validate --config config.json
```

## Architecture

### Modular Calculation Pipeline

The codebase follows a strictly modular design where each module (M02-M07) implements a specific portion of the YDT 2721 standard. The main `complete_link_budget()` function in `calculator.py` orchestrates all modules in sequence:

1. **M02 (satellite.py)**: Satellite SFD calculation, antenna gain per area
2. **M03 (carrier.py)**: Symbol rate, noise bandwidth, allocated bandwidth, bandwidth ratio
3. **M04 (earth_station.py)**: Antenna gain, pointing angles (elevation/azimuth), G/T value
4. **M05 (space_loss.py)**: Free space loss, rain attenuation, rain noise temperature
5. **M06 (clear_sky.py)**: C/N calculations (uplink, downlink, total), interference, margin
6. **M07 (rain_impact.py)**: Rain impact on uplink (with UPC compensation) and downlink

### Key Design Patterns

- **Data Flow**: All calculation results flow through the `LinkBudgetResult` dataclass. Each module's output becomes input for subsequent modules.
- **Parameter Validation**: `param_manager.py` contains `ParameterValidator` with predefined ranges for all parameters. Always validate inputs before calculation.
- **Configuration Management**: JSON-based config files map to dataclasses (`SatelliteParams`, `CarrierParams`, `EarthStationParams`). Use `ParameterManager` for templates.

### Module Dependencies

```
calculator.py (main entry point)
├── core.satellite → SFD, antenna gain per area
├── core.carrier → symbol rate, bandwidth
├── core.earth_station → antenna gain, pointing, G/T
├── core.space_loss → free space loss, rain attenuation
├── core.clear_sky → C/N calculations, margin
└── core.rain_impact → UPC compensation, rain C/N
```

### Output Generation

The `output/` module provides multiple report formats:
- `MarkdownReportGenerator`: Human-readable markdown reports
- `ExcelReportGenerator`: Spreadsheet reports using pandas/openpyxl
- `JSONExporter`: Machine-readable data export
- `PDFReportGenerator`: Formal PDF reports

All generators take `(config, result, output_file)` as parameters.

## Important Implementation Details

### Frequency Units
- Satellite calculations use **Hz** internally
- User-facing parameters use **GHz** for convenience
- Always convert: `frequency_hz = frequency_ghz * 1e9`

### Modulation Support
The code supports BPSK, QPSK, 8PSK, 16QAM with modulation indices defined in `constants.py:MODULATION_INDEX`.

### Parameter Ranges
Critical parameter ranges are enforced in `param_manager.py:ParameterValidator.RANGES`. When adding new parameters, update this dict.

### Interference Calculations
Interference is optional in `complete_link_budget()`. When interference parameters are None, they default to 99 dB (negligible impact).

### UPC Compensation
Uplink Power Control (UPC) compensates for rain attenuation on the uplink, limited by `upc_max` parameter.

## Testing Strategy

- Unit tests in `tests/test_*.py` validate individual module calculations
- Integration test in `tests/test_integration.py` validates end-to-end calculations
- Reference values from YDT 2721 Appendix C are used for validation
