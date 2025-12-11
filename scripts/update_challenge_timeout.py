#!/usr/bin/env python3
"""
Script para actualizar el challenge timeout en todo el proyecto PlayerGold
Cambia de 100ms a 300ms para acomodar latencia global

Uso:
    python scripts/update_challenge_timeout.py --from 100 --to 300
    python scripts/update_challenge_timeout.py --verify  # Solo verificar cambios
"""

import argparse
import re
import os
from pathlib import Path
import yaml

def update_config_files(old_timeout, new_timeout, dry_run=False):
    """Update configuration files"""
    config_files = [
        'config/default.yaml',
        'config/config.py'
    ]
    
    changes = []
    
    for config_file in config_files:
        if not Path(config_file).exists():
            continue
            
        with open(config_file, 'r') as f:
            content = f.read()
        
        original_content = content
        
        if config_file.endswith('.yaml'):
            # Update YAML format: challenge_timeout: 0.1 -> 0.3
            old_value = old_timeout / 1000  # Convert ms to seconds
            new_value = new_timeout / 1000
            content = re.sub(
                rf'challenge_timeout:\s*{old_value}',
                f'challenge_timeout: {new_value}',
                content
            )
        elif config_file.endswith('.py'):
            # Update Python format: default=0.1 -> default=0.3
            old_value = old_timeout / 1000
            new_value = new_timeout / 1000
            content = re.sub(
                rf'default={old_value}',
                f'default={new_value}',
                content
            )
        
        if content != original_content:
            changes.append(f"Updated {config_file}")
            if not dry_run:
                with open(config_file, 'w') as f:
                    f.write(content)
    
    return changes

