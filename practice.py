import os

# we are going to write a script the will display all of the files/folders in the provided directory



def list_files(path="."):
    if (path == '.'):
        print("Path is not provided, so we will work on the current directory.")

    else: 
        print(f"Path is provided which is: {path} and we will work on it.")


    entries = []
    count_files=0
    count_folders=0
    for entry in os.scandir(path):
        
        if entry.is_dir():
            folder = entry.name + "/"
            entries.append(folder)
            # print(folder)
            # count_folders+=1
        elif entry.is_file():
            file = entry.name
            entries.append(file)
            # print(file)
            # count_files+=1
    # print("Count Folders: ",count_folders)
    # print("Count Files: ",count_files)
    
        

    return entries

def print_entries(entries):
    entries.sort()
    for entry in entries:
        print(entry)

entries = list_files()
print_entries(entries)
