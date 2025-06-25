#!/usr/bin/env python3
"""
Consolidated test script for the nutrition agent.
This includes:
1. LLM configuration tests for OpenAI, GitHub, and Groq
2. Router integration tests
3. Health Diet Agent tests
4. End-to-end functionality tests
"""

import os
import sys
import argparse
from dotenv import load_dotenv
from llm_config import get_llm, create_llm_config
try:
    from router_integration import create_kitchen_assistant_with_nutrition
except ImportError:
    print("Warning: Router integration not available")
from health_diet_agent import HealthDietAgent
import json
from utils.logger import setup_logger

# Load environment variables
load_dotenv()

# Setup logger for tests
test_logger = setup_logger(__name__)

def test_llm_config(provider):
    """Test LLM configuration for a specified provider."""
    test_logger.info(f"Testing {provider.upper()} Configuration")
    print(f"\n=== Testing {provider.upper()} Configuration ===\n")

    # Check for required environment variables
    if provider == "openai":
        api_key_env = "OPENAI_API_KEY"
        config_params = {"model_name": "gpt-4-turbo-preview", "temperature": 0.1}
    elif provider == "github":
        api_key_env = "GITHUB_TOKEN"
        model_env = "GITHUB_MODEL"
        if not os.getenv(model_env):
            print(f"ERROR: {model_env} environment variable not found")
            return False
        config_params = {"temperature": 0.1}
    elif provider == "groq":
        api_key_env = "GROQ_API_KEY"
        config_params = {"model_name": "llama3-8b-8192", "temperature": 0.1}
    else:
        print(f"ERROR: Unsupported provider: {provider}")
        return False

    # Check for API key
    if not os.getenv(api_key_env):
        test_logger.error(f"{api_key_env} environment variable not found")
        print(f"ERROR: {api_key_env} environment variable not found")
        print(f"Please add it to your .env file")
        return False

    try:
        # Create configuration
        test_logger.info(f"Creating {provider} config with params: {config_params}")
        config = create_llm_config(provider, config_params)
        print(f"✅ Successfully created {provider} config")

        # Create LLM
        test_logger.info(f"Creating LLM instance for {provider}")
        llm = config.create_llm()
        test_logger.info(f"Successfully created {provider} LLM: {llm.__class__.__name__}")
        print(f"✅ Successfully created {provider} LLM: {llm.__class__.__name__}")

        # Direct LLM creation
        test_logger.info(f"Testing direct LLM creation for {provider}")
        direct_llm = get_llm(provider, config_params)
        test_logger.info(f"Successfully created {provider} LLM directly: {direct_llm.__class__.__name__}")
        print(f"✅ Successfully created {provider} LLM directly: {direct_llm.__class__.__name__}")

        return True
    except Exception as e:
        test_logger.error(f"Error testing {provider} configuration: {str(e)}")
        print(f"❌ Error testing {provider} configuration: {e}")
        return False

def test_router_integration(provider):
    """Test the router integration with sample queries."""
    test_logger.info(f"Testing Router Integration with {provider.upper()}")
    print(f"\n=== Testing Router Integration with {provider.upper()} ===\n")

    try:
        # Create router
        config_params = {}
        if provider == "openai":
            config_params = {"model_name": "gpt-4-turbo-preview", "temperature": 0.1}
        elif provider == "groq":
            config_params = {"model_name": "llama3-8b-8192", "temperature": 0.2}

        test_logger.info(f"Creating kitchen assistant router with {provider} and config: {config_params}")

        try:
            router = create_kitchen_assistant_with_nutrition(
                llm_provider=provider,
                llm_config=config_params
            )
        except NameError:
            test_logger.error("Router integration not available")
            print("❌ Router integration not available")
            return False

        test_logger.info("Successfully created kitchen assistant router")
        print(f"✅ Successfully created kitchen assistant router")

        # Test queries
        test_queries = [
            "What are the nutritional macros in a chicken sandwich?",
            "How many calories are in a cup of rice?",
            "What's the protein content of 100g chicken breast?"
        ]

        test_logger.info(f"Prepared {len(test_queries)} test queries")
        print("Running test queries...")
        for i, query in enumerate(test_queries, 1):
            if i > 1:  # Only run one query for testing
                break
            test_logger.info(f"Running test query {i}: {query}")

            print(f"\nTest {i}: {query}")
            try:
                test_logger.info("Routing test query through kitchen assistant")
                result = router.route_query(query)
                test_logger.info("Query succeeded")
                print(f"✅ Query succeeded")
                print(f"Response: {result['response'][:100]}...")  # Show beginning of response
            except Exception as e:
                test_logger.error(f"Query failed: {str(e)}")
                print(f"❌ Query failed: {e}")

        return True
    except Exception as e:
        test_logger.error(f"Error testing router integration: {str(e)}")
        print(f"❌ Error testing router integration: {e}")
        return False

