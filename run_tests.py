# Cursor: Run backend test suite in isolated env, save results

import subprocess, datetime, os

today = datetime.date.today().strftime("%Y-%m-%d")
os.makedirs("test_results", exist_ok=True)
result_file = f"test_results/{today}.md"

cmd = """
docker compose up -d db redis &&
docker compose run --rm web sh -c "
  pip install pytest pytest-asyncio aiosqlite PyJWT &&
  ENV=test ENVIRONMENT=test python -m pytest backend/tests/ -v --maxfail=3 --disable-warnings
" &&
docker compose down
"""

process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
output, _ = process.communicate()

with open(result_file, "w") as f:
    f.write(f"# Test Results — {today}\n\n")
    f.write("```\n")
    f.write(output)
    f.write("\n```")

print(f"✅ Test run complete — results saved to {result_file}")
