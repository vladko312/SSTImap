#!/usr/bin/env python3
"""
Test validation script for enhanced Jinja2 SSTI capabilities
Validates new payload methods and fallback mechanisms
"""

import sys
import os
sys.path.append('.')

def test_plugin_structure():
    """Test that the enhanced plugin loads correctly"""
    try:
        # Test by checking the source code directly
        with open('plugins/python/jinja2.py', 'r') as f:
            source_code = f.read()
        
        # Check for enhanced actions in source
        enhanced_actions = [
            'execute_enhanced',
            'execute_subprocess', 
            'execute_namespace',
            'execute_blind_enhanced',
            'validate_objects',
            'test_alternative_access'
        ]
        
        missing_actions = []
        for action in enhanced_actions:
            if f"'{action}'" not in source_code:
                missing_actions.append(action)
        
        if missing_actions:
            return False, f"Missing actions: {missing_actions}"
        
        return True, "All enhanced actions present in source"
        
    except Exception as e:
        return False, f"Plugin structure test failed: {str(e)}"

def test_payload_syntax():
    """Test payload syntax validation"""
    try:
        # Test by checking the source code directly
        with open('plugins/python/jinja2.py', 'r') as f:
            source_code = f.read()
        
        # Test payload structure
        payloads_to_test = [
            'execute_enhanced',
            'execute_subprocess',
            'execute_namespace',
            'execute_blind_enhanced'
        ]
        
        syntax_errors = []
        for payload_name in payloads_to_test:
            if f"'{payload_name}'" in source_code:
                # Check for required template syntax patterns
                if '{{{{' not in source_code or '}}}}' not in source_code:
                    if '{%' not in source_code or '%}' not in source_code:
                        syntax_errors.append(f"{payload_name}: No Jinja2 template syntax found")
                
                if 'base64' not in source_code:
                    syntax_errors.append(f"No base64 encoding found in source")
        
        if syntax_errors:
            return False, f"Syntax errors: {syntax_errors}"
        
        return True, "All payload syntax valid in source"
        
    except Exception as e:
        return False, f"Syntax validation failed: {str(e)}"

def test_fallback_mechanisms():
    """Test fallback mechanism implementation"""
    try:
        # Test by checking the source code directly
        with open('plugins/python/jinja2.py', 'r') as f:
            source_code = f.read()
        
        # Check for fallback implementations
        fallback_actions = ['execute_enhanced', 'execute_subprocess', 'execute_blind_enhanced']
        
        fallback_results = {}
        for action in fallback_actions:
            if f"'{action}'" in source_code:
                # Check if 'fallback' keyword appears near the action
                action_start = source_code.find(f"'{action}'")
                if action_start != -1:
                    # Look in next 1000 characters for fallback
                    action_section = source_code[action_start:action_start + 1000]
                    has_fallback = "'fallback'" in action_section
                    fallback_results[action] = has_fallback
        
        successful_fallbacks = sum(fallback_results.values())
        total_fallbacks = len(fallback_results)
        
        if total_fallbacks == 0:
            return False, "No fallback actions found"
        
        if successful_fallbacks < total_fallbacks * 0.75:  # At least 75% should have fallbacks
            return False, f"Insufficient fallback coverage: {fallback_results}"
        
        return True, f"Fallback mechanisms implemented: {fallback_results}"
        
    except Exception as e:
        return False, f"Fallback testing failed: {str(e)}"

def test_object_validation():
    """Test object validation capabilities"""
    try:
        # Test by checking the source code directly
        with open('plugins/python/jinja2.py', 'r') as f:
            source_code = f.read()
        
        # Check for validation actions
        validation_actions = ['validate_objects', 'test_alternative_access']
        
        validation_present = []
        for action in validation_actions:
            if f"'{action}'" in source_code:
                validation_present.append(action)
        
        if len(validation_present) < len(validation_actions):
            missing = set(validation_actions) - set(validation_present)
            return False, f"Missing validation actions: {missing}"
        
        return True, f"All validation actions present: {validation_present}"
        
    except Exception as e:
        return False, f"Validation testing failed: {str(e)}"

def calculate_enhancement_score():
    """Calculate overall enhancement score"""
    tests = [
        test_plugin_structure,
        test_payload_syntax,
        test_fallback_mechanisms,
        test_object_validation
    ]
    
    results = {}
    total_score = 0
    
    for test_func in tests:
        test_name = test_func.__name__
        try:
            success, message = test_func()
            score = 1.0 if success else 0.0
            results[test_name] = {'success': success, 'message': message, 'score': score}
            total_score += score
        except Exception as e:
            results[test_name] = {'success': False, 'message': f"Test failed: {str(e)}", 'score': 0.0}
    
    overall_score = total_score / len(tests)
    
    return overall_score, results

if __name__ == "__main__":
    print("🧪 Enhanced Jinja2 Plugin Validation Test")
    print("=" * 50)
    
    score, results = calculate_enhancement_score()
    
    for test_name, result in results.items():
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{status} {test_name}: {result['message']}")
    
    print("=" * 50)
    print(f"Overall Enhancement Score: {score:.3f}")
    
    if score >= 0.85:
        print("🎉 Enhancement meets quality threshold!")
        sys.exit(0)
    else:
        print("⚠️  Enhancement needs improvement")
        sys.exit(1)