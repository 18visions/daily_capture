import os
import time
import shutil
import logging
import socket
from datetime import datetime

from picamera2 import Picamera2
from pythonjsonlogger import jsonlogger
import click

# Optional GELF logging for Logstash
try:
    import graypy
    LOGSTASH_ENABLED = True
except ImportError:
    LOGSTASH_ENABLED = False


class PiCameraUploader:
    def __init__(self, logstash_host=None, logstash_port=12201):
        self.camera = Picamera2()
        self.image_path = ""
        self.logger = self.setup_logger(logstash_host, logstash_port)

    def setup_logger(self, logstash_host, logstash_port):
        logger = logging.getLogger("PiCameraUploader")
        logger.setLevel(logging.INFO)

        log_format = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(message)s')
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(log_format)
        logger.addHandler(stream_handler)

        if LOGSTASH_ENABLED and logstash_host:
            gelf_handler = graypy.GELFUDPHandler(logstash_host, logstash_port)
            logger.addHandler(gelf_handler)

        return logger

    def capture_image(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.image_path = f"/tmp/captured_image_{timestamp}.png"
        self.logger.info("Capturing image...", extra={"event": "capture_start"})

        config = self.camera.create_still_configuration(main={"size": (3280, 2464)})
        self.camera.configure(config)
        self.camera.start()
        time.sleep(2)
        self.camera.capture_file(self.image_path)
        self.camera.stop()

        self.logger.info("Image captured", extra={"image_path": self.image_path})
        return self.image_path

    def copy_to_nfs(self, mount_point="/mnt/nas"):
        if not os.path.ismount(mount_point):
            self.logger.error("NFS mount not found", extra={"mount_point": mount_point})
            raise RuntimeError(f"{mount_point} is not mounted")

        nfs_target = os.path.join(mount_point, os.path.basename(self.image_path))
        try:
            shutil.copy2(self.image_path, nfs_target)
            self.logger.info("Copied image to NFS", extra={"nfs_path": nfs_target})
        except Exception as e:
            self.logger.error("Failed to copy image to NFS", extra={"error": str(e)})

    def cleanup(self):
        if os.path.exists(self.image_path):
            os.remove(self.image_path)
            self.logger.info("Temporary file removed", extra={"image_path": self.image_path})


@click.command()
@click.option("--nfs", is_flag=True, help="Copy captured image to NFS share")
@click.option("--keep", is_flag=True, help="Keep local image file")
@click.option("--logstash-host", help="Send logs to this Logstash host (GELF UDP)")
@click.option("--logstash-port", default=12201, show_default=True, help="Logstash GELF UDP port")
def main(nfs, keep, logstash_host, logstash_port):
    start = time.time()
    uploader = PiCameraUploader(logstash_host=logstash_host, logstash_port=logstash_port)

    try:
        uploader.capture_image()

        if nfs:
            uploader.copy_to_nfs()

        if not keep:
            uploader.cleanup()

        duration = time.time() - start
        uploader.logger.info("Process complete", extra={"duration": round(duration, 2)})

    except Exception as e:
        uploader.logger.error("Unhandled exception occurred", extra={"error": str(e)})


if __name__ == "__main__":
    main()
