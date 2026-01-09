import subprocess
import sys

def run_script(script_name):
    print(f"\n▶ Running {script_name} ...\n")
    try:
        subprocess.run([sys.executable, script_name], check=True)
    except subprocess.CalledProcessError:
        print(f"❌ Error while running {script_name}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️ Pipeline stopped by user")
        sys.exit(0)

if __name__ == "__main__":
    run_script("harvest_links.py")
    run_script("enrich_details.py")
    print("\n✅ PIPELINE COMPLETED SUCCESSFULLY")