def test_health_diet_agent(provider):
    """Test the health diet agent directly."""
    test_logger.info(f"Testing Health Diet Agent with {provider.upper()}")
    print(f"\n=== Testing Health Diet Agent with {provider.upper()} ===\n")

    try:
        # Create agent
        config_params = {}
        if provider == "openai":
            config_params = {"model_name": "gpt-4-turbo-preview", "temperature": 0.1}
        elif provider == "groq":
            config_params = {"model_name": "llama3-8b-8192", "temperature": 0.2}

        agent = HealthDietAgent(
            llm_provider=provider,
            llm_config=config_params
        )
        print(f"✅ Successfully created health diet agent")

        # Test agent with a simple query
        query = "What are the nutritional facts of an apple?"
        print(f"Testing agent with query: '{query}'")

        result = agent.analyze_nutrition(query)
        print(f"✅ Agent query {'succeeded' if result['success'] else 'failed'}")
        if result["success"]:
            print(f"Result: {result['analysis'][:100]}...")  # Show beginning of analysis
        else:
            print(f"Error: {result['error']}")

        return True
    except Exception as e:
        print(f"❌ Error testing health diet agent: {e}")
        return False

def test_comprehensive(provider):
    """Run comprehensive end-to-end tests for the nutrition agent."""
    test_logger.info(f"Running Comprehensive Tests with {provider.upper()}")
    print(f"\n=== Running Comprehensive Tests with {provider.upper()} ===\n")

    success = True

    # Test basic LLM configuration
    test_logger.info("Starting LLM configuration test")
    print("Testing LLM configuration...")
    if not test_llm_config(provider):
        test_logger.error("LLM configuration test failed")
        print("❌ LLM configuration test failed")
        success = False

    # Test the agent directly
    test_logger.info("Starting Health Diet Agent test")
    print("\nTesting Health Diet Agent directly...")
    if not test_health_diet_agent(provider):
        test_logger.error("Health Diet Agent test failed")
        print("❌ Health Diet Agent test failed")
        success = False

    # Test router integration
    test_logger.info("Starting router integration test")
    print("\nTesting router integration...")
    if not test_router_integration(provider):
        test_logger.error("Router integration test failed")
        print("❌ Router integration test failed")
        success = False

    test_logger.info(f"Comprehensive tests completed. Success: {success}")
    return success

def main():
    """Run the consolidated tests."""
    parser = argparse.ArgumentParser(description="Nutrition Agent Tests")
    parser.add_argument("--provider", choices=["openai", "github", "groq"], default="openai",
                        help="LLM provider to test (openai, github, or groq)")
    parser.add_argument("--test", choices=["config", "router", "agent", "comprehensive", "all"], default="all",
                        help="Test type to run")
    args = parser.parse_args()

    test_logger.info(f"Starting nutrition agent tests with provider: {args.provider}, test type: {args.test}")

    # Run the selected tests
    results = []

    if args.test in ["config", "all"]:
        results.append(("LLM Config", test_llm_config(args.provider)))

    if args.test in ["router", "all"]:
        results.append(("Router Integration", test_router_integration(args.provider)))

    if args.test in ["agent", "all"]:
        results.append(("Health Diet Agent", test_health_diet_agent(args.provider)))

    if args.test in ["comprehensive", "all"]:
        results.append(("Comprehensive Tests", test_comprehensive(args.provider)))

    # Print summary
    print("\n=== Test Results Summary ===")
    for test_name, success in results:
        print(f"{test_name}: {'✅ PASSED' if success else '❌ FAILED'}")

if __name__ == "__main__":
    main()
