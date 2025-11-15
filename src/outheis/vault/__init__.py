"""Vault operations: read, write, index, tags."""

from outheis.vault.reader import (
    VaultFile,
    read_file,
    iter_vault_files,
    find_by_tag,
    find_by_title,
    search_content,
)
