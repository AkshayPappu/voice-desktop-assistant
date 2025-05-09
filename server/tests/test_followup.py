import os
import sys

# Add the parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from llm.llm_handler import process_with_llm
from tools.followup_handler import handle_followup
import json

def simulate_conversation():
    """
    Simulate a conversation flow to test follow-up handling
    """
    # Simulate user ID
    user_id = "test_user_123"
    
    # Test cases with different scenarios
    test_cases = [
        # {
        #     "name": "Calendar scheduling without time",
        #     "input": "Schedule a team meeting next Friday",
        #     "expected_followup": True,
        #     "simulated_response": "2 PM"
        # },
        {
            "name": "File search without type",
            "input": "Find my files",
            "expected_followup": True,
            "simulated_response": "document"
        },
        # {
        #     "name": "Complete command (no follow-up needed)",
        #     "input": "Schedule a team meeting next Friday at 2 PM",
        #     "expected_followup": False,
        #     "simulated_response": None
        # }
    ]
    
    print("Starting follow-up test simulation...")
    print("-----------------------------------")
    
    for test in test_cases:
        print(f"\nTest: {test['name']}")
        print(f"Input: {test['input']}")
        
        # Process the initial command
        command_data = process_with_llm(test['input'], user_id)
        
        if command_data:
            print("\nCommand processed successfully:")
            print(f"Command type: {command_data['command_type']}")
            print(f"Parameters: {json.dumps(command_data['parameters'], indent=2)}")
            
            # Check if follow-up is required
            requires_followup = command_data.get("requires_followup", False)
            print(f"\nFollow-up required: {requires_followup}")
            
            if requires_followup:
                print("\nFollow-up context:")
                print(json.dumps(command_data.get("followup_context", {}), indent=2))
                
                # Handle the follow-up with simulated response
                success = handle_followup(
                    command_data, 
                    user_id, 
                    simulated_response=test['simulated_response']
                )
                print(f"Follow-up handled successfully: {success}")
        else:
            print("Failed to process command")
        
        print("-----------------------------------")

if __name__ == "__main__":
    simulate_conversation() 