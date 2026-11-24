"""Create demo-only credentials; never inspect or reuse another project's secrets."""
from pathlib import Path
import secrets

root = Path(__file__).resolve().parents[1]
path = root / ".env"
if not path.exists():
    content = (root / ".env.example").read_text()
    content = content.replace("replace-with-random-local-secret", secrets.token_hex(32))
    content = content.replace("replace-with-random-electric-secret", secrets.token_hex(32))
    path.write_text(content)
    path.chmod(0o600)
    print("Created .env with local demo secrets")
else:
    print("Using existing .env")
