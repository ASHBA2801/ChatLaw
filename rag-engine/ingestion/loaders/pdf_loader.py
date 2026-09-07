"""PDF Discovery, Validation, and Hashing Loader."""

import hashlib
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from ..models import FileHashInfo


class PDFLoader:
    """Discovers, validates, and hashes PDF documents from a specified directory."""

    def __init__(self, root_dir: str | Path):
        self.root_dir = Path(root_dir).resolve()

    def discover_files(self) -> List[Path]:
        """Recursively discovers all PDF files under the root directory.
        
        Returns:
            List of Path objects sorted deterministically by relative path.
            
        Raises:
            FileNotFoundError: If root_dir does not exist.
            NotADirectoryError: If root_dir is not a directory.
        """
        if not self.root_dir.exists():
            raise FileNotFoundError(f"Input directory does not exist: {self.root_dir}")
        if not self.root_dir.is_dir():
            raise NotADirectoryError(f"Input path is not a directory: {self.root_dir}")

        pdf_files: List[Path] = []
        for root, _, files in os.walk(self.root_dir):
            for file in files:
                if file.lower().endswith(".pdf"):
                    pdf_files.append(Path(root) / file)

        # Deterministic sorting by POSIX relative path
        pdf_files.sort(key=lambda p: p.relative_to(self.root_dir).as_posix().lower())
        return pdf_files

    @staticmethod
    def compute_sha256(file_path: Path, chunk_size: int = 65536) -> str:
        """Computes SHA-256 hash of a file efficiently in chunks.
        
        Args:
            file_path: Path to the target file.
            chunk_size: Byte size of chunks to read.
            
        Returns:
            Hex-encoded SHA-256 digest.
        """
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
        return hasher.hexdigest()

    def get_file_info(self, file_path: Path) -> FileHashInfo:
        """Extracts file metadata and calculates SHA-256 hash.
        
        Args:
            file_path: Path to the target PDF file.
            
        Returns:
            FileHashInfo model populated with metadata.
        """
        stat = file_path.stat()
        sha256_hash = self.compute_sha256(file_path)
        
        try:
            rel_path = file_path.relative_to(self.root_dir).as_posix()
        except ValueError:
            rel_path = file_path.name

        mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)

        return FileHashInfo(
            filename=file_path.name,
            relative_path=rel_path,
            absolute_path=str(file_path.resolve()),
            file_size_bytes=stat.st_size,
            sha256=sha256_hash,
            modified_at_iso=mtime.isoformat(),
        )

    def load_corpus_metadata(self) -> Tuple[List[FileHashInfo], List[str]]:
        """Discovers all PDFs and extracts their hash metadata.
        
        Returns:
            Tuple containing:
                - List of FileHashInfo objects for discovered files
                - List of duplicate SHA-256 hashes found (if any)
        """
        discovered = self.discover_files()
        file_infos: List[FileHashInfo] = []
        seen_hashes = {}
        duplicates: List[str] = []

        for path in discovered:
            info = self.get_file_info(path)
            file_infos.append(info)
            if info.sha256 in seen_hashes:
                duplicates.append(info.sha256)
            else:
                seen_hashes[info.sha256] = info.filename

        return file_infos, list(set(duplicates))

    @staticmethod
    def generate_document_id(filename: str, sha256_hash: str) -> str:
        """Generates a clean, deterministic document identifier.
        
        Example:
            'Bharatiya_Nagarik_Suraksha_Sanhita,_2023.pdf' -> 'Bharatiya_Nagarik_Suraksha_Sanhita_2023'
        """
        stem = Path(filename).stem
        # Clean special chars, replace commas and extra spaces with underscores
        clean_stem = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', stem)
        clean_stem = re.sub(r'_+', '_', clean_stem).strip('_')
        return clean_stem
