import os
import shutil

def copy_unique_files(folder1, folder2, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    # Get file names from folder2
    folder2_files = set(os.listdir(folder2))

    unique_count = 0

    for file_name in os.listdir(folder1):
        src_path = os.path.join(folder1, file_name)

        # Skip directories
        if not os.path.isfile(src_path):
            continue

        # If file NOT in folder2 → copy
        if file_name not in folder2_files:
            shutil.copy2(src_path, output_folder)
            unique_count += 1

    print(f"Copied {unique_count} unique files.")

fol1=r"D:\837\Bonner\New\bonner_837"
fol2=r"D:\837\Bonner\New\new\bonner_837"
unique=r"D:\837\Bonner\unique_new"
copy_unique_files(fol1,fol2,unique)