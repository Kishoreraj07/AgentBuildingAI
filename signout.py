import os
import logging
my_app_dir = r"C:\DroidalAgentFlow\DroidStudio"
os.makedirs(my_app_dir, exist_ok=True)
# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(my_app_dir, "login.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def delete_credentials_files():
    """
    Deletes the credentials_key.key and credentials.enc files from the DroidStudio directory.
    """
    credentials_file_path = os.path.join(my_app_dir, "credentials.enc")
    credentials_key_file_path = os.path.join(my_app_dir, "credentials_key.key")

    try:
        # Delete credentials.enc if it exists
        if os.path.exists(credentials_file_path):
            os.remove(credentials_file_path)
            logger.info(f"Successfully deleted {credentials_file_path}")
        else:
            logger.debug(f"File {credentials_file_path} does not exist, skipping deletion")

        # Delete credentials_key.key if it exists
        if os.path.exists(credentials_key_file_path):
            os.remove(credentials_key_file_path)
            logger.info(f"Successfully deleted {credentials_key_file_path}")
        else:
            logger.debug(f"File {credentials_key_file_path} does not exist, skipping deletion")

    except PermissionError as e:
        logger.error(f"Permission error while deleting credentials files: {str(e)}")
        raise Exception(f"Permission denied while deleting credentials files: {str(e)}")
    except Exception as e:
        logger.error(f"Error deleting credentials files: {str(e)}")
        raise Exception(f"Failed to delete credentials files: {str(e)}")

# delete_credentials_files()