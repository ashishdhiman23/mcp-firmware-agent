"""ELF parser for symbol resolution using addr2line."""

import subprocess
import tempfile
import os
from typing import List, Optional, Dict
from pathlib import Path

from ..models import SymbolResolution


class ElfParser:
    """Parser for ELF binaries that resolves memory addresses to symbols."""
    
    def __init__(self, addr2line_path: str = "addr2line"):
        """Initialize the ELF parser.
        
        Args:
            addr2line_path: Path to the addr2line binary
        """
        self.addr2line_path = addr2line_path
        self._check_addr2line_availability()
    
    def _check_addr2line_availability(self):
        """Check if addr2line is available on the system."""
        try:
            result = subprocess.run(
                [self.addr2line_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise FileNotFoundError("addr2line not found or not working")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            # Try alternative paths
            alternative_paths = [
                "arm-none-eabi-addr2line",
                "/usr/bin/addr2line",
                "/usr/local/bin/addr2line",
            ]
            
            for alt_path in alternative_paths:
                try:
                    result = subprocess.run(
                        [alt_path, "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        self.addr2line_path = alt_path
                        return
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    continue
            
            # If no addr2line found, disable symbol resolution
            self.addr2line_path = None
    
    def resolve_addresses(self, elf_content: bytes, addresses: List[str]) -> List[SymbolResolution]:
        """Resolve memory addresses to symbols using the ELF binary.
        
        Args:
            elf_content: Raw ELF binary content
            addresses: List of memory addresses to resolve
            
        Returns:
            List of symbol resolutions
        """
        if not self.addr2line_path or not addresses:
            return [
                SymbolResolution(address=addr, resolved=False)
                for addr in addresses
            ]
        
        resolutions = []
        
        # Create temporary file for ELF binary
        with tempfile.NamedTemporaryFile(suffix=".elf", delete=False) as temp_elf:
            try:
                temp_elf.write(elf_content)
                temp_elf.flush()
                
                # Resolve each address
                for address in addresses:
                    resolution = self._resolve_single_address(temp_elf.name, address)
                    resolutions.append(resolution)
                    
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_elf.name)
                except OSError:
                    pass
        
        return resolutions
    
    def _resolve_single_address(self, elf_path: str, address: str) -> SymbolResolution:
        """Resolve a single memory address to symbol information.
        
        Args:
            elf_path: Path to the ELF file
            address: Memory address to resolve
            
        Returns:
            Symbol resolution result
        """
        # Clean up address format
        clean_address = address.strip()
        if clean_address.startswith("0x"):
            clean_address = clean_address[2:]
        
        try:
            # Run addr2line to get function and file information
            cmd = [
                self.addr2line_path,
                "-f",  # Show function names
                "-C",  # Demangle C++ names
                "-e", elf_path,
                clean_address
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    function_name = lines[0].strip()
                    file_info = lines[1].strip()
                    
                    # Parse file:line information
                    file_name = None
                    line_number = None
                    
                    if ':' in file_info and file_info != "??:0":
                        parts = file_info.rsplit(':', 1)
                        if len(parts) == 2:
                            file_name = parts[0]
                            try:
                                line_number = int(parts[1])
                            except ValueError:
                                pass
                    
                    # Check if resolution was successful
                    resolved = (
                        function_name != "??" and 
                        file_info != "??:0" and
                        function_name.strip() != ""
                    )
                    
                    return SymbolResolution(
                        address=address,
                        function_name=function_name if function_name != "??" else None,
                        file_name=file_name,
                        line_number=line_number,
                        resolved=resolved
                    )
            
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, ValueError):
            pass
        
        # Return unresolved if anything failed
        return SymbolResolution(address=address, resolved=False)
    
    def get_symbol_info(self, elf_content: bytes) -> Dict[str, any]:
        """Get general information about the ELF binary.
        
        Args:
            elf_content: Raw ELF binary content
            
        Returns:
            Dictionary with ELF information
        """
        info = {
            "size": len(elf_content),
            "has_debug_info": False,
            "architecture": "unknown",
            "symbols_available": False
        }
        
        if not self.addr2line_path:
            return info
        
        # Create temporary file for analysis
        with tempfile.NamedTemporaryFile(suffix=".elf", delete=False) as temp_elf:
            try:
                temp_elf.write(elf_content)
                temp_elf.flush()
                
                # Check if debug information is available
                info["has_debug_info"] = self._has_debug_info(temp_elf.name)
                
                # Get architecture information
                info["architecture"] = self._get_architecture(temp_elf.name)
                
                # Check if symbols are available
                info["symbols_available"] = self._has_symbols(temp_elf.name)
                
            finally:
                try:
                    os.unlink(temp_elf.name)
                except OSError:
                    pass
        
        return info
    
    def _has_debug_info(self, elf_path: str) -> bool:
        """Check if the ELF file contains debug information."""
        try:
            # Try to resolve a dummy address to see if debug info is available
            result = subprocess.run(
                [self.addr2line_path, "-e", elf_path, "0x1000"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # If we get anything other than "??:0", debug info is likely present
            return result.returncode == 0 and "??:0" not in result.stdout
            
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False
    
    def _get_architecture(self, elf_path: str) -> str:
        """Get the architecture of the ELF file."""
        try:
            # Use file command to get architecture info
            result = subprocess.run(
                ["file", elf_path],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                output = result.stdout.lower()
                if "arm" in output:
                    return "ARM"
                elif "x86-64" in output or "x86_64" in output:
                    return "x86_64"
                elif "i386" in output:
                    return "i386"
                elif "risc-v" in output or "riscv" in output:
                    return "RISC-V"
                
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass
        
        return "unknown"
    
    def _has_symbols(self, elf_path: str) -> bool:
        """Check if the ELF file has symbol information."""
        try:
            # Use nm command to check for symbols
            result = subprocess.run(
                ["nm", elf_path],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # If nm succeeds and produces output, symbols are available
            return result.returncode == 0 and len(result.stdout.strip()) > 0
            
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False
    
    def extract_addresses_from_log(self, log_content: str) -> List[str]:
        """Extract memory addresses from log content.
        
        Args:
            log_content: Raw log content
            
        Returns:
            List of unique memory addresses found in the log
        """
        import re
        
        # Pattern to match memory addresses
        address_pattern = r"0x[0-9a-fA-F]{8}"
        
        addresses = re.findall(address_pattern, log_content)
        
        # Remove duplicates while preserving order
        unique_addresses = []
        seen = set()
        for addr in addresses:
            if addr not in seen:
                unique_addresses.append(addr)
                seen.add(addr)
        
        return unique_addresses 