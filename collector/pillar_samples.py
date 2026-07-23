"""
Pillar Samples for Eli (4B) Remediation
"""

PILLAR_SAMPLES = [
    {
        "instruction": "Implement a clean LRU Cache class in Python with O(1) time complexity for get and put.",
        "output": "```python\nfrom collections import OrderedDict\n\nclass LRUCache:\n    def __init__(self, capacity: int):\n        self.cache = OrderedDict()\n        self.capacity = capacity\n\n    def get(self, key: int) -> int:\n        if key not in self.cache:\n            return -1\n        self.cache.move_to_end(key)\n        return self.cache[key]\n\n    def put(self, key: int, value: int) -> None:\n        if key in self.cache:\n            self.cache.move_to_end(key)\n        self.cache[key] = value\n        if len(self.cache) > self.capacity:\n            self.cache.popitem(last=False)\n```",
        "lang": "py"
    },
    {
        "instruction": "Write an idiomatic Go HTTP handler with JSON request body validation and graceful error responses.",
        "output": "```go\npackage main\n\nimport (\n\t\"encoding/json\"\n\t\"net/http\"\n)\n\ntype UserRequest struct {\n\tUsername string `json:\"username\"`\n\tEmail    string `json:\"email\"`\n}\n\nfunc CreateUserHandler(w http.ResponseWriter, r *http.Request) {\n\tif r.Method != http.MethodPost {\n\t\thttp.Error(w, \"Method not allowed\", http.StatusMethodNotAllowed)\n\t\treturn\n\t}\n\n\tvar req UserRequest\n\tif err := json.NewDecoder(r.Body).Decode(&req); err != nil {\n\t\thttp.Error(w, \"Invalid JSON payload\", http.StatusBadRequest)\n\t\treturn\n\t}\n\n\tw.Header().Set(\"Content-Type\", \"application/json\")\n\tw.WriteHeader(http.StatusCreated)\n\tjson.NewEncoder(w).Encode(map[string]string{\"status\": \"created\", \"username\": req.Username})\n}\n```",
        "lang": "go"
    },
    {
        "instruction": "Create a type-safe TypeScript debounce function utility with support for leading/trailing execution.",
        "output": "```typescript\nexport function debounce<T extends (...args: any[]) => any>(\n  fn: T,\n  delayMs: number\n): (...args: Parameters<T>) => void {\n  let timeoutId: ReturnType<typeof setTimeout> | null = null;\n\n  return function (...args: Parameters<T>) {\n    if (timeoutId) clearTimeout(timeoutId);\n    timeoutId = setTimeout(() => {\n      fn(...args);\n    }, delayMs);\n  };\n}\n```",
        "lang": "ts"
    }
]
