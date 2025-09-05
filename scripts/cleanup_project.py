import os
import shutil
from pathlib import Path
from datetime import datetime

def cleanup_project():
    print("=" * 80)
    print("PROJECT CLEANUP")
    print("=" * 80)
    print()
    
    # Define paths
    project_root = Path('.')
    archive_dir = project_root / 'project_archive'
    
    # Create archive directories
    archive_dirs = {
        'scripts_reference': archive_dir / 'scripts_reference',
        'docs_processing': archive_dir / 'docs_processing',
        'temporary_outputs': archive_dir / 'temporary_outputs',
        'backups': archive_dir / 'backups'
    }
    
    for dir_name, dir_path in archive_dirs.items():
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"[OK] Created archive directory: {dir_path}")
    
    print()
    print("[INFO] Archiving key reference files...")
    print()
    
    # Archive key scripts for reference
    scripts_to_archive = [
        'verify_final_data.py',
        'verify_arcadia_mapping_complete.py',
        'double_check.py',
        'random_verification.py',
        'map_unmapped_to_arcadia.py',
        'create_full_mapping.py',
        'sync_arcadia_updates.py',
        'parse_investors_column.py',
        'create_company_cards.py',
        'apply_to_be_created_matches.py'
    ]
    
    scripts_dir = project_root / 'scripts'
    archived_scripts = 0
    for script in scripts_to_archive:
        src = scripts_dir / script
        if src.exists():
            dst = archive_dirs['scripts_reference'] / script
            shutil.copy2(src, dst)
            print(f"  [ARCHIVED] {script}")
            archived_scripts += 1
    
    print(f"\n[OK] Archived {archived_scripts} key scripts for reference")
    print()
    
    # Archive intermediate documentation
    print("[INFO] Archiving intermediate documentation...")
    docs_to_archive = [
        'unmapped_processing_report.md',
        'mapping_categories.md',
        'investor_parsing_algorithm_documentation.md',
        'target_name_mapping_documentation.md',
        'all_applied_matches_detailed.md',
        'arcadia_id_matching_report.md',
        'arcadia_sync_report.md',
        'multiple_matches_review.md',
        'to_be_created_duplicate_detection_report.md'
    ]
    
    docs_dir = project_root / 'docs'
    archived_docs = 0
    for doc in docs_to_archive:
        src = docs_dir / doc
        if src.exists():
            dst = archive_dirs['docs_processing'] / doc
            shutil.copy2(src, dst)
            print(f"  [ARCHIVED] {doc}")
            archived_docs += 1
    
    print(f"\n[OK] Archived {archived_docs} documentation files")
    print()
    
    # Archive temporary output files
    print("[INFO] Archiving temporary output files...")
    outputs_to_archive = [
        'all_applied_matches.csv',
        'to_be_created_duplicate_candidates.csv'
    ]
    
    output_dir = project_root / 'output'
    archived_outputs = 0
    for output in outputs_to_archive:
        src = output_dir / output
        if src.exists():
            dst = archive_dirs['temporary_outputs'] / output
            shutil.copy2(src, dst)
            print(f"  [ARCHIVED] {output}")
            archived_outputs += 1
    
    print(f"\n[OK] Archived {archived_outputs} temporary output files")
    print()
    
    # Now delete temporary files
    print("[INFO] Deleting temporary files...")
    print()
    
    # Delete temporary scripts
    scripts_to_delete = []
    deleted_scripts = 0
    
    # Find all scripts to delete
    for script in scripts_dir.glob('*.py'):
        script_name = script.name
        # Keep only the cleanup script and essential ones
        if script_name not in ['cleanup_project.py'] and script_name not in scripts_to_archive:
            if (script_name.startswith('fix_') or 
                script_name.startswith('analyze_') or 
                script_name.startswith('process_') or 
                script_name.startswith('clean_') or 
                script_name.startswith('detect_') or 
                script_name.startswith('check_') or
                script_name.startswith('apply_') or
                script_name.startswith('test_') or
                script_name.startswith('merge_') or
                script_name.startswith('deduplicate_') or
                script_name.startswith('update_')):
                
                scripts_to_delete.append(script)
    
    for script in scripts_to_delete:
        try:
            script.unlink()
            print(f"  [DELETED] {script.name}")
            deleted_scripts += 1
        except Exception as e:
            print(f"  [ERROR] Could not delete {script.name}: {e}")
    
    print(f"\n[OK] Deleted {deleted_scripts} temporary scripts")
    print()
    
    # Delete archived documentation (now that they're in archive)
    for doc in docs_to_archive:
        src = docs_dir / doc
        if src.exists():
            try:
                src.unlink()
                print(f"  [DELETED] docs/{doc}")
            except Exception as e:
                print(f"  [ERROR] Could not delete {doc}: {e}")
    
    # Delete temporary outputs (now that they're archived)
    for output in outputs_to_archive:
        src = output_dir / output
        if src.exists():
            try:
                src.unlink()
                print(f"  [DELETED] output/{output}")
            except Exception as e:
                print(f"  [ERROR] Could not delete {output}: {e}")
    
    print()
    
    # Clean up archive folders in scripts
    script_archives = ['_archive', 'temp_archived']
    for archive in script_archives:
        archive_path = scripts_dir / archive
        if archive_path.exists() and archive_path.is_dir():
            try:
                shutil.rmtree(archive_path)
                print(f"  [DELETED] scripts/{archive}/ directory")
            except Exception as e:
                print(f"  [ERROR] Could not delete {archive}: {e}")
    
    # Clean up output archive
    output_archive = output_dir / '_archive'
    if output_archive.exists() and output_archive.is_dir():
        try:
            shutil.rmtree(output_archive)
            print(f"  [DELETED] output/_archive/ directory")
        except Exception as e:
            print(f"  [ERROR] Could not delete output/_archive: {e}")
    
    print()
    print("=" * 80)
    print("CLEANUP SUMMARY")
    print("=" * 80)
    print()
    
    # Count remaining files
    remaining_scripts = len(list(scripts_dir.glob('*.py')))
    remaining_docs = len(list(docs_dir.glob('*.md')))
    remaining_outputs = len(list(output_dir.glob('*.csv')))
    
    print(f"Files remaining after cleanup:")
    print(f"  Scripts: {remaining_scripts} files")
    print(f"  Documentation: {remaining_docs} files")
    print(f"  Output CSV: {remaining_outputs} files")
    print()
    
    # List essential files preserved
    print("Essential files preserved:")
    print("\nOutput files:")
    for f in sorted(output_dir.glob('*.csv')):
        print(f"  ✓ {f.name}")
    
    print("\nDocumentation:")
    for f in sorted(docs_dir.glob('*.md')):
        print(f"  ✓ {f.name}")
    
    print("\nSource files:")
    src_dir = project_root / 'src'
    for f in sorted(src_dir.glob('*.csv')):
        print(f"  ✓ {f.name}")
    
    print()
    print("[SUCCESS] Project cleanup completed!")
    print(f"[INFO] Archives saved in: project_archive/")
    
if __name__ == "__main__":
    cleanup_project()