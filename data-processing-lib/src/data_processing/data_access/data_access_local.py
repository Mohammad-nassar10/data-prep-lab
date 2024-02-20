import glob
import os
from pathlib import Path

import pyarrow.parquet as pq
from data_access_s3 import *


class DataAccessLocal(DataAccess):
    """
    Implementation of the Base Data access class for local folder data access.
    """
    def __init__(
            self,
            path_config: dict[str, str],
            d_sets: list[str],
            checkpoint: bool,
            m_files: int,
    ):
        """
        Create data access class for folder based configuration
        :param path_config: dictionary of path info
        """
        self.input_folder = path_config["input_folder"]
        self.output_folder = path_config["output_folder"]
        self.d_sets = d_sets
        self.checkpoint = checkpoint
        self.m_files = m_files

    def _get_files_folder(
            self, path: str, cm_files: int, max_file_size: int = 0, min_file_size: int = MB * GB
    ) -> tuple[list[str], dict[str, float]]:
        """
        Support method.  Lists all parquet files in a directory and their sizes.
        :param path: input path
        :param max_file_size: max file size, not sure
        :param min_file_size: min file size
        :param cm_files: overwrite for the m_files in the class
        :return: tuple of file list and profile
        """
        # Get files list, their total size, max and min size of the files in the list.
        parquet_files = []
        total_input_file_size = 0
        i = 0
        for path in Path(path).rglob("*.parquet"):
            if i >= cm_files > 0:
                break
            size = path.stat().st_size
            parquet_files.append(path.name)
            total_input_file_size += size
            if min_file_size > size:
                min_file_size = size
            if max_file_size < size:
                max_file_size = size
            i += 1
        return (
            parquet_files,
            {
                "max_file_size": max_file_size / MB,
                "min_file_size": min_file_size / MB,
                "total_file_size": total_input_file_size / MB,
            },
        )

    def _get_input_files(
            self,
            input_path: str,
            output_path: str,
            cm_files: int,
            max_file_size: int = 0,
            min_file_size: int = MB * GB,
    ) -> tuple[list[str], dict[str, float]]:
        """
        Get list and size of files from input path, that do not exist in the output path
        :param input_path: input path
        :param output_path: output path
        :return: tuple of file list and profile
        """
        if not self.checkpoint:
            return self._get_files_folder(
                path=input_path, cm_files=cm_files, min_file_size=min_file_size, max_file_size=max_file_size
            )

        input_files = set(os.path.basename(path) for path in Path(input_path).rglob("*.parquet"))
        output_files = set(os.path.basename(path) for path in Path(output_path).rglob("*.parquet"))
        missing_files = input_files - output_files

        total_input_file_size = 0
        i = 0
        parquet_files = []
        for filename in missing_files:
            if i >= cm_files > 0:
                break
            parquet_files.append(filename)
            size = os.path.getsize(os.path.join(input_path, filename))
            total_input_file_size += size
            if min_file_size > size:
                min_file_size = size
            if max_file_size < size:
                max_file_size = size
            i += 1
        return (
            parquet_files,
            {
                "max_file_size": max_file_size / MB,
                "min_file_size": min_file_size / MB,
                "total_file_size": total_input_file_size / MB,
            },
        )

    def get_files_to_process(self) -> tuple[list[str], dict[str, float]]:
        """
        Get files to process
        :return: list of files and a dictionary of the files profile:
            "max_file_size",
            "min_file_size",
            "total_file_size"
        """
        # Check if we are using data sets
        if self.d_sets is not None:
            # get a list of subdirectory paths matching d_sets
            folders_to_use = []
            root_dir = Path(self.input_folder)
            for dir_name in self.d_sets:
                subdir_path = root_dir / dir_name
                if subdir_path.is_dir() and subdir_path.parent == root_dir:
                    folders_to_use.append(subdir_path.name)
            profile = {
                "max_file_size": 0.0,
                "min_file_size": 0.0,
                "total_file_size": 0.0,
            }
            if len(folders_to_use) > 0:
                # if we have valid folders
                path_list = []
                max_file_size = 0
                min_file_size = MB * GB
                total_file_size = 0
                cm_files = self.m_files
                for folder in folders_to_use:
                    plist, profile = self._get_input_files(
                        input_path=os.path.join(self.input_folder, folder),
                        output_path=os.path.join(self.output_folder, folder),
                        cm_files=cm_files,
                        min_file_size=min_file_size,
                        max_file_size=max_file_size,
                    )
                    path_list += [os.path.join(self.input_folder, folder, x) for x in plist]
                    total_file_size += profile["total_file_size"]
                    if len(path_list) >= cm_files > 0:
                        break
                    max_file_size = profile["max_file_size"] * MB
                    min_file_size = profile["min_file_size"] * MB
                    if cm_files > 0:
                        cm_files -= len(plist)
                profile["total_file_size"] = total_file_size
            else:
                path_list = []
        else:
            # Get input files list
            path_list, profile = self._get_input_files(
                input_path=self.input_folder,
                output_path=self.output_folder,
                cm_files=self.m_files,
            )
        return path_list, profile

    def get_table(self, path: str) -> pa.table:
        """
        Attempts to read a PyArrow table from the given path.

        Args:
            path (str): Path to the file containing the table.

        Returns:
            pyarrow.Table: PyArrow table if read successfully, None otherwise.
        """

        try:
            table = pq.read_table(path)
            return table
        except (FileNotFoundError, IOError, pa.ArrowException) as e:
            print(f"Error reading table from {path}: {e}")
            return None

    def get_output_location(self, path: str) -> str:
        """
        Get output location based on input
        :param path: input file location
        :return: output file location
        """
        return path.replace(self.input_folder, self.output_folder)

    def save_table(self, output_path: str, table: pa.Table) -> tuple[int, dict[str, Any]]:
        """
        Saves a pyarrow table to a file and returns information about the operation.

        Args:
            table (pyarrow.Table): The pyarrow table to save.
            output_path (str): The path to the output file.

        Returns:
            tuple: A tuple containing:
                - size_in_memory (int): The size of the table in memory (bytes).
                - file_info (dict or None): A dictionary containing:
                    - name (str): The name of the file.
                    - size (int): The size of the file (bytes).
                If saving fails, file_info will be None.
        """
        # Get table size in memory
        size_in_memory = table.nbytes
        try:
            # Write the table to parquet format
            pq.write_table(table, output_path)

            # Get file size and create file_info
            file_info = {"name": os.path.basename(output_path), "size": os.path.getsize(output_path)}
            return size_in_memory, file_info

        except Exception as e:
            print(f"Error saving table to {output_path}: {e}")
            return size_in_memory, None

    def save_job_metadata(self, metadata: dict[str, Any]) -> dict[str, Any]:
        """
        Save metadata
        :param metadata: a dictionary, containing the following keys
        (see https://github.ibm.com/arc/dmf-library/issues/158):
            "pipeline",
            "job details",
            "code",
            "job_input_params",
            "execution_stats",
            "job_output_stats"
        two additional elements:
            "source"
            "target"
        are filled bu implementation
        :return: a dictionary as
        defined https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/put_object.html
        in the case of failure dict is None
        """
        metadata["source"] = {"name": self.input_folder, "type": "path"}
        metadata["target"] = {"name": self.output_folder, "type": "path"}
        return self.save_file(
            file_path=os.path.join(self.output_folder, "metadata.json"),
            bytes_data=json.dumps(metadata, indent=2).encode(),
        )

    def get_file(self, file_path: str) -> bytes:
        """
        Gets the contents of a file as a byte array, decompressing gz files if needed.

        Args:
            file_path (str): The path to the file.

        Returns:
            bytes: The contents of the file as a byte array, or None if an error occurs.
        """

        try:
            if file_path.endswith(".gz"):
                with gzip.open(file_path, "rb") as f:
                    data = f.read()
            else:
                with open(file_path, "rb") as f:
                    data = f.read()
            return data

        except (FileNotFoundError, gzip.BadGzipFile) as e:
            print(f"Error reading file {file_path}: {e}")
            raise e

    def get_folder_files(self, folder_path: str, extensions: list[str]) -> list[bytes]:
        """
        Gets the byte contents of files with specific extensions in a directory.

        Args:
            folder_path (str): The directory path.
            extensions (list): A list of file extensions (without dots).

        Returns:
            list: A list of byte arrays, where each element is the content of a file
                matching the extensions.
        """

        matching_files = []
        for ext in extensions:
            matching_files.extend(glob.glob(os.path.join(folder_path, f"*.{ext}")))

        file_contents = []
        for filename in matching_files:
            file_contents.append(self.get_file(filename))
        return file_contents

    def save_file(self, file_path: str, bytes_data: bytes) -> dict[str, Any]:
        """
        Saves bytes to a file and returns a dictionary with file information.

        Args:
            bytes_data (bytes): The bytes data to save.
            file_path (str): The full name of the file to save.

        Returns:
            dict or None: A dictionary with "name" and "size" keys if successful,
                        or None if saving fails.
        """

        try:
            with open(file_path, "wb") as f:
                f.write(bytes_data)
            file_info = {"name": file_path, "size": os.path.getsize(file_path)}
            return file_info

        except Exception as e:
            print(f"Error saving bytes to file {file_path}: {e}")
            return None