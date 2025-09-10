"""
BFScript Streamlit WebApp

A clean two-panel interface for writing, compiling, and executing BFScript code.
"""

import streamlit as st
import tempfile
import os
import io
import sys
import pyperclip

# Import syntax-highlighted code editor
from code_editor import code_editor

# Import the compiler and interpreter
from lib.compiler.compiler import BrainfuckScriptCompiler
from lib.interpreter import BFInterpreter


class BFScriptWebApp:
    def __init__(self):
        self.setup_page_config()
        self.setup_session_state()
    
    def setup_page_config(self):
        """Configure Streamlit page settings"""
        st.set_page_config(
            page_title="BFScript IDE",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
    
    def setup_session_state(self):
        """Initialize session state variables"""
        if 'bfs_code' not in st.session_state:
            st.session_state.bfs_code = self.get_default_code()
        if 'compiled_bf' not in st.session_state:
            st.session_state.compiled_bf = ""
        if 'execution_output' not in st.session_state:
            st.session_state.execution_output = ""
        if 'last_error' not in st.session_state:
            st.session_state.last_error = ""
        if 'runtime_input' not in st.session_state:
            st.session_state.runtime_input = ""
        if 'compilation_info' not in st.session_state:
            st.session_state.compilation_info = ""
    
    def get_default_code(self):
        """Return default BFScript code"""
        return '''// Hello World in BFScript
output('H');
output('e');
output('l');
output('l');
output('o');
output(' ');
output('W');
output('o');
output('r');
output('l');
output('d');
output('!');
output('\\n');'''
    
    def get_config(self):
        """Get configuration with defaults"""
        return {
            'memory_size': 30000,
            'cell_bits': 32,
            'max_time': 5.0,
            'temp_cell_pool_size': 20,
            'auto_optimize': True,
            'program_input': ""
        }
    
    def compile_code(self, code: str, config: dict):
        """Compile BFScript code only"""
        st.session_state.last_error = ""
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.bfs', delete=False) as f:
                f.write(code)
                temp_path = f.name
            
            try:
                # Capture both stdout and stderr for compilation errors
                old_stdout = sys.stdout
                old_stderr = sys.stderr
                captured_stdout = io.StringIO()
                captured_stderr = io.StringIO()
                sys.stdout = captured_stdout
                sys.stderr = captured_stderr
                
                try:
                    # Compile with auto-optimization
                    compiler = BrainfuckScriptCompiler(temp_cell_pool_size=config['temp_cell_pool_size'])
                    bf_code = compiler.compile(temp_path)
                    
                    # Auto-optimize if enabled
                    if config['auto_optimize'] and bf_code and compiler.memory_manager.max_temp < len(compiler.temp_cell_pool_indices):
                        optimal_compiler = BrainfuckScriptCompiler(temp_cell_pool_size=compiler.memory_manager.max_temp)
                        bf_code = optimal_compiler.compile(temp_path)
                finally:
                    sys.stdout = old_stdout
                    sys.stderr = old_stderr
                
                # Capture any compilation messages
                compilation_output = captured_stdout.getvalue() + captured_stderr.getvalue()
                
                if not bf_code:
                    if compilation_output.strip():
                        st.session_state.last_error = compilation_output.strip()
                    else:
                        st.session_state.last_error = "Compilation failed - unknown error"
                    return False
                
                st.session_state.compiled_bf = bf_code
                # Store any compilation warnings/info
                if compilation_output.strip() and "error" not in compilation_output.lower():
                    st.session_state.compilation_info = compilation_output.strip()
                else:
                    st.session_state.compilation_info = ""
                return True
                
            finally:
                os.unlink(temp_path)
                
        except Exception as e:
            st.session_state.last_error = str(e)
            return False
    
    def run_code(self, config: dict):
        """Run already compiled BFScript code"""
        if not st.session_state.compiled_bf:
            st.session_state.last_error = "No compiled code available. Please compile first."
            return False
            
        st.session_state.last_error = ""
        st.session_state.execution_output = ""
        
        try:
            # Execute the compiled code
            interpreter = BFInterpreter(
                code=st.session_state.compiled_bf,
                memory_size=config['memory_size'],
                cell_bits=config['cell_bits'],
                initial_input=st.session_state.runtime_input,
                max_execution_time=config['max_time']
            )
            
            interpreter.run()
            st.session_state.execution_output = interpreter.get_output()
            return True
            
        except Exception as e:
            st.session_state.last_error = str(e)
            return False
    
    def compile_and_run(self, code: str, config: dict):
        """Compile and execute BFScript code"""
        if self.compile_code(code, config):
            return self.run_code(config)
        return False
    
    def create_settings_content(self):
        """Create settings interface content"""
        st.markdown("### Compiler Settings")
        
        temp_cell_pool_size = st.slider(
            "Temp Cell Pool Size",
            min_value=5,
            max_value=50,
            value=self.get_session_config('temp_cell_pool_size', 20)
        )
        
        auto_optimize = st.checkbox(
            "Auto-optimize Cell Pool",
            value=self.get_session_config('auto_optimize', True)
        )
        
        st.markdown("### Interpreter Settings")
        
        memory_size = st.selectbox(
            "Memory Size",
            options=[1000, 5000, 10000, 30000, 60000],
            index=[1000, 5000, 10000, 30000, 60000].index(self.get_session_config('memory_size', 30000))
        )
        
        cell_bits = st.selectbox(
            "Cell Size (bits)",
            options=[8, 16, 32, 64],
            index=[8, 16, 32, 64].index(self.get_session_config('cell_bits', 32))
        )
        
        max_time = st.number_input(
            "Max Execution Time (seconds)",
            min_value=0.1,
            max_value=60.0,
            value=self.get_session_config('max_time', 5.0),
            step=0.1
        )
        
        # Update session state
        for key, value in {
            'memory_size': memory_size,
            'cell_bits': cell_bits,
            'max_time': max_time,
            'temp_cell_pool_size': temp_cell_pool_size,
            'auto_optimize': auto_optimize
        }.items():
            st.session_state[f"config_{key}"] = value
    
    def get_session_config(self, key, default):
        """Get config value from session state or return default"""
        session_key = f"config_{key}"
        return st.session_state.get(session_key, default)
    
    def run(self):
        """Main application entry point"""
        # Add custom CSS and keyboard shortcuts
        st.markdown("""
        <style>
        /* Panel styling */
        .main-panel {
            padding: 20px;
            height: 100vh;
        }
        
        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
        }
        
        .stTabs [data-baseweb="tab"] {
            background-color: #f0f2f6 !important;
            color: #262730 !important;
            border-radius: 4px 4px 0px 0px;
            padding: 10px 20px;
            font-weight: 500;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #ffffff !important;
            color: #262730 !important;
            border-bottom: 2px solid #1f77b4 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.title("BFScript IDE")
        
        # Create two-panel layout
        left_panel, right_panel = st.columns([1, 1], gap="medium")
        
        # Get configuration
        config = self.get_config()
        
        # LEFT PANEL - Code Editor
        with left_panel:
            st.markdown("### Code Editor")
            
            # Use code_editor with proper state management
            response_dict = code_editor(
                code=st.session_state.bfs_code,
                lang="c_cpp",  # C/C++ syntax highlighting - perfect for BFScript
                theme="dark",
                height=[19, 30],  # min, max rows
                response_mode="debounce",  # Better performance for real-time updates
                options={
                    "wrap": True, 
                    "showLineNumbers": True,
                    "enableBasicAutocompletion": True,
                    "enableLiveAutocompletion": True,
                    "enableSnippets": True,
                    "highlightActiveLine": True,
                    "tabSize": 4
                },
                buttons=[
                    {
                        "name": "Copy",
                        "feather": "Copy",
                        "hasText": True,
                        "alwaysOn": True,
                        "commands": ["copyAll"],
                        "style": {"top": "0.46rem", "right": "0.4rem"}
                    }
                ]
            )
            
            # Store the current editor content - use editor content if available, fallback to session state
            current_editor_code = response_dict.get('text', '') or st.session_state.bfs_code
        
        # RIGHT PANEL - Tabbed Interface
        with right_panel:
            debugger_tab, brainfuck_tab, settings_tab = st.tabs(["Debugger", "Brainfuck", "Settings"])
            
            # DEBUGGER TAB
            with debugger_tab:
                st.markdown("### Runtime Input")
                st.session_state.runtime_input = st.text_input(
                    "Input for your program:",
                    value=st.session_state.runtime_input,
                    help="Input string that will be fed to your program when it uses input commands"
                )
                
                st.markdown("### Controls")
                if st.button("▶️ Run Code", type="primary", use_container_width=True):
                    # Always update session state with current editor content when running
                    if current_editor_code:
                        st.session_state.bfs_code = current_editor_code
                    if current_editor_code.strip():
                        with st.spinner("Compiling and running..."):
                            success = self.compile_and_run(current_editor_code, config)
                        if success:
                            st.success("Execution completed!")
                        st.rerun()
                    else:
                        st.warning("Enter some code first!")
                
                st.markdown("### Output")
                if st.session_state.last_error:
                    st.error("**Compilation/Runtime Error:**")
                    st.code(st.session_state.last_error, language=None)
                elif st.session_state.execution_output:
                    st.success("**Program Output:**")
                    st.code(st.session_state.execution_output, language=None)
                    if st.session_state.compilation_info:
                        with st.expander("ℹ️ Compilation Info"):
                            st.text(st.session_state.compilation_info)
                else:
                    st.info("Run your code to see output here")
            
            # BRAINFUCK TAB
            with brainfuck_tab:
                st.markdown("### Compiled Code")
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("🔧 Compile", use_container_width=True):
                        # Always update session state with current editor content when compiling
                        if current_editor_code:
                            st.session_state.bfs_code = current_editor_code
                        if current_editor_code.strip():
                            with st.spinner("Compiling..."):
                                success = self.compile_code(current_editor_code, config)
                            if success:
                                st.success("Compilation successful!")
                            st.rerun()
                        else:
                            st.warning("Enter some code first!")
                
                with col2:
                    if st.button("📋 Copy", use_container_width=True, disabled=not st.session_state.compiled_bf):
                        if st.session_state.compiled_bf:
                            try:
                                pyperclip.copy(st.session_state.compiled_bf)
                                st.success("Copied to clipboard!")
                            except:
                                st.warning("Copy to clipboard not available. Please select and copy manually.")
                
                if st.session_state.compiled_bf:
                    st.text_area(
                        "Generated Brainfuck:",
                        value=st.session_state.compiled_bf,
                        height=400,
                        help="The compiled Brainfuck code",
                        key="bf_output",
                        label_visibility="collapsed"
                    )
                    
                    # Stats
                    total_chars = len(st.session_state.compiled_bf)
                    command_chars = sum(1 for c in st.session_state.compiled_bf if c in '+-<>.,[]')
                    st.caption(f"📊 {total_chars} total characters, {command_chars} BF commands")
                else:
                    st.info("Compile your code to see the generated Brainfuck here")
            
            # SETTINGS TAB
            with settings_tab:
                self.create_settings_content()
    
    # Override config if settings have been modified
    def get_config(self):
        """Get configuration with user settings if available"""
        config = {
            'memory_size': 30000,
            'cell_bits': 32,
            'max_time': 5.0,
            'temp_cell_pool_size': 20,
            'auto_optimize': True,
            'program_input': ""
        }
        
        # Override with session state if available
        for key in config.keys():
            session_key = f"config_{key}"
            if session_key in st.session_state:
                config[key] = st.session_state[session_key]
        
        return config


def main():
    """Main entry point"""
    app = BFScriptWebApp()
    app.run()


if __name__ == "__main__":
    main()