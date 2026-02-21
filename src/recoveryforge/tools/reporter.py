"""
Report generator for creating HTML/CSV/PDF reports.
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import json


logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generate comprehensive recovery reports in various formats.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_html_report(
        self,
        output_path: str,
        session_data: Dict[str, Any],
        file_stats: Dict[str, int],
        drive_health: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Generate HTML report.
        
        Args:
            output_path: Output file path
            session_data: Recovery session data
            file_stats: File type statistics
            drive_health: Optional drive health data
            
        Returns:
            True if successful
        """
        try:
            html_content = self._build_html_report(session_data, file_stats, drive_health)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"HTML report saved to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error generating HTML report: {e}")
            return False
    
    def generate_csv_report(
        self,
        output_path: str,
        files_data: List[Dict[str, Any]]
    ) -> bool:
        """
        Generate CSV report of recovered files.
        
        Args:
            output_path: Output file path
            files_data: List of file data dictionaries
            
        Returns:
            True if successful
        """
        try:
            import csv
            
            if not files_data:
                self.logger.warning("No file data to export")
                return False
            
            # Get headers from first file
            headers = list(files_data[0].keys())
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(files_data)
            
            self.logger.info(f"CSV report saved to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error generating CSV report: {e}")
            return False
    
    def generate_json_report(
        self,
        output_path: str,
        report_data: Dict[str, Any]
    ) -> bool:
        """
        Generate JSON report.
        
        Args:
            output_path: Output file path
            report_data: Complete report data
            
        Returns:
            True if successful
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            self.logger.info(f"JSON report saved to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error generating JSON report: {e}")
            return False
    
    def _build_html_report(
        self,
        session_data: Dict[str, Any],
        file_stats: Dict[str, int],
        drive_health: Optional[Dict[str, Any]]
    ) -> str:
        """Build HTML report content."""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>RecoveryForge Recovery Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #1e1e2e;
            color: #ffffff;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: #2d2d3d;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }}
        h1 {{
            color: #5b9dff;
            margin-top: 0;
        }}
        h2 {{
            color: #5b9dff;
            border-bottom: 2px solid #404050;
            padding-bottom: 10px;
        }}
        .stat-card {{
            display: inline-block;
            background-color: #3d3d4d;
            padding: 20px;
            margin: 10px;
            border-radius: 8px;
            min-width: 200px;
        }}
        .stat-label {{
            color: #b0b0b0;
            font-size: 14px;
        }}
        .stat-value {{
            color: #5b9dff;
            font-size: 28px;
            font-weight: bold;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #404050;
        }}
        th {{
            background-color: #3d3d4d;
            color: #5b9dff;
            font-weight: bold;
        }}
        tr:hover {{
            background-color: #3d3d4d;
        }}
        .footer {{
            margin-top: 40px;
            text-align: center;
            color: #b0b0b0;
            font-size: 12px;
        }}
        .success {{ color: #50fa7b; }}
        .warning {{ color: #ffb86c; }}
        .error {{ color: #ff5555; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>RecoveryForge Recovery Report</h1>
        <p>Generated: {timestamp}</p>
        
        <h2>Session Summary</h2>
        <div>
            <div class="stat-card">
                <div class="stat-label">Files Found</div>
                <div class="stat-value">{session_data.get('files_found', 0)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Files Recovered</div>
                <div class="stat-value">{session_data.get('files_recovered', 0)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Data Scanned</div>
                <div class="stat-value">{self._format_bytes(session_data.get('bytes_scanned', 0))}</div>
            </div>
        </div>
        
        <h2>File Type Breakdown</h2>
        <table>
            <thead>
                <tr>
                    <th>File Type</th>
                    <th>Count</th>
                    <th>Percentage</th>
                </tr>
            </thead>
            <tbody>
"""
        
        # Add file type statistics
        total_files = sum(file_stats.values())
        for file_type, count in sorted(file_stats.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_files * 100) if total_files > 0 else 0
            html += f"""
                <tr>
                    <td>{file_type.title()}</td>
                    <td>{count}</td>
                    <td>{percentage:.1f}%</td>
                </tr>
"""
        
        html += """
            </tbody>
        </table>
"""
        
        # Add drive health if available
        if drive_health:
            html += f"""
        <h2>Drive Health</h2>
        <div class="stat-card">
            <div class="stat-label">Health Status</div>
            <div class="stat-value {self._get_health_class(drive_health.get('health_percent', 0))}">{drive_health.get('health_percent', 0):.1f}%</div>
        </div>
"""
        
        html += """
        <div class="footer">
            <p>Generated by RecoveryForge v1.0.0</p>
            <p>Open-source data recovery tool - https://github.com/r22gir/RecoveryForge</p>
        </div>
    </div>
</body>
</html>
"""
        
        return html
    
    def _format_bytes(self, bytes_val: int) -> str:
        """Format bytes to human-readable string."""
        units = ["B", "KB", "MB", "GB", "TB"]
        unit_index = 0
        size = float(bytes_val)
        
        while size >= 1024.0 and unit_index < len(units) - 1:
            size /= 1024.0
            unit_index += 1
        
        return f"{size:.2f} {units[unit_index]}"
    
    def _get_health_class(self, health_percent: float) -> str:
        """Get CSS class for health percentage."""
        if health_percent >= 80:
            return "success"
        elif health_percent >= 60:
            return "warning"
        else:
            return "error"
