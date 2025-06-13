import os, sys

# Dynamic resolver pathing for critical modules
module_paths = {
    "grpc": os.path.expanduser("~/mem0_fusion_genesis/envs/grpc_env/Lib/site-packages"),
    "torch": os.path.expanduser("~/mem0_fusion_genesis/envs/torch_env/Lib/site-packages"),
    "lang": os.path.expanduser("~/mem0_fusion_genesis/envs/lang_env/Lib/site-packages"),
}

for key, path in module_paths.items():
    if os.path.isdir(path) and path not in sys.path:
        sys.path.insert(0, path)
