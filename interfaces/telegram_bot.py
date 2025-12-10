"""
Telegram bot interface for nexus_evo
"""
import asyncio
from typing import Optional
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from agents.orchestrator import orchestrator
from macros import recorder, player, library
from tools import registry
from utils import get_logger, parse_command
from app_config import config


logger = get_logger(__name__, config.log_file, config.log_level)


class TelegramInterface:
    """Telegram bot interface for Nexus EVO"""
    
    def __init__(self):
        if not config.telegram.token:
            raise ValueError("Telegram bot token not configured")
        
        self.app = Application.builder().token(config.telegram.token).build()
        self.allowed_users = set(config.telegram.allowed_users)
        self.setup_handlers()
        logger.info("Telegram interface initialized")
    
    def setup_handlers(self):
        """Setup command and message handlers"""
        # Command handlers
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        self.app.add_handler(CommandHandler("tools", self.tools_command))
        self.app.add_handler(CommandHandler("macros", self.macros_command))
        self.app.add_handler(CommandHandler("record", self.record_command))
        self.app.add_handler(CommandHandler("stop_record", self.stop_record_command))
        self.app.add_handler(CommandHandler("play", self.play_command))
        self.app.add_handler(CommandHandler("history", self.history_command))
        
        # Message handler for tasks
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    def check_authorization(self, user_id: int) -> bool:
        """Check if user is authorized"""
        if not self.allowed_users:
            return True  # No restrictions if list empty
        return user_id in self.allowed_users
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        if not self.check_authorization(update.effective_user.id):
            await update.message.reply_text("⛔ Unauthorized access")
            return
        
        welcome = """
🤖 *Nexus EVO - Autonomous AI Agent*

I'm an intelligent orchestrator with ReAct reasoning and macro recording capabilities.

Available commands:
/help - Show detailed help
/status - Agent status
/tools - List available tools
/macros - List saved macros
/record <name> - Start recording macro
/stop_record - Stop recording
/play <macro_name> - Execute macro
/history - Task history

Just send me a message to execute a task!
        """
        await update.message.reply_text(welcome, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        if not self.check_authorization(update.effective_user.id):
            return
        
        help_text = """
📚 *Nexus EVO Help*

*Basic Usage:*
Just send me a task description and I'll use reasoning to accomplish it.

*Examples:*
- "List files in /tmp directory"
- "Check if google.com is reachable"
- "Hash the text 'hello world' using SHA256"
- "Scan ports 80,443 on example.com"

*Commands:*
/status - Show agent status and statistics
/tools - List all available tools
/macros - List saved macros
/record <name> - Start recording actions as a macro
/stop_record - Finish recording and save macro
/play <name> - Execute a saved macro
/history - Show recent task history

*Macro Recording:*
1. /record my_macro - Start recording
2. Execute tasks normally
3. /stop_record - Save the macro
4. /play my_macro - Replay the sequence

*Advanced:*
Send tasks with context by structuring like:
```
Task: scan network
Context:
- host: 192.168.1.1
- ports: [80, 443, 22]
```
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        if not self.check_authorization(update.effective_user.id):
            return
        
        status = orchestrator.get_status()
        task_history = orchestrator.get_task_history()
        
        status_text = f"""
📊 *Agent Status*

*State:* {status['state']['status']}
*Agent ID:* `{status['agent_id']}`
*Tasks Completed:* {len(task_history)}
*Tools Available:* {len(registry.list_tools())}
*Macros Saved:* {library.get_count()}
*Recording:* {"Yes ✅" if recorder.is_recording() else "No"}
        """
        
        await update.message.reply_text(status_text, parse_mode='Markdown')
    
    async def tools_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /tools command"""
        if not self.check_authorization(update.effective_user.id):
            return
        
        tools = registry.get_all_tools_info()
        
        tools_text = "🛠 *Available Tools:*\n\n"
        for tool in tools:
            tools_text += f"• *{tool['name']}*: {tool['description']}\n"
        
        await update.message.reply_text(tools_text, parse_mode='Markdown')
    
    async def macros_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /macros command"""
        if not self.check_authorization(update.effective_user.id):
            return
        
        macros = library.list_all()
        
        if not macros:
            await update.message.reply_text("📝 No saved macros")
            return
        
        macros_text = "📝 *Saved Macros:*\n\n"
        for macro in macros:
            macros_text += f"• *{macro['name']}* ({macro['steps']} steps)\n"
            macros_text += f"  {macro['description']}\n\n"
        
        await update.message.reply_text(macros_text, parse_mode='Markdown')
    
    async def record_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /record command"""
        if not self.check_authorization(update.effective_user.id):
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /record <macro_name>")
            return
        
        name = " ".join(context.args)
        macro_id = recorder.start_recording(name, f"Recorded via Telegram by {update.effective_user.username}")
        
        await update.message.reply_text(
            f"🔴 Recording started: *{name}*\nExecute tasks normally, then use /stop_record to finish",
            parse_mode='Markdown'
        )
    
    async def stop_record_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stop_record command"""
        if not self.check_authorization(update.effective_user.id):
            return
        
        if not recorder.is_recording():
            await update.message.reply_text("⚠️ Not currently recording")
            return
        
        macro = recorder.stop_recording()
        if macro:
            library.save(macro)
            await update.message.reply_text(
                f"✅ Macro saved: *{macro.name}*\n{len(macro.steps)} steps recorded",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("⚠️ No steps recorded")
    
    async def play_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /play command"""
        if not self.check_authorization(update.effective_user.id):
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /play <macro_name>")
            return
        
        name = " ".join(context.args)
        macro = library.load_by_name(name)
        
        if not macro:
            await update.message.reply_text(f"⚠️ Macro not found: {name}")
            return
        
        await update.message.reply_text(f"▶️ Executing macro: *{name}*...", parse_mode='Markdown')
        
        result = player.play(macro)
        
        status = "✅ Success" if result['success'] else "❌ Failed"
        response = f"{status}\n"
        response += f"Steps: {result['successful_steps']}/{result['total_steps']} successful"
        
        await update.message.reply_text(response)
    
    async def history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /history command"""
        if not self.check_authorization(update.effective_user.id):
            return
        
        history = orchestrator.get_task_history()
        
        if not history:
            await update.message.reply_text("📜 No task history")
            return
        
        history_text = "📜 *Recent Tasks:*\n\n"
        for task in history[-5:]:
            history_text += f"• {task['task'][:80]}...\n"
            history_text += f"  Steps: {task['reasoning_steps']}\n\n"
        
        await update.message.reply_text(history_text, parse_mode='Markdown')
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages as tasks"""
        if not self.check_authorization(update.effective_user.id):
            await update.message.reply_text("⛔ Unauthorized access")
            return
        
        task = update.message.text
        
        # Send thinking message
        thinking_msg = await update.message.reply_text("🤔 Thinking...")
        
        try:
            # Execute task
            result = orchestrator.execute(task)
            
            # Update message with result
            await thinking_msg.edit_text(f"✅ {result[:4000]}")  # Telegram limit
            
        except Exception as e:
            logger.error(f"Task execution error: {e}")
            await thinking_msg.edit_text(f"❌ Error: {str(e)[:4000]}")
    
    def run(self):
        """Run the bot"""
        logger.info("Starting Telegram bot...")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)
    
    async def send_message(self, chat_id: int, message: str):
        """Send message to specific chat"""
        await self.app.bot.send_message(chat_id=chat_id, text=message)


# Create bot instance (only if token configured)
telegram_bot = None
if config.telegram.token:
    try:
        telegram_bot = TelegramInterface()
    except Exception as e:
        logger.warning(f"Telegram bot initialization failed: {e}")

class Recorder:
    def __init__(self):
        pass
    
    def record(self, *args, **kwargs):
        return {"status": "not_implemented"}

class Player:
    def __init__(self):
        pass
    
    def play(self, *args, **kwargs):
        return {"status": "not_implemented"}

class Library:
    def __init__(self):
        pass
    
    def list(self):
        return []

recorder = Recorder()
player = Player()
library = Library()

# AUTO-PATCHED: Event loop cleanup for Termux stability
def cleanup_telegram_loop():
    """Cleanup Telegram bot event loop"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.stop()
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        loop.close()
    except Exception as e:
        print(f"Telegram loop cleanup warning: {e}")

import atexit
atexit.register(cleanup_telegram_loop)

