#!/usr/bin/env python3
"""
Token Limit Guard for Healthcare AI Tools - Production Version 2.0
Prevents token overflow when processing large diffs/commits

WHY: Large PRs (50+ files) can exceed LLM context windows, causing AI failures
ENHANCEMENTS: Dynamic thresholds, smart chunking, retry logic, monitoring

Version: 2.0.0
Author: GitOps 2.0 Healthcare Intelligence
License: MIT
"""

import logging
import subprocess
import json
import yaml
import time
from typing import Tuple, Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import os
import re


# Production logger setup
class ProductionLogger:
    """Structured logging for production monitoring"""
    
    def __init__(self, name: str, level: str = "INFO", format_type: str = "json"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        self.format_type = format_type
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            if format_type == "json":
                handler.setFormatter(self._json_formatter())
            else:
                handler.setFormatter(logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                ))
            self.logger.addHandler(handler)
    
    def _json_formatter(self):
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                log_data = {
                    'timestamp': self.formatTime(record, self.datefmt),
                    'level': record.levelname,
                    'logger': record.name,
                    'message': record.getMessage(),
                    'module': record.module,
                    'function': record.funcName,
                    'line': record.lineno
                }
                if record.exc_info:
                    log_data['exception'] = self.formatException(record.exc_info)
                return json.dumps(log_data)
        return JsonFormatter()
    
    def info(self, message: str, **kwargs):
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        self.logger.error(message, extra=kwargs)
    
    def debug(self, message: str, **kwargs):
        self.logger.debug(message, extra=kwargs)


# Initialize production logger
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "text")
logger = ProductionLogger(__name__, LOG_LEVEL, LOG_FORMAT)


class TokenLimitExceededError(Exception):
    """Raised when input exceeds safe token limits"""
    pass


class ChunkingStrategy(Enum):
    """Strategies for splitting large diffs"""
    FILE_BOUNDARY = "file"  # Split by file boundaries
    HUNK_BOUNDARY = "hunk"  # Split by diff hunks
    SIZE_BASED = "size"      # Split by size only


@dataclass
class TokenEstimate:
    """Token estimation with metadata"""
    text_length: int
    estimated_tokens: int
    max_tokens: int
    usage_percentage: float
    is_safe: bool
    model: str
    
    def to_dict(self) -> Dict:
        return {
            'text_length': self.text_length,
            'estimated_tokens': self.estimated_tokens,
            'max_tokens': self.max_tokens,
            'usage_percentage': self.usage_percentage,
            'is_safe': self.is_safe,
            'model': self.model
        }


@dataclass
class ChunkMetadata:
    """Metadata for a diff chunk"""
    chunk_index: int
    total_chunks: int
    file_count: int
    token_estimate: int
    files: List[str]


# Model capabilities (auto-detect based on model name)
MODEL_CAPABILITIES = {
    "gpt-4": {"context_window": 128_000, "output_tokens": 4_096},
    "gpt-4-turbo": {"context_window": 128_000, "output_tokens": 4_096},
    "gpt-4-32k": {"context_window": 32_000, "output_tokens": 4_096},
    "gpt-3.5-turbo": {"context_window": 16_000, "output_tokens": 4_096},
    "gpt-3.5-turbo-16k": {"context_window": 16_000, "output_tokens": 4_096},
    "claude-3-opus": {"context_window": 200_000, "output_tokens": 4_096},
    "claude-3-sonnet": {"context_window": 200_000, "output_tokens": 4_096},
    "default": {"context_window": 8_000, "output_tokens": 2_048}
}


