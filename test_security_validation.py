#!/usr/bin/env python3
"""
Security validation test for enhanced Jinja2 SSTI capabilities
Tests penetration testing effectiveness and payload security
"""

import base64
import re

def test_payload_encoding():
    """Test base64 encoding functionality"""
    test_command = "whoami"
    encoded = base64.urlsafe_b64encode(test_command.encode()).decode()
    decoded = base64.urlsafe_b64decode(encoded).decode()
    
    assert decoded == test_command, "Base64 encoding/decoding failed"
    return True, f"Base64 encoding validated: {test_command} -> {encoded[:20]}..."

def test_payload_structure():
    """Test Jinja2 template payload structure"""
    with open('plugins/python/jinja2.py', 'r') as f:
        source = f.read()
    
    # Test for proper Jinja2 template syntax
    template_patterns = [
        r'\{\{\{\{.*\}\}\}\}',  # {{{{ ... }}}}
        r'\{\%.*\%\}',         # {% ... %}
    ]
    
    results = {}
    for pattern in template_patterns:
        matches = re.findall(pattern, source)
        results[pattern] = len(matches)
    
    total_templates = sum(results.values())
    
    if total_templates < 5:
        return False, f"Insufficient template patterns found: {results}"
    
    return True, f"Template validation passed: {total_templates} patterns found"

def test_alternative_objects():
    """Test alternative object access methods"""
    with open('plugins/python/jinja2.py', 'r') as f:
        source = f.read()
    
    # Check for alternative object types
    alternative_objects = ['joiner', 'namespace', 'cycler']
    
    found_objects = []
    for obj in alternative_objects:
        if f"{obj}.__init__.__globals__" in source:
            found_objects.append(obj)
    
    if len(found_objects) < 2:
        return False, f"Insufficient alternative objects: {found_objects}"
    
    return True, f"Alternative objects validated: {found_objects}"

def test_subprocess_capabilities():
    """Test subprocess execution capabilities"""
    with open('plugins/python/jinja2.py', 'r') as f:
        source = f.read()
    
    # Check for subprocess-related patterns
    subprocess_indicators = [
        '__subclasses__',
        'communicate',
        'Popen',
        'shell=True'
    ]
    
    found_indicators = []
    for indicator in subprocess_indicators:
        if indicator in source:
            found_indicators.append(indicator)
    
    if len(found_indicators) < 3:
        return False, f"Insufficient subprocess capabilities: {found_indicators}"
    
    return True, f"Subprocess capabilities validated: {found_indicators}"

def test_blind_detection():
    """Test blind injection detection capabilities"""
    with open('plugins/python/jinja2.py', 'r') as f:
        source = f.read()
    
    # Check for blind detection patterns
    blind_patterns = [
        'sleep',
        'delay',
        '_blind',
        'time'
    ]
    
    found_patterns = []
    for pattern in blind_patterns:
        if pattern in source:
            found_patterns.append(pattern)
    
    if len(found_patterns) < 3:
        return False, f"Insufficient blind detection: {found_patterns}"
    
    return True, f"Blind detection validated: {found_patterns}"

def test_security_effectiveness():
    """Test overall security penetration testing effectiveness"""
    with open('plugins/python/jinja2.py', 'r') as f:
        source = f.read()
    
    # Count total execution methods
    execution_methods = [
        'execute_enhanced',
        'execute_subprocess', 
        'execute_namespace',
        'execute_blind_enhanced',
        'execute_timing_test'
    ]
    
    available_methods = []
    for method in execution_methods:
        if f"'{method}'" in source:
            available_methods.append(method)
    
    effectiveness_score = len(available_methods) / len(execution_methods)
    
    if effectiveness_score < 0.8:
        return False, f"Low effectiveness score: {effectiveness_score:.2f}"
    
    return True, f"Security effectiveness validated: {effectiveness_score:.2f} ({len(available_methods)}/{len(execution_methods)} methods)"

def run_security_validation():
    """Run comprehensive security validation"""
    tests = [
        test_payload_encoding,
        test_payload_structure,
        test_alternative_objects,
        test_subprocess_capabilities,
        test_blind_detection,
        test_security_effectiveness
    ]
    
    results = {}
    total_score = 0
    
    print("🔒 Security Validation Test Suite")
    print("=" * 50)
    
    for test_func in tests:
        test_name = test_func.__name__
        try:
            success, message = test_func()
            score = 1.0 if success else 0.0
            status = "✅ PASS" if success else "❌ FAIL"
            
            results[test_name] = {'success': success, 'message': message, 'score': score}
            total_score += score
            
            print(f"{status} {test_name}: {message}")
            
        except Exception as e:
            results[test_name] = {'success': False, 'message': f"Test error: {str(e)}", 'score': 0.0}
            print(f"❌ FAIL {test_name}: Test error: {str(e)}")
    
    overall_score = total_score / len(tests)
    
    print("=" * 50)
    print(f"Security Validation Score: {overall_score:.3f}")
    
    if overall_score >= 0.85:
        print("🎉 Security validation PASSED!")
        return True, overall_score
    else:
        print("⚠️  Security validation needs improvement")
        return False, overall_score

if __name__ == "__main__":
    success, score = run_security_validation()
    exit(0 if success else 1)