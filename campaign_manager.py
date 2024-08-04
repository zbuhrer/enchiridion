import os
from pathlib import Path
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers import MarkdownLexer
from prompt_toolkit.styles import Style

# Importing necessary components from io.py
from input_controller import InputOutput, AutoCompleter

class CampaignPrompts:
    main_system = """Act as an expert Dungeon Master and campaign manager.
Take requests for changes to the supplied Markdown files containing D&D campaign information.
If the request is ambiguous, ask questions."""

    lazy_prompt = """You are a diligent and creative Dungeon Master!
You NEVER leave placeholders or incomplete sections in campaign files!
You always FULLY DEVELOP the needed campaign elements!"""

    # Add more prompts as needed

class CampaignManager:
    def __init__(self, root_dir):
        self.root_dir = Path(root_dir)
        self.files = {}
        self.load_files()
        self.prompts = CampaignPrompts()
        self.io = InputOutput(pretty=True, input_history_file=".campaign_history")

    def load_files(self):
        # Load all markdown files in the root directory and subdirectories
        for file in self.root_dir.glob('**/*.md'):
            self.files[file.relative_to(self.root_dir)] = file.read_text()

    def save_file(self, file_path, content):
        full_path = self.root_dir / file_path
        full_path.write_text(content)
        self.files[file_path] = content

    def process_edit_request(self, request):
        # TODO: Implement AI processing of edit request
        # This is where we'd integrate with an AI model to generate edits
        pass

    def apply_edits(self, file_path, edits):
        # Apply the edits to the specified file
        if file_path in self.files:
            # TODO: Implement edit application logic
            self.save_file(file_path, self.files[file_path])
        else:
            print(f"File {file_path} not found in the campaign.")

    def display_file_contents(self, file_path):
        if file_path in self.files:
            print(f"Contents of {file_path}:")
            print(self.files[file_path])
        else:
            print(f"File {file_path} not found in the campaign.")

def main():
    campaign_dir = input("Enter the path to your D&D campaign directory: ")
    manager = CampaignManager(campaign_dir)

    # Create a WordCompleter with commands and file names
    commands = ['edit', 'view', 'exit']
    completer = WordCompleter(commands + list(manager.files.keys()))

    # Create a PromptSession
    session = PromptSession(
        lexer=PygmentsLexer(MarkdownLexer),
        completer=completer,
        style=Style.from_dict({
            'completion-menu.completion': 'bg:#008888 #ffffff',
            'completion-menu.completion.current': 'bg:#00aaaa #000000',
        }),
        complete_while_typing=True,
    )

    while True:
        try:
            user_input = session.prompt("D&D Campaign Manager > ")
            
            if user_input.lower() == 'exit':
                break
            elif user_input.lower().startswith('view'):
                _, file_path = user_input.split(maxsplit=1)
                manager.display_file_contents(file_path)
            elif user_input.lower().startswith('edit'):
                _, file_path = user_input.split(maxsplit=1)
                edit_request = session.prompt(f"Enter your edit request for {file_path}: ")
                edits = manager.process_edit_request(edit_request)
                manager.apply_edits(file_path, edits)
            else:
                print("Unknown command. Available commands: view, edit, exit")
        
        except KeyboardInterrupt:
            continue
        except EOFError:
            break

    print("Thank you for using the D&D Campaign Manager!")

if __name__ == "__main__":
    main()
