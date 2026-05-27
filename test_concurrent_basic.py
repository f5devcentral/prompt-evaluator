# MIT License
#
# Copyright (c) 2025 Andy Ryan
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

#!/usr/bin/env python3
"""
Basic test for concurrent evaluator to verify it loads and runs without errors.
This doesn't make actual API calls - just tests the infrastructure.
"""

import sys
from prompt_evaluator_concurrent import (
    LoadDatasetNode,
    ConcurrentScanPromptsNode,
    ConcurrentMetricsNode,
    create_concurrent_evaluation_flow
)

def test_node_creation():
    """Test that nodes can be created with various configurations."""
    print("Testing node creation...")
    
    # Test LoadDatasetNode
    load_node = LoadDatasetNode()
    print("✓ LoadDatasetNode created")
    
    # Test ConcurrentScanPromptsNode with different configurations
    concurrent_node_1 = ConcurrentScanPromptsNode(concurrency=5)
    print("✓ ConcurrentScanPromptsNode created (concurrency=5)")
    
    concurrent_node_2 = ConcurrentScanPromptsNode(concurrency=10, rate_limit=50)
    print("✓ ConcurrentScanPromptsNode created (concurrency=10, rate_limit=50)")
    
    # Test ConcurrentMetricsNode
    metrics_node = ConcurrentMetricsNode()
    print("✓ ConcurrentMetricsNode created")
    
    print("\nAll nodes created successfully!")
    return True

def test_flow_creation():
    """Test that the concurrent evaluation flow can be created."""
    print("\nTesting flow creation...")
    
    # Test with default parameters
    flow_1 = create_concurrent_evaluation_flow()
    print("✓ Flow created with default parameters")
    
    # Test with custom parameters
    flow_2 = create_concurrent_evaluation_flow(concurrency=20, rate_limit=100)
    print("✓ Flow created with custom parameters (concurrency=20, rate_limit=100)")
    
    print("\nAll flows created successfully!")
    return True

def test_concurrent_scan_node_attributes():
    """Test that ConcurrentScanPromptsNode has expected attributes."""
    print("\nTesting ConcurrentScanPromptsNode attributes...")
    
    node = ConcurrentScanPromptsNode(concurrency=15, rate_limit=25)
    
    assert node.concurrency == 15, "Concurrency not set correctly"  # nosec B101
    print("✓ Concurrency set correctly")
    
    assert node.rate_limit == 25, "Rate limit not set correctly"  # nosec B101
    print("✓ Rate limit set correctly")
    
    assert node.session is not None, "Session not initialized"  # nosec B101
    print("✓ Session initialized")
    
    assert node.progress_lock is not None, "Progress lock not initialized"  # nosec B101
    print("✓ Progress lock initialized")
    
    print("\nAll attributes verified!")
    return True

def main():
    """Run all tests."""
    print("=" * 60)
    print("Concurrent Evaluator Basic Tests")
    print("=" * 60)
    
    try:
        # Run tests
        test_node_creation()
        test_flow_creation()
        test_concurrent_scan_node_attributes()
        
        print("\n" + "=" * 60)
        print("✅ All basic tests passed!")
        print("=" * 60)
        return 0
    
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ Test failed: {str(e)}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
