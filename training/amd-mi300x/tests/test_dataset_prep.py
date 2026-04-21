import json
import tempfile
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from prepare_samara_dataset import prepare_samara_dataset

def test_prepare_samara_dataset():
    input_data = {
        "sessions": [{
            "participant_id": "P001",
            "study_group": "A",
            "day_number": 1,
            "messages": [
                {"role": "user", "content": "Hi"},
                {"role": "assistant", "content": "Hello!"}
            ]
        }]
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(input_data, f)
        input_path = f.name
    
    output_path = tempfile.mktemp(suffix='.jsonl')
    prepare_samara_dataset(input_path, output_path)
    
    with open(output_path, 'r') as f:
        lines = f.readlines()
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["input"] == "Hi"
        assert data["output"] == "Hello!"
    
    os.unlink(input_path)
    os.unlink(output_path)
