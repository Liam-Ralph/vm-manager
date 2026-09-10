# Imports

import os
import sys


# Global Variables

if len(sys.argv) < 3:
    exit(1)
PATH_VMS = sys.argv[1]
VM_EXT = sys.argv[2]


# Main Function

def main():

    for path, dirs, files in os.walk(PATH_VMS):
        vm_path = False
        for file in files:
            if file.endswith(VM_EXT):
                vm_path = True
                break
        if vm_path:
            size = 0
            for subfiles in os.walk(path)[2]:
                for subfile in subfiles:
                    size += os.path.getsize(subfile)
            dirs[:] = []
            print(size, path)

if __name__ == "__main__":
    main()