def update_documentation(old_timeout, new_timeout, dry_run=False):
    """Update documentation files"""
    doc_patterns = [
        '**/*.md',
        'README.md'
    ]
    
    changes = []
    
    for pattern in doc_patterns:
        for doc_file in Path('.').glob(pattern):
            if not doc_file.is_file():
                continue
                
            with open(doc_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Update various formats
            replacements = [
                (rf'<{old_timeout}ms', f'<{new_timeout}ms'),
                (rf'{old_timeout}ms', f'{new_timeout}ms'),
                (rf'{old_timeout}.*millisecond', f'{new_timeout} milliseconds'),
                (rf'{old_timeout}.*milisegundo', f'{new_timeout} milisegundos'),
            ]
            
            for old_pattern, new_text in replacements:
                content = re.sub(old_pattern, new_text, content, flags=re.IGNORECASE)
            
            if content != original_content:
                changes.append(f"Updated {doc_file}")
                if not dry_run:
                    with open(doc_file, 'w', encoding='utf-8') as f:
                        f.write(content)
    
    return changes

def update_source_code(old_timeout, new_timeout, dry_run=False):
    """Update source code files"""
    source_patterns = [
        '**/*.py',
        'src/**/*.py',
        'tests/**/*.py'
    ]
    
    changes = []
    
    for pattern in source_patterns:
        for source_file in Path('.').glob(pattern):
            if not source_file.is_file():
                continue
                
            with open(source_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Update various code patterns
            replacements = [
                # Timeout values in milliseconds
                (rf'timeout_ms.*==.*{old_timeout}', f'timeout_ms == {new_timeout}'),
                (rf'timeout_ms.*=.*{old_timeout}', f'timeout_ms = {new_timeout}'),
                
                # Response time checks
                (rf'response_time_ms.*>=.*{old_timeout}', f'response_time_ms >= {new_timeout}'),
                (rf'response_time_ms.*<.*{old_timeout}', f'response_time_ms < {new_timeout}'),
                
                # Computation time checks
                (rf'computation_time_ms.*>=.*{old_timeout}', f'computation_time_ms >= {new_timeout}'),
                (rf'computation_time_ms.*<.*{old_timeout}', f'computation_time_ms < {new_timeout}'),
                
                # Processing time assertions
                (rf'processing_time_ms.*<.*{old_timeout}', f'processing_time_ms < {new_timeout}'),
                
                # Average time checks
                (rf'avg_time.*>.*{old_timeout}', f'avg_time > {new_timeout}'),
                
                # Comments and strings
                (rf'{old_timeout}ms', f'{new_timeout}ms'),
                (rf'<{old_timeout}ms', f'<{new_timeout}ms'),
                (rf'>{old_timeout}ms', f'>{new_timeout}ms'),
                (rf'exceeds {old_timeout}ms', f'exceeds {new_timeout}ms'),
                
                # Sleep timeouts (convert to seconds)
                (rf'time\.sleep\({old_timeout/1000}\)', f'time.sleep({new_timeout/1000})'),
            ]
            
            for old_pattern, new_text in replacements:
                content = re.sub(old_pattern, new_text, content)
            
            if content != original_content:
                changes.append(f"Updated {source_file}")
                if not dry_run:
                    with open(source_file, 'w', encoding='utf-8') as f:
                        f.write(content)
    
    return changes

def verify_changes(old_timeout, new_timeout):
    """Verify that changes were applied correctly"""
    print(f"\n🔍 Verifying changes from {old_timeout}ms to {new_timeout}ms...")
    
    # Check config files
    config_file = Path('config/default.yaml')
    if config_file.exists():
        with open(config_file, 'r') as f:
            content = f.read()
        
        expected_value = new_timeout / 1000
        if f'challenge_timeout: {expected_value}' in content:
            print(f"✅ Config file updated correctly: {expected_value}s")
        else:
            print(f"❌ Config file not updated correctly")
    
    # Check for remaining old references
    remaining_refs = []
    for pattern in ['**/*.py', '**/*.md']:
        for file_path in Path('.').glob(pattern):
            if not file_path.is_file():
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if f'{old_timeout}ms' in content or f'<{old_timeout}ms' in content:
                    remaining_refs.append(str(file_path))
            except:
                continue
    
    if remaining_refs:
        print(f"\n⚠️  Found {len(remaining_refs)} files with remaining {old_timeout}ms references:")
        for ref in remaining_refs[:10]:  # Show first 10
            print(f"   - {ref}")
        if len(remaining_refs) > 10:
            print(f"   ... and {len(remaining_refs) - 10} more")
    else:
        print(f"✅ No remaining {old_timeout}ms references found")

def main():
    parser = argparse.ArgumentParser(
        description='Update challenge timeout throughout PlayerGold project',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Update from 100ms to 300ms
  python scripts/update_challenge_timeout.py --from 100 --to 300
  
  # Dry run to see what would be changed
  python scripts/update_challenge_timeout.py --from 100 --to 300 --dry-run
  
  # Verify changes were applied
  python scripts/update_challenge_timeout.py --verify --from 100 --to 300
        """
    )
    
    parser.add_argument(
        '--from',
        dest='old_timeout',
        type=int,
        default=100,
        help='Old timeout value in milliseconds (default: 100)'
    )
    
    parser.add_argument(
        '--to',
        dest='new_timeout',
        type=int,
        default=300,
        help='New timeout value in milliseconds (default: 300)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without making changes'
    )
    
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify that changes were applied correctly'
    )
    
    args = parser.parse_args()
    
    if args.verify:
        verify_changes(args.old_timeout, args.new_timeout)
        return
    
    print(f"🔄 Updating challenge timeout: {args.old_timeout}ms → {args.new_timeout}ms")
    if args.dry_run:
        print("🔍 DRY RUN - No files will be modified")
    
    all_changes = []
    
    # Update configuration files
    print("\n📝 Updating configuration files...")
    config_changes = update_config_files(args.old_timeout, args.new_timeout, args.dry_run)
    all_changes.extend(config_changes)
    
    # Update documentation
    print("\n📚 Updating documentation...")
    doc_changes = update_documentation(args.old_timeout, args.new_timeout, args.dry_run)
    all_changes.extend(doc_changes)
    
    # Update source code
    print("\n💻 Updating source code...")
    code_changes = update_source_code(args.old_timeout, args.new_timeout, args.dry_run)
    all_changes.extend(code_changes)
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"   Configuration files: {len(config_changes)} updated")
    print(f"   Documentation files: {len(doc_changes)} updated")
    print(f"   Source code files: {len(code_changes)} updated")
    print(f"   Total files: {len(all_changes)} updated")
    
    if all_changes:
        print(f"\n📋 Files modified:")
        for change in all_changes[:20]:  # Show first 20
            print(f"   ✅ {change}")
        if len(all_changes) > 20:
            print(f"   ... and {len(all_changes) - 20} more")
    
    if not args.dry_run and all_changes:
        print(f"\n🎉 Successfully updated challenge timeout from {args.old_timeout}ms to {args.new_timeout}ms!")
        print(f"💡 Run with --verify to check that all changes were applied correctly")
    elif args.dry_run:
        print(f"\n💡 Run without --dry-run to apply these changes")

if __name__ == "__main__":
    main()