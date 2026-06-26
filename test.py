import json

log_path = r'C:\Users\Administrateur\.gemini\antigravity\brain\cf3e5cff-81dc-4c6c-981e-72d7e868b41e\.system_generated\logs\overview.txt'
with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        if '"step_index":182' in line:
            data = json.loads(line)
            code = data['tool_calls'][0]['args']['CodeContent']
            print("240 to 280:", repr(code[240:280]))
            break
