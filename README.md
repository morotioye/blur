# **blur** – open-source ai grammar correction tool  

basil is a simple, terminal-based macos tool for real-time grammar correction using openai and anthropic models. it runs quietly in the background, triggered by a customizable shortcut. just highlight your text, press your hotkey, and blur handles the rest.

---

### 🚀 **features**  
- **clipboard monitoring** – detects and processes copied text automatically  
- **ai model options** – choose between openai's gpt-3.5 and anthropic's claude  
- **customizable shortcut** – set your own hotkey to trigger corrections  
- **background process** – no need to keep the terminal open  
- **auto-start on boot** – basil runs automatically when you log in  

---

### 🛠️ **installation**  
1. **clone the repo**  
   ```bash
   git clone https://github.com/yourusername/basil.git
   cd basil
   ```

2. **set up virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   ```

3. **install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### 💻 **development**
1. **run the application**
   ```bash
   python blur.py
   ```

2. **usage**
   - Press `⌘ + Shift + C` to display the currently selected text
   - Press `Ctrl + C` in the terminal to exit

### 🔄 **current status**
- Phase 1: Basic clipboard monitoring and shortcut detection [In Progress]
