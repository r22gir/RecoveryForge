"""
Tests for all new AI, cloud, and tools modules added to RecoveryForge.
"""

import os
import math
import struct
import tempfile
import pytest
import sys
from pathlib import Path

src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_tmp(data: bytes, suffix: str) -> str:
    """Write bytes to a temporary file and return its path."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)
    return path


def _jpeg_bytes() -> bytes:
    """Minimal valid JPEG bytes (SOI + APP0 + EOI)."""
    return (
        b"\xff\xd8\xff\xe0"  # SOI + APP0 marker
        b"\x00\x10"          # APP0 length (16)
        b"JFIF\x00"          # Identifier
        b"\x01\x01"          # Version
        b"\x00"              # Aspect ratio units
        b"\x00\x01\x00\x01"  # X/Y density
        b"\x00\x00"          # Thumbnail size
        b"\xff\xd9"          # EOI
    )


def _pdf_bytes() -> bytes:
    """Minimal valid PDF bytes."""
    return b"%PDF-1.4\n%%EOF"


def _zip_bytes() -> bytes:
    """Create a minimal valid ZIP in memory."""
    import io
    import zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("hello.txt", "Hello, World!")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# AI package imports
# ---------------------------------------------------------------------------

class TestAIImports:
    def test_image_tagger_import(self):
        from recoveryforge.ai.image_tagger import AIImageTagger
        assert AIImageTagger is not None

    def test_ocr_engine_import(self):
        from recoveryforge.ai.ocr_engine import OCREngine
        assert OCREngine is not None

    def test_ransomware_detector_import(self):
        from recoveryforge.ai.ransomware_detector import RansomwareDetector
        assert RansomwareDetector is not None

    def test_quality_scorer_import(self):
        from recoveryforge.ai.quality_scorer import MLQualityScorer
        assert MLQualityScorer is not None

    def test_fragment_assembler_import(self):
        from recoveryforge.ai.fragment_assembler import AIFragmentAssembler
        assert AIFragmentAssembler is not None

    def test_drive_predictor_import(self):
        from recoveryforge.ai.drive_predictor import DriveFailurePredictor
        assert DriveFailurePredictor is not None

    def test_ai_package_init(self):
        from recoveryforge.ai import (
            AIImageTagger, OCREngine, RansomwareDetector,
            MLQualityScorer, AIFragmentAssembler, DriveFailurePredictor,
        )
        for cls in [AIImageTagger, OCREngine, RansomwareDetector,
                    MLQualityScorer, AIFragmentAssembler, DriveFailurePredictor]:
            assert cls is not None


# ---------------------------------------------------------------------------
# AIImageTagger
# ---------------------------------------------------------------------------

class TestAIImageTagger:
    def setup_method(self):
        from recoveryforge.ai.image_tagger import AIImageTagger
        self.tagger = AIImageTagger(model_size="nano")

    def test_instantiation(self):
        assert self.tagger is not None
        assert self.tagger.model_size == "nano"

    def test_model_size_map(self):
        from recoveryforge.ai.image_tagger import AIImageTagger
        for size in ("nano", "small", "medium", "large"):
            t = AIImageTagger(model_size=size)
            assert t._model_name.endswith(".pt")

    def test_detect_objects_missing_file(self):
        result = self.tagger.detect_objects("/nonexistent/file.jpg")
        assert result == []

    def test_detect_faces_missing_file(self):
        result = self.tagger.detect_faces("/nonexistent/file.jpg")
        assert result == []

    def test_classify_scene_no_detections(self):
        from recoveryforge.ai.image_tagger import _infer_scene
        scene = _infer_scene([])
        assert scene.scene_type == "unknown"

    def test_classify_scene_with_office_labels(self):
        from recoveryforge.ai.image_tagger import _infer_scene
        scene = _infer_scene(["laptop", "monitor", "keyboard"])
        assert scene.scene_type == "office"
        assert scene.confidence > 0

    def test_generate_tags_missing_file(self):
        tags = self.tagger.generate_tags("/nonexistent/file.jpg")
        assert isinstance(tags, list)

    def test_batch_process_empty(self):
        results = self.tagger.batch_process([])
        assert results == {}

    def test_batch_process_callback(self):
        called = []
        def cb(current, total, path):
            called.append((current, total, path))
        self.tagger.batch_process(["/nonexistent/a.jpg", "/nonexistent/b.jpg"], callback=cb)
        assert len(called) == 2


# ---------------------------------------------------------------------------
# OCREngine
# ---------------------------------------------------------------------------

class TestOCREngine:
    def setup_method(self):
        from recoveryforge.ai.ocr_engine import OCREngine
        self.engine = OCREngine(languages=["eng"])

    def test_instantiation(self):
        assert self.engine is not None
        assert self.engine._lang_string == "eng"

    def test_multi_language(self):
        from recoveryforge.ai.ocr_engine import OCREngine
        eng = OCREngine(languages=["eng", "fra"])
        assert eng._lang_string == "eng+fra"

    def test_extract_text_missing_file(self):
        result = self.engine.extract_text("/nonexistent/image.png")
        assert result.error is not None
        assert result.text == ""

    def test_extract_with_positions_missing_file(self):
        result = self.engine.extract_with_positions("/nonexistent/image.png")
        assert result == []

    def test_detect_language_missing_file(self):
        result = self.engine.detect_language("/nonexistent/image.png")
        assert isinstance(result, str)

    def test_extract_tables_missing_file(self):
        result = self.engine.extract_tables("/nonexistent/image.png")
        assert result == []

    def test_make_searchable_pdf_missing_file(self):
        result = self.engine.make_searchable_pdf("/nonexistent/image.png", "/tmp/out.pdf")
        assert result is False


# ---------------------------------------------------------------------------
# RansomwareDetector
# ---------------------------------------------------------------------------

class TestRansomwareDetector:
    def setup_method(self):
        from recoveryforge.ai.ransomware_detector import RansomwareDetector
        self.detector = RansomwareDetector()

    def test_instantiation(self):
        assert self.detector is not None

    def test_calculate_entropy_random_data(self):
        import os
        data = os.urandom(4096)
        path = _write_tmp(data, ".bin")
        try:
            entropy = self.detector.calculate_entropy(path)
            assert 6.0 <= entropy <= 8.0  # Random data should be high entropy
        finally:
            os.unlink(path)

    def test_calculate_entropy_zero_data(self):
        data = b"\x00" * 4096
        path = _write_tmp(data, ".bin")
        try:
            entropy = self.detector.calculate_entropy(path)
            assert entropy == 0.0
        finally:
            os.unlink(path)

    def test_calculate_entropy_missing_file(self):
        entropy = self.detector.calculate_entropy("/nonexistent/file.bin")
        assert entropy == 0.0

    def test_analyze_file_missing_file(self):
        analysis = self.detector.analyze_file("/nonexistent/file.bin")
        assert analysis.error is not None

    def test_analyze_file_known_extension(self):
        data = b"some data"
        path = _write_tmp(data, ".wncry")
        try:
            analysis = self.detector.analyze_file(path)
            assert analysis.extension_match == ".wncry"
            assert analysis.family is not None
            assert analysis.family.name == "WannaCry"
        finally:
            os.unlink(path)

    def test_analyze_file_high_entropy(self):
        import os
        data = os.urandom(32768)
        path = _write_tmp(data, ".dat")
        try:
            analysis = self.detector.analyze_file(path)
            assert analysis.is_likely_encrypted is True
        finally:
            os.unlink(path)

    def test_find_decryptor_known_family(self):
        decryptor = self.detector.find_decryptor("WannaCry")
        assert decryptor is not None
        assert "WannaKiwi" in decryptor.name or "Wanna" in decryptor.name

    def test_find_decryptor_unknown_family(self):
        decryptor = self.detector.find_decryptor("NonExistentFamily")
        # Should return the generic No More Ransom entry
        assert decryptor is not None

    def test_scan_directory_not_a_dir(self):
        results = self.detector.scan_directory("/nonexistent/directory")
        assert results == []

    def test_identify_ransomware_family_missing_file(self):
        family = self.detector.identify_ransomware_family("/nonexistent/file.bin")
        assert family is None

    def test_extract_shadow_copies_non_windows(self):
        import platform
        copies = self.detector.extract_shadow_copies("C:")
        if platform.system() != "Windows":
            assert copies == []


# ---------------------------------------------------------------------------
# MLQualityScorer
# ---------------------------------------------------------------------------

class TestMLQualityScorer:
    def setup_method(self):
        from recoveryforge.ai.quality_scorer import MLQualityScorer
        self.scorer = MLQualityScorer()

    def test_instantiation(self):
        assert self.scorer is not None

    def test_score_file_missing_file(self):
        result = self.scorer.score_file("/nonexistent/file.jpg")
        assert result.score == 0.0

    def test_score_valid_jpeg(self):
        path = _write_tmp(_jpeg_bytes(), ".jpg")
        try:
            result = self.scorer.score_file(path)
            assert 0.0 <= result.score <= 1.0
            assert result.file_type in ("jpg", "jpeg")
        finally:
            os.unlink(path)

    def test_score_valid_pdf(self):
        path = _write_tmp(_pdf_bytes(), ".pdf")
        try:
            result = self.scorer.score_file(path)
            assert 0.0 <= result.score <= 1.0
        finally:
            os.unlink(path)

    def test_score_corrupt_file(self):
        path = _write_tmp(b"\x00" * 1024, ".jpg")
        try:
            result = self.scorer.score_file(path)
            # Corrupt file (wrong header) should score lower
            assert result.score < 0.9
        finally:
            os.unlink(path)

    def test_predict_recoverability_good_file(self):
        path = _write_tmp(_jpeg_bytes(), ".jpg")
        try:
            pred = self.scorer.predict_recoverability(path)
            assert isinstance(pred.is_recoverable, bool)
            assert 0.0 <= pred.probability <= 1.0
        finally:
            os.unlink(path)

    def test_analyze_corruption_missing_file(self):
        result = self.scorer.analyze_corruption("/nonexistent/file.jpg")
        assert result.is_corrupt is True
        assert result.corruption_type == "missing"

    def test_analyze_corruption_intact_jpeg(self):
        path = _write_tmp(_jpeg_bytes(), ".jpg")
        try:
            result = self.scorer.analyze_corruption(path)
            assert result.corruption_type in ("none", "header_corrupt")
        finally:
            os.unlink(path)

    def test_suggest_repair_no_corruption(self):
        path = _write_tmp(_jpeg_bytes(), ".jpg")
        try:
            suggestions = self.scorer.suggest_repair(path)
            assert len(suggestions) >= 1
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# AIFragmentAssembler
# ---------------------------------------------------------------------------

class TestAIFragmentAssembler:
    def setup_method(self):
        from recoveryforge.ai.fragment_assembler import AIFragmentAssembler
        self.assembler = AIFragmentAssembler()

    def test_instantiation(self):
        assert self.assembler is not None

    def test_analyze_fragments_empty(self):
        result = self.assembler.analyze_fragments([])
        assert result == []

    def test_analyze_fragments(self):
        frags = [b"Hello world!", b"\xff\xd8\xff" + b"\x00" * 10]
        analyses = self.assembler.analyze_fragments(frags)
        assert len(analyses) == 2
        assert analyses[0].index == 0
        assert analyses[1].has_header is True
        assert analyses[1].detected_type == "jpg"

    def test_find_boundaries_single_type(self):
        import os as _os
        data = _jpeg_bytes() + b"\x00" * 512 + _pdf_bytes()
        boundaries = self.assembler.find_boundaries(data)
        assert 0 in boundaries
        assert len(boundaries) >= 1

    def test_predict_order_empty(self):
        assert self.assembler.predict_order([]) == []

    def test_predict_order_header_first(self):
        frag_body = b"\x00" * 512
        frag_header = _jpeg_bytes()
        order = self.assembler.predict_order([frag_body, frag_header])
        # Header fragment (index 1) should come first
        assert order[0] == 1

    def test_reassemble_preserves_all_data(self):
        frags = [b"Part A ", b"Part B ", b"Part C"]
        assembled = self.assembler.reassemble(frags)
        # All bytes should be present (in some order)
        total_len = sum(len(f) for f in frags)
        assert len(assembled) == total_len

    def test_validate_assembly_valid_jpeg(self):
        result = self.assembler.validate_assembly(_jpeg_bytes(), "jpg")
        assert result.is_valid is True
        assert result.file_type == "jpg"

    def test_validate_assembly_empty(self):
        result = self.assembler.validate_assembly(b"", "jpg")
        assert result.is_valid is False

    def test_validate_assembly_wrong_type(self):
        result = self.assembler.validate_assembly(_jpeg_bytes(), "pdf")
        assert result.is_valid is False


# ---------------------------------------------------------------------------
# DriveFailurePredictor
# ---------------------------------------------------------------------------

class TestDriveFailurePredictor:
    def setup_method(self):
        from recoveryforge.ai.drive_predictor import DriveFailurePredictor
        self.predictor = DriveFailurePredictor()

    def test_instantiation(self):
        assert self.predictor is not None

    def test_predict_failure_healthy_drive(self):
        smart = {5: 0, 187: 0, 197: 0, 198: 0, 194: 35, 9: 5000}
        pred = self.predictor.predict_failure(smart)
        assert pred.failure_probability < 0.3
        assert pred.risk_level in ("low", "medium")

    def test_predict_failure_critical_drive(self):
        smart = {5: 50, 187: 100, 197: 20, 198: 10, 194: 70}
        pred = self.predictor.predict_failure(smart)
        assert pred.failure_probability > 0.5
        assert pred.risk_level in ("high", "critical")
        assert len(pred.contributing_factors) > 0

    def test_predict_failure_string_keys(self):
        smart = {"Reallocated_Sector_Ct": 10, "Current_Pending_Sector": 5}
        pred = self.predictor.predict_failure(smart)
        assert pred.failure_probability > 0

    def test_estimate_lifespan_no_poh(self):
        estimate = self.predictor.estimate_lifespan({})
        assert estimate.estimated_days_remaining is None

    def test_estimate_lifespan_with_poh(self):
        smart = {9: 10000, 5: 0, 197: 0}
        estimate = self.predictor.estimate_lifespan(smart)
        assert estimate.estimated_days_remaining is not None
        assert estimate.estimated_days_remaining > 0

    def test_detect_anomalies_no_change(self):
        snap = {5: 0, 197: 0, 194: 40}
        anomalies = self.predictor.detect_anomalies([snap, snap])
        assert anomalies == []

    def test_detect_anomalies_reallocated_increase(self):
        prev = {5: 0, 197: 0}
        curr = {5: 3, 197: 0}
        anomalies = self.predictor.detect_anomalies([prev, curr])
        assert len(anomalies) > 0
        assert any(a.attribute_id == 5 for a in anomalies)

    def test_detect_anomalies_temp_spike(self):
        prev = {194: 35}
        curr = {194: 55}
        anomalies = self.predictor.detect_anomalies([prev, curr])
        assert any(a.attribute_id == 194 for a in anomalies)

    def test_get_recommendations_healthy(self):
        smart = {5: 0, 197: 0, 194: 35, 9: 5000}
        recs = self.predictor.get_recommendations(smart)
        assert len(recs) >= 1
        assert any("monitor" in r.action.lower() or "routine" in r.urgency for r in recs)

    def test_get_recommendations_critical(self):
        # Drive with many bad sectors, pending sectors, uncorrectable errors,
        # and extreme temperature to push failure probability above 0.70
        smart = {5: 100, 187: 200, 197: 50, 198: 30, 194: 75}
        recs = self.predictor.get_recommendations(smart)
        assert any(r.urgency in ("immediate", "soon") for r in recs)


# ---------------------------------------------------------------------------
# CloudCacheParser
# ---------------------------------------------------------------------------

class TestCloudCacheParser:
    def setup_method(self):
        from recoveryforge.cloud.cache_parser import CloudCacheParser
        self.parser = CloudCacheParser()

    def test_instantiation(self):
        assert self.parser is not None

    def test_detect_cloud_apps(self):
        apps = self.parser.detect_cloud_apps()
        assert isinstance(apps, list)
        # At least some known apps should be in the list
        services = {a.service for a in apps}
        assert "google_drive" in services or "onedrive" in services or "dropbox" in services

    def test_parse_google_drive_missing_path(self):
        result = self.parser.parse_google_drive("/nonexistent/path")
        assert result == []

    def test_parse_onedrive_missing_path(self):
        result = self.parser.parse_onedrive("/nonexistent/path")
        assert result == []

    def test_parse_dropbox_missing_path(self):
        result = self.parser.parse_dropbox("/nonexistent/path")
        assert result == []

    def test_parse_icloud_missing_path(self):
        result = self.parser.parse_icloud("/nonexistent/path")
        assert result == []

    def test_scan_directory_fallback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some test files
            Path(tmpdir, "test1.txt").write_text("hello")
            Path(tmpdir, "subdir").mkdir()
            Path(tmpdir, "subdir", "test2.jpg").write_bytes(_jpeg_bytes())
            result = self.parser._scan_directory(tmpdir, "test_service")
            assert len(result) == 2
            services = {f.service for f in result}
            assert "test_service" in services

    def test_reconstruct_paths(self):
        from recoveryforge.cloud.cache_parser import CloudFile
        files = [
            CloudFile(name="a.txt", local_path="/local/a.txt", cloud_path="/cloud/a.txt"),
            CloudFile(name="b.jpg", local_path="/local/b.jpg", cloud_path=""),
        ]
        mapping = self.parser.reconstruct_paths(files)
        assert mapping["/local/a.txt"] == "/cloud/a.txt"
        assert mapping["/local/b.jpg"] == "/local/b.jpg"


# ---------------------------------------------------------------------------
# FileRepairToolkit
# ---------------------------------------------------------------------------

class TestFileRepairToolkit:
    def setup_method(self):
        from recoveryforge.tools.file_repair import FileRepairToolkit
        self.toolkit = FileRepairToolkit()
        self.tmpdir = tempfile.mkdtemp()

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _out(self, name: str) -> str:
        return str(Path(self.tmpdir) / name)

    def test_instantiation(self):
        assert self.toolkit is not None

    def test_can_repair_known_types(self):
        for ext in ("jpg", "jpeg", "pdf", "docx", "xlsx", "pptx", "zip"):
            assert self.toolkit.can_repair(f"file.{ext}") is True

    def test_can_repair_unknown_type(self):
        assert self.toolkit.can_repair("file.xyz") is False

    def test_repair_jpeg_valid(self):
        src = _write_tmp(_jpeg_bytes(), ".jpg")
        out = self._out("repaired.jpg")
        try:
            result = self.toolkit.repair_jpeg(src, out)
            assert result.success is True
            assert Path(out).exists()
            assert result.bytes_recovered > 0
        finally:
            os.unlink(src)

    def test_repair_jpeg_missing_eoi(self):
        # JPEG without EOI marker
        data = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        src = _write_tmp(data, ".jpg")
        out = self._out("repaired_no_eoi.jpg")
        try:
            result = self.toolkit.repair_jpeg(src, out)
            assert result.success is True
            # EOI should be appended
            with open(out, "rb") as fh:
                repaired = fh.read()
            assert repaired.endswith(b"\xff\xd9")
        finally:
            os.unlink(src)

    def test_repair_jpeg_no_soi(self):
        data = b"\x00" * 100
        src = _write_tmp(data, ".jpg")
        out = self._out("no_soi.jpg")
        try:
            result = self.toolkit.repair_jpeg(src, out)
            assert result.success is False
        finally:
            os.unlink(src)

    def test_repair_jpeg_missing_file(self):
        result = self.toolkit.repair_jpeg("/nonexistent/file.jpg", self._out("x.jpg"))
        assert result.success is False

    def test_repair_pdf_valid(self):
        src = _write_tmp(_pdf_bytes(), ".pdf")
        out = self._out("repaired.pdf")
        try:
            result = self.toolkit.repair_pdf(src, out)
            assert result.success is True
            assert Path(out).exists()
        finally:
            os.unlink(src)

    def test_repair_pdf_missing_eof(self):
        data = b"%PDF-1.4\nsome content\n"  # no %%EOF
        src = _write_tmp(data, ".pdf")
        out = self._out("repaired_no_eof.pdf")
        try:
            result = self.toolkit.repair_pdf(src, out)
            assert result.success is True
            with open(out, "rb") as fh:
                content = fh.read()
            assert b"%%EOF" in content
        finally:
            os.unlink(src)

    def test_repair_pdf_missing_file(self):
        result = self.toolkit.repair_pdf("/nonexistent/file.pdf", self._out("x.pdf"))
        assert result.success is False

    def test_repair_archive_valid_zip(self):
        src = _write_tmp(_zip_bytes(), ".zip")
        out = self._out("repaired.zip")
        try:
            result = self.toolkit.repair_archive(src, out)
            assert result.success is True
            assert Path(out).exists()
        finally:
            os.unlink(src)

    def test_repair_archive_not_a_zip(self):
        src = _write_tmp(b"\x00" * 100, ".zip")
        out = self._out("not_a_zip.zip")
        try:
            result = self.toolkit.repair_archive(src, out)
            assert result.success is False
        finally:
            os.unlink(src)

    def test_repair_archive_missing_file(self):
        result = self.toolkit.repair_archive("/nonexistent/file.zip", self._out("x.zip"))
        assert result.success is False

    def test_repair_office_delegates(self):
        src = _write_tmp(_zip_bytes(), ".docx")
        out = self._out("repaired.docx")
        try:
            result = self.toolkit.repair_office(src, out)
            # Should succeed since DOCX is ZIP-based
            assert isinstance(result.success, bool)
            assert "[Office]" in result.details
        finally:
            os.unlink(src)

    def test_auto_repair_jpeg(self):
        src = _write_tmp(_jpeg_bytes(), ".jpg")
        out = self._out("auto_repaired.jpg")
        try:
            result = self.toolkit.auto_repair(src, out)
            assert result.success is True
        finally:
            os.unlink(src)

    def test_auto_repair_pdf(self):
        src = _write_tmp(_pdf_bytes(), ".pdf")
        out = self._out("auto_repaired.pdf")
        try:
            result = self.toolkit.auto_repair(src, out)
            assert result.success is True
        finally:
            os.unlink(src)

    def test_auto_repair_unknown_type(self):
        src = _write_tmp(b"Unknown data format", ".xyz")
        out = self._out("auto_repaired.xyz")
        try:
            result = self.toolkit.auto_repair(src, out)
            # Falls back to copy
            assert result.success is True
            assert "No specific repair strategy" in result.details
        finally:
            os.unlink(src)

    def test_tools_package_export(self):
        from recoveryforge.tools import FileRepairToolkit
        assert FileRepairToolkit is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
