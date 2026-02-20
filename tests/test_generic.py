
import os
import shutil
import tempfile
import pytest
from librephone.extractor import Extractor
from librephone.typedefs import Bintypes

def test_clone_generic_fallback():
    # Verify Extractor can instantiate without devices.lst crashing
    # Verify clone_generic method is present and callable

    e = Extractor()
    assert hasattr(e, "clone_generic")

    # Simple check on clone_generic logic
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a dummy structure
        bin_dir = os.path.join(tmpdir, "bin")
        os.makedirs(bin_dir)

        # Create a file
        fpath = os.path.join(bin_dir, "test_file")
        with open(fpath, "wb") as f:
            f.write(bytes([0x7f, 0x45, 0x4c, 0x46])) # ELF64

        # Output dir
        out_dir = os.path.join(tmpdir, "output")
        os.makedirs(out_dir)

        # Call clone_generic
        # Note: clone_generic skips output directory itself if it's inside input directory to avoid recursion?
        # No, find_files recursively scans.
        # If out_dir is inside tmpdir, find_files will pick it up as "ELF64" if it finds files inside.
        # Since out_dir is empty initially, find_files won't find anything there.
        # But as we copy, find_files loop runs on os.walk() generator. Modifying dir while walking?
        # os.walk behavior: if topdown=True (default), we can modify dirs in-place to prune.
        # find_files uses os.walk(indir).
        # To be safe, put out_dir outside tmpdir or rely on copy behavior.
        # Let's put out_dir outside.

        with tempfile.TemporaryDirectory() as out_tmp:
            out_dir = out_tmp # Use separate temp dir for output

            e.clone_generic(tmpdir, out_dir)

            # Check if file copied
            # It should copy to output/bin/test_file
            # Note: clone_generic logic copies relative paths.
            # If indir is /tmp/foo, and file is /tmp/foo/bin/test_file.
            # relpath is bin/test_file.
            # dst is /tmp/output/bin/test_file.

            expected_dst = os.path.join(out_dir, "bin", "test_file")
            assert os.path.exists(expected_dst)
