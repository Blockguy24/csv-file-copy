import argparse
import csv
from collections import OrderedDict
from os.path import exists, join, abspath
from shutil import copy


def is_long_path_available() -> bool:
    from sys import platform
    if platform == "win32":
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SYSTEM\\CurrentControlSet\\Control\\FileSystem")
        long_paths: int = 0
        try:
            # Attempt to read value from registry
            long_paths = winreg.QueryValueEx(key, "LongPathsEnabled")[0]
        except FileNotFoundError:
            """
            This is alright because long_paths has a default value of zero,
            and if LongPathsEnabled doesn't exist in the registry, we can assume
            it is disabled.
            """
            pass
        return bool(long_paths)
    else:
        # Systems such as macosx and linux do not have this limitation
        return True


def check_path_length(path: str) -> bool:
    return is_long_path_available() or len(path) < 260


def main():
    """
    Main function for csv-file-copy.py
    """
    parser = argparse.ArgumentParser(description="Copy files based on the contents of a CSV file")
    parser.add_argument("csv_file", help="CSV file specifying files to copy")
    parser.add_argument("source_dir", help="Source directory")
    parser.add_argument("target_dir", help="Target directory")
    parser.add_argument("-c", "--column-name", default="filename",
                        help="Column to read from the CSV file (default: \"filename\")")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="Suppress program output")
    parser.add_argument("-o", "--overwrite", action="store_true",
                        help="Overwrite file if it already exists in destination (default: skip file)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Don't copy files, just print what would've been copied")
    args: argparse.Namespace = parser.parse_args()

    if not args.quiet:
        print(f"CSV file: \"{args.csv_file}\"")
        print(f"Column to read: \"{args.column_name}\"")
        print(f"Source directory: \"{args.source_dir}\"")
        print(f"Destination directory: \"{args.target_dir}\"")
        print(f"Overwrite existing: {args.overwrite}")
        print(f"Dry Run: {args.dry_run}")
        print()

    for file in (args.csv_file, args.source_dir, args.target_dir):
        if not exists(file):
            parser.error(f"\"{file}\" does not exist")

    with open(args.csv_file) as f:
        reader: csv.DictReader = csv.DictReader(f)
        row: OrderedDict
        try:
            files = [row[args.column_name] for row in reader]  # Get only file names
        except KeyError:
            # Column not found
            parser.error(f"Column \"{args.column_name}\" does not exist")
        files = list(OrderedDict.fromkeys(files))  # Remove duplicates

    copied: int = 0
    not_found: int = 0
    already_exist: int = 0
    path_error: int = 0
    for file in files:
        source_file_exists: bool = exists(join(args.source_dir, file))

        if not args.overwrite and exists(join(args.target_dir, file)):
            # If the target file already exists, and overwrite is not specified, skip this file
            if not args.quiet:
                print(f"Skipping \"{file}\"")
            already_exist += 1

        elif source_file_exists and check_path_length(abspath(join(args.target_dir, file))):
            # If the source file exists and path length check succeeds, copy file
            if not args.quiet:
                print(f"Copying \"{file}\"...")
            if not args.dry_run:
                copy(join(args.source_dir, file), args.target_dir)
            copied += 1

        elif source_file_exists:
            # If the source file exists, but the path length is too long, skip this file
            if not args.quiet:
                print(f"Path length too long, skipping: \"{file}\"")
            path_error += 1

        else:
            # If the source file doesn't exist, skip it
            if not args.quiet:
                print(f"File \"{file}\" does not exist")
            not_found += 1

    if not args.quiet:
        print()
        print("Operation complete")
        print(f"{copied} files copied")
        # Only print stat if used
        if not_found:
            print(f"{not_found} files not found in source")
        if already_exist:
            print(f"{already_exist} files already exist in destination")
        if path_error:
            print(f"{path_error} files have path lengths that are too long for the destination")


if __name__ == '__main__':
    main()
