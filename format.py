import subprocess
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

def list_drives():
    drives = []
    try:
        result = subprocess.run("lsblk -o NAME,TYPE,SIZE,MOUNTPOINT -l", shell=True, check=True, capture_output=True, text=True)
        for line in result.stdout.splitlines()[1:]:
            parts = line.split()
            if len(parts) > 1 and parts[1] == 'disk':
                drive_info = {
                    "name": f"/dev/{parts[0]}",
                    "size": parts[2],
                    "mountpoint": parts[3] if len(parts) > 3 else "Not mounted"
                }
                drives.append(drive_info)
    except subprocess.CalledProcessError as e:
        print(Fore.RED + f"Failed to list drives: {e}")
    return drives

def unmount_drive(device_path):
    try:
        mountpoint = subprocess.run(f"lsblk -no MOUNTPOINT {device_path}", shell=True, check=True, capture_output=True, text=True).stdout.strip()
        if mountpoint:
            print(Fore.YELLOW + f"Unmounting {device_path} from {mountpoint}...")
            subprocess.run(f"sudo umount {device_path}", shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(Fore.RED + f"Failed to unmount drive: {e}")

def format_drive(device_path):
    print(Fore.RED + Style.BRIGHT + f"WARNING: This will format the device {device_path}. All data will be lost!")
    confirmation = input(Fore.CYAN + "Type 'yes' to continue: ").strip().lower()

    if confirmation != 'yes':
        print(Fore.GREEN + "Operation canceled.")
        return False

    unmount_drive(device_path)

    command = f"sudo mkfs.ext4 {device_path}"

    try:
        print(Fore.YELLOW + f"Formatting device {device_path}...")
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(Fore.GREEN + result.stdout)
        print(Fore.GREEN + "Device formatted successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(Fore.RED + "An error occurred while formatting the device.")
        print(Fore.RED + e.stderr)
        return False

def create_partition(device_path):
    print(Fore.YELLOW + f"Creating a new partition on {device_path}...")

    partition_type = input(Fore.CYAN + "Enter partition type (primary/logical): ").strip().lower()
    file_system_type = input(Fore.CYAN + "Enter file system type (ext4/ntfs/fat32 etc.): ").strip().lower()
    start_size = input(Fore.CYAN + "Enter start size (e.g., 0%): ").strip()
    end_size = input(Fore.CYAN + "Enter end size (e.g., 100%): ").strip()

    try:
        subprocess.run(f"sudo parted {device_path} mklabel gpt", shell=True, check=True)
        subprocess.run(f"sudo parted -a opt {device_path} mkpart {partition_type} {file_system_type} {start_size} {end_size}", shell=True, check=True)

        partition_path = f"{device_path}1"
        subprocess.run(f"sudo mkfs.{file_system_type} {partition_path}", shell=True, check=True)

        print(Fore.GREEN + f"Partition created and formatted successfully on {device_path}.")
    except subprocess.CalledProcessError as e:
        print(Fore.RED + "An error occurred while creating the partition.")
        print(Fore.RED + e.stderr)

if __name__ == "__main__":
    drives = list_drives()
    if not drives:
        print(Fore.RED + "No drives found.")
        exit()

    print(Fore.CYAN + "Available drives:")
    for i, drive in enumerate(drives):
        print(Fore.MAGENTA + f"{i + 1}: {drive['name']} ({drive['size']}, {drive['mountpoint']})")

    try:
        choice = int(input(Fore.CYAN + "Select a drive number to format: ")) - 1
        if 0 <= choice < len(drives):
            selected_drive = drives[choice]['name']
            if format_drive(selected_drive):
                partition_choice = input(Fore.CYAN + "Would you like to create a partition on this drive? (yes/no): ").strip().lower()
                if partition_choice == 'yes':
                    create_partition(selected_drive)
                else:
                    print(Fore.GREEN + "Partitioning skipped.")
        else:
            print(Fore.RED + "Invalid choice.")
    except ValueError:
        print(Fore.RED + "Invalid input. Please enter a number.")

