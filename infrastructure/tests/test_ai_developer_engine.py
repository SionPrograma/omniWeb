import pytest
import os
import shutil
from backend.core.ai_developer.code_analyzer import code_analyzer
from backend.core.ai_developer.patch_generator import patch_generator
from backend.core.ai_developer.chip_editor import chip_editor
from backend.core.ai_developer.code_validator import code_validator
from backend.core.ai_developer.module_reloader import module_reloader

def test_chip_analysis():
    # We'll use chip-finanzas if it exists, or create a dummy one
    chip_slug = "finanzas"
    analysis = code_analyzer.analyze_chip(chip_slug)
    
    assert "slug" in analysis
    assert "frontend" in analysis
    assert "backend" in analysis
    assert "routes_detected" in analysis

def test_patch_generation():
    chip_analysis = {
        "frontend": ["frontend/index.html"],
        "backend": ["core/router.py"],
        "slug": "test-chip"
    }
    
    # Test UI patch
    patches = patch_generator.generate_patch("añadir boton de exportar pdf", chip_analysis)
    assert len(patches) > 0
    assert any(p["action"] == "insert_before" for p in patches)
    
    # Test API patch
    patches = patch_generator.generate_patch("crear endpoint de reporte", chip_analysis)
    assert any(p["action"] == "append" for p in patches)

def test_code_validation():
    valid_code = "def hello(): print('world')"
    invalid_code = "def hello(: print('world')"
    unsafe_code = "import os; os.system('rm -rf /')"
    
    assert code_validator.validate_python(valid_code) is True
    assert code_validator.validate_python(invalid_code) is False
    assert code_validator.is_safe(unsafe_code) is False

def test_safe_chip_editor():
    # Create a temporary dummy chip
    chip_slug = "dummy-test"
    chip_path = f"chips/chip-{chip_slug}"
    os.makedirs(f"{chip_path}/frontend", exist_ok=True)
    os.makedirs(f"{chip_path}/core", exist_ok=True)
    
    index_path = f"{chip_path}/frontend/index.html"
    with open(index_path, "w") as f:
        f.write("<html><body><h1>Test</h1></body></html>")
        
    patches = [
        {
            "file": "frontend/index.html",
            "action": "insert_before",
            "target": "</body>",
            "content": "<p>AI Patch</p>",
            "description": "Test patch"
        }
    ]
    
    result = chip_editor.apply_patches(chip_slug, patches)
    assert result["status"] == "success"
    
    with open(index_path, "r") as f:
        content = f.read()
        assert "<p>AI Patch</p>" in content
        
    # Clean up
    shutil.rmtree(chip_path)

def test_module_reloader():
    assert module_reloader.reload_chip("finanzas") is True
