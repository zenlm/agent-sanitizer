"""Core sanitizer logic for cleaning agent logs."""

import json
import re
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from tqdm import tqdm

from .detectors import SecurityDetector


class AgentSanitizer:
    """Sanitize agent logs for safe sharing."""
    
    def __init__(self, detector: Optional[SecurityDetector] = None):
        self.detector = detector or SecurityDetector()
        self.stats = {
            'files_processed': 0,
            'lines_processed': 0,
            'lines_modified': 0,
            'replacements': {},
        }
        
        # Replacement patterns
        self.replacements = [
            # Credentials
            (re.compile(r'\bsk-[a-zA-Z0-9]{48,}\b'), '[REDACTED_API_KEY]'),
            (re.compile(r'\bsk-ant-[a-zA-Z0-9\-]{95,}\b'), '[REDACTED_API_KEY]'),
            (re.compile(r'\bghp_[a-zA-Z0-9]{36}\b'), '[REDACTED_GITHUB_TOKEN]'),
            (re.compile(r'Bearer\s+[a-zA-Z0-9\-._~+/]+=*', re.I), 'Bearer [REDACTED_TOKEN]'),
            
            # Passwords (conservative - only if quoted)
            (re.compile(r'(?:password|passwd|pwd)[\s:=]+["\']([^"\']{6,})["\']', re.I),
             lambda m: m.group(0).replace(m.group(1), '[REDACTED_PASSWORD]')),
            
            # SSH/PGP keys
            (re.compile(r'-----BEGIN .*? PRIVATE KEY-----.*?-----END .*? PRIVATE KEY-----', re.S),
             '[REDACTED_PRIVATE_KEY]'),
        ]
        
        # Email safe list
        self.safe_emails = {'user@example.com', 'test@example.com', 'admin@example.com'}
    
    def scan_directory(self, directory: Path, format: str = 'auto') -> Dict[str, int]:
        """Scan directory and return issue summary."""
        issues = {}
        
        # Find log files based on format
        if format == 'auto':
            format = self._detect_format(directory)
        
        files = self._find_log_files(directory, format)
        
        for file_path in tqdm(files, desc="Scanning"):
            file_issues = self._scan_file(file_path, format)
            for category, count in file_issues.items():
                issues[category] = issues.get(category, 0) + count
        
        issues['total'] = sum(v for k, v in issues.items() if k != 'total')
        return issues
    
    def sanitize_directory(
        self,
        input_dir: Path,
        output_dir: Path,
        dry_run: bool = False,
        format: str = 'auto'
    ) -> Dict:
        """Sanitize all files in directory."""
        if format == 'auto':
            format = self._detect_format(input_dir)
        
        files = self._find_log_files(input_dir, format)
        
        if not dry_run:
            # Create backup
            backup_dir = input_dir.parent / f"{input_dir.name}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create output structure
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / 'splits').mkdir(exist_ok=True)
        
        for file_path in tqdm(files, desc="Sanitizing"):
            relative = file_path.relative_to(input_dir)
            output_file = output_dir / relative
            
            self._sanitize_file(file_path, output_file, format, dry_run)
        
        return self.stats
    
    def _detect_format(self, directory: Path) -> str:
        """Auto-detect log format."""
        # Check for Claude Code logs
        if (directory / 'projects').exists() or directory.name == 'projects':
            return 'claude'
        # Check for Cursor logs
        if 'cursor' in str(directory).lower():
            return 'cursor'
        # Check for Continue logs
        if 'continue' in str(directory).lower():
            return 'continue'
        # Default
        return 'claude'
    
    def _find_log_files(self, directory: Path, format: str) -> list[Path]:
        """Find log files based on format."""
        if format == 'claude':
            # Claude Code: Look for JSONL files in projects directory
            if directory.name == 'projects':
                return list(directory.glob('*/*.jsonl'))
            elif (directory / 'projects').exists():
                return list((directory / 'projects').glob('*/*.jsonl'))
            else:
                return list(directory.rglob('*.jsonl'))
        else:
            # Generic: Find all JSONL files
            return list(directory.rglob('*.jsonl'))
    
    def _scan_file(self, file_path: Path, format: str) -> Dict[str, int]:
        """Scan single file for issues."""
        issues = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        data = json.loads(line)
                        text = self._extract_text(data, format)
                        location = f"{file_path.name}:L{line_num}"
                        file_issues = self.detector.scan_text(text, location)
                        
                        for category, count in file_issues.items():
                            issues[category] = issues.get(category, 0) + count
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass
        
        return issues
    
    def _sanitize_file(
        self,
        input_path: Path,
        output_path: Path,
        format: str,
        dry_run: bool
    ):
        """Sanitize single file."""
        cleaned_lines = []
        lines_modified = 0
        
        try:
            with open(input_path, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    self.stats['lines_processed'] += 1
                    
                    try:
                        data = json.loads(line)
                        cleaned_data, was_modified = self._sanitize_interaction(data, format)
                        
                        if was_modified:
                            lines_modified += 1
                            self.stats['lines_modified'] += 1
                        
                        cleaned_lines.append(json.dumps(cleaned_data, ensure_ascii=False))
                    except json.JSONDecodeError:
                        cleaned_lines.append(line.rstrip())
            
            if not dry_run:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    for line in cleaned_lines:
                        f.write(line + '\n')
            
            self.stats['files_processed'] += 1
            
        except Exception as e:
            print(f"Error processing {input_path}: {e}")
    
    def _extract_text(self, data: dict, format: str) -> str:
        """Extract all text from interaction."""
        texts = []
        
        if format == 'claude':
            for item in data.get('content', []):
                if item.get('type') == 'thinking':
                    texts.append(item.get('thinking', ''))
                elif item.get('type') == 'text':
                    texts.append(item.get('text', ''))
            texts.append(data.get('cwd', ''))
        else:
            # Generic extraction
            texts.append(json.dumps(data))
        
        return ' '.join(texts)
    
    def _sanitize_interaction(self, data: dict, format: str) -> tuple[dict, bool]:
        """Sanitize single interaction."""
        modified = False
        
        if format == 'claude':
            # Sanitize content blocks
            for item in data.get('content', []):
                if item.get('type') == 'thinking' and 'thinking' in item:
                    cleaned, was_modified = self._clean_text(item['thinking'])
                    if was_modified:
                        item['thinking'] = cleaned
                        modified = True
                
                if item.get('type') == 'text' and 'text' in item:
                    cleaned, was_modified = self._clean_text(item['text'])
                    if was_modified:
                        item['text'] = cleaned
                        modified = True
            
            # Sanitize cwd
            if 'cwd' in data:
                cleaned, was_modified = self._clean_text(data['cwd'])
                if was_modified:
                    data['cwd'] = cleaned
                    modified = True
        else:
            # Generic sanitization
            data_str = json.dumps(data)
            cleaned, was_modified = self._clean_text(data_str)
            if was_modified:
                data = json.loads(cleaned)
                modified = True
        
        return data, modified
    
    def _clean_text(self, text: str) -> tuple[str, bool]:
        """Clean text and return (cleaned_text, was_modified)."""
        if not text or not isinstance(text, str):
            return text, False
        
        original = text
        
        for pattern, replacement in self.replacements:
            if callable(replacement):
                text = pattern.sub(replacement, text)
            else:
                text = pattern.sub(replacement, text)
        
        # Clean emails (keep safe ones)
        email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        emails = email_pattern.findall(text)
        for email in emails:
            if email.lower() not in self.safe_emails and not email.endswith('@example.com'):
                text = text.replace(email, 'user@example.com')
                self.stats['replacements']['emails'] = self.stats['replacements'].get('emails', 0) + 1
        
        # Track replacements
        if text != original:
            self.stats['replacements']['credentials'] = self.stats['replacements'].get('credentials', 0) + 1
        
        return text, text != original
