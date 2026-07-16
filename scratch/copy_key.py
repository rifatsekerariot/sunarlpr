import shutil
import os
import traceback

src = "C:/Users/Ms\u0131/.ssh/id_rsa"
dst = "D:/Antigravity/temp_id_rsa"

try:
    if os.path.exists(src):
        shutil.copy(src, dst)
        print("Success: Copied key from", src, "to", dst)
    else:
        # Try directory iteration as safety fallback
        users_dir = "C:/Users"
        copied = False
        for folder in os.listdir(users_dir):
            if folder.startswith("Ms"):
                possible_src = os.path.join(users_dir, folder, ".ssh", "id_rsa")
                if os.path.exists(possible_src):
                    shutil.copy(possible_src, dst)
                    print("Fallback Success: Copied key from", possible_src)
                    copied = True
                    break
        if not copied:
            print("Error: Private key file not found in any Ms* directory.")
except Exception as e:
    print("Copy Error:", str(e))
    traceback.print_exc()
