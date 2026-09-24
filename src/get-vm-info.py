# Imports

import hashlib
import os
import sys


# Function

def get_vm_info(vms_path: str, vm_path: str, vm_hashfile_path: str) -> str:
    vm_full_path = os.path.join(vms_path, vm_path)
    md5_hash = hashlib.md5()
    with open(os.path.join(vm_full_path, vm_hashfile_path), "rb") as file:
        for chunk in iter(lambda: file.read(4096), b""):
            md5_hash.update(chunk)
    size = 0
    for subpath, subdirs, subfiles in os.walk(vm_full_path):
        for subfile in subfiles:
            size += os.path.getsize(os.path.join(subpath, subfile))
    return f"{md5_hash.hexdigest()} {size}"


# Run Function

if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(1)
    vms_path = sys.argv[1]
    vm_path = sys.argv[2]
    vm_hashfile_path = sys.argv[3]
    print(get_vm_info(vms_path, vm_path, vm_hashfile_path), end="")
