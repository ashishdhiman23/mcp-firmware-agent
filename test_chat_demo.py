#!/usr/bin/env python3
"""
Demo script for testing the MCP Firmware Analysis Chat System.

This script demonstrates how to:
1. Create a chat session
2. Send messages to the AI
3. Upload log files
4. Get conversation history
5. Export sessions

Usage:
    python test_chat_demo.py
"""

import asyncio
import aiohttp
import json
import time
from pathlib import Path


class ChatDemo:
    """Demo client for the MCP Firmware Chat API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the demo client.
        
        Args:
            base_url: Base URL of the MCP server
        """
        self.base_url = base_url
        self.session_id = None
    
    async def create_session(self):
        """Create a new chat session."""
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/chat/sessions") as response:
                if response.status == 200:
                    data = await response.json()
                    self.session_id = data["session_id"]
                    print(f"✅ Created chat session: {self.session_id[:8]}...")
                    return data
                else:
                    error = await response.text()
                    print(f"❌ Failed to create session: {error}")
                    return None
    
    async def send_message(self, message: str, context_type: str = "general"):
        """Send a message to the chat session.
        
        Args:
            message: Message to send
            context_type: Type of context for the response
        """
        if not self.session_id:
            print("❌ No active session. Create a session first.")
            return None
        
        payload = {
            "message": message,
            "context_type": context_type
        }
        
        print(f"👤 You: {message}")
        print("🤖 AI is thinking...")
        
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/sessions/{self.session_id}/messages",
                json=payload
            ) as response:
                
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    print(f"🤖 Assistant ({response_time:.1f}s): {data['response']}")
                    
                    if data.get('suggestions'):
                        print("\n💡 Suggestions:")
                        for i, suggestion in enumerate(data['suggestions'], 1):
                            print(f"   {i}. {suggestion}")
                    
                    print()  # Empty line for readability
                    return data
                else:
                    error = await response.text()
                    print(f"❌ Failed to send message: {error}")
                    return None
    
    async def upload_file(self, file_path: str):
        """Upload a log file to the chat session.
        
        Args:
            file_path: Path to the log file
        """
        if not self.session_id:
            print("❌ No active session. Create a session first.")
            return None
        
        file_path = Path(file_path)
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            return None
        
        print(f"📁 Uploading file: {file_path.name}")
        print("🔄 Analyzing...")
        
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            with open(file_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename=file_path.name)
                data.add_field('analyze_immediately', 'true')
                
                async with session.post(
                    f"{self.base_url}/chat/sessions/{self.session_id}/upload",
                    data=data
                ) as response:
                    
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ Upload complete ({response_time:.1f}s)")
                        
                        if result.get('auto_analysis_message'):
                            print(f"🤖 Auto-Analysis: {result['auto_analysis_message']}")
                        
                        if result.get('analysis'):
                            analysis = result['analysis']
                            print(f"📊 Analysis ID: {analysis['analysis_id']}")
                            print(f"📈 Confidence: {analysis['confidence_score']*100:.1f}%")
                        
                        print()  # Empty line for readability
                        return result
                    else:
                        error = await response.text()
                        print(f"❌ Failed to upload file: {error}")
                        return None
    
    async def get_capabilities(self):
        """Get chat capabilities."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/chat/capabilities") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None
    
    async def get_conversation_history(self):
        """Get conversation history for the current session."""
        if not self.session_id:
            print("❌ No active session.")
            return None
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/chat/sessions/{self.session_id}/history"
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None
    
    async def export_session(self, format: str = "json"):
        """Export the current session.
        
        Args:
            format: Export format ("json" or "markdown")
        """
        if not self.session_id:
            print("❌ No active session.")
            return None
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/chat/sessions/{self.session_id}/export",
                params={"format": format}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    filename = f"chat_export_{self.session_id[:8]}.{format}"
                    
                    with open(filename, 'w') as f:
                        if format == "json":
                            f.write(result['content'])
                        else:
                            f.write(result['content'])
                    
                    print(f"💾 Session exported to: {filename}")
                    return result
                else:
                    return None


async def demo_conversation():
    """Run a demo conversation."""
    print("🚀 MCP Firmware Analysis Chat Demo")
    print("=" * 50)
    
    # Initialize demo client
    demo = ChatDemo()
    
    # Create session
    await demo.create_session()
    if not demo.session_id:
        return
    
    # Show capabilities
    capabilities = await demo.get_capabilities()
    if capabilities:
        print("\n🧠 AI Capabilities:")
        for query_type in capabilities.get('supported_queries', []):
            print(f"   • {query_type}")
        print()
    
    # Demo conversation
    print("🎯 Starting demo conversation...")
    print()
    
    # Ask general questions
    await demo.send_message(
        "How do I debug a hard fault in an ARM Cortex-M microcontroller?",
        "debug_assistant"
    )
    
    await demo.send_message(
        "What are the most common causes of stack overflows in embedded systems?",
        "troubleshooting"
    )
    
    await demo.send_message(
        "Can you explain the difference between a hard fault and a memory management fault?",
        "general"
    )
    
    # Try to upload a sample log file if it exists
    sample_logs = [
        "test_logs/sample_crash.log",
        "mcp_firmware_agent/test_logs/sample_crash.log",
        "sample_logs/sample_crash.log"
    ]
    
    for log_path in sample_logs:
        if Path(log_path).exists():
            await demo.upload_file(log_path)
            
            # Ask follow-up questions about the uploaded log
            await demo.send_message(
                "Can you explain this crash in more detail?",
                "log_analysis"
            )
            
            await demo.send_message(
                "What should I check next to prevent this issue?",
                "troubleshooting"
            )
            break
    else:
        print("📝 No sample log files found for upload demo")
    
    # Show conversation history
    print("📜 Getting conversation history...")
    history = await demo.get_conversation_history()
    if history:
        print(f"💬 Total messages in conversation: {len(history['conversation_history'])}")
    
    # Export session
    print("💾 Exporting session...")
    await demo.export_session("markdown")
    
    print("\n✅ Demo completed successfully!")
    print(f"🔗 Web interface: http://localhost:8000/chat")
    print(f"📚 API docs: http://localhost:8000/docs")


async def interactive_chat():
    """Run an interactive chat session."""
    print("🤖 Interactive Firmware Chat")
    print("=" * 40)
    print("Type 'quit' to exit, 'upload <file>' to upload a log file")
    print()
    
    demo = ChatDemo()
    await demo.create_session()
    
    if not demo.session_id:
        return
    
    while True:
        try:
            user_input = input("👤 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("👋 Goodbye!")
                break
            
            if user_input.startswith('upload '):
                file_path = user_input[7:].strip()
                await demo.upload_file(file_path)
            elif user_input:
                await demo.send_message(user_input)
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        asyncio.run(interactive_chat())
    else:
        asyncio.run(demo_conversation())
        
        print("\n🎮 To run interactive mode:")
        print("python test_chat_demo.py interactive") 