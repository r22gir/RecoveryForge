# Setup Guide

## System Requirements

### Operating System
- **Linux**: Ubuntu 20.04+ / Debian 10+ / Fedora 33+
- **Windows**: Windows 10 or later
- **macOS**: macOS 11 (Big Sur) or later

### Hardware
- **CPU**: Dual-core processor or better
- **RAM**: 4GB minimum, 8GB+ recommended
- **Storage**: 1GB for installation, additional space for recovered files
- **Python**: 3.8 or higher

## Installation

### Step 1: Install Python Dependencies

```bash
# Clone the repository
git clone https://github.com/r22gir/RecoveryForge.git
cd RecoveryForge

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python packages
pip install -r requirements.txt
```

### Step 2: Install System Dependencies

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y \
    scalpel \
    testdisk \
    tesseract-ocr \
    smartmontools \
    python3-magic \
    libmagic1
```

#### Fedora
```bash
sudo dnf install -y \
    scalpel \
    testdisk \
    tesseract \
    smartmontools \
    python3-magic \
    file-libs
```

#### macOS
```bash
brew install \
    scalpel \
    testdisk \
    tesseract \
    smartmontools \
    libmagic
```

#### Windows
1. Install Python 3.8+ from [python.org](https://www.python.org)
2. Download and install:
   - Tesseract OCR: https://github.com/UB-Mannheim/tesseract/wiki
   - Smartmontools: https://www.smartmontools.org/
3. Add installation directories to PATH

### Step 3: Optional - Install AI Features

For advanced AI-powered tagging with YOLO v8:

```bash
pip install torch torchvision ultralytics
```

Note: This adds ~2GB of dependencies and requires GPU for optimal performance.

## Configuration

### Basic Configuration

RecoveryForge works with sensible defaults, but you can customize settings:

```bash
# Copy example configuration
cp config/default_config.yaml config/user_config.yaml

# Edit configuration
nano config/user_config.yaml
```

### SMART Monitoring Setup

For drive health monitoring, ensure smartmontools is properly configured:

#### Linux
```bash
# Enable SMART on your drives
sudo smartctl -s on /dev/sda

# Test SMART access
sudo smartctl -a /dev/sda
```

#### Windows
Run as Administrator:
```cmd
smartctl -s on \\.\PhysicalDrive0
smartctl -a \\.\PhysicalDrive0
```

## Running RecoveryForge

### GUI Application

```bash
# Run from project directory
python -m src.recoveryforge

# Or if installed
recoveryforge
```

### Command Line (Future)

```bash
# Quick scan
recoveryforge scan /path/to/scan --output ~/recovered

# Full scan with all features
recoveryforge scan /dev/sda1 --all-features --output ~/recovered
```

## Troubleshooting

### "Permission Denied" Errors

RecoveryForge may need elevated privileges for:
- Raw device access
- SMART monitoring
- Low-level disk operations

**Linux/macOS:**
```bash
sudo python -m src.recoveryforge
```

**Windows:**
Right-click and "Run as Administrator"

### PyQt6 Import Errors

If PyQt6 fails to import:

```bash
# Try reinstalling
pip uninstall PyQt6 PyQt6-Qt6 PyQt6-sip
pip install --no-cache-dir PyQt6
```

### SMART Monitoring Not Working

1. Verify smartmontools is installed:
   ```bash
   smartctl --version
   ```

2. Check drive support:
   ```bash
   sudo smartctl -i /dev/sda
   ```

3. Enable SMART if disabled:
   ```bash
   sudo smartctl -s on /dev/sda
   ```

### Tesseract OCR Errors

1. Verify installation:
   ```bash
   tesseract --version
   ```

2. Install language data if needed:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install tesseract-ocr-eng
   
   # macOS
   brew install tesseract-lang
   ```

### Memory Issues

For large disk scans, increase chunk size in configuration:

```yaml
scanner:
  chunk_size: 2097152  # 2MB instead of 1MB
  max_memory: 4096  # Maximum MB to use
```

## Getting Help

- **Documentation**: Check `docs/` directory
- **Issues**: [GitHub Issues](https://github.com/r22gir/RecoveryForge/issues)
- **Discussions**: [GitHub Discussions](https://github.com/r22gir/RecoveryForge/discussions)

## Next Steps

1. Read the [User Manual](user_manual.md) for detailed usage instructions
2. Check [API Documentation](api_documentation.md) if integrating with other tools
3. Review [Algorithms](algorithms.md) to understand how recovery works
4. See [Recovery Scenarios](recovery_scenarios.md) for common use cases
