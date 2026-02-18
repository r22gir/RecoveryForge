# RecoveryForge User Manual

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [User Interface](#user-interface)
4. [Recovery Workflows](#recovery-workflows)
5. [Advanced Features](#advanced-features)
6. [Best Practices](#best-practices)

## Introduction

RecoveryForge is a professional-grade data recovery tool designed to recover deleted or lost files from storage devices. It combines multiple recovery techniques with an intuitive user interface.

### Key Features

- **File Carving**: Recover files based on signatures (200+ file types)
- **SMART Monitoring**: Check drive health before recovery
- **Deduplication**: Identify and remove duplicate files
- **Content Analysis**: Extract metadata and classify files
- **Modern UI**: Dark-themed interface with real-time updates

## Getting Started

### Launching RecoveryForge

```bash
python -m src.recoveryforge
```

The main window will open with four main tabs:
1. **Dashboard**: Overview of recovery operations
2. **Drive Manager**: Select drives for scanning
3. **Scanner**: Configure and run recovery scans
4. **File Browser**: View and manage recovered files

### Quick Recovery Workflow

1. Go to **Drive Manager** tab
2. Select the drive containing lost files
3. Switch to **Scanner** tab
4. Choose output directory
5. Select file types to recover
6. Click "Start Scan"
7. View results in **File Browser**
8. Select files and recover

## User Interface

### Dashboard

The dashboard provides real-time statistics:

- **Files Found**: Total files discovered during scan
- **Files Recovered**: Files successfully recovered
- **Data Scanned**: Amount of data processed
- **Scan Progress**: Current scan completion percentage

**File Types Discovered** shows breakdown by category (images, documents, etc.)

### Drive Manager

Displays all detected storage devices with:

- **Device path** (e.g., /dev/sda1, C:\)
- **Model** and serial number
- **Filesystem type** (NTFS, ext4, etc.)
- **Capacity** (total, used, free space)
- **Removable status** (USB drives, SD cards)

**Actions:**
- Click "Select for Scan" to choose a drive
- Click "Refresh" to update drive list

### Scanner Panel

Configure your recovery scan:

**Scan Source:**
- Browse to select file or device to scan
- Can scan disk images (.img, .dd files)

**Output Directory:**
- Choose where recovered files will be saved
- Creates subdirectories by file type

**File Types:**
- Select which types to recover
- Options: Images, Documents, Videos, Audio, Archives, Executables, Databases
- "All Types" for comprehensive scan

**Controls:**
- **Start Scan**: Begin recovery operation
- **Stop**: Cancel ongoing scan
- **Progress Bar**: Shows scan completion
- **Log**: Displays scan events and errors

### File Browser

View and manage discovered files:

**Features:**
- **Search**: Filter files by name or type
- **Table View**: Shows filename, type, category, size, offset
- **Multi-select**: Ctrl+click or Shift+click to select multiple
- **Sort**: Click column headers to sort

**Actions:**
- **Select All**: Select all visible files
- **Deselect All**: Clear selection
- **Recover Selected**: Recover checked files to output directory

## Recovery Workflows

### Recovering Deleted Photos

1. **Select Source**: Choose SD card or camera drive
2. **Configure Scan**:
   - Check only "Images" type
   - Set output to "~/RecoveredPhotos"
3. **Start Scan**: Monitor progress
4. **Review Results**: Preview thumbnails in browser
5. **Select Quality Files**: Filter by quality score
6. **Recover**: Save selected photos

### Recovering Documents from Formatted Drive

1. **Health Check**: Use Drive Manager to check SMART status
2. **Full Scan**:
   - Select formatted drive
   - Enable "Documents" and "Archives"
   - Start comprehensive scan
3. **Deduplication**: Run deduplicator on results
4. **Organization**: Group by date or folder structure
5. **Validation**: Check file integrity scores
6. **Recovery**: Recover validated files

### Emergency Data Recovery

When a drive is failing:

1. **Immediate Backup**: If drive is still accessible, backup first
2. **Health Assessment**: Check SMART data for imminent failure
3. **Quick Scan**: Focus on critical file types only
4. **Priority Recovery**: Recover most important files first
5. **Stop on Errors**: Don't stress failing drive further

## Advanced Features

### Drive Health Monitoring

Access SMART data to assess drive condition:

- **Health Percentage**: Overall drive health (0-100%)
- **Temperature**: Current drive temperature
- **Power-On Hours**: Total operating time
- **Reallocated Sectors**: Bad sectors remapped
- **Pending Sectors**: Sectors waiting for reallocation

**Warning Signs:**
- Health < 80%: Warning - backup soon
- Health < 60%: Critical - backup immediately
- Pending sectors > 0: Imminent failure risk

### Deduplication

Find and remove duplicate files:

1. After recovery, select files to check
2. Choose deduplication method:
   - **Exact**: SHA-256 hash matching
   - **Fuzzy**: ssdeep similarity (requires ssdeep)
   - **Metadata**: Name/size matching
3. Review duplicate groups
4. Keep best copy (oldest, best location)
5. Delete duplicates to save space

### Content Analysis

Extract metadata from recovered files:

- **Images**: EXIF data (camera, GPS, date)
- **Documents**: Author, title, creation date
- **PDFs**: Page count, text content
- **Videos**: Resolution, duration, codec

### Quality Scoring

Each recovered file gets a quality score (0-100%):

- **100%**: Complete, valid file
- **80-99%**: Minor issues, likely usable
- **50-79%**: Partial recovery, may be corrupted
- **<50%**: Heavily corrupted or incomplete

**Factors:**
- File size (too small = incomplete)
- Entropy (randomness check)
- Header/footer validation
- Structure consistency

### Reporting

Generate comprehensive reports:

**HTML Report:**
- Visual summary with charts
- File type breakdown
- Drive health analysis
- Recovery statistics

**CSV Export:**
- Spreadsheet of all recovered files
- Metadata for each file
- Import into Excel/Sheets

**JSON Export:**
- Machine-readable format
- For automation/integration
- Complete session data

## Best Practices

### Before Recovery

1. **Stop Using Drive**: Prevent overwriting deleted data
2. **Check Health**: Assess drive condition with SMART
3. **Plan Output**: Ensure enough space for recovered files
4. **Know What to Recover**: Focus on specific file types

### During Recovery

1. **Monitor Progress**: Watch for errors or slow progress
2. **Don't Interrupt**: Let scan complete if possible
3. **Note Errors**: Log any issues for troubleshooting
4. **Save Session**: Some features support resuming

### After Recovery

1. **Validate Files**: Check that files open correctly
2. **Run Deduplication**: Remove duplicates to save space
3. **Organize Files**: Sort by type, date, or importance
4. **Backup**: Create backup of recovered files
5. **Generate Report**: Document recovery for records

### Performance Tips

- **USB 3.0**: Use fast interface for external drives
- **Local Output**: Save to fast local drive, not network
- **Limit Types**: Only scan needed file types
- **Close Programs**: Free up memory during scan
- **SSD vs HDD**: SSDs scan faster than HDDs

### Security Considerations

- **Private Data**: Recovered files may contain sensitive information
- **Secure Deletion**: Use secure erase before disposal
- **Encryption**: Consider encrypting recovered data
- **Ransomware**: Scan recovered files for malware

## Troubleshooting

### Scan is Very Slow

- Check drive health - failing drives are slow
- Reduce chunk size in settings
- Close other programs using the drive
- Check for USB 2.0 vs 3.0 connection

### No Files Found

- Verify correct drive selected
- Try scanning with "All Types"
- Data may be overwritten beyond recovery
- Check scan log for errors

### Files are Corrupted

- Lower quality files may be incomplete
- Try different recovery method
- Use file repair tools for specific formats
- Partial recovery is sometimes unavoidable

### Permission Errors

- Run as administrator/sudo for device access
- Check file system permissions
- Ensure output directory is writable
- Some devices require elevated privileges

## Getting Help

- **Documentation**: docs/ directory
- **GitHub Issues**: Report bugs or request features
- **Discussions**: Ask questions, share tips
- **Email**: support@recoveryforge.org (if available)

---

For technical details, see [API Documentation](api_documentation.md)
