# Import os library: provides functions for interacting with the operating system, such as file paths, directory operations, and environment variables
import os
# Import shutil library: provides high-level file operations, including copying, moving, and removing files and directories
import shutil


# Function to create a new folder at the specified path with the given name
def create_folder(path, name):
    new_path = os.path.join(path, name)  # Join the base path and folder name to create the full path
    os.makedirs(new_path, exist_ok=True)  # Create the directory structure; exist_ok=True prevents error if folder already exists
    return new_path  # Return the path of the newly created folder


# Function to create a new text file at the specified path with the given name
def create_file(path, name):
    new_path = os.path.join(path, name)  # Join the path and name to create the full file path
    with open(new_path, "w") as f:  # Open the file in write mode
        f.write("")  # Write an empty string to create the file
    return new_path  # Return the path of the newly created file


# Function to delete a file or folder at the specified path
def delete_item(path):
    if os.path.isdir(path):  # Check if the path is a directory
        shutil.rmtree(path)  # If it's a directory, remove the entire directory tree
    else:  # If it's not a directory, it's a file
        os.remove(path)  # Remove the file


# Function to rename a file or folder from old_path to new_name
def rename_item(old_path, new_name):
    parent = os.path.dirname(old_path)  # Get the parent directory of the old path
    new_path = os.path.join(parent, new_name)  # Join the parent directory with the new name to create the new path
    os.rename(old_path, new_path)  # Rename the item from old_path to new_path
    return new_path  # Return the new path after renaming


# Function to read the contents of a file at the specified path
def read_file(path):
    with open(path, "r", errors="replace") as f:  # Open the file in read mode; errors="replace" handles encoding errors by replacing them
        return f.read()  # Read and return the entire content of the file


# Function to write content to a file at the specified path
def write_file(path, content):
    with open(path, "w") as f:  # Open the file in write mode (overwrites existing content)
        f.write(content)  # Write the provided content to the file


# Function to list the contents of a directory, separating folders and files
def list_directory(path):
    try:  # Try to list the directory contents
        entries = os.listdir(path)  # Get all entries in the directory
    except PermissionError:  # If there's a permission error (e.g., access denied)
        return [], []  # Return empty lists for folders and files
    folders = sorted([e for e in entries if os.path.isdir(os.path.join(path, e))])  # Filter and sort directory entries that are folders
    files = sorted([e for e in entries if os.path.isfile(os.path.join(path, e))])  # Filter and sort directory entries that are files
    return folders, files