class TokenLimitGuard:
    """
    Production-ready token limit guard with dynamic thresholds
    
    Enhancements in v2.0:
    - Dynamic threshold detection based on model
    - Smart chunking strategies
    - Retry logic with exponential backoff
    - Cost estimation and monitoring
    - Configuration file support
    """
    
    def __init__(
        self,
        model: str = "gpt-4",
        safety_margin: float = 0.7,
        chars_per_token: int = 4,
        config_file: Optional[str] = None,
        enable_retry: bool = True,
        max_retries: int = 3
    ):
        """
        Initialize token limit guard
        
        Args:
            model: AI model name for dynamic threshold
            safety_margin: Percentage of context to use (0.0-1.0)
            chars_per_token: Average characters per token
            config_file: Path to production.yaml config
            enable_retry: Enable retry logic for transient failures
            max_retries: Maximum retry attempts
        """
        self.model = model
        self.safety_margin = safety_margin
        self.chars_per_token = chars_per_token
        self.enable_retry = enable_retry
        self.max_retries = max_retries
        
        # Load configuration
        self.config = self._load_config(config_file)
        
        # Detect model capabilities
        self.capabilities = self._detect_model_capabilities(model)
        self.max_tokens = int(self.capabilities["context_window"] * safety_margin)
        
        # Performance tracking
        self.total_checks = 0
        self.total_chunks_created = 0
        self.total_retries = 0
        
        logger.info(
            f"TokenLimitGuard initialized: model={model}, "
            f"max_tokens={self.max_tokens:,}, "
            f"safety_margin={safety_margin}"
        )
    
    def _load_config(self, config_file: Optional[str]) -> Dict:
        """Load configuration from file"""
        if not config_file:
            # Try default locations
            config_paths = [
                "config/production.yaml",
                "../config/production.yaml",
                "../../config/production.yaml",
            ]
            for path in config_paths:
                if Path(path).exists():
                    config_file = path
                    break
        
        if config_file and Path(config_file).exists():
            try:
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
                logger.info(f"Loaded configuration from {config_file}")
                return config.get('safety', {})
            except Exception as e:
                logger.warning(f"Failed to load config from {config_file}: {e}")
        
        return {}
    
    def _detect_model_capabilities(self, model: str) -> Dict[str, int]:
        """
        Dynamically detect model capabilities
        
        Returns:
            Dict with context_window and output_tokens
        """
        # Check exact match
        if model in MODEL_CAPABILITIES:
            return MODEL_CAPABILITIES[model]
        
        # Check prefix match (e.g., "gpt-4-0613" matches "gpt-4")
        for known_model, caps in MODEL_CAPABILITIES.items():
            if model.startswith(known_model):
                logger.info(f"Matched {model} to {known_model} capabilities")
                return caps
        
        # Fallback to default
        logger.warning(f"Unknown model '{model}', using default capabilities")
        return MODEL_CAPABILITIES["default"]
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count from text
        WHY: Quick approximation without external tiktoken dependency
        """
        return len(text) // self.chars_per_token
    
    def check_token_limit(
        self,
        text: str,
        context: str = "input"
    ) -> TokenEstimate:
        """
        Check if text exceeds safe token limits
        
        Args:
            text: Text to check
            context: Context description for logging
        
        Returns:
            TokenEstimate with details
        """
        self.total_checks += 1
        
        text_length = len(text)
        estimated_tokens = self.estimate_tokens(text)
        usage_percentage = (estimated_tokens / self.max_tokens) * 100
        is_safe = estimated_tokens <= self.max_tokens
        
        estimate = TokenEstimate(
            text_length=text_length,
            estimated_tokens=estimated_tokens,
            max_tokens=self.max_tokens,
            usage_percentage=usage_percentage,
            is_safe=is_safe,
            model=self.model
        )
        
        if not is_safe:
            logger.warning(
                f"{context} exceeds token limit: "
                f"{estimated_tokens:,} > {self.max_tokens:,} tokens "
                f"({usage_percentage:.1f}%)"
            )
        else:
            logger.debug(
                f"{context} within token limit: "
                f"{estimated_tokens:,}/{self.max_tokens:,} tokens "
                f"({usage_percentage:.1f}%)"
            )
        
        return estimate
    
    def validate_for_ai_processing(
        self,
        text: str,
        context: str = "input",
        raise_on_exceed: bool = True
    ) -> TokenEstimate:
        """
        Validate that input is within safe token limits
        
        Args:
            text: Text to validate
            context: Context description
            raise_on_exceed: Raise exception if limit exceeded
        
        Returns:
            TokenEstimate
        
        Raises:
            TokenLimitExceededError: If raise_on_exceed and limit exceeded
        """
        estimate = self.check_token_limit(text, context)
        
        if not estimate.is_safe and raise_on_exceed:
            raise TokenLimitExceededError(
                f"{context} too large for {self.model}: "
                f"{estimate.estimated_tokens:,} tokens "
                f"(max: {estimate.max_tokens:,}). "
                f"\nConsider:\n"
                f"  1. Break PR into smaller changesets (< 100 files)\n"
                f"  2. Use chunking mode (--chunk flag)\n"
                f"  3. Switch to model with larger context ({self._suggest_larger_model()})\n"
                f"  4. Process files in batches"
            )
        
        return estimate
    
    def _suggest_larger_model(self) -> str:
        """Suggest a model with larger context window"""
        current_window = self.capabilities["context_window"]
        
        # Find models with larger context
        larger_models = [
            (name, caps["context_window"])
            for name, caps in MODEL_CAPABILITIES.items()
            if caps["context_window"] > current_window
        ]
        
        if larger_models:
            larger_models.sort(key=lambda x: x[1])
            return larger_models[0][0]
        
        return "claude-3-opus (200K context)"
    
    def chunk_text_smartly(
        self,
        text: str,
        strategy: ChunkingStrategy = ChunkingStrategy.FILE_BOUNDARY,
        overlap_lines: int = 5
    ) -> List[Tuple[str, ChunkMetadata]]:
        """
        Split large text into token-safe chunks using smart strategies
        
        Args:
            text: Text to chunk
            strategy: Chunking strategy
            overlap_lines: Lines of overlap between chunks (for context)
        
        Returns:
            List of (chunk_text, metadata) tuples
        """
        max_chars = self.max_tokens * self.chars_per_token
        
        if strategy == ChunkingStrategy.FILE_BOUNDARY:
            chunks = self._chunk_by_file_boundaries(text, max_chars, overlap_lines)
        elif strategy == ChunkingStrategy.HUNK_BOUNDARY:
            chunks = self._chunk_by_hunk_boundaries(text, max_chars)
        else:  # SIZE_BASED
            chunks = self._chunk_by_size(text, max_chars)
        
        self.total_chunks_created += len(chunks)
        logger.info(f"Created {len(chunks)} chunks using {strategy.value} strategy")
        
        return chunks
    
    def _chunk_by_file_boundaries(
        self,
        diff_text: str,
        max_chars: int,
        overlap_lines: int
    ) -> List[Tuple[str, ChunkMetadata]]:
        """Split diff by file boundaries (preserves semantic meaning)"""
        # Split by file boundaries
        file_diffs = []
        current_file = []
        current_filename = None
        
        for line in diff_text.splitlines():
            if line.startswith("diff --git"):
                if current_file:
                    file_diffs.append((current_filename, "\n".join(current_file)))
                    current_file = []
                # Extract filename from diff header
                match = re.search(r'diff --git a/(.*?) b/', line)
                current_filename = match.group(1) if match else "unknown"
            current_file.append(line)
        
        if current_file:
            file_diffs.append((current_filename, "\n".join(current_file)))
        
        # Group files into chunks under max_chars
        chunks = []
        current_chunk = []
        current_files = []
        current_size = 0
        
        for filename, file_diff in file_diffs:
            file_size = len(file_diff)
            
            # Single file exceeds limit - must split it
            if file_size > max_chars:
                # Save current chunk if any
                if current_chunk:
                    metadata = ChunkMetadata(
                        chunk_index=len(chunks),
                        total_chunks=0,  # Will update later
                        file_count=len(current_files),
                        token_estimate=self.estimate_tokens("\n\n".join(current_chunk)),
                        files=current_files.copy()
                    )
                    chunks.append(("\n\n".join(current_chunk), metadata))
                    current_chunk = []
                    current_files = []
                    current_size = 0
                
                # Split large file by hunks
                file_chunks = self._split_large_file(file_diff, filename, max_chars)
                chunks.extend(file_chunks)
            
            # Normal file - add to current chunk
            elif current_size + file_size <= max_chars:
                current_chunk.append(file_diff)
                current_files.append(filename)
                current_size += file_size
            
            # Would exceed - start new chunk
            else:
                if current_chunk:
                    metadata = ChunkMetadata(
                        chunk_index=len(chunks),
                        total_chunks=0,
                        file_count=len(current_files),
                        token_estimate=self.estimate_tokens("\n\n".join(current_chunk)),
                        files=current_files.copy()
                    )
                    chunks.append(("\n\n".join(current_chunk), metadata))
                current_chunk = [file_diff]
                current_files = [filename]
                current_size = file_size
        
        # Add remaining chunk
        if current_chunk:
            metadata = ChunkMetadata(
                chunk_index=len(chunks),
                total_chunks=0,
                file_count=len(current_files),
                token_estimate=self.estimate_tokens("\n\n".join(current_chunk)),
                files=current_files.copy()
            )
            chunks.append(("\n\n".join(current_chunk), metadata))
        
        # Update total_chunks in metadata
        total = len(chunks)
        for i, (chunk_text, meta) in enumerate(chunks):
            meta.chunk_index = i
            meta.total_chunks = total
        
        return chunks
    
    def _split_large_file(
        self,
        file_diff: str,
        filename: str,
        max_chars: int
    ) -> List[Tuple[str, ChunkMetadata]]:
        """Split a single large file by diff hunks"""
        hunks = file_diff.split("@@")
        header = hunks[0]  # File header
        
        chunks = []
        current_chunk = [header]
        current_size = len(header)
        
        for hunk in hunks[1:]:
            hunk_with_sep = "@@" + hunk
            hunk_size = len(hunk_with_sep)
            
            if current_size + hunk_size > max_chars:
                # Save current chunk
                metadata = ChunkMetadata(
                    chunk_index=len(chunks),
                    total_chunks=0,
                    file_count=1,
                    token_estimate=self.estimate_tokens("".join(current_chunk)),
                    files=[filename]
                )
                chunks.append(("".join(current_chunk), metadata))
                current_chunk = [header, hunk_with_sep]
                current_size = len(header) + hunk_size
            else:
                current_chunk.append(hunk_with_sep)
                current_size += hunk_size
        
        if len(current_chunk) > 1:  # More than just header
            metadata = ChunkMetadata(
                chunk_index=len(chunks),
                total_chunks=0,
                file_count=1,
                token_estimate=self.estimate_tokens("".join(current_chunk)),
                files=[filename]
            )
            chunks.append(("".join(current_chunk), metadata))
        
        # Update total_chunks
        total = len(chunks)
        for chunk_text, meta in chunks:
            meta.total_chunks = total
        
        return chunks
    
    def _chunk_by_hunk_boundaries(
        self,
        diff_text: str,
        max_chars: int
    ) -> List[Tuple[str, ChunkMetadata]]:
        """Split diff by hunk boundaries"""
        # Simple hunk-based splitting
        hunks = diff_text.split("@@")
        chunks = []
        current_chunk = []
        current_size = 0
        
        for hunk in hunks:
            hunk_with_sep = "@@" + hunk if chunks else hunk
            hunk_size = len(hunk_with_sep)
            
            if current_size + hunk_size > max_chars and current_chunk:
                metadata = ChunkMetadata(
                    chunk_index=len(chunks),
                    total_chunks=0,
                    file_count=0,
                    token_estimate=self.estimate_tokens("".join(current_chunk)),
                    files=[]
                )
                chunks.append(("".join(current_chunk), metadata))
                current_chunk = [hunk_with_sep]
                current_size = hunk_size
            else:
                current_chunk.append(hunk_with_sep)
                current_size += hunk_size
        
        if current_chunk:
            metadata = ChunkMetadata(
                chunk_index=len(chunks),
                total_chunks=len(chunks) + 1,
                file_count=0,
                token_estimate=self.estimate_tokens("".join(current_chunk)),
                files=[]
            )
            chunks.append(("".join(current_chunk), metadata))
        
        return chunks
    
    def _chunk_by_size(
        self,
        text: str,
        max_chars: int
    ) -> List[Tuple[str, ChunkMetadata]]:
        """Split text by size only (no semantic boundaries)"""
        chunks = []
        for i in range(0, len(text), max_chars):
            chunk_text = text[i:i + max_chars]
            metadata = ChunkMetadata(
                chunk_index=len(chunks),
                total_chunks=0,
                file_count=0,
                token_estimate=self.estimate_tokens(chunk_text),
                files=[]
            )
            chunks.append((chunk_text, metadata))
        
        # Update total_chunks
        total = len(chunks)
        for chunk_text, meta in chunks:
            meta.total_chunks = total
        
        return chunks
    
    def retry_with_backoff(
        self,
        func,
        *args,
        **kwargs
    ) -> Any:
        """
        Retry function with exponential backoff
        
        Args:
            func: Function to retry
            *args: Function arguments
            **kwargs: Function keyword arguments
        
        Returns:
            Function result
        
        Raises:
            Last exception if all retries fail
        """
        if not self.enable_retry:
            return func(*args, **kwargs)
        
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except (TokenLimitExceededError, subprocess.TimeoutExpired) as e:
                last_exception = e
                self.total_retries += 1
                
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(
                        f"Retry {attempt + 1}/{self.max_retries} after {wait_time}s: {e}"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {self.max_retries} retries failed")
        
        raise last_exception
    
    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int = 0,
        model: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Estimate cost for token usage
        
        Args:
            input_tokens: Input token count
            output_tokens: Output token count (estimated)
            model: Model name (uses self.model if None)
        
        Returns:
            Dict with cost breakdown
        """
        model = model or self.model
        
        # Pricing per 1M tokens (as of 2025)
        pricing = {
            "gpt-4": {"input": 30.0, "output": 60.0},
            "gpt-4-turbo": {"input": 10.0, "output": 30.0},
            "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
            "claude-3-opus": {"input": 15.0, "output": 75.0},
            "claude-3-sonnet": {"input": 3.0, "output": 15.0},
            "default": {"input": 10.0, "output": 30.0}
        }
        
        rates = pricing.get(model, pricing["default"])
        
        input_cost = (input_tokens / 1_000_000) * rates["input"]
        output_cost = (output_tokens / 1_000_000) * rates["output"]
        total_cost = input_cost + output_cost
        
        return {
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost_usd": round(input_cost, 4),
            "output_cost_usd": round(output_cost, 4),
            "total_cost_usd": round(total_cost, 4)
        }
    
    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "safety_margin": self.safety_margin,
            "total_checks": self.total_checks,
            "total_chunks_created": self.total_chunks_created,
            "total_retries": self.total_retries,
            "retry_enabled": self.enable_retry
        }


