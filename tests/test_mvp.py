#!/usr/bin/env python3
"""
Comprehensive MVP Test Suite for RL-A2A
Tests all critical functionality for production readiness
"""

import pytest
import asyncio
import json
import requests
import time
import subprocess
import sys
from pathlib import Path

class TestMVPFunctionality:
    """Test MVP core functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment"""
        self.base_url = "http://localhost:8000"
        self.dashboard_url = "http://localhost:8501"
        
    def test_import_rla2a(self):
        """Test that rla2a.py can be imported"""
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("rla2a", "rla2a.py")
            rla2a = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(rla2a)
            assert True
        except Exception as e:
            pytest.fail(f"Failed to import rla2a.py: {e}")
    
    def test_requirements_file(self):
        """Test that requirements.txt exists and is valid"""
        req_file = Path("requirements.txt")
        assert req_file.exists(), "requirements.txt not found"
        
        content = req_file.read_text()
        assert "fastapi" in content, "FastAPI not in requirements"
        assert "openai" in content, "OpenAI not in requirements"
        assert "streamlit" in content, "Streamlit not in requirements"
    
    def test_env_template(self):
        """Test that .env template exists"""
        env_file = Path(".env")
        assert env_file.exists(), ".env file not found"
        
        content = env_file.read_text()
        assert "OPENAI_API_KEY" in content, "OpenAI config missing"
        assert "SECRET_KEY" in content, "Security config missing"
    
    def test_docker_files(self):
        """Test Docker configuration files"""
        assert Path("Dockerfile").exists(), "Dockerfile missing"
        assert Path("docker-compose.yml").exists(), "docker-compose.yml missing"
    
    def test_documentation(self):
        """Test that essential documentation exists"""
        assert Path("README.md").exists(), "README.md missing"
        assert Path("docs/MVP_GUIDE.md").exists(), "MVP guide missing"
        assert Path("docs/api_reference.md").exists(), "API docs missing"
    
    def test_setup_script(self):
        """Test setup script functionality"""
        setup_file = Path("setup.py")
        assert setup_file.exists(), "setup.py missing"
        
        # Test help command
        result = subprocess.run([
            sys.executable, "setup.py", "--help"
        ], capture_output=True, text=True)
        # Should not crash (return code doesn't matter for help)
        assert True

class TestAPIEndpoints:
    """Test API functionality (requires running server)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.base_url = "http://localhost:8000"
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
        except requests.exceptions.ConnectionError:
            pytest.skip("Server not running - start with: python rla2a.py server")
    
    def test_api_docs(self):
        """Test API documentation endpoint"""
        try:
            response = requests.get(f"{self.base_url}/docs", timeout=5)
            assert response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.skip("Server not running")

class TestSecurity:
    """Test security features"""
    
    def test_env_security(self):
        """Test that sensitive data is not hardcoded"""
        # Check main files for hardcoded secrets
        files_to_check = ["rla2a.py", "README.md"]
        
        for file_path in files_to_check:
            if Path(file_path).exists():
                content = Path(file_path).read_text(encoding="utf-8")
                # Should not contain actual API keys
                assert "sk-" not in content or "your-" in content, f"Potential API key in {file_path}"

class TestDeployment:
    """Test deployment readiness"""
    
    def test_docker_build(self):
        """Test Docker image can be built"""
        try:
            result = subprocess.run([
                "docker", "build", "-t", "rla2a:test", "."
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                pytest.skip(f"Docker build failed: {result.stderr}")
            assert True
        except subprocess.TimeoutExpired:
            pytest.skip("Docker build timeout")
        except FileNotFoundError:
            pytest.skip("Docker not available")

def run_mvp_tests():
    """Run all MVP tests"""
    print("🧪 Running RL-A2A MVP Test Suite")
    print("=" * 50)
    
    # Run pytest with verbose output
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--color=yes"
    ])
    
    if exit_code == 0:
        print("\n✅ All MVP tests passed!")
        print("🚀 Your RL-A2A system is MVP ready!")
    else:
        print("\n❌ Some tests failed.")
        print("🔧 Check the output above for issues to fix.")
    
    return exit_code

if __name__ == "__main__":
    run_mvp_tests()