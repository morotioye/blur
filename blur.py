#!/usr/bin/env python3

import rumps
import pyperclip
from rich.console import Console
from rich.panel import Panel
import sys
import os
from openai import OpenAI
from dotenv import load_dotenv
import threading
import time
from AppKit import (
    NSEvent, NSKeyDownMask, NSCommandKeyMask, NSAlternateKeyMask,
    NSWorkspace, NSPasteboard, NSStringPboardType
)
from ApplicationServices import (
    AXUIElementCreateSystemWide,
    AXUIElementCopyAttributeValue,
    kAXValueAttribute,
    kAXSelectedTextAttribute,
    kAXFocusedUIElementAttribute,
    AXUIElementSetAttributeValue
)

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Initialize rich console for terminal output
console = Console()

class BlurApp(rumps.App):
    def __init__(self):
        super(BlurApp, self).__init__("✍️", quit_button=None)
        
        # Setup menu items
        self.menu = [
            rumps.MenuItem("Clean Up Selection (⌘+⌥+E)", callback=self.cleanup_selection),
            rumps.MenuItem("Clean Up Clipboard (⌘+⌥+C)", callback=self.cleanup_clipboard),
            None,  # Separator
            rumps.MenuItem("Display Clipboard (⌘+⇧+C)", callback=self.display_clipboard),
            None,  # Separator
            rumps.MenuItem("Quit", callback=self.quit_app)
        ]
        
        # Status indicator
        self.processing = False
        
        # Setup keyboard monitoring
        mask = NSKeyDownMask
        NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(mask, self.handle_event)

    def handle_event(self, event):
        try:
            # Get the key and modifiers
            characters = event.characters()
            modifiers = event.modifierFlags()
            
            # Check for Command + Option + E
            if (modifiers & NSCommandKeyMask and 
                modifiers & NSAlternateKeyMask and 
                characters.lower() == 'e'):
                self.cleanup_selection(None)
                
            # Check for Command + Option + C
            elif (modifiers & NSCommandKeyMask and 
                  modifiers & NSAlternateKeyMask and 
                  characters.lower() == 'c'):
                self.cleanup_clipboard(None)
        except:
            pass

    def get_selected_text(self):
        """Get the currently selected text using Accessibility API"""
        try:
            # Get system-wide accessibility element
            system = AXUIElementCreateSystemWide()
            console.print("[yellow]Debug: Created system-wide element[/yellow]")
            
            # Get focused element
            focused, error = AXUIElementCopyAttributeValue(system, kAXFocusedUIElementAttribute, None)
            console.print(f"[yellow]Debug: Focused element: {focused}, Error: {error}[/yellow]")
            if focused is None:  # Only check if focused is None, not error
                console.print("[red]Debug: No focused element found[/red]")
                return None
                
            # Get selected text
            selected_text, error = AXUIElementCopyAttributeValue(focused, kAXSelectedTextAttribute, None)
            console.print(f"[yellow]Debug: Selected text result: {selected_text}, Error: {error}[/yellow]")
            
            # Handle various types that might be returned
            if selected_text is None:
                console.print("[red]Debug: No selected text found[/red]")
                return None
            
            # Convert to string if it's not already
            try:
                text = str(selected_text).strip()
                if text and not text.isdigit():  # Avoid returning just numbers which might be internal values
                    return text
                console.print("[red]Debug: Invalid text content[/red]")
                return None
            except:
                console.print("[red]Debug: Could not convert selection to text[/red]")
                return None
                
        except Exception as e:
            console.print(f"[red]Debug: Error in get_selected_text: {str(e)}[/red]")
            return None

    def replace_text(self, new_text):
        """Replace the currently selected text using Accessibility API"""
        try:
            # Get system-wide accessibility element
            system = AXUIElementCreateSystemWide()
            console.print("[yellow]Debug: Created system-wide element for replacement[/yellow]")
            
            # Get focused element
            focused, error = AXUIElementCopyAttributeValue(system, kAXFocusedUIElementAttribute, None)
            console.print(f"[yellow]Debug: Focused element for replacement: {focused}, Error: {error}[/yellow]")
            if focused is None:  # Only check if focused is None, not error
                console.print("[red]Debug: No focused element found for replacement[/red]")
                return False
                
            # Set the value of the selected text
            error = AXUIElementSetAttributeValue(focused, kAXSelectedTextAttribute, str(new_text))
            console.print(f"[yellow]Debug: Replace text result - Error: {error}[/yellow]")
            return error == 0
        except Exception as e:
            console.print(f"[red]Debug: Error in replace_text: {str(e)}[/red]")
            return False

    def process_text_async(self, text, is_selection=True):
        """Process text with OpenAI in a separate thread"""
        try:
            # Update menu item to show processing
            menu_item = "Clean Up Selection (⌘+⌥+E)" if is_selection else "Clean Up Clipboard (⌘+⌥+C)"
            self.menu[menu_item].title = "Processing..."
            
            # Call OpenAI API
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that improves text clarity and fixes grammar, spelling, and punctuation. Keep the same meaning but make it clearer and more professional. Maintain the original tone and intent."},
                    {"role": "user", "content": text}
                ]
            )
            
            # Get the improved text
            improved_text = response.choices[0].message.content
            
            if is_selection:
                # Replace the text directly using accessibility API
                success = self.replace_text(improved_text)
            else:
                # Just copy to clipboard for clipboard mode
                pyperclip.copy(improved_text)
                success = True

            if success:
                # Show notification
                rumps.notification(
                    title="Blur",
                    subtitle="Text cleaned and " + ("replaced" if is_selection else "copied to clipboard"),
                    message=improved_text[:100] + ("..." if len(improved_text) > 100 else "")
                )
                
                # Print to terminal if available
                if sys.stdout.isatty():
                    console.print("\n[bold green]Original text:[/bold green]")
                    console.print(Panel(text, title="✍️ Original", border_style="yellow"))
                    console.print("\n[bold green]Improved text:[/bold green]")
                    console.print(Panel(improved_text, title="✨ Cleaned", border_style="blue"))
            else:
                rumps.notification(
                    title="Blur",
                    subtitle="Error",
                    message="Could not process text"
                )
            
        except Exception as e:
            rumps.notification(
                title="Blur",
                subtitle="Error",
                message=str(e)
            )
            if sys.stdout.isatty():
                console.print(f"[red]Error: {str(e)}[/red]")
        
        finally:
            # Reset menu item
            self.menu[menu_item].title = menu_item
            self.processing = False

    @rumps.clicked("Clean Up Selection (⌘+⌥+E)")
    def cleanup_selection(self, _):
        """Clean up the selected text using AI"""
        console.print("\n[bold blue]Starting cleanup_selection[/bold blue]")
        if self.processing:
            console.print("[yellow]Debug: Still processing previous request[/yellow]")
            rumps.notification(
                title="Blur",
                subtitle="Please wait",
                message="Still processing previous text..."
            )
            return
        
        # Get the selected text using accessibility API
        console.print("[yellow]Debug: Attempting to get selected text[/yellow]")
        selected_text = self.get_selected_text()
        
        if not selected_text:
            console.print("[red]Debug: No text was selected[/red]")
            rumps.notification(
                title="Blur",
                subtitle="Error",
                message="No text selected!"
            )
            return
            
        console.print(f"[green]Debug: Got selected text: {selected_text[:100]}{'...' if len(selected_text) > 100 else ''}[/green]")
        self.processing = True
        # Process in background
        threading.Thread(target=self.process_text_async, args=(selected_text, True), daemon=True).start()

    @rumps.clicked("Clean Up Clipboard (⌘+⌥+C)")
    def cleanup_clipboard(self, _):
        """Clean up the clipboard content using AI"""
        if self.processing:
            rumps.notification(
                title="Blur",
                subtitle="Please wait",
                message="Still processing previous text..."
            )
            return
        
        text = pyperclip.paste()
        if not text:
            rumps.notification(
                title="Blur",
                subtitle="Error",
                message="No text in clipboard!"
            )
            return
            
        self.processing = True
        # Process in background
        threading.Thread(target=self.process_text_async, args=(text, False), daemon=True).start()

    @rumps.clicked("Display Clipboard (⌘+⇧+C)")
    def display_clipboard(self, _):
        """Display the current clipboard content"""
        text = pyperclip.paste()
        if text:
            # Print to terminal if running from terminal
            if sys.stdout.isatty():
                console.print(Panel(text, title="📋 Copied Text", border_style="blue"))
            
            # Also show as notification
            rumps.notification(
                title="Blur",
                subtitle="Current clipboard content:",
                message=text[:100] + ("..." if len(text) > 100 else "")
            )
        else:
            if sys.stdout.isatty():
                console.print("[yellow]No text found in clipboard![/yellow]")
            rumps.notification(
                title="Blur",
                subtitle="Error",
                message="No text found in clipboard!"
            )

    def quit_app(self, _):
        """Quit the application"""
        rumps.quit_application()

def main():
    # Print welcome message if running from terminal
    if sys.stdout.isatty():
        console.print("[bold green]Blur - Type at the Speed of Thought[/bold green]")
        console.print("The application is now running in your menu bar")
        console.print("Click the ✍️ icon to access the menu")
        console.print("\n[bold]Instructions:[/bold]")
        console.print("1. Write your text anywhere")
        console.print("2. Either:")
        console.print("   a) Select text and press ⌘+⌥+E to clean up the selection")
        console.print("   b) Copy text and press ⌘+⌥+C to clean up clipboard content")
        console.print("3. The text will be improved with AI\n")
    
    # Start the app
    BlurApp().run()

if __name__ == "__main__":
    main() 