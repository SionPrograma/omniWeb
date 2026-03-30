import psutil
import platform
import subprocess

print('--- SYSTEM INFO ---')
print(f'System: {platform.system()} {platform.release()}')
print(f'Machine: {platform.machine()}')
print(f'Processor: {platform.processor()}')
print(f'RAM Total: {psutil.virtual_memory().total / (1024**3):.2f} GB')
print(f'RAM Available: {psutil.virtual_memory().available / (1024**3):.2f} GB')

print('\n--- OLLAMA CHECK ---')
try:
    # Use shell=True for windows to locate ollama in PATH if it's there
    ollama_vers = subprocess.check_output(['ollama', '--version'], text=True, shell=True).strip()
    print('Ollama Version:', ollama_vers)
    
    ollama_list = subprocess.check_output(['ollama', 'list'], text=True, shell=True).strip()
    print('Installed Models:')
    print(ollama_list)
except Exception as e:
    print('Ollama not found or error:', e)