def get_git_diff(
    ref: str = "HEAD",
    max_files: Optional[int] = None,
    timeout: int = 30
) -> str:
    """
    Get git diff with optional file limit
    WHY: Allow progressive loading if full diff is too large
    
    Args:
        ref: Git reference
        max_files: Maximum files to include
        timeout: Command timeout in seconds
    
    Returns:
        Git diff text
    """
    # Sanitize ref (WHY: prevent command injection)
    bad_chars = [';', '&', '|', '`', '$', '(', ')', '>', '<', '\n']
    if any(c in ref for c in bad_chars):
        raise ValueError(f"Invalid git ref: {ref}")
    
    try:
        if max_files:
            # Get list of changed files
            proc = subprocess.Popen(
                ["git", "diff", ref, "--name-only"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            files_out, _ = proc.communicate(timeout=timeout)
            files = files_out.decode('utf-8').splitlines()[:max_files]
            
            if not files:
                return ""
            
            # Get diff for specific files
            cmd = ["git", "diff", ref, "--"] + files
        else:
            cmd = ["git", "diff", ref]
        
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        out, err = proc.communicate(timeout=timeout)
        
        if proc.returncode != 0:
            logger.error(f"Git diff failed: {err.decode('utf-8')}")
            return ""
        
        return out.decode('utf-8', errors='replace')
        
    except subprocess.TimeoutExpired:
        proc.kill()
        logger.error(f"Git diff timed out after {timeout}s")
        return ""
    except Exception as e:
        logger.error(f"Error getting git diff: {e}")
        return ""


if __name__ == "__main__":
    import sys
    
    # Check for test mode
    if "--test" in sys.argv:
        print("[OK] Token limit guard module loaded successfully")
        print(f"   - {len(MODEL_CAPABILITIES)} model configurations")
        print("   - Dynamic threshold detection")
        print("   - Smart chunking strategies: 3")
        print("   - Retry logic with exponential backoff")
        sys.exit(0)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Token limit guard operational. Use as module for AI operations.")

