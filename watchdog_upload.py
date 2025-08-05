from watchdog_upload import Observer
from watchdog_upload import FileSystemEventHandler
import os
import subprocess
import time

UPLOAD_DIR = "uploads"

class UploadHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.log'):
            print(f"New log file detected: {event.src_path}")
            subprocess.run(["python", "dbschema.py", event.src_path])

if __name__ == "__main__":

    event_handler = UploadHandler()
    observer = Observer()
    observer.schedule(event_handler, path=UPLOAD_DIR, recursive=False)
    
    print("Starting to monitor uploads directory...")
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    
    observer.join()