import os
import subprocess
from pathlib import Path

def create_shortcuts():
    target_bat = Path(__file__).resolve().parent / "baslat.bat"
    work_dir = target_bat.parent

    # Find Desktop folders
    desktop_candidates = [
        Path(os.path.expanduser("~/Desktop")),
        Path(os.environ.get("USERPROFILE", "C:/Users/sinan.nergiz")) / "Desktop",
        Path(os.environ.get("USERPROFILE", "C:/Users/sinan.nergiz")) / "OneDrive - Stftex" / "Masaüstü",
        Path(os.environ.get("USERPROFILE", "C:/Users/sinan.nergiz")) / "OneDrive - Stftex" / "Desktop",
    ]

    # Also query registry / environment for Desktop
    try:
        res = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", "[Environment]::GetFolderPath('Desktop')"],
            text=True
        ).strip()
        if res:
            desktop_candidates.append(Path(res))
    except Exception:
        pass

    created_any = False
    for desk in set(desktop_candidates):
        if desk.exists():
            lnk_path = desk / "StoryTime Studio.lnk"
            # VBS script to create the link
            vbs_code = f'''
Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "{str(lnk_path).replace('\\', '\\\\')}"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "{str(target_bat).replace('\\', '\\\\')}"
oLink.WorkingDirectory = "{str(work_dir).replace('\\', '\\\\')}"
oLink.Description = "StoryTime Studio - 2D AI Storytime Animation Studio"
oLink.IconLocation = "shell32.dll,115"
oLink.Save
'''
            vbs_file = work_dir / "_temp_make_lnk.vbs"
            vbs_file.write_text(vbs_code, encoding="utf-8")
            subprocess.run(["cscript", "//nologo", str(vbs_file)], check=True)
            if vbs_file.exists():
                vbs_file.unlink()
            print(f"Created shortcut at: {lnk_path}")
            created_any = True

    if not created_any:
        print("Warning: No desktop directory found.")

if __name__ == "__main__":
    create_shortcuts()
