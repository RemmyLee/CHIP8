import os
import sys

if len(sys.argv) != 2:
    print("Usage: python rename_roms.py <path_to_your_roms_directory>")
    sys.exit(1)

# Directory where your CHIP-8 ROMs are stored
rom_directory = sys.argv[1]

# Byte patterns that are unique to SUPERCHIP and XO-CHIP, respectively
# These are hypothetical examples; you'll need to replace them with the actual signatures
superchip_signatures = [b"\x00\xC0", b"\xF0\x00"]
xo_chip_signatures = [b"\x50\x40", b"\xF8\x00"]


def check_for_signature(file_path, signatures):
    with open(file_path, "rb") as file:
        file_content = file.read()
        for signature in signatures:
            if signature in file_content:
                return True
    return False


# Loop through all files in the directory
for filename in os.listdir(rom_directory):
    # Construct the full file path
    file_path = os.path.join(rom_directory, filename)

    # Skip directories
    if os.path.isdir(file_path):
        continue

    # Check the ROM for each type of signature
    if check_for_signature(file_path, xo_chip_signatures):
        new_name = "XOCHIP_" + filename
    elif check_for_signature(file_path, superchip_signatures):
        new_name = "SUPERCHIP_" + filename
    else:
        new_name = "CHIP8_" + filename

    # Construct the full new file path
    new_file_path = os.path.join(rom_directory, new_name)

    # Rename the file
    os.rename(file_path, new_file_path)
    print(f"Renamed '{filename}' to '{new_name}'")

print("All ROMs have been checked and renamed accordingly.")
