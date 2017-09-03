import sys

output = sys.argv[1]

if output.count("hello from generated job") != 2:
    raise Exception("'hello from generated job' not found")

if output.count("[infrabox] Job finished finished successfully") != 2:
    raise Exception("job did not finish successfully")
