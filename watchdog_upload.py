from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import logging
import time
from dbschema import process_log_file

logging.basicConfig(level=logging.INFO)

UPLOAD_DIR = "uploads"

#inherits file system event handler
class MyHandler(FileSystemEventHandler):
    #triggered when a file/folder is created 
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.log'):
            logging.info(f"[Watchdog] Detected new file: {event.src_path}")
            # Call the function to process the log file
            try:
                process_log_file(event.src_path)
            except Exception as e:
                logging.error(f"[Watchdog] Error processing file {event.src_path}: {e}")


def start_watchdog(path="./uploads"):
    if not os.path.exists(path):
        os.makedirs(path)
    observer = Observer() #create an observer instance
    observer.schedule(MyHandler(), path=path, recursive=True) #recursive=True means it will watch all subdirectories
    observer.start()
    logging.info("[Watchdog] Started watching %s", path)

    try:
        while True:
            time.sleep(1) #keep the thread alive
    except KeyboardInterrupt:# if user interrupts the program
        observer.stop()
    observer.join()