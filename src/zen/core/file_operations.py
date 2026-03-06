"""
Zen File Manager for MCP Server
Handles file upload/download operations using BLOB (LONGVARBINARY) storage
Based on successful test_blob_clob_upload_sqlalchemy.py results

Modified for actian-zen: Uses ZenConnection for shared engine management.
"""

import os
import hashlib
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine, Table, Column, Integer, String, LargeBinary, MetaData, select, text
from sqlalchemy.orm import Session


class ZenFileManager:
    """Manager for file upload/download operations using Zen BLOB storage"""

    def __init__(self, connection):
        """
        Initialize file manager.

        Args:
            connection: ZenConnection instance (preferred) or connection string (legacy)
        """
        # Import here to avoid circular import
        from .connection import ZenConnection

        if isinstance(connection, ZenConnection):
            # Use shared engine from ZenConnection
            self.engine = connection.get_engine()
            self._owns_engine = False
            self._zen_connection = connection
        else:
            # Legacy: create own engine
            connection_string = connection
            if not connection_string.startswith('zen://'):
                connection_string = f"zen://?odbc_connect={connection_string}"

            self.engine = create_engine(connection_string, echo=False)
            self._owns_engine = True
            self._zen_connection = None

        self.metadata = MetaData()

    def compute_file_hash(self, file_path):
        """Compute SHA256 hash of file"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(65536)  # 64KB chunks
                if not chunk:
                    break
                sha256.update(chunk)
        return sha256.hexdigest()

    def upload_file(self, table_name, file_path, metadata_fields=None):
        """
        Upload file to database BLOB column

        Args:
            table_name: Name of table with BLOB column
            file_path: Path to file to upload
            metadata_fields: Dict of additional metadata fields

        Returns:
            dict with upload result and file info
        """
        try:
            file_path = Path(file_path)

            # Check file exists
            if not file_path.exists():
                return {
                    "uploaded": False,
                    "error": f"File not found: {file_path}"
                }

            # Get file info
            file_size = file_path.stat().st_size
            file_name = file_path.name

            # Read file data
            with open(file_path, 'rb') as f:
                file_data = f.read()

            # Compute hash
            file_hash = self.compute_file_hash(file_path)

            # Build insert data
            insert_data = {
                "file_name": file_name,
                "file_data": file_data,
                "file_size": file_size,
                "file_hash": file_hash,
                "upload_date": datetime.now()
            }

            # Add user metadata fields
            if metadata_fields:
                insert_data.update(metadata_fields)

            # Reflect table and insert
            table = Table(table_name, self.metadata, autoload_with=self.engine)

            with self.engine.begin() as conn:
                result = conn.execute(table.insert().values(**insert_data))
                inserted_id = result.lastrowid if hasattr(result, 'lastrowid') else None

            return {
                "uploaded": True,
                "file_name": file_name,
                "file_size": file_size,
                "file_hash": file_hash,
                "table": table_name,
                "id": inserted_id,
                "upload_date": insert_data["upload_date"].isoformat(),
                "sqlputdata_used": file_size > 15360  # > 15KB threshold
            }

        except Exception as e:
            return {
                "uploaded": False,
                "error": str(e),
                "file_path": str(file_path)
            }

    def download_file(self, table_name, file_id, output_path, id_column="id", blob_column="file_data"):
        """
        Download file from database BLOB column

        Args:
            table_name: Name of table with BLOB column
            file_id: ID of file record to download
            output_path: Path where file should be saved
            id_column: Name of ID column (default: "id")
            blob_column: Name of BLOB column (default: "file_data")

        Returns:
            dict with download result and file info
        """
        try:
            output_path = Path(output_path)

            # Reflect table
            table = Table(table_name, self.metadata, autoload_with=self.engine)

            # Query file data
            with self.engine.connect() as conn:
                query = select(table).where(table.c[id_column] == file_id)
                result = conn.execute(query).first()

                if not result:
                    return {
                        "downloaded": False,
                        "error": f"File with ID {file_id} not found in {table_name}"
                    }

                # Get BLOB data
                file_data = result._mapping[blob_column]

                if file_data is None:
                    return {
                        "downloaded": False,
                        "error": f"No BLOB data found for ID {file_id}"
                    }

                # Get other metadata
                file_name = result._mapping.get("file_name", f"downloaded_{file_id}")
                stored_size = result._mapping.get("file_size", len(file_data))
                stored_hash = result._mapping.get("file_hash", None)

            # Write to output file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(file_data)

            # Compute hash for verification
            downloaded_hash = self.compute_file_hash(output_path)

            # Verify integrity
            hash_match = (downloaded_hash == stored_hash) if stored_hash else None
            size_match = len(file_data) == stored_size

            return {
                "downloaded": True,
                "file_name": file_name,
                "output_path": str(output_path),
                "file_size": len(file_data),
                "stored_size": stored_size,
                "downloaded_hash": downloaded_hash,
                "stored_hash": stored_hash,
                "hash_verified": hash_match,
                "size_verified": size_match,
                "integrity": "VERIFIED" if (hash_match and size_match) else "UNVERIFIED",
                "sqlgetdata_chunks": (len(file_data) // 65536) + 1
            }

        except Exception as e:
            return {
                "downloaded": False,
                "error": str(e),
                "table": table_name,
                "file_id": file_id
            }

    def list_files(self, table_name, id_column="id"):
        """
        List files stored in table

        Args:
            table_name: Name of table with file records
            id_column: Name of ID column (default: "id")

        Returns:
            dict with list of files and their metadata
        """
        try:
            table = Table(table_name, self.metadata, autoload_with=self.engine)

            # Select all except BLOB data (avoid loading large data)
            columns_to_select = [c for c in table.c if c.name != "file_data" and c.name != "binary_data"]

            with self.engine.connect() as conn:
                query = select(*columns_to_select).order_by(table.c[id_column].desc())
                results = conn.execute(query).fetchall()

                files = []
                for row in results:
                    file_info = dict(row._mapping)
                    files.append(file_info)

                return {
                    "table": table_name,
                    "file_count": len(files),
                    "files": files
                }

        except Exception as e:
            return {
                "error": str(e),
                "table": table_name
            }

    def delete_file(self, table_name, file_id, id_column="id"):
        """
        Delete file from database

        Args:
            table_name: Name of table
            file_id: ID of file to delete
            id_column: Name of ID column (default: "id")

        Returns:
            dict with deletion result
        """
        try:
            table = Table(table_name, self.metadata, autoload_with=self.engine)

            with self.engine.begin() as conn:
                result = conn.execute(
                    table.delete().where(table.c[id_column] == file_id)
                )

                if result.rowcount > 0:
                    return {
                        "deleted": True,
                        "file_id": file_id,
                        "table": table_name
                    }
                else:
                    return {
                        "deleted": False,
                        "error": f"File with ID {file_id} not found",
                        "table": table_name
                    }

        except Exception as e:
            return {
                "deleted": False,
                "error": str(e),
                "table": table_name,
                "file_id": file_id
            }

    def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
