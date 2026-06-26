import json
import os

log_path = r'C:\Users\Administrateur\.gemini\antigravity\brain\cf3e5cff-81dc-4c6c-981e-72d7e868b41e\.system_generated\logs\overview.txt'
out_path = r'c:\PROJETL3\CantineDjango\frontend\dashboard-cuisinier-step182.html'

with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        if '"step_index":182' in line:
            data = json.loads(line)
            code = data['tool_calls'][0]['args']['CodeContent']
            with open(out_path, 'w', encoding='utf-8') as out_f:
                out_f.write(code)
            print("Successfully extracted step 182 code!")
            break
